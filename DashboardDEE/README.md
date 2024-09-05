# Dashboard (Desktop Application)
![FlightPlan](https://github.com/dronsEETAC/DashboardDEE/assets/100842082/76f5d3fc-f58b-4b54-9053-b9ba91224eb2)

The Dashboard is a front-end desktop application developed in python and tkinter. It allows the user to do a bunch of things, including:
- Showing the picture/video stream sent by the camera service
- Free guiding the drone
- Simple flight planning
- Creating a flight plan were images and pictures can be taken
- Showing telemetry data
- Starting/Stopping a LED sequence in the drone

## Demo
This video es a short demo of some of the functionalities of the Dashboard.
[Dashboard in action](https://youtu.be/08v7_bG5FcM)

In the video:
1. A mosquitto broker is started in port 1884. This will serve as internal broker.
2. Since the demo is in simulation mode, the Mission Planner simulator is started.
3. Both the camera service and the autopilot service are started in global and simulation modes, and will user the public broker broker.hivemq.com as external broker. Note that the camera service may take some time to start (be patient).
4. The Dashboard is started. A configuration pannel is presented to the user who can decide modes, external brokers, configure the monitor (record messages published in brokers) and configure the data service (that currently can only record positions).
5. The user get pictures and video stream from the camera service.
6. The user connect with the autopilot (the simulator). Note that telemetry info comes as soon as the autopilot is connected.
7. The user arms and takes off. The Mission Planner pannel is shown to chech that everything is working. Note that the drone 8. stops at 5 meters of altitude, ignoring the altitud introduced by the user.
The user guides the drone in different directions and returns to home.
9. A simple mission planner is opened to introduce and run a flight plan. Note that we can indicate the waypoints where the drone must take a picture and send it to the Dashboard.
10. A second option form flight planning is used to generate a scan of a rectangular area.
11. The flight plan is save into a file and reloaded to be run again.

You can also play with a third option for flight planning (spiral) or to start/stop the monitor from the main pannel of the Dashboard, or to show the positions recorded by the data service in case it was asked to do so or to play with the LEDs service.

## Demo flight plan

This second video, aims to show the modifications made at the time of obtaining data during a flight, mainly images and videos. During all the execution, the ground backend will be started, and it can also be seen how the different communications are exchanged between Docker containers, which contain the different services that take part in the execution of a flight, changing the way these communications took part before.

[Execution of flight plan in action](https://www.youtube.com/watch?v=gr8pJP8eNJE&ab_channel=DronsEETAC)

In the video:
1. The ground backend is started.
2. Docker containers are started in production mode, connected to external broker broker.hivemq.com.
3. Connection to drone is done, allowing to start functionality "Fix waypoints by hand".
4. Flight plan is created, saved into the ground backend using "Save to Db" button, and executed using "Run" button.
5. The flight is monitored, and the exchange of information between Docker containers can be seen through RPi terminal
6. Once the drone has ended the flight correctly, "Save Media" button is selected to flight information from air backend to ground backend
7. Using the functionality "Previous flights", the results of the flight made, or any other desired, can be analyzed, allowing to watch the images and videos taken, obtained from the ground backend.



## Installation and contribution
In order to run and contribute to this module you need Pythion 3.7. We recommend PyCharm as IDE for development.
To contribute to must follow the contribution protocol describen in the main repo of the Drone Engineering Ecosystem.
[![DroneEngineeringEcosystem Badge](https://img.shields.io/badge/DEE-MainRepo-brightgreen.svg)](https://github.com/dronsEETAC/DroneEngineeringEcosystemDEE)

