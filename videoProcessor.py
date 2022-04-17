import cv2

import numpy as np

import cvlib as cv
from cvlib.object_detection import draw_bbox

from aiortc import MediaStreamTrack
from av import VideoFrame


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """
    start_frame_number = 50
    kind = "video"

    def __init__(self, track, transform):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform
        self.faceCascade = cv2.CascadeClassifier(
            './cascades/haarcascade_frontalface_default.xml')

    async def recv(self):
        frame = await self.track.recv()

        if self.transform == "object":
            old_img = frame.to_ndarray(format="bgr24")
            # Perform the object detection
            bbox, label, conf = cv.detect_common_objects(
                old_img, confidence=0.25, model='yolov3-tiny', enable_gpu=False)
            img = draw_bbox(old_img, bbox, label, conf)

        elif self.transform == "face":
            # Detect faces with Haarcascade
            img = frame.to_ndarray(format="bgr24")
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(20, 20)
            )
            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

        elif self.transform == "facecv":
            img = frame.to_ndarray(format="bgr24")
            # apply face detection
            faces, confidences = cv.detect_face(img)
            # loop through detected faces
            for idx, f in enumerate(faces):
                (startX, startY) = f[0], f[1]
                (endX, endY) = f[2], f[3]
                # draw rectangle over face
                cv2.rectangle(img, (startX, startY),
                              (endX, endY), (0, 255, 0), 2)
                text = "{:.2f}%".format(confidences[idx] * 100)
                Y = startY - 10 if startY - 10 > 10 else startY + 10
                # write confidence percentage on top of face rectangle
                img = cv2.putText(img, text, (startX, Y), cv2.FONT_HERSHEY_SCRIPT_COMPLEX, 0.7,
                                  (0, 255, 0), 2)

        elif self.transform == "edges":
            # perform edge detection
            img = frame.to_ndarray(format="bgr24")
            img = cv2.cvtColor(cv2.Canny(img, 100, 200), cv2.COLOR_GRAY2BGR)

        elif self.transform == "rotate":
            # rotate image
            img = frame.to_ndarray(format="bgr24")
            rows, cols, _ = img.shape
            M = cv2.getRotationMatrix2D(
                (cols / 2, rows / 2), frame.time * 45, 1)
            img = cv2.warpAffine(img, M, (cols, rows))

        elif self.transform == "cartoon":
            img = frame.to_ndarray(format="bgr24")

            # prepare color
            img_color = cv2.pyrDown(cv2.pyrDown(img))
            for _ in range(6):
                img_color = cv2.bilateralFilter(img_color, 9, 9, 7)
            img_color = cv2.pyrUp(cv2.pyrUp(img_color))

            # prepare edges
            img_edges = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            img_edges = cv2.adaptiveThreshold(
                cv2.medianBlur(img_edges, 7),
                255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY,
                9,
                2,
            )
            img_edges = cv2.cvtColor(img_edges, cv2.COLOR_GRAY2RGB)

            # combine color and edges
            img = cv2.bitwise_and(img_color, img_edges)

        else:
            # No transformation at all
            return frame

        # rebuild a VideoFrame, preserving timing information
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame
