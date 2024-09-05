import base64
import json
from paho.mqtt.client import ssl
import threading

import tkinter as tk
from tkinter import simpledialog, messagebox

import cv2 as cv
import numpy as np

import paho.mqtt.client as mqtt
from datetime import datetime as dt

from dashboardClasses.DataBaseManagerClass import DataBaseManagerWindow
from dashboardClasses.LEDsControllerClass import LEDsController
from dashboardClasses.CameraControllerClass import CameraController
from dashboardClasses.AutopilotControllerClass import AutopilotController
from dashboardClasses.ShowRecordedPositionsClass import RecordedPositionsWindow
from dashboardClasses.FlightPlanDesignerClass import FlightPlanDesignerWindow
from PIL import ImageTk, Image
from dashboardClasses.AutopilotService import *
from tkinter import simpledialog


class MyDialog(tk.simpledialog.Dialog):
    def __init__(self, parent, title):
        self.my_username = None
        self.my_password = None
        super().__init__(parent, title)

    def body(self, frame):
        # print(type(frame)) # tkinter.Frame
        self.my_username_label = tk.Label(frame, width=25, text="Username")
        self.my_username_label.pack()
        self.my_username_box = tk.Entry(frame, width=25)
        self.my_username_box.pack()

        self.my_password_label = tk.Label(frame, width=25, text="Password")
        self.my_password_label.pack()
        self.my_password_box = tk.Entry(frame, width=25)
        self.my_password_box.pack()
        self.my_password_box["show"] = "*"

        return frame

    def ok_pressed(self):
        self.my_username = self.my_username_box.get()
        self.my_password = self.my_password_box.get()
        self.destroy()

    def cancel_pressed(self):
        self.destroy()

    def buttonbox(self):
        self.ok_button = tk.Button(self, text="OK", width=5, command=self.ok_pressed)
        self.ok_button.pack(side="left")
        cancel_button = tk.Button(
            self, text="Cancel", width=5, command=self.cancel_pressed
        )
        cancel_button.pack(side="right")
        self.bind("<Return>", lambda event: self.ok_pressed())
        self.bind("<Escape>", lambda event: self.cancel_pressed())


class CredentialsInput(simpledialog.Dialog):
    def body(self, master):

        tk.Label(master, text="Username:").grid(row=0)
        tk.Label(master, text="Password:").grid(row=1)

        self.e1 = tk.Entry(master)
        self.e2 = tk.Entry(master)

        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        return self.e1  # initial focus

    def apply(self):
        self.username = self.e1.get()
        self.password = self.e2.get()


