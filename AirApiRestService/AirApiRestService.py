import ssl
import requests
import json
import math
import threading
import paho.mqtt.client as mqtt
import time
from paho.mqtt.client import ssl
from datetime import datetime as dt


def process_message(message, client):
    global vehicle
    global direction
    global go
    global sending_telemetry_info
    global sending_topic
    global op_mode
    global sending_topic
    global state

    splited = message.topic.split("/")
    origin = splited[0]
    command = splited[2]
    sending_topic = "airApiService/" + origin
    print('recibo ', command)

    if command == "addFlightPlan":
        try:
            data = json.loads(message.payload)
            requests.post("http://127.0.0.1:8001/add_flightplan", json=data)
            print(data)
        except Exception as e:
            print("Error saving flight plan:", e)

    if command == "addFlight":
        try:
            data = json.loads(message.payload)
            requests.post("http://127.0.0.1:8001/add_flight2", json=data)
            print(data)
        except Exception as e:
            print("Error saving flight plan:", e)

    if command == "getFlightPlan":
        try:
            flightplan_id_ground = json.loads(message.payload)
            flightplan_response = requests.get(
                "http://127.0.0.1:8001/get_flight_plan/", json=flightplan_id_ground
            )
            flightplan = flightplan_response.json()
            flightplan_json = json.dumps(flightplan)
            print(flightplan_json)
            client.publish("groundApiService/" + origin + "/flightPlan", flightplan_json)
        except Exception as e:
            print("Error getting flight plan:", e)

    if command == "getAllFlightPlans":
        try:
            flightPlans_response = requests.get("http://127.0.0.1:8001/get_all_flightPlans")
            flightPlans = flightPlans_response.json()
            flightPlans_json = json.dumps(flightPlans)
            print(flightPlans_json)
            # Publicar los flight plans como un mensaje MQTT
            client.publish("airApiService/" + origin + "/allFlightPlans", flightPlans_json)
        except Exception as e:
            print("Error getting all flights:", e)

    if command == "getAllFlights":
        try:
            flights_response = requests.get("http://127.0.0.1:8001/get_all_flights/")
            flights = flights_response.json()
            flights_json = json.dumps(flights)
            print(flights_json)
            client.publish("airApiService/" + origin + "/allFlights", flights_json)
        except Exception as e:
            print("Error getting all flights:", e)

    if command == "pictures":
        try:
            image_name = json.loads(message.payload)
            picture = requests.get(f"http://127.0.0.1:8001/media/pictures/", image_name)
            response = picture.json()
            response_json = json.dumps(response)
            print(response_json)
            client.publish("airApiService/" + origin + "/picture", response_json)
        except Exception as e:
            print("Error getting all flights:", e)

    if command == "position":
        print("Position: ", message.payload)

    if command == "go":
        direction = message.payload.decode("utf-8")
        print("Going ", direction)
        go = True

    if command == "deleteFlightPlan":
        try:
            flight_plan_id = message.payload.decode("utf-8")
            response = requests.delete(f"http://127.0.0.1:8001/delete_flight_plan/{flight_plan_id}")
            if response.status_code == 200:
                print(f"Deleted flight plan {flight_plan_id} successfully")
                client.publish(f"{sending_topic}/deleteFlightPlanResponse", json.dumps({"success": True, "message": "Flight plan deleted successfully"}))
            else:
                error_message = response.json().get('detail', 'Unknown error')
                print(f"Failed to delete flight plan {flight_plan_id}: {error_message}")
                client.publish(f"{sending_topic}/deleteFlightPlanResponse", json.dumps({"success": False, "message": error_message}))
        except Exception as e:
            print(f"Error deleting flight plan {flight_plan_id}: {e}")
            client.publish(f"{sending_topic}/deleteFlightPlanResponse", json.dumps({"success": False, "message": str(e)}))

    if command == "deleteFlight":
        try:
            flight_id = message.payload.decode("utf-8")
            response = requests.delete(f"http://127.0.0.1:8001/delete_flight/{flight_id}")
            if response.status_code == 200:
                print(f"Deleted flight {flight_id} successfully")
                client.publish(f"{sending_topic}/deleteFlightResponse", json.dumps({"success": True, "message": "Flight deleted successfully"}))
            else:
                error_message = response.json().get('detail', 'Unknown error')
                print(f"Failed to delete flight {flight_id}: {error_message}")
                client.publish(f"{sending_topic}/deleteFlightResponse", json.dumps({"success": False, "message": error_message}))
        except Exception as e:
            print(f"Error deleting flight {flight_id}: {e}")
            client.publish(f"{sending_topic}/deleteFlightResponse", json.dumps({"success": False, "message": str(e)}))


    if command == "updateFlightPlan":
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            flight_plan_id = payload.get("id")
            update_data = payload.get("data")
            response = requests.put(f"http://127.0.0.1:8001/update_flight_plan/{flight_plan_id}", json=update_data)
            if response.status_code == 200:
                print(f"Updated flight plan {flight_plan_id} successfully")
                client.publish(f"{sending_topic}/updateFlightPlanResponse",
                               json.dumps({"success": True, "message": "Flight plan updated successfully"}))
            else:
                error_message = response.json().get('detail', 'Unknown error')
                print(f"Failed to update flight plan {flight_plan_id}: {error_message}")
                client.publish(f"{sending_topic}/updateFlightPlanResponse",
                               json.dumps({"success": False, "message": error_message}))
        except Exception as e:
            print(f"Error updating flight plan {flight_plan_id}: {e}")
            client.publish(f"{sending_topic}/updateFlightPlanResponse",
                           json.dumps({"success": False, "message": str(e)}))



