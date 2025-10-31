import RPi.GPIO as GPIO
import time
print("loading baseplate drivers...")

GPIO.setmode(GPIO.BCM)


class focusStepper():
    def __init__(self, delay=0.001, GPIO_pins=(12, 16, 20, 21), debug=True):
        self.in1, self.in2, self.in3, self.in4 = GPIO_pins
        self.step_delay = delay
        self.step_per_revolution = (360/1.8)*2 #NEMA's datasheet says one revolution is 200 steps.
        #since we are using microstepping, we need to times 2.
        
        self.step_sequence = [ #half step
            (1,0,0,0),
            (1,1,0,0),
            (0,1,0,0),
            (0,1,1,0),
            (0,0,1,0),
            (0,0,1,1),
            (0,0,0,1),
            (1,0,0,1),
        ]
        self.num_steps_in_sequence = len(self.step_sequence)
        self.position = 0
        self.sequence_index = 0

        for pin in GPIO_pins:
            GPIO.setup(pin,GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
    def _set_step(self, values):
        GPIO.output(self.in1, values[0])
        GPIO.output(self.in2, values[1])
        GPIO.output(self.in3, values[2])
        GPIO.output(self.in4, values[3])
        
    def goTo(self, microSteps):
        steps_to_move = microSteps-self.position
        direction = 1 if steps_to_move>0 else -1
        
        for _ in range(abs(steps_to_move)):
            self.sequence_index = (self.sequence_index+direction)% self.num_steps_in_sequence
            self._set_step(self.step_sequence[self.sequence_index])
            time.sleep(self.step_delay)
        
        self.position = microSteps
        self._set_step((0,0,0,0))
        
    def start(self):
        self.position=0
        
    def end(self):
        GPIO.cleanup()
        

class baseplateDrivers():
    def __init__(self, delay=0.001, GPIO_pins=[(17,27,22,10),(5,6,13,26)], debug=True):
        self.in1, self.in2, self.in3, self.in4 = GPIO_pins[0]
        self.in5, self.in6, self.in7, self.in8 = GPIO_pins[1]
        self.step_delay = delay
        
        self.step_sequence = [ #half step
            (1,0,0,0),
            (1,1,0,0),
            (0,1,0,0),
            (0,1,1,0),
            (0,0,1,0),
            (0,0,1,1),
            (0,0,0,1),
            (1,0,0,1),
        ]
        
        self.num_steps_in_sequence = len(self.step_sequence)
        self.position1 = 0
        self.sequence_index1 = 0
        self.position2 = 0
        self.sequence_index2 = 0
        
        for pins in GPIO_pins:
            for pin in pins:
                GPIO.setup(pin,GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
    
    def _set_step(self, motor:int, values):
        if motor==1:
            GPIO.output(self.in1, values[0])
            GPIO.output(self.in2, values[1])
            GPIO.output(self.in3, values[2])
            GPIO.output(self.in4, values[3])
        else:
            GPIO.output(self.in5, values[0])
            GPIO.output(self.in6, values[1])
            GPIO.output(self.in7, values[2])
            GPIO.output(self.in8, values[3])
      
    def runMotor1(self, microSteps):
        steps_to_move = microSteps-self.position1
        direction = 1 if steps_to_move>0 else -1
        
        for _ in range(abs(steps_to_move)):
            self.sequence_index1 = (self.sequence_index1+direction)% self.num_steps_in_sequence
            self._set_step(1, self.step_sequence[self.sequence_index1])
            time.sleep(self.step_delay)
        
        self.position1 = microSteps
        self._set_step(1, (0,0,0,0))
        
    def runMotor2(self, microSteps):
        steps_to_move = microSteps-self.position2
        direction = 1 if steps_to_move>0 else -1
        
        for _ in range(abs(steps_to_move)):
            self.sequence_index2 = (self.sequence_index2+direction)% self.num_steps_in_sequence
            self._set_step(2, self.step_sequence[self.sequence_index2])
            time.sleep(self.step_delay)
        
        self.position2 = microSteps
        self._set_step(2, (0,0,0,0)) 
               
    def end(self):
        GPIO.cleanup()
        
    def start(self):
        self.position1=0
        self.position2=0
        
if __name__ == "__main__":
    print("initialising FOCUS motors!")
    focus = focusStepper(GPIO_pins=(12,16,20,21)) #4.7 rotations to go full range
    #revo per step is 400
    full_cycle = int(focus.step_per_revolution*4.7)
    focus.start()
    focus.goTo(full_cycle)
    time.sleep(3)
    focus.goTo(0)
    
    
    time.sleep(10)
    
    print("baseplate drivers!")

    base = baseplateDrivers(delay=0.003, GPIO_pins=[(10,27,22,17),(26,6,13,5)])
    base.start()
    
    base.runMotor1(5200)
    base.runMotor2(400)
    time.sleep(3)    
    base.runMotor1(0)
    base.runMotor2(0)
    
    base.end()
    focus.end()
    
    print("finish!")
