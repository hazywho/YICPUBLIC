from tmc_driver import tmc_2209

print("loading baseplate drivers... ()")

class focusStepper():
    def __init__(self, acceleration=1000, max_speed=250, control_pin=21, GPIO_pins=(16,20), port="/dev/ttyAMA0", debug=True):
        self.myMotor = tmc_2209.Tmc2209(tmc_2209.TmcEnableControlPin(control_pin), 
                                        tmc_2209.TmcMotionControlStepDir(*GPIO_pins), 
                                        tmc_2209.TmcComUart(port), 
                                        loglevel=tmc_2209.Loglevel.DEBUG)
        if debug:
            self.myMotor.tmc_logger.loglevel=tmc_2209.Loglevel.DEBUG
        self.myMotor.movement_abs_rel = tmc_2209.MovementAbsRel.ABSOLUTE
        self.myMotor.set_direction_reg(False)
        self.myMotor.set_current(300)
        self.myMotor.set_interpolation(True)
        self.myMotor.set_spreadcycle(False)
        self.myMotor.set_microstepping_resolution(128)
        self.myMotor.set_internal_rsense(False)
        self.myMotor.acceleration_fullstep = acceleration
        self.myMotor.max_speed_fullstep = max_speed
                
    def goTo(self, microSteps):
        self.myMotor.run_to_position_steps(microSteps) #move to absolute position 400 (µsteps)
        
    def end(self):
        self.myMotor.set_motor_enabled(False)
        
    def start(self):
        self.myMotor.set_motor_enabled(True)

class baseplateDrivers():
    def __init__(self, acceleration=1000, max_speed=250, control_pin=[21,22], GPIO_pins=[(18,22),(17,21)], port=["/dev/ttyAMA0", "/dev/ttyAMA1"], debug=True):
        self.tmc1 = tmc_2209.Tmc2209(tmc_2209.TmcEnableControlPin(control_pin[0]), 
                                        tmc_2209.TmcMotionControlStepDir(*(GPIO_pins[0])), 
                                        tmc_2209.TmcComUart(port[0]), 
                                        driver_address=0)
        
        self.tmc2 = tmc_2209.Tmc2209(tmc_2209.TmcEnableControlPin(control_pin[1]), 
                                        tmc_2209.TmcMotionControlStepDir(*(GPIO_pins[1])), 
                                        tmc_2209.TmcComUart(port[1]), 
                                        driver_address=1)
        
        if debug:
            self.tmc1.tmc_logger.loglevel=tmc_2209.Loglevel.DEBUG
            self.tmc2.tmc_logger.loglevel=tmc_2209.Loglevel.DEBUG
            
        self.tmc1.movement_abs_rel = tmc_2209.MovementAbsRel.ABSOLUTE
        self.tmc2.movement_abs_rel = tmc_2209.MovementAbsRel.ABSOLUTE
        
        print("reading from drivers...")
        print(self.tmc1.read_ioin())
        print(self.tmc2.read_ioin())
        
        #settings for TMC1
        self.tmc1.set_direction_reg(False)
        self.tmc1.set_current(300)
        self.tmc1.set_interpolation(True)
        self.tmc1.set_spreadcycle(False)
        self.tmc1.set_microstepping_resolution(128)
        self.tmc1.set_internal_rsense(False)
        self.tmc1.acceleration_fullstep = acceleration
        self.tmc1.max_speed_fullstep = max_speed
           
        #settings for tmc2     
        self.tmc2.set_direction_reg(False)
        self.tmc2.set_current(300)
        self.tmc2.set_interpolation(True)
        self.tmc2.set_spreadcycle(False)
        self.tmc2.set_microstepping_resolution(128)
        self.tmc2.set_internal_rsense(False)
        self.tmc2.acceleration_fullstep = acceleration
        self.tmc2.max_speed_fullstep = max_speed
        
    def runMotor1(self, microSteps):
        self.tmc1.run_to_position_steps(microSteps) #move to absolute position 400 (µsteps)
        
    def runMotor2(self, microSteps):
        self.tmc2.run_to_position_steps(microSteps) #move to absolute position 400 (µsteps)
        
    def end(self):
        self.tmc1.set_motor_enabled(False)
        self.tmc2.set_motor_enabled(False)
        
    def start(self):
        self.tmc1.set_motor_enabled(True)
        self.tmc2.set_motor_enabled(True)
        