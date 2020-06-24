FROM ubuntu:bionic

RUN apt-get update && apt-get install -y locales && locale-gen en_US.UTF-8
RUN locale-gen ru_RU.UTF-8
ENV LANG ru_RU.utf8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

RUN apt-get update && \
    apt-get install software-properties-common -y && \
    apt-get install -y build-essential python3-dev python3-pip && \
    apt-get install -y libreoffice

ADD requirements.txt .
RUN pip3 install -r requirements.txt

RUN mkdir /dedoc
ADD dedoc /dedoc
ENV PYTHONPATH /
