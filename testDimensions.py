# import cv2
# from ultralytics import YOLO
# model = YOLO("yolo11n.pt")

# print(model.names)
# preds = model.predict("test.jpg")
# cv2.waitKey(0)
# counter = {}
# for name in preds[0].names.values():
#     counter[name]=0
    
# for key in preds[0].boxes.cls:
#     name = preds[0].names[int(key)]
#     print(name)
    
#     counter[name] += 1
    

# print(counter)

test:dict = {}
keyd:dict = {"item1": {"he he he ha":123},"item2": {"he he he ha":124}}

for key in keyd:
    print(key)
    test[key]=keyd[key]
    
print(test)