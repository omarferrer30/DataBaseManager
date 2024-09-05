import math
import tkinter as tk
from tkinter import messagebox, PhotoImage
from tkinter.ttk import Treeview, Scrollbar, Style
from datetime import datetime as dt
from datetime import datetime
import json
from PIL import Image, ImageTk

from dashboardClasses.FlightPlanDesignerClass import FlightPlanDesignerWindow


class DataBaseManagerWindow:
    def __init__(self, frame, client):
        self.frame = frame
        self.client = client
        self.client.publish("dashBoard/groundApiService/getAllFlightPlans")
        self.client.publish("dashBoard/airApiService/getAllFlightPlans")
        self.client.publish("dashBoard/groundApiService/getAllFlights")
        self.client.publish("dashBoard/airApiService/getAllFlights")
        self.newWindow = None
        self.tierra_treeview = None
        self.aire_treeview = None
        self.tierra_flights_treeview = None
        self.aire_flights_treeview = None
        self.loaded_flight_plans_tierra = []
        self.loaded_flight_plans_aire = []

    def openDBManagerWindow(self):
        self.newWindow = tk.Toplevel(self.frame)
        self.newWindow.title("Data Bases Manager")
        self.newWindow.geometry("900x700")
        self.newWindow.configure(bg='#2E2E2E')

        # Estilos
        style = Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="#D3D3D3",
                        foreground="black",
                        rowheight=25,
                        fieldbackground="#D3D3D3",
                        font=('Helvetica', 12))
        style.map('Treeview', background=[('selected', '#347083')])

        style.configure("Treeview.Heading",
                        background="#4CAF50",  # Color verde para la API de Tierra
                        foreground="white",
                        font=('Helvetica', 12, 'bold'))

        style.configure("TButton",
                        background="#5DADE2",
                        foreground="white",
                        font=('Helvetica', 12, 'bold'))
        style.map('TButton', background=[('active', '#2E86C1')])

        title_label = tk.Label(self.newWindow, text="Data Base Manager", font=("Helvetica", 24, "bold"), fg="#FFFFFF",
                               bg='#2E2E2E')
        title_label.grid(row=0, column=0, columnspan=2, pady=20)

        main_frame = tk.Frame(self.newWindow, bg='#2E2E2E')
        main_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)

        # Configuración de las columnas y filas para que se expandan
        self.newWindow.grid_rowconfigure(1, weight=1)
        self.newWindow.grid_columnconfigure(0, weight=1)
        self.newWindow.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Marco izquierdo con tabla de flight plans de la API de Tierra
        left_frame = tk.Frame(main_frame, bg='#D5F5E3')
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left_label = tk.Label(left_frame, text=" Ground API - Flight Plans", font=("Helvetica", 16, "bold"),
                              fg="#1D8348", bg='#D5F5E3')
        left_label.pack()

        # Scrollbar para la tabla de flight plans de la API de Tierra
        left_scrollbar_y = Scrollbar(left_frame, orient="vertical")
        left_scrollbar_y.pack(side="right", fill="y")

        left_scrollbar_x = Scrollbar(left_frame, orient="horizontal")
        left_scrollbar_x.pack(side="bottom", fill="x")

        self.tierra_treeview = Treeview(left_frame, columns=(
            "Title", "DateAdded", "NumWaypoints", "NumPics", "NumVids", "PicInterval", "VidTimeStatic"),
                                        show="headings",
                                        yscrollcommand=left_scrollbar_y.set, xscrollcommand=left_scrollbar_x.set,
                                        style="Treeview")
        self.tierra_treeview.heading("Title", text="Title")
        self.tierra_treeview.heading("DateAdded", text="DateAdded")
        self.tierra_treeview.heading("NumWaypoints", text="NumWaypoints")
        self.tierra_treeview.heading("NumPics", text="NumPics")
        self.tierra_treeview.heading("NumVids", text="NumVids")
        self.tierra_treeview.heading("PicInterval", text="PicInterval")
        self.tierra_treeview.heading("VidTimeStatic", text="VidTimeStatic")
        self.tierra_treeview.pack(fill="both", expand=True)

        left_scrollbar_y.config(command=self.tierra_treeview.yview)
        left_scrollbar_x.config(command=self.tierra_treeview.xview)

        # Marco derecho con tabla de flight plans de la API de Aire
        right_frame = tk.Frame(main_frame, bg='#AED6F1')
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        right_label = tk.Label(right_frame, text="Air API - Flight Plans", font=("Helvetica", 16, "bold"), fg="#1B4F72",
                               bg='#AED6F1')
        right_label.pack()

        # Scrollbar para la tabla de flight plans de la API de Aire
        right_scrollbar_y = Scrollbar(right_frame, orient="vertical")
        right_scrollbar_y.pack(side="right", fill="y")

        right_scrollbar_x = Scrollbar(right_frame, orient="horizontal")
        right_scrollbar_x.pack(side="bottom", fill="x")

        self.aire_treeview = Treeview(right_frame, columns=(
            "Title", "DateAdded", "NumWaypoints", "NumPics", "NumVids", "PicInterval", "VidTimeStatic"),
                                      show="headings",
                                      yscrollcommand=right_scrollbar_y.set, xscrollcommand=right_scrollbar_x.set,
                                      style="Treeview")
        self.aire_treeview.heading("Title", text="Title")
        self.aire_treeview.heading("DateAdded", text="DateAdded")
        self.aire_treeview.heading("NumWaypoints", text="NumWaypoints")
        self.aire_treeview.heading("NumPics", text="NumPics")
        self.aire_treeview.heading("NumVids", text="NumVids")
        self.aire_treeview.heading("PicInterval", text="PicInterval")
        self.aire_treeview.heading("VidTimeStatic", text="VidTimeStatic")
        self.aire_treeview.pack(fill="both", expand=True)

        right_scrollbar_y.config(command=self.aire_treeview.yview)
        right_scrollbar_x.config(command=self.aire_treeview.xview)

        # Marco izquierdo con tabla de flights de la API de Tierra
        left_flights_frame = tk.Frame(main_frame, bg='#D5F5E3')
        left_flights_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        left_flights_label = tk.Label(left_flights_frame, text="Ground API - Flights", font=("Helvetica", 16, "bold"),
                                      fg="#1D8348", bg='#D5F5E3')
        left_flights_label.pack()

        # Scrollbar para la tabla de flights de la API de Tierra
        left_flights_scrollbar_y = Scrollbar(left_flights_frame, orient="vertical")
        left_flights_scrollbar_y.pack(side="right", fill="y")

        left_flights_scrollbar_x = Scrollbar(left_flights_frame, orient="horizontal")
        left_flights_scrollbar_x.pack(side="bottom", fill="x")

        self.tierra_flights_treeview = Treeview(left_flights_frame, columns=(
            "Title", "Date", "Description", "NumPics", "NumVids", "FlightSuccess"), show="headings",
                                                yscrollcommand=left_flights_scrollbar_y.set,
                                                xscrollcommand=left_flights_scrollbar_x.set,
                                                style="Treeview")
        self.tierra_flights_treeview.heading("Title", text="Title")
        self.tierra_flights_treeview.heading("Date", text="Date")
        self.tierra_flights_treeview.heading("Description", text="Description")
        self.tierra_flights_treeview.heading("NumPics", text="NumPics")
        self.tierra_flights_treeview.heading("NumVids", text="NumVids")
        self.tierra_flights_treeview.heading("FlightSuccess", text="FlightSuccess")
        self.tierra_flights_treeview.pack(fill="both", expand=True)

        left_flights_scrollbar_y.config(command=self.tierra_flights_treeview.yview)
        left_flights_scrollbar_x.config(command=self.tierra_flights_treeview.xview)

        right_flights_frame = tk.Frame(main_frame, bg='#AED6F1')
        right_flights_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        right_flights_label = tk.Label(right_flights_frame, text="Air API - Flights", font=("Helvetica", 16, "bold"),
                                       fg="#1B4F72", bg='#AED6F1')
        right_flights_label.pack()

        right_flights_scrollbar_y = Scrollbar(right_flights_frame, orient="vertical")
        right_flights_scrollbar_y.pack(side="right", fill="y")

        right_flights_scrollbar_x = Scrollbar(right_flights_frame,
                                              orient="horizontal")
        right_flights_scrollbar_x.pack(side="bottom", fill="x")

        self.aire_flights_treeview = Treeview(right_flights_frame, columns=(
            "Title", "Date", "Description", "NumPics", "NumVids", "FlightSuccess"), show="headings",
             yscrollcommand=right_flights_scrollbar_y.set,
             xscrollcommand=right_flights_scrollbar_x.set,
             style="Treeview")
        self.aire_flights_treeview.heading("Title", text="Title")
        self.aire_flights_treeview.heading("Date", text="Date")
        self.aire_flights_treeview.heading("Description", text="Description")
        self.aire_flights_treeview.heading("NumPics", text="NumPics")
        self.aire_flights_treeview.heading("NumVids", text="NumVids")
        self.aire_flights_treeview.heading("FlightSuccess", text="FlightSuccess")
        self.aire_flights_treeview.pack(fill="both", expand=True)

        right_flights_scrollbar_y.config(command=self.aire_flights_treeview.yview)
        right_flights_scrollbar_x.config(
            command=self.aire_flights_treeview.xview)

        self.update_style_for_air_api()

        self.tierra_treeview.bind("<Button-3>", self.show_context_menu)
        self.aire_treeview.bind("<Button-3>", self.show_context_menu)
        self.tierra_flights_treeview.bind("<Button-3>", self.show_context_menu)
        self.aire_flights_treeview.bind("<Button-3>", self.show_context_menu)

        return self

    def update_style_for_air_api(self):
        style = Style()
        style.configure("AirAPI.Treeview.Heading",
                        background="#5DADE2",
                        foreground="white",
                        font=('Helvetica', 12, 'bold'))

        self.aire_treeview.configure(style="AirAPI.Treeview")
        self.aire_flights_treeview.configure(style="AirAPI.Treeview")

    def loadFromDBLeft(self, flightPlans):
        self.loaded_flight_plans_tierra = flightPlans
        if not self.newWindow:
            print("Error: La ventana de administración de la base de datos no está abierta.")

        print('flightPlans:' + flightPlans[1]['Title'])
        waypoints = flightPlans

        for item in self.tierra_treeview.get_children():
            self.tierra_treeview.delete(item)

        for waypoint in waypoints:
            try:
                timestamp = waypoint["DateAdded"]["$date"] / 1000
                formatted_date = dt.fromtimestamp(timestamp).strftime("%m-%d %H:%M:%S")
                self.tierra_treeview.insert(
                    "",
                    "end",
                    iid=waypoint["_id"]["$oid"],
                    values=(
                        waypoint["Title"],
                        formatted_date,
                        waypoint["NumWaypoints"],
                        waypoint["NumPics"],
                        waypoint["NumVids"],
                        waypoint["PicInterval"],
                        waypoint.get("VidTimeStatic", 0)
                    ),
                    text=json.dumps(waypoint),
                )
            except KeyError as e:
                print(f"Error: Key missing en los datos: {e}")
            except Exception as e:
                print(f"Error inesperado: {e}")

    def loadFromDBRight(self, flightPlans):
        self.loaded_flight_plans_aire = flightPlans
        if not self.aire_treeview:
            print("Error: La ventana de administración de la base de datos no está abierta.")
            return

        waypoints = flightPlans

        for item in self.aire_treeview.get_children():
            self.aire_treeview.delete(item)

        for plan in waypoints:
            try:
                timestamp = plan["DateAdded"]["$date"] / 1000
                formatted_date = dt.fromtimestamp(timestamp).strftime("%m-%d %H:%M:%S")
                self.aire_treeview.insert(
                    "",
                    "end",
                    iid=plan["_id"]["$oid"],
                    values=(
                        plan["Title"],
                        formatted_date,
                        plan["NumWaypoints"],
                        plan["NumPics"],
                        plan["NumVids"],
                        plan["PicInterval"],
                        plan.get("VidTimeStatic", 0)
                    ),
                    text=json.dumps(plan),
                )
            except KeyError as e:
                print(f"Error: Clave faltante en los datos: {e}")
            except Exception as e:
                print(f"Error inesperado: {e}")

    def loadFlightsFromDBLeft(self, flights):
        if not self.newWindow:
            print("Error: La ventana de administración de la base de datos no está abierta.")

        for item in self.tierra_flights_treeview.get_children():
            self.tierra_flights_treeview.delete(item)

        for flight in flights:
            try:
                date_timestamp = flight["Date"]["$date"] / 1000
                start_timestamp = flight["startTime"]["$date"] / 1000
                end_timestamp = flight["endTime"]["$date"] / 1000
                formatted_date = dt.fromtimestamp(date_timestamp).strftime("%m-%d %H:%M:%S")
                formatted_start_time = dt.fromtimestamp(start_timestamp).strftime("%m-%d %H:%M:%S")
                formatted_end_time = dt.fromtimestamp(end_timestamp).strftime("%m-%d %H:%M:%S")
                self.tierra_flights_treeview.insert(
                    "",
                    "end",
                    iid=flight["_id"]["$oid"],
                    values=(
                        flight["Title"],
                        formatted_date,
                        flight["Description"],
                        flight["NumPics"],
                        flight["NumVids"],
                        flight["FlightSuccess"]
                    ),
                    text=json.dumps(flight),
                )
            except KeyError as e:
                print(f"Error: Clave faltante en los datos: {e}")
            except Exception as e:
                print(f"Error inesperado: {e}")

    def loadFlightsFromDBRight(self, flights):
        if not self.aire_flights_treeview:
            print("Error: La ventana de administración de la base de datos no está abierta.")
            return

        for item in self.aire_flights_treeview.get_children():
            self.aire_flights_treeview.delete(item)

        for flight in flights:
            try:
                date_timestamp = flight["Date"]["$date"] / 1000
                start_timestamp = flight["startTime"]["$date"] / 1000
                end_timestamp = flight["endTime"]["$date"] / 1000
                formatted_date = dt.fromtimestamp(date_timestamp).strftime("%m-%d %H:%M:%S")
                formatted_start_time = dt.fromtimestamp(start_timestamp).strftime("%m-%d %H:%M:%S")
                formatted_end_time = dt.fromtimestamp(end_timestamp).strftime("%m-%d %H:%M:%S")
                self.aire_flights_treeview.insert(
                    "",
                    "end",
                    iid=flight["_id"]["$oid"],
                    values=(
                        flight["Title"],
                        formatted_date,
                        flight["Description"],
                        flight["NumPics"],
                        flight["NumVids"],
                        flight["FlightSuccess"]
                    ),
                    text=json.dumps(flight),
                )
            except KeyError as e:
                print(f"Error: Clave faltante en los datos: {e}")
            except Exception as e:
                print(f"Error inesperado: {e}")

    def show_context_menu(self, event):
        tree = event.widget
        item_id = tree.identify_row(event.y)
        if item_id:
            tree.selection_set(item_id)
            menu = tk.Menu(self.newWindow, tearoff=0, bg='#2E2E2E', fg='#FFFFFF')
            menu.add_command(label="Editar", command=lambda: self.edit_plan(tree, item_id))
            menu.add_command(label="Eliminar", command=lambda: self.confirm_delete(tree, item_id))
            menu.add_command(label="Duplicar", command=lambda: self.duplicate_plan(tree, item_id))
            menu.add_command(label="Ver", command=lambda: self.view_waypoints(tree, item_id))
            if tree == self.tierra_treeview or tree == self.tierra_flights_treeview:
                menu.add_command(label="Pasar a API de Aire", command=lambda: self.move_to_aire(tree, item_id))
            else:
                menu.add_command(label="Pasar a API de Tierra", command=lambda: self.move_to_tierra(tree, item_id))
            menu.post(event.x_root, event.y_root)

    def confirm_delete(self, tree, plan_id):
        confirm_window = tk.Toplevel(self.newWindow)
        confirm_window.title("Confirm Delete")
        confirm_window.geometry("300x100")
        confirm_window.transient(self.newWindow)
        confirm_window.grab_set()
        confirm_window.configure(bg='#2E2E2E')
        confirm_window.protocol("WM_DELETE_WINDOW",
                                lambda: self.close_confirm_window(confirm_window))

        self.newWindow.update_idletasks()
        window_width = self.newWindow.winfo_width()
        window_height = self.newWindow.winfo_height()
        window_x = self.newWindow.winfo_x()
        window_y = self.newWindow.winfo_y()

        popup_width = 300
        popup_height = 100

        x = window_x + (window_width // 2) - (popup_width // 2)
        y = window_y + (window_height // 2) - (popup_height // 2)
        confirm_window.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

        confirm_label = tk.Label(confirm_window, text="Are you sure you want to delete this item?", bg='#2E2E2E',
                                 fg='#FFFFFF', wraplength=280)
        confirm_label.pack(pady=10)
        button_frame = tk.Frame(confirm_window, bg='#2E2E2E')
        button_frame.pack(pady=10)
        confirm_button = tk.Button(button_frame, text="Yes",
                                   command=lambda: self.delete_plan(tree, plan_id, confirm_window), bg='#5DADE2',
                                   fg='white')
        confirm_button.pack(side="left", padx=10)
        cancel_button = tk.Button(button_frame, text="No", command=lambda: self.close_confirm_window(confirm_window),
                                  bg='#E74C3C', fg='white')
        cancel_button.pack(side="left", padx=10)

    def close_confirm_window(self, window):
        window.grab_release()
        window.destroy()

    def edit_plan(self, tree, plan_id):
        item = tree.item(plan_id)
        plan_data = json.loads(item['text'])

        edit_window = tk.Toplevel(self.newWindow)
        edit_window.title("Editar Flight Plan")
        edit_window.transient(self.newWindow)
        edit_window.grab_set()
        edit_window.configure(bg='#2E2E2E')
        edit_window.resizable(True, True)

        # canvas
        canvas = tk.Canvas(edit_window, bg='#2E2E2E')
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # scrollbar
        scrollbar = tk.Scrollbar(edit_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)
        # frame for canvas
        form_frame = tk.Frame(canvas, bg='#2E2E2E')
        canvas.create_window((0, 0), window=form_frame, anchor="nw")

        form_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        title_var = tk.StringVar(value=plan_data.get('Title', ''))
        pic_interval_var = tk.DoubleVar(value=plan_data.get('PicInterval', 0))
        vid_interval_var = tk.DoubleVar(value=plan_data.get('VidTimeStatic', 0))

        tk.Label(form_frame, text="Title", bg='#2E2E2E', fg='#FFFFFF').grid(row=0, column=0, padx=10, pady=5)
        tk.Entry(form_frame, textvariable=title_var, bg='#1C1C1C', fg='#FFFFFF').grid(row=0, column=1, padx=10, pady=5)

        tk.Label(form_frame, text="Pic Interval", bg='#2E2E2E', fg='#FFFFFF').grid(row=1, column=0, padx=10, pady=5)
        tk.Entry(form_frame, textvariable=pic_interval_var, bg='#1C1C1C', fg='#FFFFFF').grid(row=1, column=1, padx=10,
                                                                                             pady=5)

        tk.Label(form_frame, text="Vid Time Static", bg='#2E2E2E', fg='#FFFFFF').grid(row=2, column=0, padx=10, pady=5)
        tk.Entry(form_frame, textvariable=vid_interval_var, bg='#1C1C1C', fg='#FFFFFF').grid(row=2, column=1, padx=10,
                                                                                             pady=5)

        tk.Label(form_frame, text="Flight Waypoints", bg='#2E2E2E', fg='#FFFFFF', font=('Helvetica', 10, 'bold')).grid(
            row=3, column=0, columnspan=2, pady=5)
        waypoints_frame = tk.Frame(form_frame, bg='#2E2E2E')
        waypoints_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="nsew")

        waypoint_vars = []
        for i, wp in enumerate(plan_data.get('FlightWaypoints', [])):
            self.add_waypoint_row(waypoints_frame, waypoint_vars, i, wp)
        if not waypoint_vars:
            self.add_waypoint_row(waypoints_frame, waypoint_vars)

        tk.Label(form_frame, text="Pics Waypoints", bg='#2E2E2E', fg='#FFFFFF', font=('Helvetica', 10, 'bold')).grid(
            row=5 + len(waypoint_vars), column=0, columnspan=2, pady=5)
        pics_waypoints_frame = tk.Frame(form_frame, bg='#2E2E2E')
        pics_waypoints_frame.grid(row=6 + len(waypoint_vars), column=0, columnspan=2, pady=10, sticky="nsew")

        pics_waypoint_vars = []
        for i, wp in enumerate(plan_data.get('PicsWaypoints', [])):
            self.add_waypoint_row(pics_waypoints_frame, pics_waypoint_vars, i, wp)
        if not pics_waypoint_vars:
            self.add_waypoint_row(pics_waypoints_frame, pics_waypoint_vars)

        tk.Label(form_frame, text="Static Vid Waypoints", bg='#2E2E2E', fg='#FFFFFF',
                 font=('Helvetica', 10, 'bold')).grid(
            row=7 + len(waypoint_vars) + len(pics_waypoint_vars), column=0, columnspan=2, pady=5)
        vids_waypoints_frame = tk.Frame(form_frame, bg='#2E2E2E')
        vids_waypoints_frame.grid(row=8 + len(waypoint_vars) + len(pics_waypoint_vars), column=0, columnspan=2, pady=10,
                                  sticky="nsew")

        vids_waypoint_vars = []
        for i, wp in enumerate(plan_data.get('VidWaypoints', [])):
            self.add_waypoint_row(vids_waypoints_frame, vids_waypoint_vars, i, wp)
        if not vids_waypoint_vars:
            self.add_waypoint_row(vids_waypoints_frame, vids_waypoint_vars)

        add_waypoint_button = tk.Button(form_frame, text="Añadir Waypoint a Flight",
                                        command=lambda: self.add_waypoint_row(waypoints_frame, waypoint_vars),
                                        bg='#5DADE2', fg='white')
        add_waypoint_button.grid(row=9 + len(waypoint_vars) + len(pics_waypoint_vars) + len(vids_waypoint_vars),
                                 column=0, columnspan=2, pady=10)

        add_pic_waypoint_button = tk.Button(form_frame, text="Añadir Waypoint a Pics",
                                            command=lambda: self.add_waypoint_row(pics_waypoints_frame,
                                                                                  pics_waypoint_vars),
                                            bg='#5DADE2', fg='white')
        add_pic_waypoint_button.grid(row=10 + len(waypoint_vars) + len(pics_waypoint_vars) + len(vids_waypoint_vars),
                                     column=0, columnspan=2, pady=10)

        add_vid_waypoint_button = tk.Button(form_frame, text="Añadir Waypoint a Static Vid",
                                            command=lambda: self.add_waypoint_row(vids_waypoints_frame,
                                                                                  vids_waypoint_vars, is_static=True),
                                            bg='#5DADE2', fg='white')
        add_vid_waypoint_button.grid(row=11 + len(waypoint_vars) + len(pics_waypoint_vars) + len(vids_waypoint_vars),
                                     column=0, columnspan=2, pady=10)

        # Botón para guardar los cambios
        save_button = tk.Button(form_frame, text="Guardar",
                                command=lambda: self.save_plan_edit(tree, plan_id, title_var, pic_interval_var,
                                                                    vid_interval_var, waypoint_vars,
                                                                    pics_waypoint_vars, vids_waypoint_vars,
                                                                    edit_window),
                                bg='#5DADE2', fg='white')
        save_button.grid(row=12 + len(waypoint_vars) + len(pics_waypoint_vars) + len(vids_waypoint_vars), column=0,
                         columnspan=2, pady=20)

        form_frame.update_idletasks()
        width = form_frame.winfo_width() + 30
        height = form_frame.winfo_height() + 30
        screen_width = edit_window.winfo_screenwidth()
        screen_height = edit_window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        edit_window.geometry(f"{width}x{height}+{x}+{y}")
        edit_window.minsize(width, height)

    def add_waypoint_row(self, parent_frame, waypoint_vars, index=None, wp=None, is_static=False):
        if wp is None:
            wp = {}

        lat_var = tk.DoubleVar(value=wp.get('lat', 0.0))
        lon_var = tk.DoubleVar(value=wp.get('lon', 0.0))
        height_or_length_var = tk.DoubleVar(value=wp.get('height', 0.0) if not is_static else wp.get('length', 0.0))

        row = len(waypoint_vars) if index is None else index

        tk.Label(parent_frame, text=f"Waypoint {row + 1} Lat", bg='#2E2E2E', fg='#FFFFFF').grid(row=row, column=0,
                                                                                                padx=10, pady=5)
        tk.Entry(parent_frame, textvariable=lat_var, bg='#1C1C1C', fg='#FFFFFF').grid(row=row, column=1, padx=10,
                                                                                      pady=5)

        tk.Label(parent_frame, text=f"Waypoint {row + 1} Lon", bg='#2E2E2E', fg='#FFFFFF').grid(row=row, column=2,
                                                                                                padx=10, pady=5)
        tk.Entry(parent_frame, textvariable=lon_var, bg='#1C1C1C', fg='#FFFFFF').grid(row=row, column=3, padx=10,
                                                                                      pady=5)

        if is_static:
            tk.Label(parent_frame, text=f"Waypoint {row + 1} Length", bg='#2E2E2E', fg='#FFFFFF').grid(row=row,
                                                                                                       column=4,
                                                                                                       padx=10, pady=5)
            tk.Entry(parent_frame, textvariable=height_or_length_var, bg='#1C1C1C', fg='#FFFFFF').grid(row=row,
                                                                                                       column=5,
                                                                                                       padx=10, pady=5)
        else:
            tk.Label(parent_frame, text=f"Waypoint {row + 1} Height", bg='#2E2E2E', fg='#FFFFFF').grid(row=row,
                                                                                                       column=4,
                                                                                                       padx=10, pady=5)
            tk.Entry(parent_frame, textvariable=height_or_length_var, bg='#1C1C1C', fg='#FFFFFF').grid(row=row,
                                                                                                       column=5,
                                                                                                       padx=10, pady=5)

        remove_button = tk.Button(parent_frame, text="Eliminar",
                                  command=lambda: self.remove_waypoint_row(parent_frame, waypoint_vars, row),
                                  bg='#E74C3C', fg='white')
        remove_button.grid(row=row, column=6, padx=10, pady=5)

        waypoint_vars.append((lat_var, lon_var, height_or_length_var))

    def remove_waypoint_row(self, parent_frame, waypoint_vars, index):
        for widget in parent_frame.grid_slaves():
            if int(widget.grid_info()["row"]) == index:
                widget.grid_forget()

        waypoint_vars.pop(index)

        for i in range(index, len(waypoint_vars)):
            for widget in parent_frame.grid_slaves():
                if int(widget.grid_info()["row"]) == i + 1:
                    widget.grid_configure(row=i)

    def save_plan_edit(self, tree, plan_id, title_var, pic_interval_var, vid_interval_var,
                       waypoint_vars, pics_waypoint_vars, vids_waypoint_vars, edit_window):

        updated_waypoints = []
        for lat_var, lon_var, height_or_length_var in waypoint_vars:
            updated_waypoints.append({
                "lat": lat_var.get(),
                "lon": lon_var.get(),
                "height": height_or_length_var.get(),
                "takePic": False,
                "videoStart": False,
                "videoStop": False,
                "staticVideo": False
            })

        for pic_wp in updated_waypoints:
            for lat_var, lon_var, height_or_length_var in pics_waypoint_vars:
                if (pic_wp["lat"] == lat_var.get() and
                        pic_wp["lon"] == lon_var.get() and
                        pic_wp["height"] == height_or_length_var.get()):
                    pic_wp["takePic"] = True

        for vid_wp in updated_waypoints:
            for lat_var, lon_var, _ in vids_waypoint_vars:
                if (vid_wp["lat"] == lat_var.get() and
                        vid_wp["lon"] == lon_var.get()):
                    vid_wp["staticVideo"] = True

        updated_data = {
            "Title": title_var.get(),
            "PicInterval": pic_interval_var.get(),
            "VidInterval": vid_interval_var.get(),
            "waypoints": updated_waypoints,
            "PicsWaypoints": [],
            "VidWaypoints": []
        }

        service = "groundApiService" if tree in [self.tierra_treeview,
                                                 self.tierra_flights_treeview] else "airApiService"
        self.client.publish(f"dashBoard/{service}/updateFlightPlan", json.dumps({"id": plan_id, "data": updated_data}))
        edit_window.grab_release()
        edit_window.destroy()
        self.refresh_flight_plans()

    def view_waypoints(self, tree, plan_id):
        item = tree.item(plan_id)
        plan_data = json.loads(item['text'])

        if tree in [self.tierra_flights_treeview, self.aire_flights_treeview]:
            flight_plan = plan_data.get("FlightPlan")
            if flight_plan and flight_plan.get("_id") and flight_plan["_id"].get("$oid"):
                flight_plan_id = flight_plan["_id"]["$oid"]
                flight_plan_data = self.find_flight_plan_by_id(flight_plan_id, tree)
                if flight_plan_data:
                    waypoints = flight_plan_data.get("FlightWaypoints", [])
                    self.open_waypoint_viewer(waypoints, flight_plan_data)
                else:
                    messagebox.showerror("Error", "Flight Plan not found for the selected flight.")
            else:
                messagebox.showerror("Error", "No FlightPlan ID found in the selected flight.")
        else:
            waypoints = plan_data.get("FlightWaypoints", plan_data.get("waypoints", []))
            self.open_waypoint_viewer(waypoints, plan_data)

    def open_waypoint_viewer(self, waypoints, plan_data):
        new_window = tk.Toplevel(self.newWindow)
        new_window.title("Waypoint Viewer")
        new_window.geometry("900x700")
        new_window.configure(bg="#1B1B1B")

        title_label = tk.Label(new_window, text="Waypoint Viewer", font=("Helvetica", 20, "bold"), fg="#00BFFF",
                               bg="#1B1B1B")
        title_label.pack(pady=10)

        canvas_frame = tk.Frame(new_window, bg="#1B1B1B")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(canvas_frame, bg="#FFFFFF")
        canvas.pack(fill=tk.BOTH, expand=True)

        canvas.update()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        self.img = Image.open("assets/dronLab.png")
        self.img = self.img.resize((canvas_width, canvas_height), Image.ANTIALIAS)
        self.bg = ImageTk.PhotoImage(self.img)
        self.image = canvas.create_image(0, 0, image=self.bg, anchor="nw")

        self.draw_waypoints(canvas, waypoints, plan_data)

    def draw_waypoints(self, canvas, waypoints, plan_data):
        if not waypoints:
            return

        pics_waypoints = plan_data.get('PicsWaypoints', [])
        vid_waypoints = plan_data.get('VidWaypoints', [])

        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        margin = 50

        min_lat = min(wp['lat'] for wp in waypoints)
        max_lat = max(wp['lat'] for wp in waypoints)
        min_lon = min(wp['lon'] for wp in waypoints)
        max_lon = max(wp['lon'] for wp in waypoints)

        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        if lat_range == 0: lat_range = 1
        if lon_range == 0: lon_range = 1
        scale = min((canvas_width - 2 * margin) / lon_range, (canvas_height - 2 * margin) / lat_range)

        center_x = canvas_width / 2
        center_y = canvas_height / 2

        prev_x = None
        prev_y = None

        for i, wp in enumerate(waypoints):
            x = center_x + (wp['lon'] - min_lon - lon_range / 2) * scale
            y = center_y - (wp['lat'] - min_lat - lat_range / 2) * scale

            if any(wp['lat'] == pic_wp['lat'] and wp['lon'] == pic_wp['lon'] for pic_wp in pics_waypoints):
                color = 'yellow'
            elif any(wp['lat'] == vid_wp['lat'] and wp['lon'] == vid_wp['lon'] for vid_wp in vid_waypoints):
                color = 'green'
            else:
                color = "#00BFFF"

            canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill=color, outline=color)

            canvas.create_text(x, y - 10, text=str(i + 1), font=("Arial", 10, "bold"), fill="#000000")

            coordinates_text = f"({wp['lat']}, {wp['lon']})"
            canvas.create_text(x, y + 15, text=coordinates_text, font=("Arial", 8), fill="#000000")

            if prev_x is not None and prev_y is not None:
                canvas.create_line(prev_x, prev_y, x, y, fill="#FF4500", width=2, arrow=tk.LAST)

            prev_x = x
            prev_y = y

    def find_flight_plan_by_id(self, flight_plan_id, tree):
        if tree == self.tierra_flights_treeview:
            flight_plans = self.loaded_flight_plans_tierra
        else:
            flight_plans = self.loaded_flight_plans_aire

        for plan in flight_plans:
            current_id = plan.get("_id", {}).get("$oid")
            if current_id == flight_plan_id:
                return plan
        return None

    def delete_plan(self, tree, plan_id, confirm_window):
        service = "groundApiService" if tree in [self.tierra_treeview,
                                                 self.tierra_flights_treeview] else "airApiService"
        delete_command = "deleteFlightPlan" if tree in [self.tierra_treeview, self.aire_treeview] else "deleteFlight"
        print(f"Deleting plan {plan_id} in tree {tree} using {service} with command {delete_command}")
        self.client.publish(f"dashBoard/{service}/{delete_command}", plan_id)
        confirm_window.grab_release()
        confirm_window.destroy()
        self.refresh_flight_plans()

    def format_datetime(self, dt_obj):
        return dt_obj.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]

    def duplicate_plan(self, tree, plan_id):
        print(f"Duplicating plan {plan_id} in tree {tree}")
        item = tree.item(plan_id)
        plan_data = json.loads(item['text'])

        if tree in [self.tierra_treeview, self.aire_treeview]:

            new_title = plan_data['Title'] + "_copia"

            waypoints = plan_data["FlightWaypoints"]

            for wp in waypoints:
                if "lat" not in wp or "lon" not in wp or "height" not in wp:
                    print("Waypoint data missing keys:", wp)

            waypoints_corrected = [
                {
                    "lat": wp["lat"],
                    "lon": wp["lon"],
                    "height": wp["height"],
                    "takePic": wp.get("takePic", False),
                    "videoStart": wp.get("videoStart", False),
                    "videoStop": wp.get("videoStop", False),
                    "staticVideo": wp.get("staticVideo", False)
                }
                for wp in waypoints
            ]

            for pic_wp in waypoints_corrected:
                for pic in plan_data["PicsWaypoints"]:
                    if (pic_wp["lat"] == pic["lat"] and
                            pic_wp["lon"] == pic["lon"] and
                            pic_wp["height"] == pic["height"]):
                        pic_wp["takePic"] = True

            for vid_wp in waypoints_corrected:
                for vid in plan_data["VidWaypoints"]:
                    if vid.get("mode") == "static":
                        if (vid_wp["lat"] == vid["lat"] and
                                vid_wp["lon"] == vid["lon"]):
                            vid_wp["staticVideo"] = True
                            vid_wp["videoStart"] = False
                            vid_wp["videoStop"] = False
                            vid_wp["height"] = vid["length"]

            data = {
                "title": new_title,
                "waypoints": waypoints_corrected,
                "PicInterval": plan_data["PicInterval"],
                "VidInterval": plan_data.get("VidTimeStatic", 0),
                "PicsWaypoints": [],
                "VidWaypoints": []
            }

            service = "groundApiService" if tree == self.tierra_treeview else "airApiService"
            print("Duplicating data:", data)
            self.client.publish(f"dashBoard/{service}/addFlightPlan", json.dumps(data))

        elif tree in [self.tierra_flights_treeview, self.aire_flights_treeview]:

            date = datetime.fromtimestamp(plan_data["Date"]["$date"] / 1000).strftime('%Y-%m-%dT%H:%M:%S')
            start_time = datetime.fromtimestamp(plan_data["startTime"]["$date"] / 1000).strftime('%Y-%m-%dT%H:%M:%S')
            end_time = datetime.fromtimestamp(plan_data["startTime"]["$date"] / 1000).strftime('%Y-%m-%dT%H:%M:%S')

            pictures = [{"id": pic["$oid"]} for pic in plan_data.get("Pictures", [])]

            videos = [{"id": vid["$oid"]} for vid in plan_data.get("Videos", [])]
            new_title = plan_data['Title'] + "_copia"
            data = {
                "Title": new_title,
                "Date": date,
                "startTime": start_time,
                "endTime": end_time,
                "Description": plan_data.get("Description"),
                "GeofenceActive": plan_data.get("GeofenceActive", False),
                "Flightplan": plan_data["FlightPlan"]["_id"]["$oid"],
                "NumPics": float(plan_data["NumPics"]),
                "Pictures": pictures,
                "NumVids": float(plan_data["NumVids"]),
                "Videos": videos,
                "FlightSuccess": plan_data.get("FlightSuccess")
            }

            service = "groundApiService" if tree == self.tierra_flights_treeview else "airApiService"
            print("Duplicating data:", data)
            self.client.publish(f"dashBoard/{service}/addFlight", json.dumps(data))

        self.refresh_flight_plans()

    def move_to_aire(self, tree, plan_id):
        print(f"Moving plan {plan_id} from {tree} to Aire")
        item = tree.item(plan_id)
        plan_data = json.loads(item['text'])

        new_title = plan_data['Title']

        if tree in [self.tierra_treeview]:
            waypoints = plan_data["FlightWaypoints"]
            waypoints_corrected = [
                {
                    "lat": wp["lat"],
                    "lon": wp["lon"],
                    "takePic": wp.get("takePic", False),
                    "videoStart": wp.get("videoStart", False),
                    "videoStop": wp.get("videoStop", False),
                    "staticVideo": wp.get("staticVideo", False)
                }
                for wp in waypoints
            ]
            data = {
                "title": new_title,
                "waypoints": waypoints_corrected,
                "PicInterval": plan_data["PicInterval"],
                "VidInterval": plan_data.get("VidTimeStatic", 0),
            }

            self.client.publish(f"dashBoard/airApiService/addFlightPlan", json.dumps(data))

        elif tree in [self.tierra_flights_treeview]:
            date = datetime.fromtimestamp(plan_data["Date"]["$date"] / 1000).strftime('%Y-%m-%dT%H:%M:%S')
            start_time = datetime.fromtimestamp(plan_data["startTime"]["$date"] / 1000).strftime('%Y-%m-%dT%H:%M:%S')
            end_time = datetime.fromtimestamp(plan_data["endTime"]["$date"] / 1000).strftime('%Y-%m-%dT%H:%M:%S')

            pictures = [{"_id": pic["$oid"]} for pic in plan_data.get("Pictures", [])]
            videos = [{"_id": vid["$oid"]} for vid in plan_data.get("Videos", [])]

            data = {
                "Title": new_title,
                "Date": date,
                "startTime": start_time,
                "endTime": end_time,
                "Description": plan_data.get("Description"),
                "GeofenceActive": plan_data.get("GeofenceActive", False),
                "Flightplan": plan_data["FlightPlan"]["_id"]["$oid"],  # Referencia correcta al OID del FlightPlan
                "NumPics": float(plan_data["NumPics"]),
                "Pictures": pictures,
                "NumVids": float(plan_data["NumVids"]),
                "Videos": videos,
                "FlightSuccess": plan_data.get("FlightSuccess")
            }

            self.client.publish(f"dashBoard/airApiService/addFlight", json.dumps(data))

        self.refresh_flight_plans()

    def move_to_tierra(self, tree, plan_id):
        print(f"Moving plan {plan_id} from {tree} to Tierra")
        item = tree.item(plan_id)
        plan_data = json.loads(item['text'])

        new_title = plan_data['Title']

        if tree in [self.aire_treeview]:
            waypoints = plan_data["FlightWaypoints"]
            waypoints_corrected = [
                {
                    "lat": wp["lat"],
                    "lon": wp["lon"],
                    "takePic": wp.get("takePic", False),
                    "videoStart": wp.get("videoStart", False),
                    "videoStop": wp.get("videoStop", False),
                    "staticVideo": wp.get("staticVideo", False)
                }
                for wp in waypoints
            ]
            data = {
                "title": new_title,
                "waypoints": waypoints_corrected,
                "PicInterval": plan_data["PicInterval"],
                "VidInterval": plan_data.get("VidTimeStatic", 0),
            }

            self.client.publish(f"dashBoard/groundApiService/addFlightPlan", json.dumps(data))

        elif tree in [self.aire_flights_treeview]:
            date = datetime.fromtimestamp(plan_data["Date"]["$date"] / 1000).strftime('%Y-%m-%dT%H:%M:%S')
            start_time = datetime.fromtimestamp(plan_data["startTime"]["$date"] / 1000).strftime('%Y-%m-%dT%H:%M:%S')
            end_time = datetime.fromtimestamp(plan_data["endTime"]["$date"] / 1000).strftime('%Y-%m-%dT%H:%M:%S')

            pictures = [{"_id": pic["$oid"]} for pic in plan_data.get("Pictures", [])]
            videos = [{"_id": vid["$oid"]} for vid in plan_data.get("Videos", [])]

            data = {
                "Title": new_title,
                "Date": date,
                "startTime": start_time,
                "endTime": end_time,
                "Description": plan_data.get("Description"),
                "GeofenceActive": plan_data.get("GeofenceActive", False),
                "Flightplan": plan_data["FlightPlan"]["_id"]["$oid"],
                "NumPics": float(plan_data["NumPics"]),
                "Pictures": pictures,
                "NumVids": float(plan_data["NumVids"]),
                "Videos": videos,
                "FlightSuccess": plan_data.get("FlightSuccess")
            }

            self.client.publish(f"dashBoard/groundApiService/addFlight", json.dumps(data))

        self.refresh_flight_plans()

    def refresh_flight_plans(self):
        self.client.publish("dashBoard/groundApiService/getAllFlightPlans")
        self.client.publish("dashBoard/airApiService/getAllFlightPlans")
        self.client.publish("dashBoard/groundApiService/getAllFlights")
        self.client.publish("dashBoard/airApiService/getAllFlights")
