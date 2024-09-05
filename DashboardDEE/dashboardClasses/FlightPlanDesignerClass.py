import itertools
import tkinter as tk
from ttkwidgets import CheckboxTreeview
from tkinter import *
import json
import math
from geographiclib.geodesic import Geodesic
import requests
from datetime import datetime as dt
import os.path as path
import time
from bson import ObjectId

from tkinter.filedialog import asksaveasfile, askopenfilename
from tkinter import messagebox
from tkinter.ttk import Treeview
from PIL import Image, ImageTk
from io import BytesIO
import vlc
from dashboardClasses.TelemetryInfoFrameClass import TelemetryInfoFrame


class VideoPlayer(tk.Toplevel):
    def __init__(self, parent, file_name):
        super().__init__(parent)
        self.title("Video")
        self.geometry("800x600")

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        # Implementada una especie de caché la cual almacena el video la primera vez que es visualizado, y las próximas simplemente lo consulta
        if path.exists(f"Videos/{file_name}"):
            self.media = self.instance.media_new(f"Videos/{file_name}")
        else:
            messagebox.showinfo(message="Downloading the video. Please wait patiently", title="Video")
            time.sleep(1)
            response = requests.get(f"http://127.0.0.1:8000/media/videos/{file_name}")
            if response.status_code == 200:
                with open(f"Videos/{file_name}", "wb") as file:
                    file.write(response.content)
                    self.media = self.instance.media_new(f"Videos/{file_name}")
        self.media_player.set_media(self.media)

        self.video_frame = tk.Frame(self, bg="black")
        self.video_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.win_id = self.video_frame.winfo_id()
        self.media_player.set_hwnd(self.win_id)

        self.control_frame = tk.Frame(self)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.play_button = tk.Button(self.control_frame, text="Play", command=self.play)
        self.play_button.pack(side=tk.LEFT, padx=(300, 0))

        self.pause_button = tk.Button(self.control_frame, text="Pause", command=self.pause)
        self.pause_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(self.control_frame, text="Stop", command=self.stop)
        self.stop_button.pack(side=tk.LEFT)

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.media_player.play()

    def play(self):
        self.media_player.play()

    def pause(self):
        self.media_player.pause()

    def stop(self):
        self.media_player.stop()

    def close(self):
        self.media_player.stop()
        self.destroy()


class ComputeCoords:
    def __init__(self):
        self.geod = Geodesic.WGS84
        self.mpp = 0.1122
        self.ppm = 1 / self.mpp
        # one point (x,y) in the canvas and the corresponding position (lat,lon)
        self.refCoord = [651, 279]
        self.refPosition = [41.2763748, 1.9889669]

    def convertToCoords(self, position):
        g = self.geod.Inverse(
            float(position[0]),
            float(position[1]),
            self.refPosition[0],
            self.refPosition[1],
        )
        azimuth = 180 - float(g["azi2"])
        dist = float(g["s12"])

        # ATENCION: NO SE POR QUE AQUI TENGO QUE RESTAR EN VEZ DE SUMAR
        x = self.refCoord[0] - math.trunc(
            dist * self.ppm * math.sin(math.radians(azimuth))
        )
        y = self.refCoord[1] - math.trunc(
            dist * self.ppm * math.cos(math.radians(azimuth))
        )
        return x, y

    def convertToPosition(self, coords):
        # compute distance with ref coords
        dist = (
            math.sqrt(
                (coords[0] - self.refCoord[0]) ** 2
                + (coords[1] - self.refCoord[1]) ** 2
            )
            * self.mpp
        )
        # compute azimuth
        # azimuth = math.degrees(math.atan2((self.previousx - e.x), (self.previousy - e.y))) * (-1)

        azimuth = math.degrees(
            math.atan2((self.refCoord[0] - coords[0]), (self.refCoord[1] - coords[1]))
        ) * (-1)
        if azimuth < 0:
            azimuth = azimuth + 360
        # compute lat,log of new wayp
        g = self.geod.Direct(
            float(self.refPosition[0]), float(self.refPosition[1]), azimuth, dist
        )
        lat = float(g["lat2"])
        lon = float(g["lon2"])
        return lat, lon


class ChoiceWindow:
    def __init__(self, parent, text1, text2):
        self.parent = parent
        self.result = None

        self.window = tk.Toplevel(parent)
        self.window.title("Camino alternativo")

        self.window.rowconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)
        self.window.rowconfigure(2, weight=1)
        self.window.rowconfigure(3, weight=1)
        self.window.columnconfigure(0, weight=1)
        self.window.columnconfigure(1, weight=1)

        label1 = tk.Label(
            self.window, text="¿No prefieres el camino alternativo más corto?"
        )
        label1.grid(row=0, columnspan=2, column=0, sticky="nsew")

        original = "Longitud de tu camino: " + text1
        label2 = tk.Label(self.window, text=original)
        label2.grid(row=1, columnspan=2, column=0, sticky="nsew")

        propuesta = "Longitud del camino más corto: " + text2
        label3 = tk.Label(self.window, text=propuesta)
        label3.grid(row=2, columnspan=2, column=0, sticky="nsew")

        yes_button = tk.Button(
            self.window,
            text="Si",
            fg="white",
            bg="green",
            command=self.yes_button_clicked,
        )
        yes_button.grid(row=3, column=0, sticky="nsew", padx=20, pady=20)
        no_button = tk.Button(
            self.window, text="No", fg="white", bg="red", command=self.no_button_clicked
        )
        no_button.grid(row=3, column=1, sticky="nsew", padx=20, pady=20)

    def yes_button_clicked(self):
        self.result = "Sí"
        self.window.destroy()

    def no_button_clicked(self):
        self.result = "No"
        self.window.destroy()


class WaypointsWindow:
    def buildFrame(self, frame):
        self.window = tk.LabelFrame(frame, text="Waypoints")
        lab = tk.Label(self.window, text="List of waypoints", font=("Calibri", 20))
        lab.grid(row=0, column=0)

        self.table = CheckboxTreeview(self.window)
        self.table.grid(row=1, column=0, padx=20)
        self.table.bind("<<TreeviewSelect>>", self.checkbox_changed)
        self.wpNumber = 1
        return self.window

    def setData(self, waypointsIds, canvas):
        self.waypointsIds = waypointsIds
        self.canvas = canvas

    def removeEntries(self):
        for i in self.table.get_children():
            self.table.delete(i)
        self.wpNumber = 1

    def insertHome(self, lat, lon):
        self.table.insert(
            parent="",
            index="end",
            iid=0,
            text="H:  {0:5}, {1:5}".format(round(lat, 6), round(lon, 6)),
        )

    def checkbox_changed(self, event):
        item_id = self.table.focus()
        checkedList = self.table.get_checked()
        if self.table.item(item_id)["text"].split(":")[0] == "H":
            item = 0
        else:
            item = int(self.table.item(item_id)["text"].split(":")[0])
        # print (self.table.item(item_id)['values'])
        # checked = self.table.item(item_id, "values")[0]
        print(f"Clicked on item: {item_id}")
        print("Checked lisr ", checkedList)
        if item_id in checkedList:
            self.canvas.itemconfig(self.waypointsIds[item]["ovalId"], fill="orange")
        else:
            self.canvas.itemconfig(self.waypointsIds[item]["ovalId"], fill="blue")

    def insertWP(self, lat, lon):
        # complete a single digit wpNumber with left-size zero
        res = str(self.wpNumber).rjust(2, "0")
        item = self.table.insert(
            parent="",
            index="end",
            iid=self.wpNumber,
            text="{0}:  {1:5}, {2:5}".format(res, round(lat, 6), round(lon, 6)),
        )
        self.wpNumber = self.wpNumber + 1

    def getCoordinates(self, wpId):
        entries = self.table.get_children()
        for i in range(1, len(entries)):
            if int(self.table.item(entries[i])["text"].split(":")[0]) == int(wpId):
                k = i
                break

        location = self.table.item(entries[k])["text"].split(":")[1].split(",")
        lat = float(location[0])
        lon = float(location[1])

        return lat, lon

    def changeCoordinates(self, wpId, lat, lon):
        entries = self.table.get_children()
        for i in range(1, len(entries)):
            if int(self.table.item(entries[i])["text"].split(":")[0]) == int(wpId):
                k = i
                break
        # complete a single digit wpNumber with left-size zero
        res = str(wpId).rjust(2, "0")
        self.table.item(
            entries[k],
            text="{0}:  {1:5}, {2:5}".format(res, round(lat, 6), round(lon, 6)),
        )

    def markTakePicture(self, wpId):
        print("wp ID ", wpId)
        entries = self.table.get_children()
        print("entries ", entries)
        if wpId == "H":
            self.table.change_state(entries[0], "checked")
        else:
            for i in range(1, len(entries)):
                print("entry ", i)
                print(self.table.item(entries[i])["text"].split(":")[0])
                if int(self.table.item(entries[i])["text"].split(":")[0]) == int(wpId):
                    k = i
                    break
            self.table.change_state(entries[k], "checked")

    def unmarkTakePicture(self, wpId):
        entries = self.table.get_children()
        if wpId == "H":
            self.table.change_state(entries[0], "unchecked")
        else:
            for i in range(1, len(entries)):
                if int(self.table.item(entries[i])["text"].split(":")[0]) == int(wpId):
                    k = i
                    break
            self.table.change_state(entries[k], "unchecked")

    def insertRTL(self):
        self.table.insert(parent="", index="end", iid=self.wpNumber, text="RTL")

    def getWaypoints(self, waypointsIds, canvas):
        waypoints = []

        checkedList = self.table.get_checked()
        entries = self.table.get_children()
        video_active = False

        for i, entry in enumerate(entries[:-1]):

            location = self.table.item(entry)["text"].split(":")[1].split(",")
            lat = float(location[0])
            lon = float(location[1])

            waypoint_color = canvas.itemcget(waypointsIds[i]["ovalId"], "fill")
            print("waypoint ", i, waypoint_color)
            if entry in checkedList or waypoint_color == "orange":
                take = True
            else:
                take = False

            is_red = waypoint_color == "red"
            video_start = False
            video_stop = False

            if is_red:
                if video_active:
                    video_stop = True
                else:
                    video_start = True
                video_active = not video_active

            static_video = False
            if waypoint_color == "green":
                static_video = True

            waypoints.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "takePic": take,
                    "videoStart": video_start,
                    "videoStop": video_stop,
                    "staticVideo": static_video,
                }
            )
        return waypoints

    def checkLastEntry(self):
        self.table.change_state(self.table.get_children()[-1], "checked")

    def focus_force(self):
        self.window.focus_force()


def haversine_distance(point1, point2):
    # Calcula la distancia entre dos puntos (latitud, longitud) usando la fórmula de haversine
    R = 6371  # Radio de la Tierra en kilómetros
    lat1 = point1["lat"]
    lon1 = point1["lon"]
    lat2 = point2["lat"]
    lon2 = point2["lon"]

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
        math.radians(lat1)
    ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


def tsp_starting_from_first(waypoints):
    # Encuentra el camino más corto que recorre todos los puntos, empezando y regresando al primero
    shortest_distance = float("inf")
    shortest_path = []

    for perm in itertools.permutations(waypoints[1:]):
        total_distance = haversine_distance(waypoints[0], perm[0])
        for i in range(len(perm) - 1):
            total_distance += haversine_distance(perm[i], perm[i + 1])
        total_distance += haversine_distance(
            perm[-1], waypoints[0]
        )  # Volver al punto de partida

        if total_distance < shortest_distance:
            shortest_distance = total_distance
            shortest_path = [waypoints[0]] + list(perm) + [waypoints[0]]
    shortest_distance = round(shortest_distance * 1000, 2)
    return shortest_path, shortest_distance