class ConfigurationPanel:
    def buildFrame(self, fatherFrame, callback):
        self.callback = callback
        self.fatherFrame = fatherFrame
        self.ParameterFrame = tk.Frame(fatherFrame)
        self.ParameterFrame.rowconfigure(0, weight=6)
        self.ParameterFrame.rowconfigure(1, weight=1)
        self.ParameterFrame.rowconfigure(2, weight=1)

        self.ParameterFrame.columnconfigure(0, weight=1)
        self.ParameterFrame.columnconfigure(1, weight=1)
        self.ParameterFrame.columnconfigure(2, weight=1)
        self.ParameterFrame.columnconfigure(3, weight=1)
        self.ParameterFrame.columnconfigure(4, weight=1)

        self.operationModeFrame = tk.LabelFrame(
            self.ParameterFrame, text="Operation mode"
        )
        self.operationModeFrame.grid(row=0, column=0, padx=10, pady=10, sticky="nesw")
        self.var1 = tk.StringVar()
        self.var1.set("simulation")
        tk.Radiobutton(
            self.operationModeFrame,
            text="simulation",
            variable=self.var1,
            value="simulation",
            command=self.operationModeChanged,
        ).grid(row=0, sticky="W")

        tk.Radiobutton(
            self.operationModeFrame,
            text="production",
            variable=self.var1,
            value="production",
            command=self.operationModeChanged,
        ).grid(row=1, sticky="W")

        self.communicationModeFrame = tk.LabelFrame(
            self.ParameterFrame, text="Communication mode"
        )
        self.communicationModeFrame.grid(
            row=0, column=1, padx=10, pady=10, sticky="nesw"
        )
        self.var2 = tk.StringVar()
        self.var2.set("global")
        tk.Radiobutton(
            self.communicationModeFrame,
            text="local",
            variable=self.var2,
            value="local",
            command=self.communicationModeChanged,
        ).grid(row=0, sticky="W")

        tk.Radiobutton(
            self.communicationModeFrame,
            text="global",
            variable=self.var2,
            value="global",
            command=self.communicationModeChanged,
        ).grid(row=1, sticky="W")

        tk.Radiobutton(
            self.communicationModeFrame,
            text="direct",
            variable=self.var2,
            value="direct",
            command=self.communicationModeChanged,
        ).grid(row=2, sticky="W")

        self.externalBrokerFrame = tk.LabelFrame(
            self.ParameterFrame, text="External broker"
        )
        self.externalBrokerFrame.grid(
            row=0, column=2, padx=10, pady=(10, 0), sticky="nesw"
        )
        self.var3 = tk.StringVar()
        self.var3.set("hivemq")

        self.externalBrokerOption1 = tk.Radiobutton(
            self.externalBrokerFrame,
            text="hivemq",
            variable=self.var3,
            value="hivemq",
            command=self.credentialsToggle,
        )
        self.externalBrokerOption1.grid(row=0, sticky="W")

        self.externalBrokerOption2 = tk.Radiobutton(
            self.externalBrokerFrame,
            text="hivemq (certificate)",
            variable=self.var3,
            value="hivemq_cert",
            command=self.credentialsToggle,
        )
        self.externalBrokerOption2.grid(row=1, sticky="W")

        self.externalBrokerOption3 = tk.Radiobutton(
            self.externalBrokerFrame,
            text="classpip (certificate)",
            variable=self.var3,
            value="classpip_cert",
            command=self.credentialsToggle,
        )
        self.externalBrokerOption3.grid(row=2, sticky="W")

        self.externalBrokerOption4 = tk.Radiobutton(
            self.externalBrokerFrame,
            text="classpip (credentials)",
            variable=self.var3,
            value="classpip_cred",
            command=self.credentialsToggle,
        )
        self.externalBrokerOption4.grid(row=3, sticky="W")

        """  self.credentialsFrame = tk.LabelFrame(
            self.externalBrokerFrame, text="Credentials"
        )

        self.usernameLbl = tk.Label(self.credentialsFrame, text="username")
        self.usernameLbl.grid(row=0, column=0)
        self.usernameBox = tk.Entry(self.credentialsFrame)
        self.usernameBox.grid(row=0, column=1)
        self.passLbl = tk.Label(self.credentialsFrame, text="pass")
        self.passLbl.grid(row=1, column=0)
        self.passBox = tk.Entry(self.credentialsFrame)
        self.passBox.grid(row=1, column=1)
        """
        self.monitorFrame = tk.LabelFrame(self.ParameterFrame, text="Monitor")
        self.monitorFrame.grid(row=0, column=3, padx=10, pady=10, sticky="nesw")
        self.monitorOptions = [
            "Autopilot service in external broker",
            "Camera service in external broker",
            "Dashboard in external broker",
        ]
        self.monitorOptionsSelected = []
        self.monitorCheckBox = []

        for option in self.monitorOptions:
            self.monitorOptionsSelected.append(tk.Variable(value=0))
            self.monitorCheckBox.append(
                tk.Checkbutton(
                    self.monitorFrame,
                    text=option,
                    variable=self.monitorOptionsSelected[-1],
                ).pack(anchor=tk.W)
            )

        self.dataServiceFrame = tk.LabelFrame(self.ParameterFrame, text="Data service")
        self.dataServiceFrame.grid(row=0, column=4, padx=10, pady=10, sticky="nesw")
        self.dataServiceOptions = ["Record positions"]
        self.dataServiceOptionsSelected = []
        self.dataServiceCheckBox = []

        for option in self.dataServiceOptions:
            self.dataServiceOptionsSelected.append(tk.Variable(value=0))
            checkOption = tk.Checkbutton(
                self.dataServiceFrame,
                text=option,
                variable=self.dataServiceOptionsSelected[-1],
            )
            checkOption.pack(anchor=tk.W)
            self.dataServiceCheckBox.append(checkOption)

        self.closeButton = tk.Button(
            self.ParameterFrame,
            text="Configure the Drone Engineering Ecosystem",
            bg="red",
            fg="white",
            command=self.closeButtonClicked,
        )

        self.closeButton.grid(
            row=2, column=0, columnspan=5, padx=10, pady=10, sticky="nesw"
        )

        self.image = Image.open("assets/global_simulation.png")
        self.image = self.image.resize((700, 400), Image.ANTIALIAS)
        self.bg = ImageTk.PhotoImage(self.image)
        self.canvas = tk.Canvas(self.ParameterFrame, width=00, height=400)
        self.canvas.grid(row=3, column=0, columnspan=5, padx=10, pady=10, sticky="nesw")

        self.canvas.create_image(0, 0, image=self.bg, anchor="nw")

        return self.ParameterFrame

    def changePicture(self, communication_mode, operation_mode):
        file = "assets/" + communication_mode + "_" + operation_mode + ".png"
        """
        if communication_mode == 'global' and operation_mode == 'simulation':
            self.image = Image.open("assets/global_simulation.png")
        if communication_mode == 'global' and operation_mode == 'production':
            self.image = Image.open("assets/global_production.png")
        """
        self.image = Image.open(file)
        self.image = self.image.resize((700, 400), Image.ANTIALIAS)
        self.bg = ImageTk.PhotoImage(self.image)
        # self.canvas = tk.Canvas(self.ParameterFrame, width=500, height=400)
        # self.canvas.grid(row=3, column=0, columnspan=5, padx=10, pady=10, sticky="nesw")

        self.canvas.create_image(0, 0, image=self.bg, anchor="nw")

    def credentialsToggle(self):
        if self.var3.get() == "classpip_cred" or self.var3.get() == "classpip_cert":
            dialog = MyDialog(title="Credentials", parent=self.fatherFrame)
            self.username = dialog.my_username
            self.password = dialog.my_password

            """res = CredentialsInput(title="Credentials", parent=self.fatherFrame)
            self.username = res.username
            self.password = res.password"""

            """  username = simpledialog.askstring("Login", "Username for classpip")
            password = simpledialog.askstring("Login", "Password for classpip", show='*')
            self.username = 'dronsEETAC'
            self.password = 'mimara1456.'
              if username and password:
                messagebox.showinfo("OK")
            else:
                messagebox.showinfo("Username or password missing")
            """
            """   else:
            self.credentialsFrame.grid_forget()"""

    def communicationModeChanged(self):
        if self.var2.get() == "local" or self.var2.get() == "direct":
            for checkBox in self.dataServiceCheckBox:
                checkBox.pack_forget()
        else:
            for checkBox in self.dataServiceCheckBox:
                checkBox.pack()

        if self.var2.get() == "global":
            self.externalBrokerOption1.grid(row=0, sticky="W")
            self.externalBrokerOption2.grid(row=1, sticky="W")
            self.externalBrokerOption3.grid(row=2, sticky="W")
            self.externalBrokerOption4.grid(row=2, sticky="W")
            # if self.var3.get() == "classpip.upc.edu":
            #    self.credentialsFrame.grid(row=3, sticky="W")

        else:
            self.externalBrokerOption1.grid_forget()
            self.externalBrokerOption2.grid_forget()
            self.externalBrokerOption3.grid_forget()
            self.externalBrokerOption4.grid_forget()
            # if self.var3.get() == "classpip.upc.edu":
            #    self.credentialsFrame.grid_forget()
        self.changePicture(self.var2.get(), self.var1.get())

    def operationModeChanged(self):
        if self.var2.get() == "global":
            self.externalBrokerOption1.grid(row=0, sticky="W")
            self.externalBrokerOption2.grid(row=1, sticky="W")
            self.externalBrokerOption3.grid(row=2, sticky="W")
            self.externalBrokerOption3.grid(row=2, sticky="W")
            # if self.var3.get() == "classpip.upc.edu":
            #    self.credentialsFrame.grid(row=3, sticky="W")
        else:
            self.externalBrokerOption1.grid_forget()
            self.externalBrokerOption2.grid_forget()
            self.externalBrokerOption3.grid_forget()
            self.externalBrokerOption4.grid_forget()
            # if self.var3.get() == "classpip.upc.edu":
            #    self.credentialsFrame.grid_forget()

        self.changePicture(self.var2.get(), self.var1.get())

    def closeButtonClicked(self):

        monitorOptions = []
        for i in range(0, len(self.monitorCheckBox)):
            if self.monitorOptionsSelected[i].get() == "1":
                monitorOptions.append(self.monitorOptions[i])

        dataServiceOptions = []
        for i in range(0, len(self.dataServiceCheckBox)):
            if self.dataServiceOptionsSelected[i].get() == "1":
                dataServiceOptions.append(self.dataServiceOptions[i])

        parameters = {
            "operationMode": self.var1.get(),
            "communicationMode": self.var2.get(),
            "externalBroker": self.var3.get(),
            "monitorOptions": monitorOptions,
            "dataServiceOptions": dataServiceOptions,
        }
        if self.var3.get() == "classpip_cred" or self.var3.get() == "classpip_cert":
            """parameters["username"] = self.usernameBox.get()
            parameters["pass"] = self.passBox.get()"""
            parameters["username"] = self.username
            parameters["pass"] = self.password

        self.callback(parameters)
        self.fatherFrame.destroy()


