FROM ubuntu:bionic-20210118

RUN apt-get update && apt-get install -y locales && locale-gen en_US.UTF-8
RUN locale-gen ru_RU.UTF-8
ENV LANG ru_RU.utf8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

RUN apt-get update && apt-get install software-properties-common -y \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get install software-properties-common -y \
    && apt update \
    && apt-get install -y build-essential python3.5 python3.5-dev python3-pip \
    && apt-get install -y libreoffice

ADD requirements.txt .
RUN python3.5 -m pip install pip==20.1.1 --upgrade && pip3.5 install -r requirements.txt

RUN mkdir /dedoc
ADD dedoc /dedoc
ADD VERSION /
ENV PYTHONPATH /
