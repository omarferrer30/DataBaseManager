import tkinter as tk


class TelemetryInfoFrame:
    def buldFrame(self, fatherFrame):
        self.telemetryInfoFrame = tk.LabelFrame(
            fatherFrame, text="Telemetry info", width=50
        )

        self.telemetryInfoFrame.rowconfigure(0, weight=1)
        self.telemetryInfoFrame.rowconfigure(1, weight=1)
        self.telemetryInfoFrame.rowconfigure(2, weight=1)
        self.telemetryInfoFrame.columnconfigure(0, weight=1)
        self.telemetryInfoFrame.columnconfigure(1, weight=1)
        self.telemetryInfoFrame.columnconfigure(2, weight=1)
        self.telemetryInfoFrame.columnconfigure(3, weight=1)

        self.latLabel = tk.Label(self.telemetryInfoFrame, text="lat", width=8)
        self.latLabel.grid(row=0, column=0, padx=2, pady=5, sticky=tk.E)
        self.latBox = tk.Label(
            self.telemetryInfoFrame, text="lat", width=12, font=("Courier", 12, "bold")
        )
        self.latBox.grid(
            row=0, column=1, padx=2, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.headingLabel = tk.Label(self.telemetryInfoFrame, text="heading", width=8)
        self.headingLabel.grid(row=0, column=2, padx=2, pady=5, sticky=tk.E)
        self.headingBox = tk.Label(
            self.telemetryInfoFrame,
            width=5,
            text="heading",
            font=("Courier", 12, "bold"),
        )
        self.headingBox.grid(
            row=0, column=3, padx=2, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.lonLabel = tk.Label(self.telemetryInfoFrame, text="lon", width=8)
        self.lonLabel.grid(row=1, column=0, padx=2, pady=5, sticky=tk.E)
        self.lonBox = tk.Label(
            self.telemetryInfoFrame, text="lon", width=12, font=("Courier", 12, "bold")
        )
        self.lonBox.grid(
            row=1, column=1, padx=2, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.speedLabel = tk.Label(self.telemetryInfoFrame, text="speed", width=8)
        self.speedLabel.grid(row=1, column=2, padx=2, pady=5, sticky=tk.E)
        self.speedBox = tk.Label(
            self.telemetryInfoFrame, width=5, text="speed", font=("Courier", 12, "bold")
        )
        self.speedBox.grid(
            row=1, column=3, padx=2, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.altitudeLabel = tk.Label(self.telemetryInfoFrame, text="altitude", width=8)
        self.altitudeLabel.grid(row=2, column=0, padx=2, pady=5, sticky=tk.E)
        self.altitudeBox = tk.Label(
            self.telemetryInfoFrame,
            width=12,
            text="altitude",
            font=("Courier", 12, "bold"),
        )
        self.altitudeBox.grid(
            row=2, column=1, padx=2, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        self.batteryLabel = tk.Label(self.telemetryInfoFrame, text="battery", width=8)
        self.batteryLabel.grid(row=2, column=2, padx=2, pady=5, sticky=tk.E)
        self.batteryBox = tk.Label(
            self.telemetryInfoFrame,
            width=5,
            text="battery",
            font=("Courier", 12, "bold"),
        )
        self.batteryBox.grid(
            row=2, column=3, padx=2, pady=5, sticky=tk.N + tk.S + tk.E + tk.W
        )

        return self.telemetryInfoFrame

    def showTelemetryInfo(self, telemetyInfo):

        self.latBox["text"] = round(telemetyInfo["lat"], 6)
        self.lonBox["text"] = round(telemetyInfo["lon"], 6)
        self.speedBox["text"] = round(telemetyInfo["groundSpeed"], 2)
        self.headingBox["text"] = round(telemetyInfo["heading"], 0)
        self.altitudeBox["text"] = round(telemetyInfo["altitude"], 2)
        self.batteryBox["text"] = round(telemetyInfo["battery"], 0)