# treatment of messages received from global broker
def on_message(client, userdata, message):
    global myAutopilotController
    global myCameraController
    global panel
    global lbl
    global table
    global originlat, originlon
    global new_window

    splited = message.topic.split("/")
    origin = splited[0]
    destination = splited[1]
    command = splited[2]

    if origin == "cameraService":
        if command == "videoFrame":
            img = base64.b64decode(message.payload)
            # converting into numpy array from buffer
            npimg = np.frombuffer(img, dtype=np.uint8)
            # Decode to Original Frame
            img = cv.imdecode(npimg, 1)
            # show stream in a separate opencv window
            img = cv.resize(img, (640, 480))
            cv.imshow("Stream", img)
            cv.waitKey(1)

        if command == "picture":
            img = base64.b64decode(message.payload)
            myCameraController.putPicture(img)

        if command == "resultFlightPicture":
            print("recibo picture")
            img = message.payload
            img_name = splited[3]
            img_route = 'Pictures/' + img_name
            nparr = np.frombuffer(img, np.uint8)
            image = cv.imdecode(nparr, cv.IMREAD_COLOR)
            cv.imwrite(img_route, image)
            print('Imagen recibida y guardada en:', img_route)

        if command == "resultFlightVideo":
            print("recibo video")
            video_bytes = message.payload
            video_name = splited[3]
            video_route = 'Videos/' + video_name
            with open(video_route, 'wb') as file:
                file.write(video_bytes)
            print('Video recibido y guardado en:', video_route)

    if origin == "autopilotService":

        if command == "telemetryInfo":
            # telemetry_info contains the state of the autopilot.
            # this is enough for the autopilot controller to decide what to do next
            telemetry_info = json.loads(message.payload)
            myAutopilotController.showTelemetryInfo(telemetry_info)

    if origin == "dataService" and command == "storedPositions":
        # receive the positions stored by the data service
        data = message.payload.decode("utf-8")
        # converts received string to json
        data_json = json.loads(data)
        myRecordedPositionsWindow.putStoredPositions(data_json)

    if origin == "groundApiService":

        if command == "allFlights":
            flights = message.payload.decode("utf-8")
            flights_json = json.loads(flights)
            myAutopilotController.showFlightsInfo(flights_json)
            myAutopilotController.showFlightsInfo2(flights_json)

        if command == "allFlightPlans":
            flights = message.payload.decode("utf-8")
            flights_json = json.loads(flights)
            myAutopilotController.showFlightPlansInfo(flights_json["Waypoints"])
            myAutopilotController.showFlightPlansInfo2(flights_json["Waypoints"])

        if command == "flightPlan":
            flight = message.payload.decode("utf-8")
            flight_json = json.loads(flight)
            print(flight_json)

        if command == "flight":
            flight = message.payload.decode("utf-8")
            flight_json = json.loads(flight)
            print(flight_json)

        if command == "pictures":
            picture = message.payload.decode("utf-8")
            picture_json = json.loads(picture)
            print(picture_json)

        if command == "deleteFlightPlanResponse":
             response = message.payload.decode("utf-8")
             response_json = json.loads(response)

        if command == "deleteFlightResponse":
             response = message.payload.decode("utf-8")
             response_json = json.loads(response)

        if command == "updateFlightPlanResponse":
            response = message.payload.decode("utf-8")
            response_json = json.loads(response)

    if origin == "airApiService":

        if command == "allFlights":
            flights = message.payload.decode("utf-8")
            flights_json = json.loads(flights)
            myAutopilotController.showFlightsInfo(flights_json)
            myAutopilotController.showFlightsInfo3(flights_json)

        if command == "allFlightPlans":
                flights = message.payload.decode("utf-8")
                flights_json = json.loads(flights)
                myAutopilotController.showFlightPlansInfo3(flights_json["Waypoints"])

        if command == "flightPlan":
                flight = message.payload.decode("utf-8")
                flight_json = json.loads(flight)

        if command == "pictures":
                picture = message.payload.decode("utf-8")
                picture_json = json.loads(picture)
                print(picture_json)

        if command == "deleteFlightPlanResponse":
                 response = message.payload.decode("utf-8")
                 response_json = json.loads(response)
                 print(response_json)

        if command == "deleteFlightResponse":
             response = message.payload.decode("utf-8")
             response_json = json.loads(response)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connection OK")
    else:
        messagebox.showinfo("Bad connection")
        print("Bad connection")


