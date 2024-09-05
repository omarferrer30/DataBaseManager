import logging

from mongoengine import connect
from starlette.middleware.cors import CORSMiddleware
from typing import List

from classes import *
import json
import os
import asyncio
from PIL import Image
from io import BytesIO
from moviepy.editor import VideoFileClip
import numpy as np
import cv2 as cv
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import paho.mqtt.client as mqtt
from pymongo import MongoClient
from bson import ObjectId
from pydantic.error_wrappers import ValidationError
import logging

app = FastAPI()
connect(db="DEE", host="localhost", port=27017)
client = MongoClient('127.0.0.1:27017')
db = client['DEE']

'''
Esta parte del codigo es para uso del la aplicación movil en flutter.
Aun no sabemos cómo hacer que flutter se connecte con  MQTT. Como alternativa temporal, 
hacemos que flutter se comunique con el autopilot service a través de la APIREST, que si que 
puede comunicarse via MQTT.
En el momento en que se solucione el problema de la conexión de flutter a MQTT esta parte del código
se elmimiará'''

################################################################33

client = mqtt.Client(client_id="fastApi", transport='websockets')
is_connected = False


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {str(rc)}")
    client.subscribe("autopilotService/WebApp/telemetryInfo", 2)
    # client.subscribe("+/fastApi/#", 2)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global is_connected
    # print(f"{msg.topic} {str(msg.payload)}")
    if msg.topic == "autopilotService/WebApp/telemetryInfo":
        is_connected = True


# MQTT Callbacks
client.on_connect = on_connect
client.on_message = on_message

@app.get("/connection_status")
async def get_connection_status():
    global is_connected
    return {"is_connected": is_connected}

""" Función antigua para la aplicación de Flutter """

"""
@app.post("/executeFlightPlan")
async def execute_flight_plan(plan: List[WaypointMQTT]):
    # Convert the FlightPlan to a JSON string
    plan_json = json.dumps(jsonable_encoder(plan))

    # Publish the plan to the MQTT broker
    client.publish("WebApp/autopilotService/executeFlightPlan", plan_json)
    return {"message": "Flight plan published"}
# End MQTT Callbacks

"""

@app.get("/get_results_flight_flutter/{flight_id}")
async def get_results_flight_flutter(flight_id: str):
    client.publish("WebApp/cameraService/getResultFlightFlutter", flight_id)
    return {"message": "Trying to obtain images and pictures"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            ErrorResponse(
                success=False,
                message="Validation error",
                errors=exc.errors(),
            )
        ),
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            ErrorResponse(success=False, message=exc.detail)
        ),
    )

@app.get("/")
def home():
    return RedirectResponse(url="/docs")


@app.get("/get_all_flights")
def get_all_flights():
    flights = Flights.objects()
    flights_data = []

    for flight in flights:
        individual_flight = json.loads(flight.to_json())
        # Populate related documents
        individual_flight["FlightPlan"] = json.loads(flight.FlightPlan.to_json())
        flights_data.append(individual_flight)
    print(flights_data)
    return flights_data


@app.post("/add_flightplan", responses={422: {"model": ErrorResponse}})
def add_flightplan(data: FlightPlanData):
    try:
        title = data.title
        waypoints = data.waypoints
        pic_interval = data.PicInterval
        vid_interval = data.VidInterval

        num_waypoints = len(waypoints)
        num_pics = 0
        num_vids = 0
        flight_waypoints = []
        pics_waypoints = []
        vid_waypoints = []
        for w in waypoints:
            waypoint = Waypoint(lat=w.lat, lon=w.lon, height=w.height)
            flight_waypoints.append(waypoint)
            if w.takePic:
                pics_waypoints.append(waypoint)
                num_pics += 1
            if w.videoStart or w.videoStop:
                if w.videoStart:
                    num_vids += 1
                    waypoint_vid = VideoPlan(mode="moving", latStart=w.lat, lonStart=w.lon)
                if w.videoStop:
                    waypoint_vid.latEnd = w.lat
                    waypoint_vid.lonEnd = w.lon
                    vid_waypoints.append(waypoint_vid)
            if w.staticVideo:
                num_vids += 1
                static_vid = VideoPlan(mode="static", lat=w.lat, lon=w.lon, length=vid_interval)
                vid_waypoints.append(static_vid)

        new_flight_plan = FlightPlan(Title=title,
                                     NumWaypoints=num_waypoints,
                                     FlightWaypoints=flight_waypoints,
                                     NumPics=num_pics,
                                     PicsWaypoints=pics_waypoints,
                                     NumVids=num_vids,
                                     VidWaypoints=vid_waypoints,
                                     PicInterval=pic_interval,
                                     VidTimeStatic=vid_interval)
        new_flight_plan.save()
        id_flightplan = str(new_flight_plan.id)
        return {"success": True, "message": "Waypoints Saved", "id": id_flightplan}

    except Exception as e:
        raise HTTPException(status_code=400, detail={str(e)})


