import cv2
from positionMotorsServo import baseplateDrivers, focusStepper
import dotenv
from AI import client
from ultralytics import YOLO
import time
import random
import datetime


class main():
    def __init__(self, slideArea: float = 3.24, waterData: dict = {"eee"}, camPort:int = 0):
        #setup save and output paths
        self.imgPath = "images/"
        self.outputPath = "output/"
        self.env=".env"
        
        #setup focusMotor
        self.focusMotor = focusStepper(GPIO_pins=(21,16,20)) #4.7 rotations to go full range
        self.focusMotor.start()
        #setup baseplateDrivers
        self.baseplate = baseplateDrivers(delay=0.001, GPIO_pins=(19,25))
        self.baseplate.start()
        self.baseplate.runMotor1(0)
        self.baseplate.runMotor2(0)

        #setup camera
        self.camera=cv2.VideoCapture(camPort)
        self.calibrated=False
        self.slideArea=slideArea #in cm^2
        self.waterData=waterData #WILL NEED TO ADD INTERFACE TO WATER DATA.
        
        #setup GEMINI API
        self.API_KEY=dotenv.get_key(self.env,"GEMENI_KEY")

        x = datetime.datetime.now()
        formatted = x.strftime("%d/%m/%Y")
        self.thinkingPrompt = f"""
        You are Bob, a senior plankton analyst and marine ecologist. Your primary role is to analyze water sample data and generate concise, professional ecological summary reports. You are known for your keen eye and ability to connect water quality metrics with plankton population dynamics.
        You will receive data for each new sample analysis. The data will be structured as follows:
        
        --- START OF DATA ---
        **Images:**
        [Image 1]
        [Image 2]
        ...

        {{
            "plankton_data":{{
                "plankton_name1":{{
                    "density":0.5,
                    "amount":400
                }},
                "plankton_name2":{{
                    "density":0.5,
                    "amount":200
                }}
            }}
            "water_sample_data":{{
                "pH": 7,
                "Dissolved Oxygen": 3.4,
                "Biochemical Oxygen Demand": 2.7,
                "Chemical Oxygen Demand": 23,
                "Nitrogen (ammonia)": 8.62
            }}
        }}

        --- END OF DATA ---

        Your task is to analyze all the provided data and generate a report in the following format:

        ---
        **Ecological Summary Report**

        **Date of Analysis:** {formatted}

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
        self.model = YOLO(r"/home/hezy/Downloads/YIC2025-main/YOLO/runs/detect/train/weights/best.pt") #trained model file here!!
        self.names = {} #setup our counter list
        for name in self.model.names.values():
            self.names[name] = 0
        
        print(self.imgPath)
        print(self.outputPath)
      
    def _getVariance(self, img):
        img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(img, cv2.CV_64F).var()
    
    def getBestImg(self, minClearVariance = 0): #calibration+img Changed HEREEE!!!!!!!!! original:40
        try:
            counter=0
            lastBestVar=0
            self.bestVarPos=0
            steps = 1
            self.bestImg = None
            imgList = []
            bigls=[]
            
            if self.calibrated:
                ret, capturedImage = self.camera.read()
                variance = self._getVariance(capturedImage)
                bigls.append(capturedImage)
                if not ret:
                    print("no image captured!")
                if variance<minClearVariance:
                    self._clearCalibration()
                    return self.getBestImg()
                
                cv2.putText(capturedImage, "{}: {:.2f}".format("Clearness: ", variance), (10, 30), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 255), 3)
                imgList.append(capturedImage)
                
                return (capturedImage, variance, imgList, bigls)
            else:
                #start focus loop
                while counter<self.focusMotor.step_per_revolution*1.5:
                    ret, capturedImage = self.camera.read()
                    variance = self._getVariance(capturedImage)
                    bigls.append(capturedImage)
                    if not ret:
                        print("no image captured!")
                    if variance>lastBestVar:
                        lastBestVar=variance
                        self.bestVarPos=counter
                        self.bestImg=capturedImage.copy() #save pic
                    cv2.putText(capturedImage, "{}: {:.2f}".format("Clearness: ", variance), (10, 30), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 255), 3)
                    imgList.append(capturedImage)
                    self.focusMotor.goTo(microSteps=steps*counter) #steps in microsteps
                    # cv2.imwrite(f"{self.imgPath}/{counter}_{round(variance,3)}.png", capturedImage)
                    counter+=5 #interval to move
                    time.sleep(0.3)
                
                self.focusMotor.goTo(self.bestVarPos) #go back to position of best accuracy
                # self.camera.release() no need anymore cause its gonna run a lot anyways
                cv2.imwrite(f"{self.outputPath}/best.png", self.bestImg) #save down best img as file
                self.calibrated=True
                print("saved best img!")
                return (self.bestImg, lastBestVar, imgList, bigls)
        except Exception as e:
            print(e)
            self.end()
            return False
        
    def _clearCalibration(self): #reset calibration
        self.focusMotor.goTo(0)
        self.calibrated=False
        
    def _createPlanktonData(self, image: list, slideArea): #function to create report output from image list. EDIT LATER: train our model first, then get our desired preds
        counter = self.names.copy() # (dict format) this is the count of how many species have now much amount
        slideArea = float(slideArea)
        imageContainsPlanktons=[]
        
        for singleImage in image:
            preds = self.model.predict(singleImage, stream=False)
            # cv2.waitKey(0)
            if len(preds[0].boxes.cls) > 0:
                imageContainsPlanktons.append(singleImage)
                
                for key in preds[0].boxes.cls:
                    name = preds[0].names[int(key)]
                    counter[name]+=1 #add count to set species when yolo predicts that it exists in img
            
        plank_dat : dict = {}
        for key in counter:
            plank_dat[key]={
                "density":float(counter[key])/slideArea, #last changed place here !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                "amount":int(counter[key])
            }
           
        return plank_dat, imageContainsPlanktons #calculates plankton data only.
    
    def getGemeniResponse(self, data: list, images: list, random_sample=False, selection=2): #get gemeni response
        if random_sample and len(images)>=selection:
            images = random.sample(images, selection)
        response = self.client.getResponse(images=images, prompt=data)
        return response
    
    def _createWaterData(self, waterData: dict):
        #in case we need any additional things to edit.
        return waterData
    
    def moveAroundAndProcess(self,x_res=50,y_res=50): #n+havent been used. Use it next update.
        listImg = []
        listAnnotatedImg = []

        #only taking image once since baseplate not work.
        # img, variance , listAnnotatedImg, fullLstImg= self.getBestImg()
        # listImg.append(img)

        limitx = 180
        limity = 180
        resolution = (int(limitx/x_res), int(limity/y_res)) #x, then y. This is the steps.
        for x in range(1, limitx, resolution[0]): #move ins steps of limit.
            for y in range(1, limity, resolution[1]):
                self.baseplate.runMotor1(microSteps=y) #set to y pos
                img, variance, curAnnotatedImg, curListImg = self.getBestImg()
                listImg.append(img)
                cv2.putText(img, "{}: {:.2f}".format("ClearImage", variance), (10, 30), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 255), 3)
                listAnnotatedImg.append(img)

                print(f"column {y}, row{x}")
                print(f"variance: {variance}")
                
            self.baseplate.runMotor2(microSteps=x) #set to x pos
        self.baseplate.runMotor1(0)
        self.baseplate.runMotor2(0)

        planktonDataJSON, imgThatContainsPlanktons = self._createPlanktonData(listImg, slideArea=self.slideArea)
        waterDataJSON = self._createWaterData(self.waterData)
        dataJSON = {"plankton_data":planktonDataJSON,
                    "water_sample_data":waterDataJSON}
        print(dataJSON)
        response = self.getGemeniResponse(images=imgThatContainsPlanktons, data=dataJSON, random_sample=True)
        print(response)
        
        return response, listImg, listAnnotatedImg
    
    def end(self):
        self.baseplate.end()
        self.focusMotor.end()
        self.camera.release()
        cv2.destroyAllWindows()
        
        
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
    
