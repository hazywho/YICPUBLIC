from google import genai
from google.genai import types
import cv2
import dotenv

class client():
    def __init__(self, key:str, model_name='gemini-2.5-flash', basePrompt = "What is this picture about?"):
        self.client = genai.Client(api_key=key)
        self.name=model_name
        self.basePrompt=basePrompt
       
    def getResponse(self, images: list, prompt: dict): #give the img in bytes
        self.masterPrompt = f"""
        {self.basePrompt}
        {prompt}
        """
        contents = [self.masterPrompt]
        
        for img in images: #load image lists
            is_success, im_buf_arr = cv2.imencode(".jpg", img)
            if is_success:    
                contents.append(
                    types.Part.from_bytes(
                        data=im_buf_arr.tobytes(),
                        mime_type="image/jpeg"
                    )
                )
            else:
                print("err")
                return 0
            
        self.response = self.client.models.generate_content(
            model=self.name,
            contents=contents
        )
        return self.response.text
    
if __name__ == "__main__":
    key = dotenv.get_key(".env", key_to_get="GEMENI_KEY")
    AI = client(key=key)
    data = cv2.imread(r"C:\Users\zanyi\Documents\GitHub\YIC2025\test.jpg")
    response = AI.getResponse(images=[data], prompt={"name":"Hezy"})
    
    print(response.text)