FROM ubuntu:20.04

RUN apt-get update

RUN apt-get install -y sudo
RUN apt-get install -y nano
RUN apt-get install -y python3.7
RUN apt-get install -y python3-pip
#RUN pip3 install paho-mqtt
#RUN pip3 install paho
#RUN pip3 install fastapi
#RUN pip3 install mongoengine
#RUN pip3 install uvicorn

RUN mkdir /app
WORKDIR /app
ADD . /app
# Verifica si /media ya existe antes de intentar crearlo
#RUN test -d /media || mkdir /media

# Verifica si /media/videos ya existe antes de intentar crearlo
#RUN test -d /media/videos || mkdir /media/videos

# Verifica si /media/pictures ya existe antes de intentar crearlo
#RUN test -d /media/pictures || mkdir /media/pictures

RUN pip install -r requirements.txt

EXPOSE 9000