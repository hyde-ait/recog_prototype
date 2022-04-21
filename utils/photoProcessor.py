import cvlib as cv
import cv2
import numpy as np

from utils.videoProcessor import cartoon_effect, edge_detect, face_detect, face_detect_cvlib, gender_recog_cvlib, object_detect_cvlib


def processPhoto(image, transform):
    binary_file = open("file.png", "wb")
    binary_file.write(image)
    binary_file.close()
    img = cv2.imread("file.png")

    if transform == "object":
        img = object_detect_cvlib(img)

    elif transform == "face":
        img = face_detect(img)

    elif transform == "facecv":
        img = face_detect_cvlib(img)

    elif transform == "gender":
        img = gender_recog_cvlib(img)

    elif transform == "edges":
        img = edge_detect(img)

    elif transform == "cartoon":
        img = cartoon_effect(img)

    f = "file.png"
    cv2.imwrite(f, img)
    image_bytes = cv2.imencode('.png', img)[1]
    print(type(image_bytes))

    return image_bytes
