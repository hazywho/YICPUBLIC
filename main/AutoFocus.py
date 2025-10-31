import cv2
from positionMotors import baseplateDrivers, focusStepper
import dotenv
from AI import client
from ultralytics import YOLO

class main():
    def __init__(self, slideArea: int = 400, waterData: dict = {"eee"}, camPort:int = 0):
        #setup save and output paths
        self.imgPath = "main/images"
        self.outputPath = "main/output"
        self.env=".env"
        
        #setup motors
        self.debug=True
        #setup focusMotor
        self.max_speed = 250 #try to microstep
        self.controlPin=21
        self.acceleration=1000
        self.GPIO_pins=(15,18) #only specify 2
        self.port = "/dev/ttyAMA0"
        self.focusMotor = focusStepper(acceleration=self.acceleration, max_speed=self.max_speed, control_pin=self.controlPin,
                                       GPIO_pins=self.GPIO_pins, port=self.port, debug=self.debug)
        self.focusMotor.start()
        self.focusMotor.goTo(0) #go to default position
        #setup baseplateDrivers
        self.baseplate_max_speed = 250 #try to microstep
        self.baseplate_controlPin=[21,23] #RMB CHANGE
        self.baseplate_acceleration=1000
        self.baseplate_GPIO_pins=[(15,18),(17,19)] #NEED TO CHANGE WHEN FINALISED HARDWARE
        self.baseplate_port = ["/dev/ttyAMA0", "/dev/ttyAMA1"]
        self.baseplate = baseplateDrivers(acceleration=self.baseplate_acceleration,max_speed=self.baseplate_max_speed,control_pin=self.baseplate_controlPin,
                                          GPIO_pins=self.baseplate_GPIO_pins,port=self.baseplate_port,debug=self.debug)  
        self.baseplate.start()
        self.baseplate.runMotor1(0) #goto defualt position
        self.baseplate.runMotor2(0)     
        
        #setup camera
        self.camera=cv2.VideoCapture(camPort)
        self.calibrated=False
        self.slideArea=slideArea #in cm^2
        self.waterData=waterData #WILL NEED TO ADD INTERFACE TO WATER DATA.
        
        #setup GEMINI API
        self.API_KEY=dotenv.get_key(self.env,"GEMENI_KEY")
        self.thinkingPrompt = """
        You are Bob, a senior plankton analyst and marine ecologist. Your primary role is to analyze water sample data and generate concise, professional ecological summary reports. You are known for your keen eye and ability to connect water quality metrics with plankton population dynamics.
        You will receive data for each new sample analysis. The data will be structured as follows:
        
        --- START OF DATA ---
        **Images:**
        [Image 1]
        [Image 2]
        ...

        {
            "plankton_data":{
                "plankton_name1":{
                    "density":0.5,
                    "amount":400
                },
                "plankton_name2":{
                    "density":0.5,
                    "amount":200
                }
            }
            "water_sample_data":{
                "pH": 7,
                "Dissolved Oxygen": 3.4,
                "Biochemical Oxygen Demand": 2.7,
                "Chemical Oxygen Demand": 23,
                "Nitrogen (ammonia)": 8.62
            }
        }

        --- END OF DATA ---

        Your task is to analyze all the provided data and generate a report in the following format:

        ---
        **Ecological Summary Report**

        **Date of Analysis:** September 10, 2025
        **Location:** Jelutong, Penang

        **1. Executive Summary:**
        (Provide a 2-3 sentence overview of the water sample's condition and the dominant plankton species found. Mention any immediate concerns.)

        **2. Plankton Population Analysis:**

        Dominant Species: (List the top 2-3 plankton species by amount and density.)

        Biodiversity Index: (State whether the diversity is High, Moderate, or Low based on the number of different species identified.)

        Key Observations: (Briefly describe what you see in the images. For example: "Images show a high concentration of copepods with some visible diatom chains. No significant algal blooms are apparent.")

        **3. Water Quality Assessment:**
        (Briefly analyze the provided water quality metrics. Compare them to typical healthy ranges (e.g., pH 6.5-8.5, low BOD/COD). State whether the conditions are favorable, stressed, or poor for diverse aquatic life.)

        **4. Conclusion & Recommendation:**
        (Conclude with an overall assessment. For example: "The sample indicates a moderately healthy ecosystem, though the slightly elevated BOD warrants monitoring." or "The low biodiversity and poor water quality suggest a stressed environment requiring further investigation.")
        """ 
        self.client = client(key=self.API_KEY, basePrompt=self.thinkingPrompt) #using gemeni flash name
        
        #setup YOLO
        self.model = YOLO("yolo11n.pt")
        self.names = {} #setup our counter list
        for name in self.model.names.values():
            self.names[name] = 0
        
        print(self.imgPath)
        print(self.outputPath)
      
    def _getVariance(self, img):
        img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(img, cv2.CV_64F).var()
    
    def getBestImg(self, limit=30, minClearVariance = 40): #calibration+img
        try:
            if self.calibrated==True:
                ret, bestImg=self.camera.read()
                variance = self._getVariance(bestImg)
                if variance<minClearVariance:
                    self.calibrated=False
                    return self.getBestImg()
                return (bestImg, variance)
            else: #if its not calibrated it should run the focus loop and get to maximum focus.
                counter=0
                limit=limit
                lastBestVar=0
                self.bestVarPos=0
                steps = 1
                self.bestImg = None
                
                #start loop
                while counter<limit:
                    ret, capturedImage = self.camera.read()
                    variance = self._getVariance(capturedImage)
                    
                    if not ret:
                        print("no image captured!")
                    if variance>lastBestVar:
                        lastBestVar=variance
                        self.bestVarPos=counter
                        self.bestImg=capturedImage.copy() #save pic
                        
                    self.focusMotor.goTo(microSteps=steps*counter) #steps in microsteps
                    cv2.imwrite(f"{self.imgPath}/{counter}_{round(variance,3)}.png", capturedImage)
                    counter+=1
                
                self.focusMotor.goTo(steps*self.bestVarPos) #go back to position of best accuracy
                # self.camera.release() no need anymore cause its gonna run a lot anyways
                cv2.imwrite(f"{self.outputPath}/best.png", self.bestImg) #save down best img as file
                self.calibrated=True
                print("saved best img!")
            return (self.bestImg, lastBestVar)
        except Exception as e:
            print(e)
            self.end()
            return False
        
    def _clearCalibration(self): #reset calibration
        self.calibrated=False
        
    def _createPlanktonData(self, image: list, slideArea : int): #function to create report output from image list. EDIT LATER: train our model first, then get our desired preds
        counter = self.names.copy() # (dict format) this is the count of how many species have now much amount
        for singleImage in image:
            preds = self.model.predict(singleImage, stream=False)
            
            for key in preds[0].boxes.cls:
                name = preds[0].names[int(key)]
                counter[name]+=1 #add count to set species when yolo predicts that it exists in img
        
        plank_dat : dict = {}
        for key in counter:
            plank_dat[key]={
                "density":counter[key]/slideArea,
                "amount":counter[key]
            }
           
        return plank_dat #calculates plankton data only.
    
    def getGemeniResponse(self, data: list, images: list): #get gemeni response
        response = self.client.getResponse(images=images, prompt=data)
        return response
    
    def _createWaterData(self, waterData: dict):
        #in case we need any additional things to edit.
        return waterData
    
    def moveAroundAndProcess(self,steps=1,x_range=5,y_range=5): #n+havent been used. Use it next update.
        listImg = []
        listAnnotatedImg = []
        for x in range(y_range):
            for y in range(x_range):
                self.baseplate.runMotor1(microSteps=steps*y) #set to y pos
                img, variance = self.getBestImg()
                listImg.append(img)
                cv2.putText(img, "{}: {:.2f}".format("ClearImage", variance), (10, 30), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 255), 3)
                listAnnotatedImg.append(img)

                print(f"column {y}, row{x}")
                print(f"variance: {variance}")
                
            self.baseplate.runMotor2(microSteps=steps*x) #set to x pos
        
        planktonDataJSON = self._createPlanktonData(listImg, slideArea=self.slideArea)
        waterDataJSON = self._createWaterData(self.waterData)
        dataJSON = {"plankton_data":planktonDataJSON,
                    "water_sample_data":waterDataJSON}
        response = self.getGemeniResponse(dataJSON)
        
        return response, listImg, listAnnotatedImg
    
    def end(self):
        self.baseplate.end()
        self.focusMotor.end()
        self.camera.release()
        cv2.destroyAllWindows()
        exit()
        
        
if __name__ == "__main__":
    system = main()
    print("taking photo")
    status = system.getBestImg()
    if status:
        response = system.moveAroundAndProcess()
        
        print("AI analysis")
        print(response)
    else:
        print("calibration eror")
        
    system.end()
    