def on_internal_message(client, userdata, message):
    global internal_client
    process_message(message, internal_client)


def on_external_message(client, userdata, message):
    global external_client
    process_message(message, external_client)


def on_connect(external_client, userdata, flags, rc):
    if rc == 0:
        print("Connection OK")
    else:
        print("Bad connection")


def airApiService(connection_mode, operation_mode, external_broker, username, password):
    global op_mode
    global external_client
    global internal_client
    global state

    state = 'disconnected'

    print('Connection mode: ', connection_mode)
    print('Operation mode: ', operation_mode)
    internal_client = mqtt.Client("airApiService_internal")
    internal_client.on_message = on_internal_message
    internal_client.connect("localhost", 1884)

    external_client = mqtt.Client("airApiService_external", transport="websockets")
    external_client.on_message = on_external_message
    external_client.on_connect = on_connect

    if connection_mode == "global":
        if external_broker == "hivemq":
            external_client.connect("broker.hivemq.com", 8000)
            print('Connected to broker.hivemq.com:8000')

        elif external_broker == "hivemq_cert":
            external_client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                                    tls_version=ssl.PROTOCOL_TLS, ciphers=None)
            external_client.connect("broker.hivemq.com", 8884)
            print('Connected to broker.hivemq.com:8884')

        elif external_broker == "classpip_cred":
            external_client.username_pw_set(username, password)
            external_client.connect("classpip.upc.edu", 8000)
            print('Connected to classpip.upc.edu:8000')

        elif external_broker == "classpip_cert":
            external_client.username_pw_set(username, password)
            external_client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED,
                                    tls_version=ssl.PROTOCOL_TLS, ciphers=None)
            external_client.connect("classpip.upc.edu", 8883)
            print('Connected to classpip.upc.edu:8883')
        elif external_broker == "localhost":
            external_client.connect("localhost", 8000)
            print('Connected to localhost:8000')
        elif external_broker == "localhost_cert":
            print('Not implemented yet')

    elif connection_mode == "local":
        if operation_mode == "simulation":
            external_client.connect("localhost", 8000)
            print('Connected to localhost:8000')
        else:
            external_client.connect("10.10.10.1", 8000)
            print('Connected to 10.10.10.1:8000')

    print("Waiting....")
    external_client.subscribe("+/airApiService/#", 2)
    external_client.subscribe("cameraService/+/#", 2)
    internal_client.subscribe("+/airApiService/#")
    internal_client.loop_start()
    if operation_mode == 'simulation':
        external_client.loop_forever()
    else:
        # external_client.loop_start() #when executed on board use loop_start instead of loop_forever
        external_client.loop_forever()


if __name__ == '__main__':
    import sys

    connection_mode = sys.argv[1]  # global or local
    operation_mode = sys.argv[2]  # simulation or production
    username = None
    password = None
    if connection_mode == 'global':
        external_broker = sys.argv[3]
        if external_broker == 'classpip_cred' or external_broker == 'classpip_cert':
            username = sys.argv[4]
            password = sys.argv[5]
    else:
        external_broker = None

    airApiService(connection_mode, operation_mode, external_broker, username, password)
