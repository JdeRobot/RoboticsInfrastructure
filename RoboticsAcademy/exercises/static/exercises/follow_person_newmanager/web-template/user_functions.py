from shared.image import SharedImage
from shared.value import SharedValue
from shared.laserdata import SharedLaserData

import numpy as np
import cv2
from interfaces.ssd_detection import NeuralNetwork, BoundingBox
from coco_labels import LABEL_MAP

# Define HAL functions
class HALFunctions:
    def __init__(self):
        # Initialize image variable
        self.shared_image = SharedImage("halimage")
        self.shared_v = SharedValue("velocity")
        self.shared_w = SharedValue("angular")
        self.shared_laserdata = SharedLaserData("laserdata")

        self.net = NeuralNetwork()
    
    def getLaserData(self):
        data = self.shared_laserdata.get()
        return data

    def getBoundingBoxes(self, img):
        rows = img.shape[0]
        cols = img.shape[1]
        detections = self.net.detect(img)
        bounding_boxes = []
        for detection in detections:
            bounding_box = BoundingBox(
                int(detection[1]),
                LABEL_MAP[int(detection[1])],
                float(detection[2]),
                detection[3]*cols,
                detection[4]*rows,
                detection[5]*cols,
                detection[6]*rows)
            bounding_boxes.append(bounding_box)
        return bounding_boxes
        
    # Get image function
    def getImage(self):
        image = self.shared_image.get()
        return image

    # Send velocity function
    def sendV(self, velocity):
        self.shared_v.add(velocity)

    # Send angular velocity function
    def sendW(self, angular):
        self.shared_w.add(angular)

# Define GUI functions
class GUIFunctions:
    def __init__(self):
        # Initialize image variable
        self.shared_image = SharedImage("guiimage")

    # Show image function
    def showImage(self, image):
        # Reshape to 3 channel if it has only 1 in order to display it
        if (len(image.shape) < 3):
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        self.shared_image.add(image)