def configure(configuration_parameters):
    global panelFrame
    global client
    client = mqtt.Client("Dashboard-Omar", transport="websockets")
    client.on_message = on_message
    client.on_connect = on_connect
    if configuration_parameters["communicationMode"] == "global":
        if configuration_parameters["externalBroker"] == "hivemq":
            client.connect("broker.hivemq.com", 8000)
            print("Connected to broker.hivemq.com:8000")

        elif configuration_parameters["externalBroker"] == "hivemq_cert":
            client.tls_set(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None,
            )
            client.connect("broker.hivemq.com", 8884)
            print("Connected to broker.hivemq.com:8884")

        elif configuration_parameters["externalBroker"] == "classpip_cred":
            client.username_pw_set(
                configuration_parameters["username"], configuration_parameters["pass"]
            )
            print(configuration_parameters["username"])
            client.connect("classpip.upc.edu", 8000)
            print("Connected to classpip.upc.edu:8000")

        elif configuration_parameters["externalBroker"] == "classpip_cert":
            client.username_pw_set(
                configuration_parameters["username"], configuration_parameters["pass"]
            )
            client.tls_set(
                ca_certs=None,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None,
            )
            client.connect("classpip.upc.edu", 8883)
            print("Connected to classpip.upc.edu:8883")

    elif configuration_parameters["communicationMode"] == "local":
        if configuration_parameters["operationMode"] == "simulation":
            #client.connect("localhost", 8000)
            client.connect("192.168.208.2",8000)
            print("Connected to localhost:8000")
        else:
            client.connect("10.10.10.1", 8000)
            print("Connected to 10.10.10.1:8000")

    else:  # direct communication mode
        client.connect("192.168.208.2", 8000)
        #client.connect("localhost", 8000)
        # run Autopilot service in local
        w = threading.Thread(
            target=AutopilotService,
            args=[
                configuration_parameters["operationMode"],
            ],
        )
        w.start()

    client.loop_start()
    client.subscribe("+/dashBoard/#")

    if configuration_parameters["monitorOptions"]:
        monitorOptions = json.dumps(configuration_parameters["monitorOptions"])
        client.publish("dashBoard/monitor/setOptions", monitorOptions)

    if configuration_parameters["dataServiceOptions"]:
        dataServiceOptions = json.dumps(configuration_parameters["dataServiceOptions"])
        print("envio al data service ", dataServiceOptions)
        client.publish("dashBoard/dataService/setOptions", dataServiceOptions)

    myCameraController.putClient(client)
    myAutopilotController.putClient(client)
    myRecordedPositionsWindow.putClient(client)
    # this is to maximize the main window
    master.deiconify()


