"""import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pyppeteer import launch
import os
import math
from dashboardClasses.FlightPlanDesignerClass import FlightPlanDesignerWindow
from dashboardClasses.ControlFrameClass import ControlFrame

from dashboardClasses.TelemetryInfoFrameClass import TelemetryInfoFrame


class AutopilotController:

    def buildFrame(self, frame):

        self.frame = frame
        self.flightPlanDesignerWindow = None
        self.autopilotControlFrame = tk.LabelFrame(frame, text="FLight control", padx=5, pady=5)
        self.autopilotControlFrame.rowconfigure(0, weight=1)
        self.autopilotControlFrame.rowconfigure(1, weight=5)
        self.autopilotControlFrame.rowconfigure(2, weight=1)
        self.autopilotControlFrame.columnconfigure(0, weight=1)
        self.autopilotControlFrame.columnconfigure(1, weight=1)

        self.connectButton = tk.Button(
            self.autopilotControlFrame,
            text="Connect",
            bg="red",
            fg="white",
            command=self.connect_button_clicked,
        )
        self.connectButton.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

        # Telemetry info ----------------------
        self.myTelemetryInfoFrameClass = TelemetryInfoFrame()
        self.telemetryInfoFrame = self.myTelemetryInfoFrameClass.buldFrame(self.autopilotControlFrame)
        self.telemetryInfoFrame.grid(row=1, column=0, padx=20, sticky=tk.N + tk.S + tk.E + tk.W)

        # Control ----------------------
        self.myControlFrameClass = ControlFrame()
        self.myControlFrame = self.myControlFrameClass.buldFrame(self.autopilotControlFrame)
        self.myControlFrame.grid(row=1, column=1, padx=20, sticky=tk.N + tk.S + tk.E + tk.W)

        # Mission planner frame ----------------------
        self.missionPlannerFrame = tk.LabelFrame(self.autopilotControlFrame, text="Mission planner")
        self.missionPlannerFrame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


        missionPlannerButton = tk.Button(
            self.missionPlannerFrame,
            text="Start mission planner",
            bg="red",
            fg="white",
            height=3,
            width=80,
            command=self.openSelectionWindow,
        )
        missionPlannerButton.pack()

        self.ppm = 2.78
        self.connected = False
        return self.autopilotControlFrame

    def connect_button_clicked(self):
        if self.connectButton["text"] == "Connect":
            self.client.publish("dashBoard/autopilotService/connect")
            self.connectButton["text"] = "Connecting ..."
            self.connectButton["bg"] = "orange"

        else:
            if not self.myControlFrameClass.isOnAir():
                self.client.publish("dashBoard/autopilotService/disconnect")
                self.myControlFrameClass.setDisconnected()
                self.connected = False
                self.connectButton["text"] = "Connect"
                self.connectButton["bg"] = "red"
            else:
                messagebox.showwarning("Warning", "No puedes desconectar. Estás volando")


    def putClient(self, client):
        self.client = client
        self.myControlFrameClass.putClient(self.client)

    def showTelemetryInfo (self, telemetry_info):
        self.myTelemetryInfoFrameClass.showTelemetryInfo(telemetry_info)
        if self.flightPlanDesignerWindow != None:
            self.flightPlanDesignerWindow.showTelemetryInfo(telemetry_info)
        self.myControlFrameClass.setState(telemetry_info['state'])

        if telemetry_info['state'] == 'connected' and not self.connected:
            self.connected = True
            self.connectButton["text"] = "Disconnect"
            self.connectButton["bg"] = "green"
            originlat = telemetry_info['lat']
            originlon = telemetry_info['lon']
            self.originPosition = (originlat,originlon)


    def openSelectionWindow(self):
        if self.connected:

            self.newWindow = tk.Toplevel(self.frame)
            self.newWindow.title("Selection window")
            self.newWindow.geometry("1000x500")
            self.label = tk.Label(self.newWindow, text="Select the method to build the flight plan", width=50,  font=("Colibri", 25))
            self.label.grid (column = 0, row = 0, columnspan = 4, pady = 30)

            canvas1 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas1.grid(row=2, column=0,  padx= 40,sticky="W")
            self.photoPoints = ImageTk.PhotoImage(Image.open("assets/points.png").resize ((200,200)))
            canvas1.create_image(0,0, image=self.photoPoints, anchor="nw")
            pointsButton = tk.Button(self.newWindow, text="Fix waypoints by hand", bg='#375E97', fg="white", width=25,
                                        command=self.selectPoints)
            pointsButton.grid(row = 3, column=0, padx=50, sticky="W")


            canvas2 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas2.grid(row=2, column=1, sticky="W")
            self.photoScan = ImageTk.PhotoImage(Image.open("assets/parallelogram.png").resize((200, 200)))
            canvas2.create_image(0,0, image=self.photoScan, anchor="nw")
            scanButton = tk.Button(self.newWindow, text="Scan a parallelogram", bg='#FB6542', fg="black", width=25,
                                     command=self.selectScan)
            scanButton.grid(row=3, column=1, padx=10, sticky="W")



            canvas3 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas3.grid(row=2, column=2, sticky="W")
            self.photoSpiral = ImageTk.PhotoImage(Image.open("assets/spiral.png").resize((200, 200)))
            canvas3.create_image(0,0, image=self.photoSpiral,  anchor="nw")
            spiral = tk.Button(self.newWindow, text="Scan in spiral", bg='#FFBB00', fg="white", width=25,
                                     command=self.selectSpiral)
            spiral.grid(row = 3, column=2,padx=10, sticky="W")

            canvas4 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas4.grid(row=2, column=3, sticky="W")
            self.photoLoad = ImageTk.PhotoImage(Image.open("assets/load.png").resize((200, 200)))
            canvas4.create_image(0, 0, image=self.photoLoad,  anchor="nw")
            load = tk.Button(self.newWindow, text="Load flight plan", bg='#3F681C', fg="white", width=25,
                               command=self.loadFlightPlan)
            load.grid(row = 3, column=3,padx=10, sticky="W")

            close = tk.Button(self.newWindow, text="close", bg='#B7BBB6', fg="white", width=100,
                               command=self.close)
            close.grid(row = 4, column=0, columnspan = 4, pady = 30)
        else:
            messagebox.showwarning("Warning", "Debes conectarte antes")

    def selectPoints (self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(self.frame, 1, self.client, self.originPosition)
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def selectScan(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(self.frame, 2, self.client, self.originPosition)
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def selectSpiral(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(self.frame, 3, self.client, self.originPosition)
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def loadFlightPlan(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(self.frame, 0, self.client, self.originPosition)
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def close(self):
        self.newWindow.destroy()


"""

