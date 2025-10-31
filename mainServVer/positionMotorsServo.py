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
    def __init__(self, delay=0.3, GPIO_pins=(13,19), freq=50, dutyCycleMin=2.5, dutyCycleMax=12.5):
        self.step_delay = delay
        
        self.serv1 = GPIO_pins[0]
        self.serv2 = GPIO_pins[1]
        
        self.PWM_FREQ=freq
        self.DUTY_CYCLE_MIN = dutyCycleMin # Approx. 0 degrees
        self.DUTY_CYCLE_MAX = dutyCycleMax # Approx. 180 degrees
        
        GPIO.setup(self.serv1, GPIO.OUT)
        GPIO.setup(self.serv2, GPIO.OUT)
        self.pwm_s1 = GPIO.PWM(self.serv1, self.PWM_FREQ)
        self.pwm_s2 = GPIO.PWM(self.serv2, self.PWM_FREQ)
    
    def _set_angle(self, motor, angle):
        angle = max(0, min(180, angle))
        # Map the angle (0-180) to the duty cycle (2.5-12.5)
        duty_cycle = self.DUTY_CYCLE_MIN + (angle / 180) * (self.DUTY_CYCLE_MAX - self.DUTY_CYCLE_MIN)
        motor.ChangeDutyCycle(duty_cycle)
        time.sleep(self.step_delay) # Give the servo time to move
      
    def runMotor1(self, microSteps):
        self._set_angle(self.pwm_s1, microSteps)
        
    def runMotor2(self, microSteps):
        self._set_angle(self.pwm_s2, microSteps)
               
    def end(self):
        GPIO.cleanup()
        
    def start(self):
        self.pwm_s1.start(0) # Start PWM with a duty cycle of 0
        self.pwm_s2.start(0) # Start PWM with a duty cycle of 0
        
        
if __name__ == "__main__":

    print("baseplate drivers!")

    base = baseplateDrivers(delay=0.01, GPIO_pins=(13,19))
    base.start()
    base.runMotor1(90)
    base.runMotor2(90)
    
    base.end()
    # focus.end()
    
    print("finish!")
