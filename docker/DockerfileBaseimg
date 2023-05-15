ARG REPOSITORY="docker.io"
FROM ubuntu:bionic-20210118


RUN apt-get update && apt-get install -y software-properties-common locales && locale-gen en_US.UTF-8
RUN locale-gen ru_RU.UTF-8
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
ENV LANG ru_RU.utf8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

# --------------------------------------------------PYTHON INSTALLATION-------------------------------------------------
RUN apt-get update && \
    apt-get -y install curl git unzip wget build-essential gcc-multilib g++-multilib git clang zlib1g-dev \
                       pkg-config libglib2.0-dev python3 python3-pip libtool binutils-dev
RUN curl https://repo.anaconda.com/archive/Anaconda3-2022.10-Linux-x86_64.sh --output anaconda.sh
RUN bash anaconda.sh -b -p /anaconda3
ENV PATH=/anaconda3/bin:$PATH
RUN conda init bash
RUN bash

RUN apt-get install -y libreoffice

# -----------------------------------------------TESSERACT INSTALLATION-------------------------------------------------
# the commands below are used to install tesseract

RUN add-apt-repository -y ppa:alex-p/tesseract-ocr-devel \
    && apt update --allow-releaseinfo-change \
    && apt-get install -y djvulibre-bin unrtf poppler-utils pstotext tesseract-ocr libjpeg-dev swig \
     libtesseract-dev libleptonica-dev unrar python-poppler automake ca-certificates g++ libtool libleptonica-dev \
     make pkg-config libpango1.0-dev

RUN git clone --depth 1 --branch 5.0.0-beta-20210916 https://github.com/tesseract-ocr/tesseract/
RUN cd tesseract && ./autogen.sh && ./configure &&  make &&  make install && ldconfig

RUN apt update --allow-releaseinfo-change \
    && apt-get install -y tesseract-ocr-rus build-essential libcairo2  \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
ENV TESSDATA_PREFIX /usr/share/tesseract-ocr/5/tessdata/
ENV PATH=/tesseract:$PATH

# for reading j2k
ENV OPENCV_IO_ENABLE_JASPER "true"

# --------------------------------------------------DOCTR INSTALLATION--------------------------------------------------
# ATTENTION: don't change an order of pip's package install here, otherwise you get conflicts
# RUN pip install setuptools==60.10.0 cffi==1.15.0
# RUN pip install python-doctr==0.5.1
# We decided to stop using Doctr. If you need it, uncomment two lines above and comment one line below to make docker image with Doctr.

RUN pip install pyclipper==1.3.0.post4 shapely==2.0.1 Pillow==9.2.0

# ----------------------------------------SECURE TORCH & TORCHVISION INSTALLATION---------------------------------------
RUN wget -O torch-1.11.0a0+git1911a63-cp39-cp39-linux_x86_64.whl https://at.ispras.ru/owncloud/index.php/s/gGZa46pboBlVZ7t/download
RUN pip install torch-1.11.0a0+git1911a63-cp39-cp39-linux_x86_64.whl
RUN wget -O torchvision-0.12.0a0+9b5a3fe-cp39-cp39-linux_x86_64.whl https://at.ispras.ru/owncloud/index.php/s/doFEAhID6OhNCkp/download
RUN pip install torchvision-0.12.0a0+9b5a3fe-cp39-cp39-linux_x86_64.whl
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/anaconda3/lib/
