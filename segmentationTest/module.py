from sklearn.cluster import KMeans
import torch
import torchvision
import torch.nn as nn
from torchvision import models
from torchsummary import summary
import numpy as np
import os
from PIL import Image
from torchvision import transforms
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from sklearn.manifold import TSNE

class separator():
    def __init__(self, verbose=True, mode="cuda"):
        self.verbose=verbose
        self.mode=mode
        
        self.model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT).to(self.mode)
        self.t = transforms.Compose([
            transforms.Resize((520,520)),
            transforms.ToTensor()
        ])
        if self.verbose:
            print(summary(model=self.model, input_size=(640,640)))
    
    def _load_images(self, images):
        loaded_images = []
        for image in images:
            data = self.t(image).to(self.mode).to(torch.float32).unsqueeze(0) #for single image predictions
            loaded_images.append(data)
        return loaded_images
    
    def _reducer(self, embeddings_np):
        reduced_embeddings = TSNE(n_components=2,perplexity=1).fit_transform(embeddings_np)
        print("embeddings are reduced, it is now:",reduced_embeddings.shape) if self.verbose else None
        return reduced_embeddings 
        
    def _clustering(self, input):
        return input
        #did until here, addd automatic clustering next 
        
    def predict(self, imageInput:list=[]):
        loaded_images = self._load_images(imageInput)
        embeddings = []
        
        with torch.no_grad():
            for image in loaded_images:
                features = self.model.features(image)
                embedding = torch.flatten(self.model.avgpool(features))
                embeddings.append(embedding.cpu().numpy())
        
        embeddings = np.stack(embeddings)
        if self.verbose:
            print(f"embedding shape: {embeddings.shape}")

    
            



if __name__ == "__main__":
    module = separator()
    mod