############################################################################
############################################################################

master = tk.Tk()
new_window = tk.Toplevel(master)
new_window.title("Configuration panel")
new_window.geometry("900x600")
confPanel = ConfigurationPanel()
confPanelFrame = confPanel.buildFrame(new_window, configure)
confPanelFrame.pack()

master.title("Main window")
master.geometry("1150x600")
master.rowconfigure(0, weight=1)
master.rowconfigure(1, weight=15)
client = None
# this is to minimize the master window so that the configuration window can be seen
master.iconify()


def close_button_clicked():
    master.destroy()


closeButton = tk.Button(
    master,
    text="Close",
    width=160,
    height=1,
    bg="red",
    fg="white",
    command=close_button_clicked,
)
closeButton.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)


# panel frame -------------------------------------------
panelFrame = tk.Frame(master)
panelFrame.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)
panelFrame.columnconfigure(0, weight=1)
panelFrame.columnconfigure(1, weight=1)
panelFrame.columnconfigure(2, weight=1)
panelFrame.columnconfigure(3, weight=3)
panelFrame.rowconfigure(0, weight=4)
panelFrame.rowconfigure(1, weight=1)

# Autopilot control frame ----------------------
myAutopilotController = AutopilotController()
autopilotControlFrame = myAutopilotController.buildFrame(panelFrame)
autopilotControlFrame.grid(
    row=0, column=0, columnspan=3, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
)