import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from pyppeteer import launch
import os
import math
from dashboardClasses.FlightPlanDesignerClass import FlightPlanDesignerWindow
from dashboardClasses.DataBaseManagerClass import DataBaseManagerWindow
from dashboardClasses.ControlFrameClass import ControlFrame

from dashboardClasses.TelemetryInfoFrameClass import TelemetryInfoFrame


class AutopilotController:
    def buildFrame(self, frame):

        self.frame = frame
        self.flightPlanDesignerWindow = None
        self.DataBaseManagerWindow = None
        self.autopilotControlFrame = tk.LabelFrame(
            frame, text="Flight control", padx=5, pady=5
        )
        self.autopilotControlFrame.rowconfigure(0, weight=1)
        self.autopilotControlFrame.rowconfigure(1, weight=5)
        self.autopilotControlFrame.rowconfigure(2, weight=1)
        self.autopilotControlFrame.columnconfigure(0, weight=1)
        self.autopilotControlFrame.columnconfigure(1, weight=1)

        self.connectButton = tk.Button(
            self.autopilotControlFrame,
            text="Connect",
            bg="red",
            fg="white",
            command=self.connect_button_clicked,
        )
        self.connectButton.grid(
            row=0,
            column=0,
            columnspan=2,
            padx=5,
            pady=5,
            sticky=tk.N + tk.S + tk.E + tk.W,
        )

        # Telemetry info ----------------------
        self.myTelemetryInfoFrameClass = TelemetryInfoFrame()
        self.telemetryInfoFrame = self.myTelemetryInfoFrameClass.buldFrame(
            self.autopilotControlFrame
        )
        self.telemetryInfoFrame.grid(
            row=1, column=0, padx=20, sticky=tk.N + tk.S + tk.E + tk.W
        )

        # Control ----------------------
        self.myControlFrameClass = ControlFrame()
        self.myControlFrame = self.myControlFrameClass.buldFrame(
            self.autopilotControlFrame
        )
        self.myControlFrame.grid(
            row=1, column=1, padx=20, sticky=tk.N + tk.S + tk.E + tk.W
        )

        # Mission planner frame ----------------------
        self.missionPlannerFrame = tk.LabelFrame(
            self.autopilotControlFrame, text="Mission planner"
        )
        self.missionPlannerFrame.grid(
            row=2,
            column=0,
            columnspan=2,
            padx=5,
            pady=5,
            sticky=tk.N + tk.S + tk.E + tk.W,
        )

        missionPlannerButton = tk.Button(
            self.missionPlannerFrame,
            text="Start mission planner",
            bg="red",
            fg="white",
            height=3,
            width=70,
            command=self.openSelectionWindow,
        )
        missionPlannerButton.pack()


        # Data Base Manager frame ----------------------
        self.dataBaseManagerFrame = tk.LabelFrame(
            self.autopilotControlFrame, text="DB Manager"
        )
        self.dataBaseManagerFrame.grid(
            row=3,
            column=0,
            columnspan=2,
            padx=5,
            pady=5,
            sticky=tk.N + tk.S + tk.E + tk.W,
        )

        dataBaseManagerButton = tk.Button(
            self.dataBaseManagerFrame,
            text="Open DB Manager",
            bg="red",
            fg="white",
            height=3,
            width=70,
            command=self.openDBManagerWindow,
        )
        dataBaseManagerButton.pack()

        self.ppm = 2.78
        self.connected = False
        return self.autopilotControlFrame

    def connect_button_clicked(self):
        if self.connectButton["text"] == "Connect":
            self.client.publish("dashBoard/autopilotService/connect")
            self.connectButton["text"] = "Connecting ..."
            self.connectButton["bg"] = "orange"

        else:
            if not self.myControlFrameClass.isOnAir():
                self.client.publish("dashBoard/autopilotService/disconnect")
                self.myControlFrameClass.setDisconnected()
                self.connected = False
                self.connectButton["text"] = "Connect"
                self.connectButton["bg"] = "red"
            else:
                messagebox.showwarning(
                    "Warning", "No puedes desconectar. Estás volando"
                )

    def putClient(self, client):
        self.client = client
        self.myControlFrameClass.putClient(self.client)

    def showTelemetryInfo(self, telemetry_info):
        self.myTelemetryInfoFrameClass.showTelemetryInfo(telemetry_info)
        if self.flightPlanDesignerWindow != None:
            self.flightPlanDesignerWindow.showTelemetryInfo(telemetry_info)
        self.myControlFrameClass.setState(telemetry_info["state"])

        if telemetry_info["state"] == "connected" and not self.connected:
            self.connected = True
            self.connectButton["text"] = "Disconnect"
            self.connectButton["bg"] = "green"
            originlat = telemetry_info["lat"]
            originlon = telemetry_info["lon"]
            self.originPosition = (originlat, originlon)
            originposition = (originlat, originlon)

    def showFlightsInfo(self, flights):
        if self.flightPlanDesignerWindow != None:
            self.flightPlanDesignerWindow.showFlightsInfo(flights)

    def showFlightsInfo2(self, flights):
        if self.DataBaseManagerWindow != None:
            self.DataBaseManagerWindow.loadFlightsFromDBLeft(flights)

    def showFlightsInfo3(self, flights):
        if self.DataBaseManagerWindow != None:
            self.DataBaseManagerWindow.loadFlightsFromDBRight(flights)
    def showFlightPlansInfo(self, flightPlans):
        if self.flightPlanDesignerWindow != None:
            self.flightPlanDesignerWindow.loadFromDB2(flightPlans)

    def openDBManagerWindow(self):

        if self.connected:
            db_manager = DataBaseManagerWindow(self.frame, self.client)
            self.DataBaseManagerWindow = db_manager.openDBManagerWindow()

        else:
            db_manager = DataBaseManagerWindow(self.frame, self.client)
            self.DataBaseManagerWindow = db_manager.openDBManagerWindow()

    def showFlightPlansInfo2(self, flightPlans):
        print(self.DataBaseManagerWindow)
        if self.DataBaseManagerWindow != None:
            self.DataBaseManagerWindow.loadFromDBLeft(flightPlans)
    def showFlightPlansInfo3(self, flightPlans):
        print(self.DataBaseManagerWindow)
        if self.DataBaseManagerWindow != None:
            self.DataBaseManagerWindow.loadFromDBRight(flightPlans)


    def openSelectionWindow(self):

        if self.connected:

            self.newWindow = tk.Toplevel(self.frame)
            self.newWindow.title("Selection window")
            self.newWindow.geometry("1200x500")
            self.label = tk.Label(
                self.newWindow,
                text="Select the method to build the flight plan",
                width=50,
                font=("Colibri", 25),
            )
            self.label.grid(column=0, row=0, columnspan=5, pady=30)

            canvas1 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas1.grid(row=2, column=0, padx=40, sticky="W")
            self.photoPoints = ImageTk.PhotoImage(
                Image.open("assets/points.png").resize((200, 200))
            )
            canvas1.create_image(0, 0, image=self.photoPoints, anchor="nw")
            pointsButton = tk.Button(
                self.newWindow,
                text="Fix waypoints by hand",
                bg="#375E97",
                fg="white",
                width=25,
                command=self.selectPoints,
            )
            pointsButton.grid(row=3, column=0, padx=50, sticky="W")

            canvas2 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas2.grid(row=2, column=1, sticky="W")
            self.photoScan = ImageTk.PhotoImage(
                Image.open("assets/parallelogram.png").resize((200, 200))
            )
            canvas2.create_image(0, 0, image=self.photoScan, anchor="nw")
            scanButton = tk.Button(
                self.newWindow,
                text="Scan a parallelogram",
                bg="#FB6542",
                fg="black",
                width=25,
                command=self.selectScan,
            )
            scanButton.grid(row=3, column=1, padx=10, sticky="W")

            canvas4 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas4.grid(row=2, column=3, sticky="W")
            self.photoLoad = ImageTk.PhotoImage(
                Image.open("assets/load.png").resize((200, 200))
            )
            canvas4.create_image(0, 0, image=self.photoLoad, anchor="nw")
            load = tk.Button(
                self.newWindow,
                text="Load flight plan",
                bg="#3F681C",
                fg="white",
                width=25,
                command=self.loadFlightPlan,
            )
            load.grid(row=3, column=3, padx=10, sticky="W")

            canvas5 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas5.grid(row=2, column=4, sticky="W")
            self.photoPreviousFlights = ImageTk.PhotoImage(
                Image.open("assets/previous.png").resize((200, 200))
            )
            canvas5.create_image(0, 0, image=self.photoPreviousFlights, anchor="nw")
            previous_flights = tk.Button(
                self.newWindow,
                text="Previous flights",
                bg="#8D4E85",
                fg="white",
                width=25,
                command=self.showPreviousFlights,
            )
            previous_flights.grid(row=3, column=4, padx=10, sticky="W")

            close = tk.Button(
                self.newWindow,
                text="close",
                bg="#B7BBB6",
                fg="white",
                width=100,
                command=self.close,
            )
            close.grid(row=4, column=0, columnspan=5, pady=30)
        else:
            self.originPosition = (78, 82)
            self.newWindow = tk.Toplevel(self.frame)
            self.newWindow.title("Selection window")
            self.newWindow.geometry("1200x500")
            self.label = tk.Label(
                self.newWindow,
                text="Select the method to build the flight plan",
                width=50,
                font=("Colibri", 25),
            )
            self.label.grid(column=0, row=0, columnspan=5, pady=30)

            canvas1 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas1.grid(row=2, column=0, padx=40, sticky="W")
            self.photoPoints = ImageTk.PhotoImage(
                Image.open("assets/points.png").resize((200, 200))
            )
            canvas1.create_image(0, 0, image=self.photoPoints, anchor="nw")
            pointsButton = tk.Button(
                self.newWindow,
                text="Fix waypoints by hand",
                bg="#375E97",
                fg="white",
                width=25,
                command=self.selectPoints,
            )
            pointsButton.grid(row=3, column=0, padx=50, sticky="W")

            canvas2 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas2.grid(row=2, column=1, sticky="W")
            self.photoScan = ImageTk.PhotoImage(
                Image.open("assets/parallelogram.png").resize((200, 200))
            )
            canvas2.create_image(0, 0, image=self.photoScan, anchor="nw")
            scanButton = tk.Button(
                self.newWindow,
                text="Scan a parallelogram",
                bg="#FB6542",
                fg="black",
                width=25,
                command=self.selectScan,
            )
            scanButton.grid(row=3, column=1, padx=10, sticky="W")

            canvas3 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas3.grid(row=2, column=2, sticky="W")
            self.photoSpiral = ImageTk.PhotoImage(
                Image.open("assets/spiral.png").resize((200, 200))
            )
            canvas3.create_image(0, 0, image=self.photoSpiral, anchor="nw")
            spiral = tk.Button(
                self.newWindow,
                text="Scan in spiral",
                bg="#FFBB00",
                fg="white",
                width=25,
                command=self.selectSpiral,
            )
            spiral.grid(row=3, column=2, padx=10, sticky="W")

            canvas4 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas4.grid(row=2, column=3, sticky="W")
            self.photoLoad = ImageTk.PhotoImage(
                Image.open("assets/load.png").resize((200, 200))
            )
            canvas4.create_image(0, 0, image=self.photoLoad, anchor="nw")
            load = tk.Button(
                self.newWindow,
                text="Load flight plan",
                bg="#3F681C",
                fg="white",
                width=25,
                command=self.loadFlightPlan,
            )
            load.grid(row=3, column=3, padx=10, sticky="W")

            canvas5 = tk.Canvas(self.newWindow, width=200, height=200)
            canvas5.grid(row=2, column=4, sticky="W")
            self.photoPreviousFlights = ImageTk.PhotoImage(
                Image.open("assets/previous.png").resize((200, 200))
            )
            canvas5.create_image(0, 0, image=self.photoPreviousFlights, anchor="nw")
            previous_flights = tk.Button(
                self.newWindow,
                text="Previous flights",
                bg="#8D4E85",
                fg="white",
                width=25,
                command=self.showPreviousFlights,
            )
            previous_flights.grid(row=3, column=4, padx=10, sticky="W")

            close = tk.Button(
                self.newWindow,
                text="close",
                bg="#B7BBB6",
                fg="white",
                width=100,
                command=self.close,
            )
            close.grid(row=4, column=0, columnspan=5, pady=30)


    def selectPoints(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(
            self.frame, 1, self.client, self.originPosition
        )
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def selectScan(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(
            self.frame, 2, self.client, self.originPosition
        )
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def selectSpiral(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(
            self.frame, 3, self.client, self.originPosition
        )
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def loadFlightPlan(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(
            self.frame, 0, self.client, self.originPosition
        )
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def showPreviousFlights(self):
        self.flightPlanDesignerWindow = FlightPlanDesignerWindow(
            self.frame, 4, self.client, self.originPosition
        )
        self.flightPlanDesignerWindow.openWindowToCreateFlightPlan()
        self.newWindow.destroy()

    def close(self):
        self.newWindow.destroy()
