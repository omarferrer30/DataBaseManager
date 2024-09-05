import tkinter as tk
from tkinter import font

import numpy as np
import cv2 as cv
from PIL import Image as Img
from PIL import ImageTk


class CameraController:
    def buildFrame(self, frame):

        # Camera control label frame ----------------------
        self.cameraControlFrame = tk.LabelFrame(
            frame, text="Camera control", padx=5, pady=5
        )

        self.cameraControlFrame.columnconfigure(0, weight=1)
        self.cameraControlFrame.columnconfigure(1, weight=1)
        self.cameraControlFrame.rowconfigure(0, weight=1)
        self.cameraControlFrame.rowconfigure(1, weight=8)
        self.cameraControlFrame.rowconfigure(2, weight=1)

        self.takePictureButton = tk.Button(
            self.cameraControlFrame,
            text="Take Picture",
            bg="red",
            fg="white",
            command=self.takePictureButtonClicked,
        )
        self.takePictureButton.grid(
            column=0, row=0, pady=5, padx=5, sticky=tk.N + tk.S + tk.E + tk.W
        )
        self.clearPictureButton = tk.Button(
            self.cameraControlFrame,
            text="Clear picture",
            bg="red",
            fg="white",
            command=self.clearPictureButtonClicked,
        )
        self.clearPictureButton.grid(
            column=1, row=0, pady=5, padx=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.picturePanel = tk.Canvas(self.cameraControlFrame)
        self.picturePanel.grid(
            column=0, row=1, columnspan=2, sticky=tk.N + tk.S + tk.E + tk.W
        )

        # self.picturePanel = tk.Label(self.cameraControlFrame,borderwidth=2, width = 60, relief="raised")
        # self.picturePanel.grid(column=0, row=1, columnspan = 2, sticky=tk.N + tk.S + tk.E + tk.W)

        self.videoStreamButton = tk.Button(
            self.cameraControlFrame,
            text="Start video stream",
            bg="red",
            fg="white",
            command=self.videoStreamButtonClicked,
        )
        self.videoStreamButton.grid(
            column=0,
            row=2,
            columnspan=2,
            pady=5,
            padx=5,
            sticky=tk.N + tk.S + tk.E + tk.W,
        )

        # self.videoPanel = tk.Label(self.cameraControlFrame,borderwidth=2, width = 30, relief="raised")
        # self.videoPanel.grid(column=0, row=3, columnspan = 2, sticky=tk.N + tk.S + tk.E + tk.W)

        self.videoStream = False

        return self.cameraControlFrame

    def putClient(self, client):
        self.client = client

    def takePictureButtonClicked(self):
        print("Take picture")
        self.client.publish("dashBoard/cameraService/takePicture")

    def clearPictureButtonClicked(self):
        self.picturePanel.destroy()
        self.picturePanel = tk.Label(
            self.cameraControlFrame, borderwidth=2, width=60, relief="raised"
        )
        self.picturePanel.grid(
            column=0, row=1, columnspan=2, sticky=tk.N + tk.S + tk.E + tk.W
        )

    def videoStreamButtonClicked(self):
        if not self.videoStream:
            self.videoStreamButton["text"] = "Stop video stream"
            self.videoStreamButton["bg"] = "green"
            self.videoStream = True
            self.client.publish("dashBoard/cameraService/startVideoStream")

        else:
            self.videoStreamButton["text"] = "Start video stream on a separaded window"
            self.videoStreamButton["bg"] = "red"
            self.videoStream = False
            self.client.publish("dashBoard/cameraService/stopVideoStream")

    def putPicture(self, jpg_original):
        self.picturePanel.destroy()

        jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
        img = cv.imdecode(jpg_as_np, 1)
        # Decode to Original Frame
        res = cv.cvtColor(img, cv.COLOR_BGR2RGB)

        self.photo = ImageTk.PhotoImage(image=Img.fromarray(res))
        self.picturePanel = tk.Canvas(self.cameraControlFrame)
        self.picturePanel.grid(
            column=0, row=1, columnspan=2, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.picturePanel.create_image(0, 0, image=self.photo, anchor=tk.NW)

        """dim = (360, 480)
        # resize image
        cv2image = cv.resize(cv2image, dim)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)

        self.picturePanel = tk.Label(self.cameraControlFrame,borderwidth=2, width = 60, relief="raised")
        self.picturePanel.grid(column=0, row=1, columnspan = 2, sticky=tk.N + tk.S + tk.E + tk.W)
        self.picturePanel.imgtk = imgtk
        self.picturePanel.configure(image=imgtk)"""


"""
    def putFrame(self, imgtk):
        self.videoPanel.imgtk = imgtk
        self.videoPanel.configure(image=imgtk)
        """