# Camera control  frame ----------------------
myCameraController = CameraController()
cameraControlFrame = myCameraController.buildFrame(panelFrame)
cameraControlFrame.grid(
    row=0, column=3, rowspan=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
)

# LEDs control frame ----------------------
ledsControlFrame = LEDsController().buildFrame(panelFrame, client)
ledsControlFrame.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

# Monitor control frame ----------------------
monitorControlFrame = tk.LabelFrame(panelFrame, text="Monitor control")
monitorControlFrame.grid(
    row=1, column=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
)
# DB Manager control frame ----------------------
#dBManagerController = DataBaseManagerWindow()
#dBManagerFrame = dBManagerController.buildFrame(panelFrame)
#autopilotControlFrame.grid(
#    row=0, column=0, columnspan=3, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
#)
def monitor_toggle():
    global client
    if monitorControlButton["text"] == "Start monitor":
        monitorControlButton["text"] = "Stop monitor"
        client.publish("dashBoard/monitor/start")
    else:
        monitorControlButton["text"] = "Start monitor"
        client.publish("dashBoard/monitor/stop")


monitorControlButton = tk.Button(
    monitorControlFrame,
    text="Start monitor",
    bg="red",
    fg="white",
    height=3,
    width=20,
    command=monitor_toggle,
)
monitorControlButton.pack(pady=5)

# Data management ----------------------
myRecordedPositionsWindow = RecordedPositionsWindow(master)

dataManagementFrame = tk.LabelFrame(panelFrame, text="Data management")
dataManagementFrame.grid(
    row=1, column=2, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
)
showRecordedPositionsButton = tk.Button(
    dataManagementFrame,
    text="Show recorded positions",
    bg="red",
    fg="white",
    height=3,
    width=20,
    command=myRecordedPositionsWindow.openWindowToShowRecordedPositions,
)
showRecordedPositionsButton.pack(pady=5)

master.mainloop()
