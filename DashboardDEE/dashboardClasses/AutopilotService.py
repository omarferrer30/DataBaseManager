import json
import math
import threading
import paho.mqtt.client as mqtt
import time
import dronekit
from dronekit import connect, Command, VehicleMode
from pymavlink import mavutil


def arm():
    """Arms vehicle and fly to aTargetAltitude"""
    print("Basic pre-arm checks")  # Don't try to arm until autopilot is ready
    vehicle.mode = dronekit.VehicleMode("GUIDED")
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)
    print("Arming motors")
    # Copter should arm in GUIDED mode

    vehicle.armed = True
    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)
    print(" Armed")


def take_off(a_target_altitude, manualControl):
    global state
    vehicle.simple_takeoff(a_target_altitude)
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        # Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt >= a_target_altitude * 0.95:
            print("Reached target altitude")
            break
        time.sleep(1)

    state = "flying"
    if manualControl:
        w = threading.Thread(target=flying)
        w.start()


def prepare_command(velocity_x, velocity_y, velocity_z):
    """
    Move vehicle in direction based on specified velocity vectors.
    """
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,  # time_boot_ms (not used)
        0,
        0,  # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame
        0b0000111111000111,  # type_mask (only speeds enabled)
        0,
        0,
        0,  # x, y, z positions (not used)
        velocity_x,
        velocity_y,
        velocity_z,  # x, y, z velocity in m/s
        0,
        0,
        0,  # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0,
        0,
    )  # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    return msg


"""
These are the different values for the state of the autopilot:
    'connected' (only when connected the telemetry_info packet will be sent every 250 miliseconds)
    'arming'
    'armed'
    'disarmed'
    'takingOff'
    'flying'
    'returningHome'
    'landing'
    'onHearth'

The autopilot can also be 'disconnected' but this state will never appear in the telemetry_info packet
when disconnected the service will not send any packet
"""


def get_telemetry_info():
    global state
    print("estado ", state)
    telemetry_info = {
        "lat": vehicle.location.global_frame.lat,
        "lon": vehicle.location.global_frame.lon,
        "heading": vehicle.heading,
        "groundSpeed": vehicle.groundspeed,
        "altitude": vehicle.location.global_relative_frame.alt,
        "battery": vehicle.battery.level,
        "state": state,
    }
    return telemetry_info


def send_telemetry_info():
    global external_client
    global sending_telemetry_info
    global sending_topic

    while sending_telemetry_info:
        external_client.publish(
            sending_topic + "/telemetryInfo", json.dumps(get_telemetry_info())
        )
        time.sleep(0.25)


def returning():
    global sending_telemetry_info
    global external_client
    global internal_client
    global sending_topic
    global state

    # wait until the drone is at home
    while vehicle.armed:
        time.sleep(1)
    state = "onHearth"


def flying():
    global direction
    global go
    speed = 1
    end = False
    cmd = prepare_command(0, 0, 0)  # stop
    while not end:
        go = False
        while not go:
            vehicle.send_mavlink(cmd)
            time.sleep(1)
        # a new go command has been received. Check direction
        print("salgo del bucle por ", direction)
        if direction == "North":
            print("vamos al norte")
            cmd = prepare_command(speed, 0, 0)  # NORTH
        if direction == "South":
            cmd = prepare_command(-speed, 0, 0)  # SOUTH
        if direction == "East":
            cmd = prepare_command(0, speed, 0)  # EAST
        if direction == "West":
            cmd = prepare_command(0, -speed, 0)  # WEST
        if direction == "NorthWest":
            cmd = prepare_command(speed, -speed, 0)  # NORTHWEST
        if direction == "NorthEst":
            cmd = prepare_command(speed, speed, 0)  # NORTHEST
        if direction == "SouthWest":
            cmd = prepare_command(-speed, -speed, 0)  # SOUTHWEST
        if direction == "SouthEst":
            cmd = prepare_command(-speed, speed, 0)  # SOUTHEST
        if direction == "Stop":
            cmd = prepare_command(0, 0, 0)  # STOP
        if direction == "RTL":
            end = True


