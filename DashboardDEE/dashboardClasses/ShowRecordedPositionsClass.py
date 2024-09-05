import tkinter as tk
from tkinter import ttk


class RecordedPositionsWindow:
    def __init__(self, frame):
        self.frame = frame

    def openWindowToShowRecordedPositions(self):
        # Open a new small window to show the positions timestamp to be received from the data service
        self.newWindow = tk.Toplevel(self.frame)

        self.newWindow.title("Recorded positions")

        self.newWindow.geometry("400x400")
        self.table = ttk.Treeview(self.newWindow)

        self.table["columns"] = ("time", "latitude", "longitude")

        self.table.column("#0", width=0, stretch=tk.NO)
        self.table.column("time", anchor=tk.CENTER, width=150)
        self.table.column("latitude", anchor=tk.CENTER, width=80)
        self.table.column("longitude", anchor=tk.CENTER, width=80)

        self.table.heading("#0", text="", anchor=tk.CENTER)
        self.table.heading("time", text="Time", anchor=tk.CENTER)
        self.table.heading("latitude", text="Latitude", anchor=tk.CENTER)
        self.table.heading("longitude", text="Longitude", anchor=tk.CENTER)

        # requiere the stored positions from the data service
        print("pido stored positions")
        self.client.subscribe("dataService/dashBoard/storedPositions")
        self.client.publish("dashBoard/dataService/getStoredPositions")
        # self.client.publish('dashBoard/dataService/getStoredPositions')

        tk.Button(
            self.newWindow,
            text="Close",
            bg="red",
            fg="white",
            command=self.closeWindowToShowRecordedPositions,
        ).pack()

    def closeWindowToShowRecordedPositions(self):
        self.newWindow.destroy()

    def putClient(self, client):
        self.client = client

    def putStoredPositions(self, dataJson):
        cont = 0
        for dataItem in dataJson:
            self.table.insert(
                parent="",
                index="end",
                iid=cont,
                text="",
                values=(dataItem["time"], dataItem["lat"], dataItem["lon"]),
            )
            cont = cont + 1

        self.table.pack()
