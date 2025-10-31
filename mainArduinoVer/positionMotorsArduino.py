from TMC_2209.TMC_2209_StepperDriver import *
import RPi.GPIO as GPIO
import time
import pyfirmata2
print("loading baseplate drivers...")

GPIO.setmode(GPIO.BCM)

class focusStepper():
    def __init__(self, GPIO_pins=(21, 16, 20), debug=True, port="/dev/ttyAMA0", microsteps=8, currentMA=500, interpolate=True, acceleration = 2000, maxSpeed = 1000):
        self.step_per_revolution = (360/1.8)*microsteps #NEMA's datasheet says one revolution is 200 steps.
        #since we are using microstepping, we need to times 2.
        
        self.tmc = TMC_2209(GPIO_pins[0], GPIO_pins[1], GPIO_pins[2], serialport=port)
        self.tmc.set_direction_reg(True)
        self.tmc.set_current(currentMA)
        self.tmc.set_interpolation(interpolate)
        self.tmc.set_spreadcycle(True)
        self.tmc.set_microstepping_resolution(microsteps)
        self.tmc.set_internal_rsense(False)
        self.tmc.set_acceleration(acceleration)
        self.tmc.set_max_speed(maxSpeed)
        
    def goTo(self, microSteps):
        self.tmc.run_to_position_steps(microSteps)
        
    def start(self):
        self.tmc.set_motor_enabled(True)
        self.tmc.run_to_position_steps(0)
        
    def end(self):
        self.tmc.set_motor_enabled(False)
        

class baseplateDrivers():
    def __init__(self, delay=0.3, GPIO_pins=(10,11), port = "/dev/ttyUSB0"):
        self.arduino = pyfirmata2.Arduino(port)
        
        self.pwm_s1 = self.arduino.get_pin(f"d:{GPIO_pins[0]}:s")
        self.pwm_s2 = self.arduino.get_pin(f"d:{GPIO_pins[1]}:s")
        
        self.step_delay=delay
    
    def _set_angle(self, motor, angle):
        angle = max(0, min(180, angle))
        # Map the angle (0-180) to the duty cycle (2.5-12.5)
        motor.write(angle)

        time.sleep(self.step_delay) # Give the servo time to move
      
    def runMotor1(self, microSteps):
        self._set_angle(self.pwm_s1, microSteps)
        
    def runMotor2(self, microSteps):
        self._set_angle(self.pwm_s2, microSteps)
               
    def end(self):
        self.arduino.exit()
        
    def start(self):
        self.pwm_s1.write(0) # Start PWM with a duty cycle of 0
        time.sleep(1)
        self.pwm_s2.write(0) # Start PWM with a duty cycle of 0
        time.sleep(1)
        
        
if __name__ == "__main__":

    # print("baseplate drivers!")

    # base = baseplateDrivers(delay=0.01, GPIO_pins=(10,11))
    # base.start()
    # time.sleep(2)
    # base.runMotor1(90)
    # time.sleep(1)
    # base.runMotor2(90)
    # time.sleep(2)
    # base.runMotor1(10)
    # time.sleep(1)
    # base.runMotor2(10)
    # time.sleep(1)

    
    # focus.end()
    
    focusMotor = focusStepper()
    focusMotor.start()
    focusMotor.goTo(600)
    time.sleep(1)
    focusMotor.goTo(0)
    focusMotor.end()
    base.end()
    print("finish!")