@app.post("/add_flight", responses={422: {"model": ErrorResponse}})
def add_flight(data: FlightData):
    try:
        startTime = data.startTime
        startTimeNew = startTime[:-3]
        pictures = []
        i=0
        while i < len(data.Pictures):
            pictures.append({
                "waypoint": data.Pictures[i].waypoint,
                "namePicture": data.Pictures[i].namePicture,
                "lat": data.Pictures[i].lat,
                "lon": data.Pictures[i].lon})
            i=i+1
        videos = []
        i=0
        while i < len(data.Videos):
            videos.append({
                "startWaypoint": data.Videos[i].startWaypoint,
                "endWaypoint": data.Videos[i].endWaypoint,
                "nameVideo": data.Videos[i].nameVideo,
                "latStart": data.Videos[i].latStart,
                "lonStart": data.Videos[i].lonStart,
                "latEnd": data.Videos[i].latEnd,
                "lonEnd": data.Videos[i].lonEnd})
            i = i + 1
        new_flight = Flights(Date=datetime.strptime(data.Date, '%Y-%m-%dT%H:%M:%S'),
                             startTime=datetime.strptime(startTimeNew, '%Y-%m-%dT%H:%M:%S.%f'),
                             GeofenceActive=data.GeofenceActive,
                             FlightPlan=ObjectId(data.Flightplan),
                             NumVids=data.NumVids,
                             NumPics=data.NumPics,
                             Pictures=pictures,
                             Videos=videos)
        new_flight.save()
        id_flight = str(new_flight.id)

    except Exception as e:
        raise HTTPException(status_code=400, detail={str(e)})


@app.get("/get_flight_plan/{flightplan_id}")
def get_flight_plan(flightplan_id: str):
    try:
        client = MongoClient('127.0.0.1:27017')
        db = client['DEE']
        collection = db['flightPlan']

        flightplan = collection.find_one({"_id": ObjectId(flightplan_id)})
        flightplan["_id"] = str(flightplan["_id"])
        flightplan["DateAdded"] = flightplan["DateAdded"].isoformat()
        client.close()
        return JSONResponse(content=flightplan, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail={str(e)})


@app.get("/get_flight/{flight_id}")
def get_flight(flight_id: str):
    try:
        client = MongoClient('127.0.0.1:27017')
        db = client['DEE']
        collection = db['flights']

        flight = collection.find_one({"_id": ObjectId(flight_id)})
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")

        flight["_id"] = str(flight["_id"])
        flight["Date"] = flight["Date"].isoformat()
        flight["startTime"] = flight["startTime"].isoformat()
        flight["endTime"] = flight["endTime"].isoformat()
        client.close()
        return JSONResponse(content=flight, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail={str(e)})

@app.get("/get_flight_plan_id/{flightplan_title}")
def get_flight_plan_id(flightplan_title: str):
    try:
        client = MongoClient('127.0.0.1:27017')
        db = client['DEE']
        collection = db['flightPlan']

        flightplan = collection.find_one({"Title": flightplan_title})
        if flightplan is None:
            return JSONResponse(content=flightplan, status_code=404)
        else:
            client.close()
            return {"success": True, "message": "Flight Plan found", "id": str(flightplan["_id"])}
    except Exception as e:
        raise HTTPException(status_code=400, detail={str(e)})

@app.post("/save_picture/{picture_name}")
async def save_picture(picture_name: str, request: Request):
    try:
        data_bytes = await request.body()

        actual_dir = os.path.dirname(os.path.abspath(__file__))
        img_route = os.path.join(actual_dir, "media", "pictures", picture_name)
        nparr = np.frombuffer(data_bytes, np.uint8)
        image = cv.imdecode(nparr, cv.IMREAD_COLOR)
        try:
            cv.imwrite(img_route, image)
        except Exception as e:
            print(f"Error al guardar la imagen: {e}")
        cv.waitKey(0)

    except Exception as e:
        raise HTTPException(status_code=400, detail={str(e)})

@app.post("/save_video/{video_name}")
async def save_video(video_name: str, request: Request):
    try:
        data_bytes = await request.body()
        actual_dir = os.path.dirname(os.path.abspath(__file__))
        vid_route = os.path.join(actual_dir, "media", "videos", video_name)

        try:
            with open(vid_route, 'wb') as file:
                file.write(data_bytes)
        except Exception as e:
            print(f"Error al guardar el video: {e}")
        cv.waitKey(0)

    except Exception as e:
        raise HTTPException(status_code=400, detail={str(e)})


