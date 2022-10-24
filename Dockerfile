FROM ubuntu:bionic-20210118

RUN apt-get update && apt-get install -y locales && locale-gen en_US.UTF-8
RUN locale-gen ru_RU.UTF-8
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
ENV LANG ru_RU.utf8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

RUN apt-get update && apt-get install software-properties-common -y \
    && apt-get install software-properties-common -y \
    && apt update \
    && apt-get install -y git build-essential python3.8 python3.8-dev python3-pip libxml2-dev libxslt-dev python-dev python3.8-distutils \
    && apt-get install -y libreoffice

ADD requirements.txt .
RUN python3.8 -m pip install pip==22.0.4 --upgrade && pip3.8 install -r requirements.txt
RUN pip3.8 install torch==1.11.0+cpu torchvision==0.12.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

RUN mkdir /dedoc
ADD dedoc /dedoc
ADD VERSION /
ENV PYTHONPATH /

CMD ["python3.8", "/dedoc/main.py", "-c", "/dedoc/config.py"]