def distanceInMeters(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the
    earth's poles. It comes from the ArduPilot test code:
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5


def executeFlightPlan(waypoints_json):
    global vehicle
    global internal_client, external_client
    global sending_topic
    global state

    altitude = 6
    origin = sending_topic.split("/")[1]

    waypoints = json.loads(waypoints_json)

    state = "arming"
    arm()
    state = "takingOff"
    take_off(altitude, False)
    state = "flying"
    # vehicle.groundspeed=3

    wp = waypoints[0]
    originPoint = dronekit.LocationGlobalRelative(
        float(wp["lat"]), float(wp["lon"]), altitude
    )

    distanceThreshold = 0.50
    for wp in waypoints[1:]:

        destinationPoint = dronekit.LocationGlobalRelative(
            float(wp["lat"]), float(wp["lon"]), altitude
        )
        vehicle.simple_goto(destinationPoint, groundspeed=3)

        currentLocation = vehicle.location.global_frame
        dist = distanceInMeters(destinationPoint, currentLocation)

        while dist > distanceThreshold:
            time.sleep(0.25)
            currentLocation = vehicle.location.global_frame
            dist = distanceInMeters(destinationPoint, currentLocation)
        print("reached")
        waypointReached = {"lat": currentLocation.lat, "lon": currentLocation.lon}

        external_client.publish(
            sending_topic + "/waypointReached", json.dumps(waypointReached)
        )

        if wp["takePic"]:
            # ask to send a picture to origin
            internal_client.publish(origin + "/cameraService/takePicture")

    vehicle.mode = dronekit.VehicleMode("RTL")
    state = "returningHome"

    currentLocation = vehicle.location.global_frame
    dist = distanceInMeters(originPoint, currentLocation)

    while dist > distanceThreshold:
        time.sleep(0.25)
        currentLocation = vehicle.location.global_frame
        dist = distanceInMeters(originPoint, currentLocation)

    state = "landing"
    while vehicle.armed:
        time.sleep(1)
    state = "onHearth"


def executeFlightPlan2(waypoints_json):
    global vehicle
    global internal_client, external_client
    global sending_topic
    global state

    altitude = 6
    origin = sending_topic.split("/")[1]

    waypoints = json.loads(waypoints_json)
    state = "arming"
    arm()
    state = "takingOff"
    take_off(altitude, False)
    state = "flying"
    cmds = vehicle.commands
    cmds.clear()

    # wp = waypoints[0]
    # originPoint = dronekit.LocationGlobalRelative(float(wp['lat']), float(wp['lon']), altitude)
    for wp in waypoints:
        cmds.add(
            Command(
                0,
                0,
                0,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                0,
                0,
                0,
                0,
                0,
                0,
                float(wp["lat"]),
                float(wp["lon"]),
                altitude,
            )
        )
    wp = waypoints[0]
    cmds.add(
        Command(
            0,
            0,
            0,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            0,
            0,
            0,
            0,
            0,
            0,
            float(wp["lat"]),
            float(wp["lon"]),
            altitude,
        )
    )
    cmds.upload()

    vehicle.commands.next = 0
    # Set mode to AUTO to start mission
    vehicle.mode = VehicleMode("AUTO")
    while True:
        nextwaypoint = vehicle.commands.next
        print("next ", nextwaypoint)
        if nextwaypoint == len(
            waypoints
        ):  # Dummy waypoint - as soon as we reach waypoint 4 this is true and we exit.
            print("Last waypoint reached")
            break
        time.sleep(0.5)

    print("Return to launch")
    state = "returningHome"
    vehicle.mode = VehicleMode("RTL")
    while vehicle.armed:
        time.sleep(1)
    state = "onHearth"


def set_direction(color):
    if color == "blueS":
        return "North"
    elif color == "yellow":
        return "East"
    elif color == "green":
        return "West"
    elif color == "pink":
        return "South"
    elif color == "purple":
        return "RTL"
    else:
        return "none"


def process_message(message, client):
    global vehicle
    global direction
    global go
    global sending_telemetry_info
    global sending_topic
    global sending_topic
    global state
    global operationMode

    splited = message.topic.split("/")
    origin = splited[0]
    command = splited[2]
    sending_topic = "autopilotService/" + origin

    if command == "connect":
        if state == "disconnected":
            print("Autopilot service connected by " + origin)
            # para conectar este autopilotService al dron al mismo tiempo que conectamos el Mission Planner
            # hay que ejecutar el siguiente comando desde PowerShell desde  C:\Users\USER>
            # mavproxy - -master =COM12 - -out = udp:127.0.0.1: 14550 - -out = udp:127.0.0.1: 14551
            # ahora el servicio puede conectarse por udp a cualquira de los dos puertos 14550 o 14551 y Mission Planner
            # al otro
            if operationMode == "simulation":
                vehicle = connect("tcp:127.0.0.1:5763", wait_ready=False, baud=115200)
                vehicle.wait_ready(True, timeout=5000)
            else:
                vehicle = connect("udp:127.0.0.1:14550", wait_ready=False, baud=57600)
                vehicle.wait_ready(True, timeout=5000)

            print("Connected to flight controller")
            state = "connected"

            # external_client.publish(sending_topic + "/connected", json.dumps(get_telemetry_info()))

            sending_telemetry_info = True
            y = threading.Thread(target=send_telemetry_info)
            y.start()
        else:
            print("Autopilot already connected")

    if command == "disconnect":
        vehicle.close()
        sending_telemetry_info = False
        state = "disconnected"

    if command == "takeOff":
        state = "takingOff"
        w = threading.Thread(target=take_off, args=[5, True])
        w.start()

    if command == "returnToLaunch":
        # stop the process of getting positions
        vehicle.mode = dronekit.VehicleMode("RTL")
        state = "returningHome"
        direction = "RTL"
        go = True
        w = threading.Thread(target=returning)
        w.start()

    if command == "armDrone":
        print("arming")
        state = "arming"
        arm()

        # the vehicle will disarm automatically is takeOff does not come soon
        # when attribute 'armed' changes run function armed_change
        vehicle.add_attribute_listener("armed", armed_change)
        state = "armed"

    if command == "disarmDrone":
        vehicle.armed = False
        while vehicle.armed:
            time.sleep(1)
        state = "disarmed"

    if command == "land":

        vehicle.mode = dronekit.VehicleMode("LAND")
        state = "landing"
        while vehicle.armed:
            time.sleep(1)
        state = "onHearth"

    if command == "go":
        direction = message.payload.decode("utf-8")
        print("Going ", direction)
        go = True

    if command == "executeFlightPlan":
        waypoints_json = str(message.payload.decode("utf-8"))
        w = threading.Thread(
            target=executeFlightPlan,
            args=[
                waypoints_json,
            ],
        )
        w.start()

    if command == "videoFrameWithColor":
        # ya se está moviendo. Solo entonces hacemos caso de los colores
        frameWithColor = json.loads(message.payload)
        d = set_direction(frameWithColor["color"])
        if d != "none":
            direction = d
            if direction == "RTL":
                vehicle.mode = dronekit.VehicleMode("RTL")
                print("cambio estado")
                state = "returningHome"
                w = threading.Thread(target=returning)
                w.start()

            go = True


def armed_change(self, attr_name, value):
    global vehicle
    global state
    print(
        "cambio a ",
    )
    if vehicle.armed:
        state = "armed"
    else:
        state = "disarmed"

    print("cambio a ", state)


def on_external_message(client, userdata, message):
    global external_client
    process_message(message, external_client)


def AutopilotService(opMode):
    global op_mode
    global external_client
    global internal_client
    global state
    global operationMode

    operationMode = opMode
    state = "disconnected"
    external_broker_address = "localhost"
    external_broker_port = 8000
    external_client = mqtt.Client("Autopilot_external", transport="websockets")
    external_client.on_message = on_external_message
    external_client.connect(external_broker_address, external_broker_port)

    print("Autopilot service waiting....")
    external_client.subscribe("+/autopilotService/#", 2)
    external_client.loop_forever()