@app.get("/get_all_flightPlans")
def get_all_flightPlans():
    waypoints = json.loads(FlightPlan.objects().to_json())
    print(waypoints)
    return {"Waypoints": waypoints}



# Serve media files
directory_path = os.path.join(os.path.dirname(__file__), "media")
app.mount("/media", StaticFiles(directory=directory_path), name="media")

@app.get("/media/pictures/{file_name}")
async def get_picture(file_name: str):
    return FileResponse(os.path.join("media", "pictures", file_name))


@app.get("/media/videos/{file_name}")
async def get_video(file_name: str):
    return FileResponse(os.path.join("media", "videos", file_name))

@app.get("/thumbnail/{file_name}")
async def get_video_thumbnail(file_name: str):
    # Load the video
    video = VideoFileClip(os.path.join("media", "videos", file_name))

    thumbnail = video.get_frame(0)
    img = Image.fromarray(np.uint8(thumbnail))

    image_io = BytesIO()
    img.save(image_io, format='JPEG')
    image_io.seek(0)

    return StreamingResponse(image_io, media_type="image/jpeg")

@app.delete("/delete_flight_plan/{flight_plan_id}")
async def delete_flight_plan(flight_plan_id: str):
    try:
        result = db.flightPlan.delete_one({"_id": ObjectId(flight_plan_id)})
        if result.deleted_count == 1:
            return {"success": True, "message": "Flight plan deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Flight plan not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/delete_flight/{flight_id}", responses={422: {"model": ErrorResponse}})
async def delete_flight(flight_id: str):
    try:
        result = db.flights.delete_one({"_id": ObjectId(flight_id)})
        if result.deleted_count == 1:
            return {"success": True, "message": "Flight deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Flight not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/add_flight2", responses={422: {"model": ErrorResponse}})
def add_flight2(data: FlightData2):
    try:

        startTime = datetime.strptime(data.startTime, '%Y-%m-%dT%H:%M:%S')
        endTime = datetime.strptime(data.endTime, '%Y-%m-%dT%H:%M:%S')
        date = datetime.strptime(data.Date, '%Y-%m-%dT%H:%M:%S')

        pictures = [ObjectId(picture.id) for picture in data.Pictures if picture.id]
        videos = [ObjectId(video.id) for video in data.Videos if video.id]

        new_flight = Flights(
            Title=data.Title,
            Date=date,
            Description=data.Description,
            startTime=startTime,
            endTime=endTime,
            GeofenceActive=data.GeofenceActive,
            FlightPlan=ObjectId(data.Flightplan),
            NumPics=data.NumPics,
            Pictures=pictures,
            NumVids=data.NumVids,
            Videos=videos,
            FlightSuccess=data.FlightSuccess
        )
        new_flight.save()

        return {"message": "Flight successfully created", "flight_id": str(new_flight.id)}

    except Exception as e:
        raise HTTPException(status_code=400, detail={str(e)})

@app.put("/update_flight_plan/{plan_id}", responses={422: {"model": ErrorResponse}})
def update_flight_plan(plan_id: str, data: UpdateFlightPlanData):
    try:
        flight_plan = FlightPlan.objects(id=ObjectId(plan_id)).first()
        if not flight_plan:
            raise HTTPException(status_code=404, detail="Flight Plan not found")


        flight_plan.Title = data.Title
        flight_plan.PicInterval = data.PicInterval
        flight_plan.VidTimeStatic = data.VidInterval


        flight_plan.NumWaypoints = len(data.waypoints)
        flight_plan.FlightWaypoints = []
        flight_plan.PicsWaypoints = []
        flight_plan.VidWaypoints = []
        flight_plan.NumPics = 0
        flight_plan.NumVids = 0

        for w in data.waypoints:
            waypoint = Waypoint(lat=w.lat, lon=w.lon, height=w.height)
            flight_plan.FlightWaypoints.append(waypoint)

            if w.takePic:
                flight_plan.PicsWaypoints.append(waypoint)
                flight_plan.NumPics += 1

            if w.staticVideo:
                flight_plan.NumVids += 1
                static_vid = VideoPlan(mode="static", lat=w.lat, lon=w.lon, length=data.VidInterval)
                flight_plan.VidWaypoints.append(static_vid)

        flight_plan.save()
        return {"success": True, "message": "Flight Plan updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail={str(e)})