class FlightPlanDesignerWindow:
    def __init__(self, frame, mode, client, originPosition):
        self.frame = frame  # father frame
        self.mode = mode
        self.client = client
        self.originPosition = originPosition
        self.originlat = originPosition[0]
        self.originlon = originPosition[1]

        self.done = False
        self.firstPoint = True
        self.secondPoint = False
        self.thirdPoint = False
        self.fourthPoint = False

        self.wpNumber = 1
        self.geod = Geodesic.WGS84
        self.waypointsIds = []
        self.defaultDistance = 10  # default distance for parallelogram and spiral scans (10 meters)
        self.canvas = None
        self.dronePositionId = None
        self.myTelemetryInfoFrameClass = None
        self.converter = ComputeCoords()
        self.state = 'waiting'

    def showTelemetryInfo(self, telemetyInfo):
        global flightPlanEnded

        if not self.closed:
            if self.mode != 4:
                self.myTelemetryInfoFrameClass.showTelemetryInfo(telemetyInfo)

            if self.canvas != None and self.dronePositionId != None:
                lat = telemetyInfo["lat"]
                lon = telemetyInfo["lon"]
                state = telemetyInfo["state"]
                newposx, newposy = self.converter.convertToCoords((lat, lon))
                # if state == 'arming' or state == 'disarmed':
                color = "yellow"

                if state == "takingOff" or state == "landing":
                    color = "orange"
                elif state == "flying":
                    color = "red"
                elif state == "returningHome":
                    color = "brown"
                    flightPlanEnded = True
                self.canvas.itemconfig(self.dronePositionId, fill=color)
                self.canvas.coords(
                    self.dronePositionId,
                    newposx - 15,
                    newposy - 15,
                    newposx + 15,
                    newposy + 15,
                )

    """'
    def setArmed(self):
        self.state = 'armed'
    def setArming(self):
        self.state = 'arming'
    def setFlying(self):
        self.state = 'flying'
    def setAtHome(self):
        self.state = 'atHome'
    def setLanding (self):
        print ('landing')
        self.state = 'landing'
    def setDisarmed(self):
        self.state = 'disarmed'
    """

    def openWindowToCreateFlightPlan(self):
        global flightPlanEnded

        flightPlanEnded = False
        self.newWindow = tk.Toplevel(self.frame)
        if self.mode == 0:
            self.newWindow.title("Load flight plan")
        elif self.mode == 4:
            self.newWindow.title("See previous flights")
        else:
            self.newWindow.title("Create and execute flight plan")
        self.newWindow.geometry("1250x850")

        self.newWindow.rowconfigure(0, weight=1)
        self.newWindow.rowconfigure(1, weight=5)
        self.newWindow.rowconfigure(2, weight=10)
        self.newWindow.columnconfigure(0, weight=5)
        self.newWindow.columnconfigure(1, weight=1)
        self.newWindow.columnconfigure(2, weight=5)
        """
        self.newWindow.rowconfigure(0, weight=1)
        self.newWindow.rowconfigure(1, weight=10)
        self.newWindow.columnconfigure(0, weight=6)
        self.newWindow.columnconfigure(1, weight=1)
        self.newWindow.columnconfigure(2, weight=3)
        """

        if self.mode == 0:
            title = tk.Label(
                self.newWindow, text="Load flight plan", font=("Calibri", 25)
            )
        elif self.mode == 4:
            title = tk.Label(
                self.newWindow, text="See previous flights", font=("Calibri", 25)
            )
        else:
            title = tk.Label(
                self.newWindow,
                text="Create and execute flight plan",
                font=("Calibri", 25),
            )
        title.grid(row=0, column=0, columnspan=3)

        self.canvas = tk.Canvas(self.newWindow, width=800, height=600)
        self.canvas.grid(row=1, column=0, rowspan=5, padx=(5, 0), sticky="ns")

        self.controlFrame = tk.LabelFrame(
            self.newWindow, text="Control", width=200, height=1200
        )
        """   self.controlFrame.rowconfigure(0, weight=1)
        self.controlFrame.rowconfigure(1, weight=1)
        self.controlFrame.rowconfigure(2, weight=1)
        self.controlFrame.rowconfigure(3, weight=1)
        self.controlFrame.rowconfigure(4, weight=1)
        self.controlFrame.columnconfigure(0, weight=1)"""

        self.controlFrame.grid(row=1, column=1, rowspan=5, padx=10)
        if self.mode == 0 or self.mode == 1:
            self.clearButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Clear",
                bg="#375E97",
                fg="white",
                command=self.clear,
            )
            self.clearButton.grid(row=0, column=0, padx=10, pady=0)
            runButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Run",
                bg="#FFBB00",
                fg="black",
                command=self.runButtonClick,
            )
            runButton.grid(row=1, column=0, padx=10, pady=10)
            saveButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Save",
                bg="#FB6542",
                fg="white",
                command=self.saveButtonClick,
            )
            saveButton.grid(row=2, column=0, padx=10, pady=10)
            sendFlightPlan = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Save in Drone",
                bg="#008000",
                fg="white",
                command=self.sendFlightPlanAir,
            )
            sendFlightPlan.grid(row=3, column=0, padx=10, pady=10)
            sendMediaApi = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Save Media",
                bg="#FFC0CB",
                fg="black",
                command=self.sendMediaApi,
            )
            sendMediaApi.grid(row=4, column=0, padx=10, pady=10)
            closeButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Close",
                bg="#B7BBB6",
                fg="white",
                command=self.closeWindowToToCreateFlightPlan,
            )
            closeButton.grid(row=5, column=0, padx=10, pady=10)

        elif self.mode == 2 or self.mode == 3:
            self.sliderFrame = tk.LabelFrame(
                self.controlFrame, text="Select separation (meters)"
            )
            self.sliderFrame.grid(row=0, column=0, padx=10, pady=(20, 20))
            self.label = tk.Label(self.sliderFrame, text="create scan first").grid(
                row=0, column=0, padx=0, pady=0
            )

            self.clearButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Clear",
                bg="#375E97",
                fg="white",
                command=self.clear,
            )
            self.clearButton.grid(row=1, column=0, padx=10, pady=(5, 20))

            runButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Run",
                bg="#FFBB00",
                fg="black",
                command=self.runButtonClick,
            )
            runButton.grid(row=2, column=0, padx=10, pady=20)

            saveButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Save",
                bg="#FB6542",
                fg="white",
                command=self.saveButtonClick,
            )
            saveButton.grid(row=3, column=0, padx=10, pady=20)

            closeButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Close",
                bg="#B7BBB6",
                fg="white",
                command=self.closeWindowToToCreateFlightPlan,
            )
            closeButton.grid(row=4, column=0, padx=10, pady=20)
        else:
            self.displayPreviousFlights()
            self.controlFrame.grid(row=0, column=2, rowspan=2, padx=10, pady=0)
            closeButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Close",
                bg="#B7BBB6",
                fg="white",
                command=self.closeWindowToToCreateFlightPlan,
            )
            closeButton.grid(row=0, column=0, padx=10, pady=20)
            viewImagesButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="View Images",
                bg="#FB6542",
                fg="white",
                command=self.openImagesWindow,
            )
            viewImagesButton.grid(row=1, column=0, padx=10, pady=20)
            clearButton = tk.Button(
                self.controlFrame,
                height=5,
                width=10,
                text="Clear",
                bg="#375E97",
                fg="white",
                command=self.clear,
            )
            clearButton.grid(row=2, column=0, padx=10, pady=20)
        if self.mode != 4:
            self.wpWindow = WaypointsWindow()
            self.wpFrame = self.wpWindow.buildFrame(self.newWindow)
            self.wpFrame.grid(row=1, column=2, padx=10)

            self.pic_interval_frame = tk.LabelFrame(
                self.newWindow, text="Pic Interval", width=200, height=100
            )
            self.pic_interval_frame.grid(row=2, column=2, padx=10, pady=(0, 0))

            self.pic_interval_var = tk.BooleanVar()
            self.pic_interval_checkbox = tk.Checkbutton(
                self.pic_interval_frame, text="Enable", variable=self.pic_interval_var
            )
            self.pic_interval_checkbox.grid(
                row=0, column=0, padx=(10, 5), pady=5, sticky="w"
            )

            self.pic_interval_label = tk.Label(
                self.pic_interval_frame, text="Interval (s):"
            )
            self.pic_interval_label.grid(
                row=1, column=0, padx=(10, 0), pady=5, sticky="w"
            )

            self.pic_interval_entry = tk.Entry(self.pic_interval_frame, width=10)
            self.pic_interval_entry.grid(
                row=1, column=1, padx=(0, 10), pady=5, sticky="w"
            )

            # Video Interval
            self.vid_interval_frame = tk.LabelFrame(
                self.newWindow, text="Static Video", width=200, height=100
            )
            self.vid_interval_frame.grid(row=3, column=2, padx=10, pady=(0, 0))

            self.vid_interval_label = tk.Label(
                self.vid_interval_frame, text="Duration (s):"
            )
            self.vid_interval_label.grid(
                row=1, column=0, padx=(10, 0), pady=5, sticky="w"
            )

            self.vid_interval_entry = tk.Entry(self.vid_interval_frame, width=10)
            self.vid_interval_entry.grid(
                row=1, column=1, padx=(0, 10), pady=5, sticky="w"
            )
            self.vid_interval_entry.insert(0, "5")

        # Se ha tabuleado la telemetría para que no sea añadida cuando se representan vuelos pasados

            self.myTelemetryInfoFrameClass = TelemetryInfoFrame()
            self.telemetryInfoFrame = self.myTelemetryInfoFrameClass.buldFrame(
                self.newWindow
            )
            self.telemetryInfoFrame.grid(row=4, column=2, padx=10, pady=(50, 20))

        # self.mpp (meters per pixel) depends on the zoom level of the dronLab picture
        # we are using a picture with zoom level = 20
        # Zoom level: 19, mpp = 0.2235
        # Zoom level: 20, mpp = 0.1122
        # more interesting information here: https://docs.mapbox.com/help/glossary/zoom-level/
        self.mpp = 0.1122
        self.ppm = 1 / self.mpp
        self.d = self.defaultDistance

        self.img = Image.open("assets/dronLab.png")
        self.img = self.img.resize((800, 600), Image.ANTIALIAS)
        self.bg = ImageTk.PhotoImage(self.img)
        self.image = self.canvas.create_image(0, 0, image=self.bg, anchor="nw")

        # I do no know why but the next sentences is necessary
        self.frame.img = self.img

        if self.mode == 0:
            instructionsText = (
                "Click in home position \nand select the file with the flight plan"
            )
        if self.mode == 1:
            instructionsText = "Click in home position \nand fix the sequence of waypoints \n (right button click to RTL)"
        if self.mode == 2:
            instructionsText = (
                "Click in home position \nand define parallelogram to be scaned"
            )
        if self.mode == 3:
            instructionsText = (
                "Click in home position \nand decide spiral direction and length"
            )
        if self.mode == 4:
            instructionsText = (
                "Click in home position \nand and select the flight you want to see"
            )

        self.instructionsTextId = self.canvas.create_text(
            300, 400, text=instructionsText, font=("Courier", 10, "bold")
        )

        bbox = self.canvas.bbox(self.instructionsTextId)
        self.instructionsBackground = self.canvas.create_rectangle(bbox, fill="yellow")
        self.canvas.tag_raise(self.instructionsTextId, self.instructionsBackground)
        home_x, home_y = self.converter.convertToCoords(
            (self.originPosition[0], self.originPosition[1])
        )
        self.homeMark = self.canvas.create_text(
            home_x, home_y, text="H", font=("Courier", 20, "bold"), fill="yellow"
        )

        self.canvas.bind("<ButtonPress-1>", self.click)
        self.canvas.bind("<Motion>", self.drag)
        self.canvas.bind("<ButtonPress-2>", self.middleClick)
        if self.mode == 1:
            self.canvas.bind("<ButtonPress-3>", self.returnToLaunch)

        self.closed = False

    def closeWindowToToCreateFlightPlan(self):
        self.firstPoint = True
        self.secondPoint = False
        self.thirdPoint = False
        self.done = False
        self.closed = True
        self.newWindow.destroy()

    def runButtonClick(self):
        global flightplan_id_ground
        global flightplan_id_drone

        waypoints = self.wpWindow.getWaypoints(self.waypointsIds, self.canvas)
        print("waypoints ", waypoints)
        waypoints_json = json.dumps(waypoints)
        self.client.publish("dashBoard/groundApiService/getFlightPlan", flightplan_id_ground)
        response_json = requests.get('http://127.0.0.1:8000/get_flight_plan/' + flightplan_id_ground).json()
        numPictures = len(response_json["PicsWaypoints"])
        numVideos = len(response_json["VidWaypoints"])
        data = {
            "GeofenceActive": True,
            "Flightplan": flightplan_id_ground,
            "NumPics": numPictures,
            "NumVids": numVideos
        }
        headers = {'Content-Type': 'application/json'}
        print("Sending data:", data)
        response = requests.get('http://192.168.208.6:9000/get_flight_plan/' + response_json["Title"]).json()
        if response == None:
            data_flightplan = {
                "title": response_json["Title"],
                "waypoints": waypoints,
                "PicInterval": response_json["PicInterval"],
                "VidInterval": response_json["VidTimeStatic"]
            }
            print("Sending data:", data_flightplan)
            headers = {"Content-Type": "application/json"}
            response_air = requests.post("http://192.168.208.6:9000/add_flightplan", json=data_flightplan, headers=headers)
            flightplan_id_drone = response_air.json()["id"]
            response = requests.get('http://192.168.208.6:9000/get_flight_plan/' + response_json["Title"]).json()
        else:
            flightplan_id_drone = response["_id"]
        numPictures = len(response["PicsWaypoints"])
        numVideos = len(response["VidWaypoints"])
        data = {
            "GeofenceActive": True,
            "Flightplan": flightplan_id_drone,
            "NumPics": numPictures,
            "NumVids": numVideos
        }
        response_air = requests.post('http://192.168.208.6:9000/add_flight', json=data, headers=headers)
        flight_id = response_air.json()["id"]
        self.client.publish("dashBoard/autopilotService/executeFlightPlan/" + flight_id, json.dumps({"id": flightplan_id_ground, "waypoints": waypoints_json}))

        self.dronPositionx = self.originlat
        self.dronPositiony = self.originlon
        self.dronePositionPixelx = self.originx
        self.dronePositionPixely = self.originy
        if self.dronePositionId == None:
            self.dronePositionId = self.canvas.create_oval(
                self.originx - 15,
                self.originy - 15,
                self.originx + 15,
                self.originy + 15,
                fill="yellow",
            )
        self.state = "arming"

    def sendFlightPlanAir(self):
        global flightplan_id_ground
        waypoints = self.wpWindow.getWaypoints(self.waypointsIds, self.canvas)
        print("waypoints ", waypoints)
        self.client.publish("dashBoard/groundApiService/getFlightPlan", flightplan_id_ground)
       # response = requests.get('http://192.168.208.6:9000/get_flight_plan/' + response_json["Title"]).json()
       # if response == None:
        #    data_flightplan = {
       #         "title": response_json["Title"],
        #        "waypoints": waypoints,
         #       "PicInterval": response_json["PicInterval"],
          #      "VidInterval": response_json["VidTimeStatic"]
           # }
            #print("Sending data:", data_flightplan)
            #headers = {"Content-Type": "application/json"}
            #requests.post("http://192.168.208.6:9000/add_flightplan", json=data_flightplan, headers=headers)
            #messagebox.showinfo(message="Flight plan has been saved in the drone", title="Flight plan")
        #else:
           # messagebox.showinfo(message="Flight plan already saved in the drone", title="Flight plan")

    def sendMediaApi(self):
        global flightPlanEnded

        if flightPlanEnded:
            self.client.publish("dashBoard/autopilotService/saveMediaApi")
            messagebox.showinfo(message="Media has been requested to the drone, and is being saved in ground backend", title="Saving Media")
            flightPlanEnded = False
        else:
            messagebox.showerror(message="Media can't be saved as there's any available",
                title="Error",
                parent=self.newWindow,
            )
    def clear(self):
        self.firstPoint = True
        self.secondPoint = False
        self.thirdPoint = False
        self.done = False
        self.wpNumber = 1

        items = self.canvas.find_all()

        for item in items:
            if item != self.image and item != self.homeMark:
                self.canvas.delete(item)

        if self.mode != 4:
            self.wpWindow.removeEntries()

        if self.mode == 2 or self.mode == 3:
            self.sliderFrame.destroy()

            self.sliderFrame = tk.LabelFrame(
                self.controlFrame, text="Select separation (meters)"
            )
            self.sliderFrame.grid(row=0, column=0, padx=10, pady=20)

            self.label = tk.Label(self.sliderFrame, text="create first").pack()

        #if self.mode == 4:
        #    for item in self.table.get_children():
        #        self.table.delete(item)

        self.d = self.defaultDistance

        if self.mode == 0:
            instructionsText = (
                "Click in home position \nand select the file with the flight plan"
            )
        if self.mode == 1:
            instructionsText = (
                "Click in home position \nand fix the sequence of waypoints"
            )
        if self.mode == 2:
            instructionsText = (
                "Click in home position \nand define parallelogram to be scaned"
            )
        if self.mode == 3:
            instructionsText = (
                "Click in home position \nand decide spiral direction and length"
            )
        if self.mode == 4:
            instructionsText = (
                "Click in home position \nand and select the flight you want to see"
            )
        if self.mode != 4:
            self.instructionsTextId = self.canvas.create_text(
                300, 400, text=instructionsText, font=("Courier", 10, "bold")
            )
            bbox = self.canvas.bbox(self.instructionsTextId)
            self.instructionsBackground = self.canvas.create_rectangle(
                bbox, fill="yellow"
            )
            self.canvas.tag_raise(self.instructionsTextId, self.instructionsBackground)
        self.waypointsIds = []
        self.canvas.bind("<Motion>", self.drag)

    def saveButtonClick(self):

        waypoints_json = self.wpWindow.getWaypoints(self.waypointsIds, self.canvas)
        static_video_points = [wp for wp in waypoints_json if wp["staticVideo"]]
        video_start_points = [wp for wp in waypoints_json if wp["videoStart"]]
        video_stop_points = [wp for wp in waypoints_json if wp["videoStop"]]

        if len(static_video_points) > 0 and not int(self.vid_interval_entry.get()) > 0:
            messagebox.showerror(
                message="No has definido la duración de los vídeos estáticos",
                title="Error",
                parent=self.newWindow,
            )
        elif len(video_start_points) != len(video_stop_points):
            messagebox.showerror(
                message="No has definido bien el inicio y final de los videos dinámicos",
                title="Error",
                parent=self.newWindow,
            )

        else:
            win = Toplevel()
            win.title("Save flight plan")
            win.geometry("300x100")
            win.resizable(False, False)
            win.focus_force()
            win.grab_set()

            # center window in center of previous window
            x = self.newWindow.winfo_x() + self.newWindow.winfo_width() / 2 - 150
            y = self.newWindow.winfo_y() + self.newWindow.winfo_height() / 2 - 50
            win.geometry("+%d+%d" % (x, y))

            message = "Introduce the title of the flight plan"
            label = Label(win, text=message).pack()
            e = Entry(win)
            e.pack()
            button1 = Button(
                win, text="Save to DB", command=lambda: self.saveToDB(win, e.get())
            ).pack()
            button2 = Button(
                win, text="Save to file", command=lambda: self.saveToFile(win)
            ).pack()

    def saveToDB(self, win, title):
        global flightplan_id_ground
        win.destroy()
        waypoints_json = self.wpWindow.getWaypoints(self.waypointsIds, self.canvas)
        pic_interval = (
            int(self.pic_interval_entry.get()) if self.pic_interval_var.get() else 0
        )
        vid_interval = (
            int(self.vid_interval_entry.get())
            if int(self.vid_interval_entry.get()) > 0
            else 0
        )
        data = {
            "title": title,
            "waypoints": waypoints_json,
            "PicInterval": pic_interval,
            "VidInterval": vid_interval,
        }
        print("Sending data:", data)
        self.client.publish(f"dashBoard/groundApiService/addFlightPlan", json.dumps(data))
        # print(self.client.publish("dashBoard/GroundApiService/addFlightPlan", json.dumps(data)))
        self.newWindow.focus_force()

    def saveToFile(self, win):
        win.destroy()
        waypoints = self.wpWindow.getWaypoints(self.waypointsIds, self.canvas)
        pic_interval = (
            int(self.pic_interval_entry.get()) if self.pic_interval_var.get() else None
        )
        data = {"waypoints": waypoints, "PicInterval": pic_interval}
        f = asksaveasfile(mode="w", defaultextension=".json")
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            messagebox.showinfo(message="Flight plan NOT saved", title="File save")
        else:
            waypoints_json = json.dumps(data)
            f.write(waypoints_json)
            f.close()
            messagebox.showinfo(message="Flight plan saved", title="File save")
        self.newWindow.focus_force()

    def populate_table(self):
            self.client.publish("dashBoard/groundApiService/getAllFlights")

    def showFlightsInfo(self, flights):
        for flight in flights:
            timestamp = flight["startTime"]["$date"] / 1000
            formatted_date = dt.fromtimestamp(timestamp).strftime("%m-%d %H:%M:%S")
            self.table.insert(
                "",
                "end",
                values=(formatted_date, flight["NumPics"], flight["NumVids"], flight["FlightPlan"]["Title"]),
                text=json.dumps(flight),
            )



    def displayPreviousFlights(self):
        global ovals_ids
        global texts_ids
        global lines_ids
        global dists_ids

        ovals_ids = []
        texts_ids = []
        lines_ids = []
        dists_ids = []
        def on_select(event):
            # self.clear()
            ovals_ids = []
            texts_ids = []
            lines_ids = []
            dists_ids = []
            item = self.table.selection()[0]
            flight_data = json.loads(self.table.item(item, "text"))
            self.currentFlightData = flight_data
            flight_plan = flight_data["FlightPlan"]
            waypoint_data = flight_plan["FlightWaypoints"]
            pics_waypoints = flight_plan["PicsWaypoints"]
            vid_waypoints = flight_plan["VidWaypoints"]

            cleaned_waypoints = []
            for fw in waypoint_data:
                take_pic = any(
                    pw["lat"] == fw["lat"] and pw["lon"] == fw["lon"]
                    for pw in pics_waypoints
                )
                start_vid = any(
                    vw["mode"] == "moving"
                    and vw["latStart"] == fw["lat"]
                    and vw["lonStart"] == fw["lon"]
                    for vw in vid_waypoints
                )
                end_vid = any(
                    vw["mode"] == "moving"
                    and vw["latEnd"] == fw["lat"]
                    and vw["lonEnd"] == fw["lon"]
                    for vw in vid_waypoints
                )
                static_vid = any(
                    vw["mode"] == "static"
                    and vw["lat"] == fw["lat"]
                    and vw["lon"] == fw["lon"]
                    for vw in vid_waypoints
                )
                cleaned_waypoints.append(
                    {
                        "lat": fw["lat"],
                        "lon": fw["lon"],
                        "takePic": take_pic,
                        "startVid": start_vid,
                        "endVid": end_vid,
                        "staticVid": static_vid,
                    }
                )
            self.drawFlightPlan(cleaned_waypoints)

        self.pfFrame = tk.LabelFrame(self.newWindow, text="Past Flights")
        lab = tk.Label(self.pfFrame, text="List Past Flights", font=("Calibri", 20))
        lab.grid(row=0, column=0)

        self.table = Treeview(
            self.pfFrame, columns=("Date", "NumPics", "NumVids", "FlightPlan"), show="headings"
        )
        self.table.grid(row=1, column=0, padx=20)
        self.table.heading("Date", text="Date")
        self.table.column("Date", minwidth=0, width=90, stretch=NO)
        self.table.heading("NumPics", text="NumPics")
        self.table.column("NumPics", minwidth=0, width=60, stretch=NO)
        self.table.heading("NumVids", text="NumVids")
        self.table.column("NumVids", minwidth=0, width=60, stretch=NO)
        self.table.heading("FlightPlan", text="FlightPlan")
        self.table.column("FlightPlan", minwidth=0, width=68, stretch=NO)

        self.table.bind("<<TreeviewSelect>>", on_select)

        self.pfFrame.grid(row=2, column=2, padx=10, pady=10)

    def drawFlightPlan(self, waypoints):
        # Global variables added to be able to select one flight after selecting another, and not duplicating their representation inside the map
        global ovals_ids
        global texts_ids
        global lines_ids
        global dists_ids

        self.waypointsIds = []
        if ovals_ids:
            for oval in ovals_ids:
                self.canvas.delete(oval)
            ovals_ids.clear()
        if texts_ids:
            for text in texts_ids:
                self.canvas.delete(text)
            texts_ids.clear()
        if lines_ids:
            for line in lines_ids:
                self.canvas.delete(line)
            lines_ids.clear()
        if dists_ids:
            for dist in dists_ids:
                self.canvas.delete(dist)
            dists_ids.clear()
        home = waypoints[0]
        ovalId = self.canvas.create_oval(self.originx - 10, self.originy - 10, self.originx + 10, self.originy + 10,
                                         fill='blue')
        ovals_ids.append(ovalId)
        textId = self.canvas.create_text(self.originx, self.originy, text='H', font=("Courier", 10, 'bold'),
                                         fill='white')
        texts_ids.append(textId)
        prev = home
        posx = self.originx
        posy = self.originy
        wpNum = 1
        vidStarted = False
        self.waypointsIds.append({
            'wpId': 'H',
            'textId': textId,
            'ovalId': ovalId,
            'lineInId': 0,
            'lineOutId': 0,
            'distanceFromId': 0,
            'distanceToId': 0,
            'lat': home['lat'],
            'lon': home['lon'],
        })
        if self.mode != 4:
            self.wpWindow.insertHome(home['lat'], home['lon'])
            if (home['takePic']):
                self.wpWindow.checkLastEntry()
            if (self.mode == 0) and (home['startVid']):
                self.canvas.itemconfig(self.waypointsIds[0]['ovalId'], fill='red')
                vidStarted = True
            if (self.mode == 0) and (home['staticVid']):
                self.canvas.itemconfig(self.waypointsIds[0]['ovalId'], fill='green')
        elif (self.mode == 4) and (home['takePic']):
            self.canvas.itemconfig(self.waypointsIds[0]['ovalId'], fill='orange')

        for wp in waypoints[1:]:
            g = self.geod.Inverse(float(prev['lat']), float(prev['lon']), float(wp['lat']), float(wp['lon']))
            azimuth = 180 - float(g['azi2'])
            dist = float(g['s12'])

            newposx = posx + math.trunc(dist * self.ppm * math.sin(math.radians(azimuth)))
            newposy = posy + math.trunc(dist * self.ppm * math.cos(math.radians(azimuth)))
            lineId = self.canvas.create_line(posx, posy, newposx, newposy, fill='blue')
            lines_ids.append(lineId)
            distId = self.canvas.create_text(posx + (newposx - posx) / 2,
                                             posy + (newposy - posy) / 2, text=str(round(dist, 2)),
                                             font=("Courier", 15, 'bold'),
                                             fill='red')
            dists_ids.append(distId)
            posx = newposx
            posy = newposy
            ovalId = self.canvas.create_oval(posx - 10, posy - 10, posx + 10, posy + 10, fill='blue')
            ovals_ids.append(ovalId)
            textId = self.canvas.create_text(posx, posy, text=str(wpNum), font=("Courier", 10, 'bold'), fill='white')
            texts_ids.append(textId)
            self.canvas.tag_raise(ovalId)
            self.canvas.tag_raise(textId)
            self.waypointsIds[-1]['lineOutId'] = lineId
            self.waypointsIds[-1]['distanceToId'] = distId
            self.waypointsIds.append({
                'wpId': str(wpNum),
                'textId': textId,
                'ovalId': ovalId,
                'lineInId': lineId,
                'lineOutId': 0,
                'distanceFromId': distId,
                'distanceToId': 0,
                'lat': wp['lat'],
                'lon': wp['lon'],
            })
            if self.mode != 4:
                self.wpWindow.insertWP(wp['lat'], wp['lon'])
                if (wp['takePic']):
                    self.wpWindow.checkLastEntry()
            wpNum = wpNum + 1
            prev = wp
            if self.mode == 4 or self.mode == 0:
                if wp['staticVid']:
                    self.canvas.itemconfig(self.waypointsIds[wpNum - 1]['ovalId'], fill='green')
                if wp['takePic']:
                    self.canvas.itemconfig(self.waypointsIds[wpNum - 1]['ovalId'], fill='orange')
                if vidStarted:
                    if wp['endVid']:
                        vidStarted = False
                        #if self.mode == 0:
                        self.canvas.itemconfig(self.waypointsIds[wpNum - 1]['ovalId'], fill='red')
                    self.canvas.itemconfig(self.waypointsIds[wpNum - 1]['lineInId'], fill='green')
                if wp['startVid']:
                    vidStarted = True
                    self.canvas.itemconfig(self.waypointsIds[wpNum - 1]['lineOutId'], fill='green')
                    #if self.mode == 0:
                    self.canvas.itemconfig(self.waypointsIds[wpNum - 1]['ovalId'], fill='red')

        lineId = self.canvas.create_line(posx, posy, self.originx, self.originy, fill='blue')
        lines_ids.append(lineId)
        g = self.geod.Inverse(float(prev['lat']), float(prev['lon']), float(home['lat']), float(home['lon']))
        dist = float(g['s12'])
        distId = self.canvas.create_text(posx + (self.originx - posx) / 2,
                                         posy + (self.originy - posy) / 2, text=str(round(dist, 2)),
                                         font=("Courier", 15, 'bold'),
                                         fill='red')
        dists_ids.append(distId)
        self.waypointsIds[-1]['lineOutId'] = lineId
        self.waypointsIds[-1]['distanceToId'] = distId
        self.waypointsIds[0]['lineInId'] = lineId
        self.waypointsIds[0]['distanceFrom'] = distId
        if self.mode != 4:
            self.wpWindow.insertRTL()
            self.wpWindow.focus_force()

        for wp in self.waypointsIds:
            if self.mode != 4 and self.mode != 0:
                self.canvas.itemconfig(wp['lineOutId'], fill="blue")
            self.canvas.itemconfig(wp['lineOutId'], width=3)
            self.canvas.tag_raise(wp['ovalId'])
            self.canvas.tag_raise(wp['textId'])

    def loadFromFile(self, win):
        win.destroy()
        fileName = askopenfilename()
        if (
            fileName is None
        ):  # asksaveasfile return `None` if dialog closed with "cancel".
            messagebox.showinfo(message="NO file selected", title="File open")
        else:
            messagebox.showinfo(message="File selected", title="File open")
            file = open(fileName)
            waypoints = json.load(file)
            self.drawFlightPlan(waypoints)
        self.newWindow.focus_force()
        self.done = True
        self.firstPoint = False

    def loadFromDB(self, win):
        win.destroy()
        global ovals_ids
        global texts_ids
        global lines_ids
        global dists_ids

        ovals_ids = []
        texts_ids = []
        lines_ids = []
        dists_ids = []

        self.clear()
        self.canvas.delete(self.instructionsTextId)
        self.canvas.delete(self.instructionsBackground)
        self.client.publish("dashBoard/groundApiService/getAllFlightPlans")


    def loadFromDB2(self, flightPlans):
        def on_select(event):
            global flightplan_id_ground
            item = tree.selection()[0]
            waypoint_data = json.loads(tree.item(item, "text"))
            flightplan_id_ground = waypoint_data["_id"]["$oid"]
            flight_waypoints = waypoint_data["FlightWaypoints"]
            pics_waypoints = waypoint_data["PicsWaypoints"]
            vid_waypoints = waypoint_data["VidWaypoints"]
            pic_interval = waypoint_data["PicInterval"]

            cleaned_waypoints = []

            for fw in flight_waypoints:
                take_pic = any(
                    pw["lat"] == fw["lat"] and pw["lon"] == fw["lon"]
                    for pw in pics_waypoints
                )
                start_vid = any(
                    vw["mode"] == "moving"
                    and vw["latStart"] == fw["lat"]
                    and vw["lonStart"] == fw["lon"]
                    for vw in vid_waypoints
                )
                end_vid = any(
                    vw["mode"] == "moving"
                    and vw["latEnd"] == fw["lat"]
                    and vw["lonEnd"] == fw["lon"]
                    for vw in vid_waypoints
                )
                static_vid = any(
                    vw["mode"] == "static"
                    and vw["lat"] == fw["lat"]
                    and vw["lon"] == fw["lon"]
                    for vw in vid_waypoints
                )
                cleaned_waypoints.append(
                    {
                        "lat": fw["lat"],
                        "lon": fw["lon"],
                        "takePic": take_pic,
                        "startVid": start_vid,
                        "endVid": end_vid,
                        "staticVid": static_vid,
                    }
                )
            print("voy a dibujar")
            self.drawFlightPlan(cleaned_waypoints)
            if pic_interval > 0:
                self.pic_interval_checkbox.select()
                self.pic_interval_entry.delete(0, END)
                self.pic_interval_entry.insert(0, pic_interval)
            else:
                self.pic_interval_checkbox.deselect()
                self.pic_interval_entry.delete(0, END)
            print("Selected waypoints:", cleaned_waypoints)
            top.destroy()

        top = Toplevel(self.newWindow)
        top.title("Select Waypoint")

        tree = Treeview(
            top,
            columns=(
                "Title",
                "DateAdded",
                "NumWaypoints",
                "PicsWaypoints",
                "PicInterval",
            ),
            show="headings",
        )
        tree.pack(fill="both", expand=True)
        # center window in center of previous window
        x = self.newWindow.winfo_x() + self.newWindow.winfo_width() / 2 - 150
        y = self.newWindow.winfo_y() + self.newWindow.winfo_height() / 2 - 50
        top.geometry("+%d+%d" % (x, y))
        tree.heading("Title", text="Title")
        tree.heading("DateAdded", text="Date")
        tree.heading("NumWaypoints", text="NumWaypoints")
        tree.heading("PicsWaypoints", text="Num Pics")
        tree.heading("PicInterval", text="PicInterval")

        for waypoint in flightPlans:
            timestamp = waypoint["DateAdded"]["$date"] / 1000
            formatted_date = dt.fromtimestamp(timestamp).strftime("%m-%d %H:%M:%S")
            tree.insert(
                "",
                "end",
                values=(
                    waypoint["Title"],
                    formatted_date,
                    waypoint["NumWaypoints"],
                    len(waypoint["PicsWaypoints"]),
                    waypoint["PicInterval"],
                ),
                text=json.dumps(waypoint),
            )

        tree.bind("<<TreeviewSelect>>", on_select)

    def display_image(self, image_name):
        image_window = tk.Toplevel(self.frame)
        image_window.title("Image")

        # Get image from the endpoint
        if path.exists(f"Pictures/{image_name}"):
            print(f"The image searched is: {image_name}")
            image = Image.open(f"Pictures/{image_name}")
        else:
            self.client.publish("dashBoard/groundApiService/pictures", image_name)
            response = requests.get(f"http://127.0.0.1:8000/media/pictures/{image_name}")
            if response.status_code == 200:
                with open(f"Pictures/{image_name}", "wb") as file:
                    file.write(response.content)
                image_data = response.content
                image = Image.open(BytesIO(image_data))

        # Resize the image if needed
        max_size = (800, 800)
        image.thumbnail(max_size, Image.ANTIALIAS)

        # Display image in the new window
        photo = ImageTk.PhotoImage(image)
        image_label = tk.Label(image_window, image=photo)
        image_label.image = (
            photo  # Keep a reference to the image to prevent garbage collection
        )
        image_label.pack()

        image_window.mainloop()

    def display_video(self, file_name):
        video_window = VideoPlayer(self.frame, file_name)
        video_window.mainloop()

    def openImagesWindow(self):
        # Create a new window
        self.imageWindow = tk.Toplevel(self.frame)
        self.imageWindow.title("Images from flight")
        self.imageWindow.geometry("1250x850")
        i = 0

        pictureIds = []
        for picture in self.currentFlightData["Pictures"]:
            pictureIds.append(picture)



        # Display images in a grid
        for i, image_name in enumerate(
            [item["path"] for item in self.currentFlightData["Pictures"]]
        ):
            # Get image thumbnail from the endpoint
            #response = requests.get(f"http://127.0.0.1:9000/media/pictures/{image_name}")
            #image_data = response.content
            #image = Image.open(BytesIO(image_data))

            if path.exists(f"Pictures/{image_name}"):
                image = Image.open(f"Pictures/{image_name}")
            else:
                self.client.publish("dashBoard/groundApiService/pictures", image_name)
                response = requests.get(f"http://127.0.0.1:8000/media/pictures/{image_name}")
                if response.status_code == 200:
                    with open(f"Pictures/{image_name}", "wb") as file:
                        file.write(response.content)
                    image_data = response.content
                    image = Image.open(BytesIO(image_data))

            # Create a thumbnail
            max_size = (200, 200)  # Adjust as needed
            image.thumbnail(max_size, Image.ANTIALIAS)

            # Create a PhotoImage object
            img = ImageTk.PhotoImage(image)

            # Create a label to hold the image, and set the image
            img_label = tk.Label(self.imageWindow, image=img)
            img_label.image = (
                img  # keep a reference to the image to prevent garbage collection
            )

            # Bind a click event to the label
            img_label.bind(
                "<Button-1>", lambda e, file=image_name: self.display_image(file)
            )

            # Position the label in the grid
            row, col = divmod(i, 5)  # Adjust the number of columns as needed
            img_label.grid(row=row, column=col, padx=5, pady=5)

    def middleClick(self, e):
        print(" middle ", self.mode, self.done)
        if self.mode != 4 and self.done:
            selected = self.canvas.find_overlapping(
                e.x - 10, e.y - 10, e.x + 10, e.y + 10
            )
            print("selected ", selected)
            selected_waypoints = [
                wp for wp in self.waypointsIds if wp["ovalId"] in selected
            ]
            if selected_waypoints:
                selected_waypoint = selected_waypoints[0]
                current_color = self.canvas.itemcget(
                    selected_waypoint["ovalId"], "fill"
                )
                print("color ", current_color)
                if current_color == "orange":
                    new_color = "red"  # start or finish video in this waypoint
                    self.wpWindow.unmarkTakePicture(selected_waypoint["wpId"])
                elif current_color == "red":
                    new_color = "green"  # record static video in this waypoint
                elif current_color == "green":
                    new_color = "blue"  # no action in this waypoint
                else:
                    new_color = "orange"  # take picture in this waypoint
                    self.wpWindow.markTakePicture(selected_waypoint["wpId"])
                print("pongo color en oval ", new_color, selected_waypoint["ovalId"])
                self.canvas.itemconfig(selected_waypoint["ovalId"], fill=new_color)
                waypoints_json = self.wpWindow.getWaypoints(
                    self.waypointsIds, self.canvas
                )
                print("Waypoints:", waypoints_json)

                # Traverse the waypoints and update line colors
                def traverse_and_update():
                    def get_color(wp):
                        return self.canvas.itemcget(wp["ovalId"], "fill")

                    def update_color(two_red_wps):
                        current_line_id = two_red_wps[0]["lineOutId"]
                        self.canvas.itemconfig(current_line_id, fill="green")
                        while current_line_id != two_red_wps[1]["lineInId"]:
                            next_wp = [
                                wp
                                for wp in all_wps
                                if wp["lineInId"] == current_line_id
                            ][0]
                            current_line_id = next_wp["lineOutId"]
                            self.canvas.itemconfig(current_line_id, fill="green")

                    all_wps = [wp for wp in self.waypointsIds]
                    wps_red = [wp for wp in self.waypointsIds if get_color(wp) == "red"]

                    # Reset all lines to blue
                    for wp in all_wps:
                        if wp["lineOutId"] is not None:
                            self.canvas.itemconfig(wp["lineOutId"], fill="blue")

                    if len(wps_red) % 2 == 0:
                        # subdivide in groups of 2
                        for i in range(0, len(wps_red), 2):
                            update_color(wps_red[i : i + 2])

                traverse_and_update()

    def click(self, e):
        def distance(x1, y1, x2, y2):
            return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

        if self.done:
            # if flight plan is done then the user wants to change the position of a waypoint
            # select the ids of elements of the canvas that are close to the clicked waypoint
            selected = self.canvas.find_overlapping(
                e.x - 10, e.y - 10, e.x + 10, e.y + 10
            )

            if selected:
                # finds the ids of the selected waypoint
                # Among the selected items there must be the id of the text of the selected waypoint
                self.waypointToMoveIds = [
                    wp for wp in self.waypointsIds if wp["textId"] in selected
                ][0]
                # now we are ready to drag the waypoint
                self.canvas.bind("<B1-Motion>", self.moveWp)

        elif self.mode == 0:
            if self.firstPoint:
                # origin point
                self.originx = e.x
                self.originy = e.y
                self.canvas.delete(self.instructionsTextId)
                self.canvas.delete(self.instructionsBackground)

                win = Toplevel()
                win.title("Select flight plan")
                win.geometry("300x100")
                win.resizable(False, False)
                win.focus_force()
                win.grab_set()

                # center window in center of previous window
                x = self.newWindow.winfo_x() + self.newWindow.winfo_width() / 2 - 150
                y = self.newWindow.winfo_y() + self.newWindow.winfo_height() / 2 - 50
                win.geometry("+%d+%d" % (x, y))

                message = "Load From file Or Database?"
                label = Label(win, text=message).pack()
                button1 = Button(
                    win, text="File", command=lambda: self.loadFromFile(win)
                ).pack()
                button2 = Button(
                    win, text="Database", command=lambda: self.loadFromDB(win)
                ).pack()

        elif self.mode == 1:

            if self.firstPoint:
                self.canvas.delete(self.instructionsTextId)
                self.canvas.delete(self.instructionsBackground)
                # the user select the position for the initial waypoint
                self.firstPoint = False
                # I must remember the clicked coordinates, that in this case will be also the origin coordinates

                # previous point
                self.previousx = e.x
                self.previousy = e.y

                # origin point
                self.originx = e.x
                self.originy = e.y

                # Create a line starting in origin
                self.lineOutId = self.canvas.create_line(
                    self.originx, self.originy, e.x, e.y
                )
                # Create oval and text por the origin (H) waypoint
                self.ovalId = self.canvas.create_oval(
                    e.x - 10, e.y - 10, e.x + 10, e.y + 10, fill="blue"
                )
                self.textId = self.canvas.create_text(
                    e.x, e.y, text="H", font=("Courier", 10, "bold"), fill="white"
                )
                # create a text for the distance
                self.distanceToId = self.canvas.create_text(
                    e.x, e.y, text="0", font=("Courier", 15, "bold"), fill="red"
                )

                # adds to the list the ids of the elements corresponding to the home waypoint
                self.waypointsIds.append(
                    {
                        "wpId": "H",
                        "textId": self.textId,
                        "ovalId": self.ovalId,
                        "lineInId": 0,
                        "lineOutId": self.lineOutId,
                        "distanceFromId": 0,
                        "distanceToId": self.distanceToId,
                    }
                )
                print("nuevo vaypoint ", self.waypointsIds)

                # current lat, lon are the origin coordinates
                # self.lat = self.originlat
                # self.lon = self.originlon
                self.lat, self.lon = self.converter.convertToPosition((e.x, e.y))

                # insert information of origin waypoint in the table
                self.wpWindow.insertHome(self.lat, self.lon)
            else:
                # the user is fixing the next waypoint
                # create the elements (line, oval, text and distance) for the new waypoint
                self.lineId = self.canvas.create_line(e.x, e.y, e.x, e.y)
                self.ovalId = self.canvas.create_oval(
                    e.x - 10, e.y - 10, e.x + 10, e.y + 10, fill="blue"
                )
                self.textId = self.canvas.create_text(
                    e.x,
                    e.y,
                    text=str(self.wpNumber),
                    font=("Courier", 10, "bold"),
                    fill="white",
                )
                self.distanceId = self.canvas.create_text(
                    e.x, e.y, text="0", font=("Courier", 15, "bold"), fill="red"
                )

                # adds the ids of the new waypoint to the list
                self.waypointsIds.append(
                    {
                        "wpId": self.wpNumber,
                        "textId": self.textId,
                        "ovalId": self.ovalId,
                        "lineInId": self.waypointsIds[-1]["lineOutId"],
                        "lineOutId": self.lineId,
                        "distanceFromId": self.waypointsIds[-1]["distanceToId"],
                        "distanceToId": self.distanceId,
                    }
                )
                print("nuevo vaypoint ", self.waypointsIds)
                self.lat, self.lon = self.converter.convertToPosition((e.x, e.y))
                """
                    # compute distance from previous waypoint
                    dist = math.sqrt((e.x - self.previousx) ** 2 + (e.y - self.previousy) ** 2) * self.mpp
                    # compute azimuth
                    azimuth = math.degrees(math.atan2((self.previousx - e.x), (self.previousy - e.y))) * (-1)
                    if azimuth < 0:
                        azimuth = azimuth + 360
                    # compute lat,log of new waypoint
                    g = self.geod.Direct(float(self.lat), float(self.lon), azimuth, dist)
                    self.lat = float(g['lat2'])
                    self.lon = float(g['lon2'])
                    """
                # insert new waypoint in table
                self.wpWindow.insertWP(self.lat, self.lon)

                # update previouos point
                self.previousx = e.x
                self.previousy = e.y
                self.wpNumber = self.wpNumber + 1

        elif self.mode == 2:
            if self.firstPoint:
                self.canvas.delete(self.instructionsTextId)
                self.canvas.delete(self.instructionsBackground)
                # the user starts defining the area (rectangle) to be scanned
                # Four points (A, B, C and D) must be defined
                self.originposx = e.x
                self.originposy = e.y
                self.originx = e.x
                self.originy = e.y
                self.firstPoint = False
                self.secondPoint = True
                # I must remember the clicked coordinates, that in this case will be also the origin coordinates

                self.points = []
                # A point
                self.Ax = e.x
                self.Ay = e.y
                self.points.append((self.Ax, self.Ay))
                self.points.append((self.Ax, self.Ay))
                self.points.append((self.Ax, self.Ay))
                self.points.append((self.Ax, self.Ay))
                self.rectangle = self.canvas.create_polygon(
                    self.points, outline="red", fill="", width=5
                )
                self.distanceX = self.canvas.create_text(
                    e.x, e.y, text="0", font=("Courier", 15, "bold"), fill="red"
                )

            elif self.secondPoint:
                # the user is fixing point B
                self.secondPoint = False
                self.thirdPoint = True

                self.Bx = e.x
                self.By = e.y

                self.azimuth1 = math.degrees(
                    math.atan2((self.Ax - e.x), (self.Ay - e.y))
                ) * (-1)
                if self.azimuth1 < 0:
                    self.azimuth1 = self.azimuth1 + 360
                self.x = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2)
                self.distanceY = self.canvas.create_text(
                    e.x, e.y, text="0", font=("Courier", 15, "bold"), fill="red"
                )

                self.wpNumber = self.wpNumber + 1
            elif self.thirdPoint:
                # the user is fixing point C
                self.thirdPoint = False
                self.azimuth2 = math.degrees(
                    math.atan2((self.Bx - e.x), (self.By - e.y))
                ) * (-1)
                if self.azimuth2 < 0:
                    self.azimuth2 = self.azimuth2 + 360
                self.y = math.sqrt((e.x - self.Bx) ** 2 + (e.y - self.By) ** 2)

                self.createScan()

                self.sliderFrame.destroy()

                self.sliderFrame = tk.LabelFrame(
                    self.controlFrame, text="Select separation (meters)"
                )
                self.sliderFrame.grid(row=0, column=0, padx=10, pady=20)

                self.slider = tk.Scale(
                    self.sliderFrame,
                    from_=2,
                    to=10,
                    length=150,
                    orient="horizontal",
                    activebackground="green",
                    tickinterval=2,
                    resolution=2,
                    command=self.reCreate,
                )
                self.slider.grid(row=0, column=0, padx=0, pady=0)

        elif self.mode == 4:
            if self.firstPoint:
                self.firstPoint = False
                self.originx = e.x
                self.originy = e.y
                self.canvas.delete(self.instructionsTextId)
                self.canvas.delete(self.instructionsBackground)
                self.populate_table()

            else:
                overlapping_items = self.canvas.find_overlapping(
                    e.x - 10, e.y - 10, e.x + 10, e.y + 10
                )
                red_items = []
                green_items = []
                orange_items = []
                item_color = ""

                line_items = [
                    item
                    for item in overlapping_items
                    if self.canvas.type(item) == "line"
                    and self.canvas.itemcget(item, "fill") in ["red", "green"]
                ]
                waypoint_items = [
                    item
                    for item in overlapping_items
                    if self.canvas.type(item) == "oval"
                    and self.canvas.itemcget(item, "fill") in ["red", "green", "orange"]
                ]

                # Process waypoints first
                for item in waypoint_items:
                    item_color = self.canvas.itemcget(item, "fill")
                    if item_color == "green":
                        green_items.append(item)
                    if item_color == "red":
                        red_items.append(item)
                    elif item_color == "orange":
                        orange_items.append(item)

                # If no waypoint is found, then process lines
                if not green_items and not red_items:
                    for item in line_items:
                        item_color = self.canvas.itemcget(item, "fill")
                        if item_color == "green":
                            green_items.append(item)
                        if item_color == "red":
                            red_items.append(item)
                        elif item_color == "orange":
                            orange_items.append(item)

                def find_closest_item(items):
                    # Find the closest green item to the clicked point
                    closest_item = None
                    min_distance = float("inf")

                    for item in items:
                        item_coords = self.canvas.coords(item)
                        item_center_x = (item_coords[0] + item_coords[2]) / 2
                        item_center_y = (item_coords[1] + item_coords[3]) / 2

                        item_distance = distance(e.x, e.y, item_center_x, item_center_y)

                        if item_distance < min_distance:
                            min_distance = item_distance
                            closest_item = item
                    return closest_item

                # Find the closest green item (static video) first
                closest_item = find_closest_item(green_items)

                # If there are no green items, check for the orange items (pictures)
                if closest_item is None and item_color != "":
                    # If the item_color is red, is a moving video
                    if item_color == "red":
                        closest_item = find_closest_item(red_items)
                    else:
                        closest_item = find_closest_item(orange_items)

                # Perform appropriate action based on the clicked item
                if closest_item:
                    item_color = self.canvas.itemcget(closest_item, "fill")
                    if item_color == "green" or item_color == "orange" or item_color == "red":
                        # Check if it is a line or waypoint and perform the appropriate action
                        if self.canvas.type(closest_item) == "line":
                            # Play the associated video
                            print("Video")
                            current_line_id = closest_item
                            start_waypoint = None
                            end_waypoint = None

                            # Find the start waypoint of the video
                            while True:
                                previous_waypoint = next(
                                    (
                                        waypoint
                                        for waypoint in self.waypointsIds
                                        if waypoint["lineOutId"] == current_line_id
                                    ),
                                    None,
                                )
                                previous_line_id = (
                                    previous_waypoint["lineInId"]
                                    if previous_waypoint
                                    else None
                                )
                                previous_line_color = (
                                    self.canvas.itemcget(previous_line_id, "fill")
                                    if previous_line_id
                                    else None
                                )

                                if previous_line_color == "green":
                                    current_line_id = previous_line_id
                                else:
                                    start_waypoint = previous_waypoint
                                    break

                            current_line_id = closest_item

                            # Find the end waypoint of the video
                            while True:
                                next_waypoint = next(
                                    (
                                        waypoint
                                        for waypoint in self.waypointsIds
                                        if waypoint["lineInId"] == current_line_id
                                    ),
                                    None,
                                )
                                next_line_id = (
                                    next_waypoint["lineOutId"]
                                    if next_waypoint
                                    else None
                                )
                                next_line_color = (
                                    self.canvas.itemcget(next_line_id, "fill")
                                    if next_line_id
                                    else None
                                )

                                if next_line_color == "green":
                                    current_line_id = next_line_id
                                else:
                                    end_waypoint = next_waypoint
                                    break

                            for video in self.currentFlightData["Videos"]:
                                video_start_lat = video["latStart"]
                                video_start_lon = video["lonStart"]
                                video_end_lat = video["latEnd"]
                                video_end_lon = video["lonEnd"]

                                if (
                                    start_waypoint["lat"] == video_start_lat
                                    and start_waypoint["lon"] == video_start_lon
                                    and end_waypoint["lat"] == video_end_lat
                                    and end_waypoint["lon"] == video_end_lon
                                ):
                                    self.display_video("Videos/" + video["nameVideo"])
                                    break

                        elif self.canvas.type(closest_item) == "oval":
                            # Open a new window with the image or static video
                            matching_waypoint = next(
                                (
                                    waypoint
                                    for waypoint in self.waypointsIds
                                    if waypoint["ovalId"] == closest_item
                                ),
                                None,
                            )
                            item_color = self.canvas.itemcget(closest_item, "fill")
                            if item_color == "red":
                                # Static video
                                print("Moving Video")
                                for video in self.currentFlightData["Videos"]:
                                    if video["latStart"] == matching_waypoint["lat"] and video["lonStart"] == matching_waypoint["lon"]:
                                        moving_video_path = video["nameVideo"]
                                    elif video["latEnd"] == matching_waypoint["lat"] and video["lonEnd"] == matching_waypoint["lon"]:
                                        moving_video_path = video["nameVideo"]
                                if moving_video_path:
                                    self.display_video(moving_video_path)
                            if item_color == "green":
                                # Static video
                                print("Static Video")
                                for video in self.currentFlightData["Videos"]:
                                    if video["latStart"] == matching_waypoint["lat"] and video["lonStart"] == matching_waypoint["lon"]:
                                        static_video_path = video["nameVideo"]
                                if static_video_path:
                                    self.display_video(static_video_path)
                            elif item_color == "orange":
                                # Image
                                print("Image")
                                picture_path = ""
                                for picture in self.currentFlightData["Pictures"]:
                                    if picture["lat"] == matching_waypoint["lat"] and picture["lon"] == matching_waypoint["lon"]:
                                        picture_path = picture["namePicture"]
                                if picture_path!= "":
                                    self.display_image(picture_path)

        else:
            if self.firstPoint:

                self.canvas.delete(self.instructionsTextId)
                self.canvas.delete(self.instructionsBackground)

                # the user starts defining the area (rectangle) to be scanned
                # Four points (A, B, C and D) must be defined

                self.originx = e.x
                self.originy = e.y
                self.firstPoint = False
                self.secondPoint = True
                # I must remember the clicked coordinates, that in this case will be also the origin coordinates

                # A point
                self.Ax = e.x
                self.Ay = e.y

                self.line = self.canvas.create_line(
                    self.Ax, self.Ay, e.x, e.y, fill="red", width=3
                )
                self.distance = self.canvas.create_text(
                    e.x, e.y, text="0", font=("Courier", 15, "bold"), fill="red"
                )
            elif self.secondPoint:
                # the user is fixing point B
                self.secondPoint = False
                self.azimuth = math.degrees(
                    math.atan2((self.Ax - e.x), (self.Ay - e.y))
                ) * (-1)
                if self.azimuth < 0:
                    self.azimuth = self.azimuth + 360
                self.x = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2)

                self.createSpiral()

                self.sliderFrame.destroy()

                self.sliderFrame = tk.LabelFrame(
                    self.controlFrame, text="Select separation (meters)"
                )
                self.sliderFrame.grid(row=0, column=0, padx=10, pady=20)
                self.slider = tk.Scale(
                    self.sliderFrame,
                    from_=10,
                    to=50,
                    length=150,
                    orient="horizontal",
                    activebackground="green",
                    tickinterval=10,
                    resolution=10,
                    command=self.reCreate,
                )
                self.slider.grid(row=0, column=0, padx=0, pady=0)

    def drag(self, e):

        if self.mode == 1:
            if not self.firstPoint:
                # the user is draging the mouse to decide where to place next waypoint
                dist = (
                    math.sqrt((e.x - self.previousx) ** 2 + (e.y - self.previousy) ** 2)
                    * self.mpp
                )

                # show distance in the middle of the line
                self.canvas.coords(
                    self.waypointsIds[-1]["distanceToId"],
                    self.previousx + (e.x - self.previousx) / 2,
                    self.previousy + (e.y - self.previousy) / 2,
                )
                self.canvas.itemconfig(
                    self.waypointsIds[-1]["distanceToId"], text=str(round(dist, 2))
                )
                # Change the coordinates of the last created line to the new coordinates
                self.canvas.coords(
                    self.waypointsIds[-1]["lineOutId"],
                    self.previousx,
                    self.previousy,
                    e.x,
                    e.y,
                )

        if self.mode == 2:
            if self.secondPoint:
                # the user is draging the mouse to decide the direction and lenght of the first dimension of parallelogram
                self.points[1] = (e.x, e.y)
                self.points[2] = (e.x, e.y)
                self.canvas.delete(self.rectangle)
                self.rectangle = self.canvas.create_polygon(
                    self.points, outline="red", fill="", width=5
                )
                dist = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2) * self.mpp

                # show distance in the middle of the line
                self.canvas.coords(
                    self.distanceX,
                    self.Ax + (e.x - self.Ax) / 2,
                    self.Ay + (e.y - self.Ay) / 2,
                )
                self.canvas.itemconfig(self.distanceX, text=str(round(dist, 2)))
            elif self.thirdPoint:
                # the user is draging the mouse to decide the direction and lenght of the second dimension of parallelogram

                dist = math.sqrt((e.x - self.Bx) ** 2 + (e.y - self.By) ** 2)
                angle = math.degrees(math.atan2((self.Bx - e.x), (self.By - e.y))) * (
                    -1
                )
                if angle < 0:
                    angle = angle + 360

                Cx = self.Bx + dist * math.cos(math.radians(angle - 90))
                Cy = self.By + dist * math.sin(math.radians(angle - 90))

                Dx = self.Ax + dist * math.cos(math.radians(angle - 90))
                Dy = self.Ay + dist * math.sin(math.radians(angle - 90))

                self.points[2] = (Cx, Cy)
                self.points[3] = (Dx, Dy)
                self.canvas.delete(self.rectangle)
                self.rectangle = self.canvas.create_polygon(
                    self.points, outline="red", fill="", width=5
                )
                # show distance in the middle of the line
                self.canvas.coords(
                    self.distanceY,
                    self.Bx + (e.x - self.Bx) / 2,
                    self.By + (e.y - self.By) / 2,
                )
                self.canvas.itemconfig(
                    self.distanceY, text=str(round(dist * self.mpp, 2))
                )

        if self.mode == 3:
            if self.secondPoint:
                # the user is draging the mouse to decide the direction and lenght of spiral
                self.canvas.coords(self.line, self.Ax, self.Ay, e.x, e.y)
                dist = math.sqrt((e.x - self.Ax) ** 2 + (e.y - self.Ay) ** 2) * self.mpp

                # show distance in the middle of the line
                self.canvas.coords(
                    self.distance,
                    self.Ax + (e.x - self.Ax) / 2,
                    self.Ay + (e.y - self.Ay) / 2,
                )
                self.canvas.itemconfig(self.distance, text=str(round(dist, 2)))

    def moveWp(self, e):
        # the user is moving a waypoints
        # the ids of this waypoint are in waypointToMoveIds
        if not self.waypointToMoveIds["wpId"] == "H":
            # can move any waypoint except home
            # move the oval and the text
            self.canvas.coords(
                self.waypointToMoveIds["ovalId"], e.x - 10, e.y - 10, e.x + 10, e.y + 10
            )
            self.canvas.coords(self.waypointToMoveIds["textId"], e.x, e.y)

            # get coordinates of lineIn and lineout
            lineInCoord = self.canvas.coords(self.waypointToMoveIds["lineInId"])
            lineOutCoord = self.canvas.coords(self.waypointToMoveIds["lineOutId"])

            # these are the coordinates of the waypoint
            wpCoord = (lineInCoord[2], lineInCoord[3])

            # compute distance and azimuth from the current position of the waypoint

            dist = (
                math.sqrt((e.x - wpCoord[0]) ** 2 + (e.y - wpCoord[1]) ** 2) * self.mpp
            )
            azimuth = math.degrees(
                math.atan2((wpCoord[0] - e.x), (wpCoord[1] - e.y))
            ) * (-1)
            if azimuth < 0:
                azimuth = azimuth + 360
            lat, lon = self.wpWindow.getCoordinates(self.waypointToMoveIds["wpId"])

            # compute new position of the waypoint
            g = self.geod.Direct(lat, lon, azimuth, dist)
            lat = float(g["lat2"])
            lon = float(g["lon2"])

            # change info in the table
            self.wpWindow.changeCoordinates(self.waypointToMoveIds["wpId"], lat, lon)
            # self.table.item(entry, values=(self.waypointToMoveIds['wpId'], lat, lon))

            # change coordinates of arriving and departing lines
            self.canvas.coords(
                self.waypointToMoveIds["lineInId"],
                lineInCoord[0],
                lineInCoord[1],
                e.x,
                e.y,
            )
            self.canvas.coords(
                self.waypointToMoveIds["lineOutId"],
                e.x,
                e.y,
                lineOutCoord[2],
                lineOutCoord[3],
            )

            if self.mode == 0 or self.mode == 1:
                # change distance labels
                distFrom = (
                    math.sqrt((e.x - lineInCoord[0]) ** 2 + (e.y - lineInCoord[1]) ** 2)
                    * self.mpp
                )
                distTo = (
                    math.sqrt(
                        (e.x - lineOutCoord[2]) ** 2 + (e.y - lineOutCoord[3]) ** 2
                    )
                    * self.mpp
                )

                # show distance in the middle of the line
                self.canvas.coords(
                    self.waypointToMoveIds["distanceFromId"],
                    lineInCoord[0] + (e.x - lineInCoord[0]) / 2,
                    lineInCoord[1] + (e.y - lineInCoord[1]) / 2,
                )
                self.canvas.itemconfig(
                    self.waypointToMoveIds["distanceFromId"],
                    text=str(round(distFrom, 2)),
                )

                self.canvas.coords(
                    self.waypointToMoveIds["distanceToId"],
                    lineOutCoord[2] + (e.x - lineOutCoord[2]) / 2,
                    lineOutCoord[3] + (e.y - lineOutCoord[3]) / 2,
                )
                self.canvas.itemconfig(
                    self.waypointToMoveIds["distanceToId"], text=str(round(distTo, 2))
                )

    def returnToLaunch(self, e):

        # right button click to finish the flight plan (only in mode 1)

        # complete the ids of the home waypoint
        self.waypointsIds[0]["lineInId"] = self.waypointsIds[-1]["lineOutId"]
        self.waypointsIds[0]["distanceFromId"] = self.waypointsIds[-1]["distanceToId"]

        # modify last line to return to launch

        self.canvas.coords(
            self.waypointsIds[-1]["lineOutId"],
            self.previousx,
            self.previousy,
            self.originx,
            self.originy,
        )

        # compute distance to home
        dist = (
            math.sqrt(
                (self.originx - self.previousx) ** 2
                + (self.originy - self.previousy) ** 2
            )
            * self.mpp
        )

        self.canvas.coords(
            self.distanceId,
            self.previousx + (self.originx - self.previousx) / 2,
            self.previousy + (self.originy - self.previousy) / 2,
        )
        self.canvas.itemconfig(self.distanceId, text=str(round(dist, 2)))

        # insert return to launch in the table
        self.wpWindow.insertRTL()

        # change color of all lines
        for wp in self.waypointsIds:
            self.canvas.itemconfig(wp["lineOutId"], fill="blue")
            self.canvas.itemconfig(wp["lineOutId"], width=3)

        # ignore mouse drag from now on
        self.canvas.unbind("<Motion>")
        self.wpWindow.setData(self.waypointsIds, self.canvas)

        self.done = True
        if len(self.waypointsIds) > 9:
            messagebox.showerror(
                message="Demasiados puntos para buscar el camino más corto. Tardaría mucho",
                title="Aviso",
                parent=self.newWindow,
            )

        else:
            waypoints = self.wpWindow.getWaypoints(self.waypointsIds, self.canvas)
            shortest_path, length = tsp_starting_from_first(waypoints)
            lengthOriginal = 0
            for wpId in self.waypointsIds:
                lengthOriginal = lengthOriginal + float(
                    self.canvas.itemcget(wpId["distanceToId"], "text")
                )
            lengthOriginal = round(lengthOriginal, 2)
            if length < lengthOriginal - 2:
                self.drawShortestPath(shortest_path, length, lengthOriginal)

    def drawShortestPath(self, waypoints, length, lengthOriginal):
        print("waypoints recibidos por shortest path ")
        for wp in waypoints:
            print("=== ", wp)
        prev = waypoints[0]
        print("prev2 ", prev)
        posx = self.originx
        posy = self.originy
        lines = []

        for wp in waypoints[1:]:
            g = self.geod.Inverse(
                float(prev["lat"]),
                float(prev["lon"]),
                float(wp["lat"]),
                float(wp["lon"]),
            )
            azimuth = 180 - float(g["azi2"])
            dist = float(g["s12"])

            newposx = posx + math.trunc(
                dist * self.ppm * math.sin(math.radians(azimuth))
            )
            newposy = posy + math.trunc(
                dist * self.ppm * math.cos(math.radians(azimuth))
            )
            lines.append(
                self.canvas.create_line(
                    posx, posy, newposx, newposy, fill="yellow", width=3
                )
            )
            prev = wp
            posx = newposx
            posy = newposy

        choice_window = ChoiceWindow(self.frame, str(lengthOriginal), str(length))
        self.frame.wait_window(choice_window.window)
        if choice_window.result == "No":
            for line in lines:
                self.canvas.delete(line)
        else:
            self.clear()

            self.drawFlightPlan(waypoints[:-1])
            print("nuevos wpID ", self.waypointsIds)
            self.done = True
            self.firstPoint = False
            self.canvas.unbind("<Motion>")
            self.canvas.bind("<ButtonPress-2>", self.middleClick)
            self.canvas.delete(self.instructionsTextId)
            self.canvas.delete(self.instructionsBackground)
            self.wpWindow.setData(self.waypointsIds, self.canvas)

    def reCreate(self, event):
        # new distance for scan has been selected
        self.d = self.slider.get()
        self.wpWindow.removeEntries()
        self.dronePositionId = None

        items = self.canvas.find_all()
        if self.mode == 2:
            for item in items:
                if (
                    item != self.rectangle
                    and item != self.image
                    and item != self.distanceY
                    and item != self.distanceX
                ):
                    self.canvas.delete(item)
            self.createScan()

        if self.mode == 3:
            for item in items:
                if item != self.line and item != self.image and item != self.distance:
                    self.canvas.delete(item)
            self.createSpiral()

    def createScan(self):

        # azimuth1 = 180 - self.azimuth1
        # azimuth2 = 180 - self.azimuth2
        azimuth1 = self.azimuth1
        azimuth2 = self.azimuth2
        self.posx = self.originposx
        self.posy = self.originposy
        num = math.ceil(self.y / (self.d * self.ppm))
        waypoints = []
        self.waypointToMoveIds = []
        lat = float(self.originlat)
        lon = float(self.originlon)
        ovalId = self.canvas.create_oval(
            self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill="blue"
        )
        textId = self.canvas.create_text(
            self.posx, self.posy, text="H", font=("Courier", 10, "bold"), fill="white"
        )
        self.waypointsIds.append(
            {
                "wpId": "H",
                "textId": textId,
                "ovalId": ovalId,
                "lineInId": 0,
                "lineOutId": 0,
            }
        )

        # insert information of origin waypoint in the table
        self.wpWindow.insertHome(lat, lon)
        cont = 1
        for i in range(num // 2):
            g = self.geod.Direct(lat, lon, azimuth1, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))
            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx =self.posx +  math.trunc(self.x * math.sin(math.radians(azimuth1)))
            # newposy = self.posy + math.trunc(self.x * math.cos(math.radians(azimuth1)))

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            # ----------------------------------
            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(self.d*self.ppm * math.sin(math.radians(azimuth2)))
            # newposy = self.posy + math.trunc(self.d*self.ppm * math.cos(math.radians(azimuth2)))

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            # -------------------------------------
            g = self.geod.Direct(lat, lon, (azimuth1 + 180) % 360, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(self.x * math.sin(math.radians((azimuth1 + 180)%360)))
            # newposy = self.posy + math.trunc(self.x * math.cos(math.radians((azimuth1 + 180)%360)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1
            # ----------------
            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(self.d*self.ppm * math.sin(math.radians(azimuth2)))
            # newposy = self.posy + math.trunc(self.d *self.ppm * math.cos(math.radians(azimuth2)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

        g = self.geod.Direct(lat, lon, azimuth1, self.x * self.mpp)
        lat = float(g["lat2"])
        lon = float(g["lon2"])
        waypoints.append({"lat": lat, "lon": lon, "takePic": False})
        self.wpWindow.insertWP(lat, lon)
        newposx, newposy = self.converter.convertToCoords((lat, lon))

        # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
        # newposx = self.posx + math.trunc(self.x * math.sin(math.radians(azimuth1)))
        # newposy = self.posy + math.trunc(self.x * math.cos(math.radians(azimuth1)))
        lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
        self.posx = newposx
        self.posy = newposy
        ovalId = self.canvas.create_oval(
            self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill="blue"
        )
        textId = self.canvas.create_text(
            self.posx,
            self.posy,
            text=str(cont),
            font=("Courier", 10, "bold"),
            fill="white",
        )
        self.waypointsIds[-1]["lineOutId"] = lineId
        self.waypointsIds.append(
            {
                "wpId": str(cont),
                "textId": textId,
                "ovalId": ovalId,
                "lineInId": lineId,
                "lineOutId": 0,
            }
        )
        cont = cont + 1

        if num % 2 != 0:
            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(self.d*self.ppm * math.sin(math.radians(azimuth2)))
            # newposy = self.posy + math.trunc(self.d*self.ppm * math.cos(math.radians(azimuth2)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1
            # ----------------------------------
            g = self.geod.Direct(lat, lon, (azimuth1 + 180) % 360, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(self.x * math.sin(math.radians((azimuth1 + 180) % 360)))
            # newposy = self.posy + math.trunc(self.x * math.cos(math.radians((azimuth1 + 180) % 360)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
        # insert return to launch in the table
        self.wpWindow.insertRTL()
        self.wpWindow.setData(self.waypointsIds, self.canvas)

        self.done = True
        # waypoints_json = json.dumps(waypoints)
        # self.client.publish("autopilotControllerCommand/executeFlightPlan", waypoints_json)

    def createScan2(self):

        azimuth1 = 180 - self.azimuth1
        azimuth2 = 180 - self.azimuth2
        self.posx = self.originposx
        self.posy = self.originposy
        num = math.ceil(self.y / (self.d * self.ppm))
        waypoints = []
        self.waypointToMoveIds = []
        lat = float(self.originlat)
        lon = float(self.originlon)
        ovalId = self.canvas.create_oval(
            self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill="blue"
        )
        textId = self.canvas.create_text(
            self.posx, self.posy, text="H", font=("Courier", 10, "bold"), fill="white"
        )
        self.waypointsIds.append(
            {
                "wpId": "H",
                "textId": textId,
                "ovalId": ovalId,
                "lineInId": 0,
                "lineOutId": 0,
            }
        )

        # insert information of origin waypoint in the table
        self.wpWindow.insertHome(lat, lon)
        cont = 1
        for i in range(num // 2):
            g = self.geod.Direct(lat, lon, azimuth1, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(self.x * math.sin(math.radians(azimuth1)))
            newposy = self.posy + math.trunc(self.x * math.cos(math.radians(azimuth1)))

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            # ----------------------------------
            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(
                self.d * self.ppm * math.sin(math.radians(azimuth2))
            )
            newposy = self.posy + math.trunc(
                self.d * self.ppm * math.cos(math.radians(azimuth2))
            )

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            # -------------------------------------
            g = self.geod.Direct(lat, lon, (azimuth1 + 180) % 360, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(
                self.x * math.sin(math.radians((azimuth1 + 180) % 360))
            )
            newposy = self.posy + math.trunc(
                self.x * math.cos(math.radians((azimuth1 + 180) % 360))
            )
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(
                self.d * self.ppm * math.sin(math.radians(azimuth2))
            )
            newposy = self.posy + math.trunc(
                self.d * self.ppm * math.cos(math.radians(azimuth2))
            )
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

        g = self.geod.Direct(lat, lon, azimuth1, self.x * self.mpp)
        lat = float(g["lat2"])
        lon = float(g["lon2"])
        waypoints.append({"lat": lat, "lon": lon, "takePic": False})
        self.wpWindow.insertWP(lat, lon)

        # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
        newposx = self.posx + math.trunc(self.x * math.sin(math.radians(azimuth1)))
        newposy = self.posy + math.trunc(self.x * math.cos(math.radians(azimuth1)))
        lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
        self.posx = newposx
        self.posy = newposy
        ovalId = self.canvas.create_oval(
            self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill="blue"
        )
        textId = self.canvas.create_text(
            self.posx,
            self.posy,
            text=str(cont),
            font=("Courier", 10, "bold"),
            fill="white",
        )
        self.waypointsIds[-1]["lineOutId"] = lineId
        self.waypointsIds.append(
            {
                "wpId": str(cont),
                "textId": textId,
                "ovalId": ovalId,
                "lineInId": lineId,
                "lineOutId": 0,
            }
        )
        cont = cont + 1

        if num % 2 != 0:
            g = self.geod.Direct(lat, lon, azimuth2, self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(
                self.d * self.ppm * math.sin(math.radians(azimuth2))
            )
            newposy = self.posy + math.trunc(
                self.d * self.ppm * math.cos(math.radians(azimuth2))
            )
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            g = self.geod.Direct(lat, lon, (azimuth1 + 180) % 360, self.x * self.mpp)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            newposx = self.posx + math.trunc(
                self.x * math.sin(math.radians((azimuth1 + 180) % 360))
            )
            newposy = self.posy + math.trunc(
                self.x * math.cos(math.radians((azimuth1 + 180) % 360))
            )
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )

        self.done = True
        self.wpWindow.setData(self.waypointsIds, self.canvas)
        # waypoints_json = json.dumps(waypoints)
        # self.client.publish("autopilotControllerCommand/executeFlightPlan", waypoints_json)

    def createSpiral(self):

        # azimuth = 180 - self.azimuth
        azimuth = self.azimuth
        self.posx = self.originx
        self.posy = self.originy
        num = math.ceil(self.x / (self.d * self.ppm))
        waypoints = []
        self.waypointToMoveIds = []
        lat = float(self.originlat)
        lon = float(self.originlon)
        ovalId = self.canvas.create_oval(
            self.posx - 10, self.posy - 10, self.posx + 10, self.posy + 10, fill="blue"
        )
        textId = self.canvas.create_text(
            self.posx, self.posy, text="H", font=("Courier", 10, "bold"), fill="white"
        )
        self.waypointsIds.append(
            {
                "wpId": "H",
                "textId": textId,
                "ovalId": ovalId,
                "lineInId": 0,
                "lineOutId": 0,
            }
        )

        # insert information of origin waypoint in the table
        self.wpWindow.insertHome(lat, lon)
        # self.table.insert(parent='', index='end', iid=0, text='', values=('H', lat,lon))
        cont = 1
        for i in range(num):
            dist = (2 * i + 1) * self.d
            g = self.geod.Direct(lat, lon, azimuth, dist)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx =self.posx +  math.trunc(dist*self.ppm * math.sin(math.radians(azimuth)))
            # newposy = self.posy + math.trunc(dist*self.ppm * math.cos(math.radians(azimuth)))

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            g = self.geod.Direct(lat, lon, azimuth + 90, dist)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc(dist*self.ppm * math.sin(math.radians(azimuth+90)))
            # newposy = self.posy + math.trunc(dist*self.ppm * math.cos(math.radians(azimuth+90)))

            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy

            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            g = self.geod.Direct(lat, lon, azimuth + 180, dist + self.d)
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc((dist+self.d)*self.ppm * math.sin(math.radians(azimuth + 180)))
            # newposy = self.posy + math.trunc((dist+self.d)*self.ppm * math.cos(math.radians(azimuth + 180)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1

            g = self.geod.Direct(lat, lon, azimuth + 270, (dist + self.d))
            lat = float(g["lat2"])
            lon = float(g["lon2"])
            waypoints.append({"lat": lat, "lon": lon, "takePic": False})
            self.wpWindow.insertWP(lat, lon)
            newposx, newposy = self.converter.convertToCoords((lat, lon))

            # self.table.insert(parent='', index='end', iid=cont, text='take picture?', values=(cont, lat, lon))
            # newposx = self.posx + math.trunc((dist+self.d)*self.ppm * math.sin(math.radians(azimuth + 270)))
            # newposy = self.posy + math.trunc((dist+self.d)*self.ppm * math.cos(math.radians(azimuth + 270)))
            lineId = self.canvas.create_line(self.posx, self.posy, newposx, newposy)
            self.posx = newposx
            self.posy = newposy
            ovalId = self.canvas.create_oval(
                self.posx - 10,
                self.posy - 10,
                self.posx + 10,
                self.posy + 10,
                fill="blue",
            )
            textId = self.canvas.create_text(
                self.posx,
                self.posy,
                text=str(cont),
                font=("Courier", 10, "bold"),
                fill="white",
            )
            self.waypointsIds[-1]["lineOutId"] = lineId
            self.waypointsIds.append(
                {
                    "wpId": str(cont),
                    "textId": textId,
                    "ovalId": ovalId,
                    "lineInId": lineId,
                    "lineOutId": 0,
                }
            )
            cont = cont + 1
        self.wpWindow.insertRTL()
        self.wpWindow.setData(self.waypointsIds, self.canvas)
        self.done = True



