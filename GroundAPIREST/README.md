# API REST for the Drone Engineering Ecosystem

## Table of Contents
1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Local set up](#local-set-up)
5. [Server set up](#server-set-up)
6. [Error](#error)
7. [Endpoints](#endpoints)
8. [Tutorial](#tutorial)

## Introduction
The APIREST module is responsible for storing data on the ground and retrieving it as requested by the rest of the ecosystem modules. The module offers a RESTful interface, so any module can access the data through HTTP requests (GET, POST, PUT, DELETE). Therefore, the communication between APIREST and the rest of modules is not implemented via MQTT, but via HTTP. The data is stored in a MongoDB database.   
      
As an example, the user can design a flightplan using some of the front-end modules of the ecosystem and store it in the APIREST module. Later, the user can retrieve the flight plan, generate the flight associated with it, and send it to the air APIREST module to allow the autopilot to execute it. In the event that the flightplan includes the obtaining of photos or videos, when the flight has landed successfully, the air APIREST module will send all the collected information to this APIREST module, to allow the possibility of the front-end module to show this information to the user.   

## Requirements

Before starting with the installation, make sure you have the following software installed on your system:

- Python 3.7
- MongoDB Community Edition
- MongoDB Database Tools
- MongoDB Compass (optional, but recommended for easier database management)
- FortiClient VPN
- PuTTY
- PyCharm (or any preferred IDE)

## Installation

You can install MongoDB and MongoDB Database Tools from the following links:
- [Install MongoDB](https://www.mongodb.com/docs/manual/administration/install-community/)
- [Install MongoDB Database Tools](https://www.mongodb.com/docs/database-tools/)

To make it easier to work with the database, it is also recommended to install [MongoDB Compass](https://www.mongodb.com/products/compass).

In order to access the Classpip server, if the user is not in the EETAC, there's a need to use a VPN, using FortiClient VPN, so its software needs to be installed:
- [Install FortiClient VPN](https://serveistic.upc.edu/ca/upclink/documentacio/connexio-a-myupclink-des-de-windows/)

## Local set up

To run and contribute, clone this repository to your local machine and install the requirements.  
    
To run the APIREST in localhost for simulation you must edit the run/debug configuration in PyCharm, as shown in the image, in order to pass the required arguments to the script. 
You will need to change from Script path to Module name and input _uvicorn_, as well as adding the following parameters: _main:app --reload_.

![image](https://github.com/Frixon21/RestApiDEE/assets/72676967/e34bd344-ee58-4d86-b2ba-dc65c5d5c117)

![image](https://github.com/Frixon21/RestApiDEE/assets/72676967/d8c9e3e4-b2a8-4df5-be1f-376d070fe58d)


To restore the database you will have to run the following command from the main RestApi directory. Keep in mind that if you did not add the mongoDB Tools to your path you will have to copy them into your folder. 
```
mongorestore dump/
```

## Server set up

Once the APIREST has been tested on localhost, the idea is to have it available on a server, allowing any user to make their desired requests and obtain the information from any device.

The server where this APIREST module is going to be found is the server used in another collaborative project, named Classpip, which offers a private access server where to run this APIREST module. This server requires credentials for access, so before trying to access it, request the necessary credentials.

Before connecting directly to it, and using PuTTY tool named PSFTP, all the different files related to the APIREST module need to be sent to the server, mainly: "classes.py", "main.py" and "requirements.txt".

The configuration needed to access the server, using PuTTY, is the following:

![](https://github.com/JordiLlaveria/GroundAPIRESTDEE/blob/manager/assets/Putty%20Configuration.JPG)

Opening this connection, the credentials mentioned are asked, and the directory where the APIREST module is located is "/jordi". When in this directory, executing the following instruction will start the module:

```
uvicorn main:app --host=0.0.0.0 --port=8105
```

![](https://github.com/JordiLlaveria/GroundAPIRESTDEE/blob/manager/assets/Putty%20Server.JPG)

At this point, the ground APIREST module is working correctly, waiting for the desired requests.

## Error

There's the possibility of receiving the following error when trying to start the module:

![](https://github.com/JordiLlaveria/GroundAPIRESTDEE/blob/manager/assets/Error%20start%20server.PNG)

If this error is received, it means that the server is already running, if it wasn't correctly stopped after making use of it, or that the process is blocked and it can't be started. In both situations, what is recommended is to stop the process completely, kill it, and then try again the uvicorn instruction. To kill it, two instructions are needed:

```
sudo netstat -tupln 
````

This instruction shows all the ungoing processes in the server, in their specific IP address, and the one that is searched is the one executed in 0.0.0.0:8105. When located, __the important value is the PID of this process__, as its the value that identifies it, and the one which is going to be used to kill it.

When this value is known, the command that needs to be executed is the following one, identifing "PID" as the PID found previously:

```
sudo kill -15 "PID"
```

If this process is executed correctly, retrying the uvicorn instruction should return the expected behavior, starting the ground APIREST module.

## Endpoints

Once the service has started, navigate to http://147.83.249.79:8105 in the case of server set up, or http://127.0.0.1:8000 in the case of local one, to see and try all the different API endpoints.

![](https://github.com/JordiLlaveria/GroundAPIRESTDEE/blob/manager/assets/Endpoints.JPG)

You will easily see the data models involved in the different API endpoints.    

## Tutorial

This is a tutorial (in Spanish) to learn how to install the APIREST and create (and test) new endpoints:      
     
[![DroneEngineeringEcosystem Badge](https://img.shields.io/badge/DEE-video_tutorial_APIREST-pink.svg)](https://www.youtube.com/playlist?list=PLyAtSQhMsD4o3VIWiQ7xYB9dx7f-C8Ju1)

     



