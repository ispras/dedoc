# Dedoc

[![Documentation Status](https://readthedocs.org/projects/dedoc/badge/?version=latest)](https://dedoc.readthedocs.io/en/latest/?badge=latest)

![Dedoc](https://github.com/ispras/dedoc/raw/master/dedoc_logo.png)

Dedoc is an open universal system for converting documents to a unified output format. 
It extracts a document’s logical structure and content, its tables, text formatting and metadata. 
The document’s content is represented as a tree storing headings and lists of any level. 
Dedoc can be integrated in a document contents and structure analysis system as a separate module.

## Workflow

![Workflow](https://github.com/ispras/dedoc/raw/master/docs/source/_static/workflow.png)

Workflow description is given [`here`](https://dedoc.readthedocs.io/en/latest/?badge=latest#workflow)

## Features and advantages
Dedoc is implemented in Python and works with semi-structured data formats (DOC/DOCX, ODT, XLS/XLSX, CSV, TXT, JSON) and none-structured data formats like images (PNG, JPG etc.), archives (ZIP, RAR etc.), PDF and HTML formats. 
Document structure extraction is fully automatic regardless of input data type. 
Metadata and text formatting are also extracted automatically. 

In 2022, the system won a grant to support the development of promising AI projects from the [Innovation Assistance Foundation (Фонд содействия инновациям)](https://fasie.ru/).

## Dedoc provides:
* Extensibility due to a flexible addition of new document formats and to an easy change of an output data format. 
* Support for extracting document structure out of nested documents having different formats. 
* Extracting various text formatting features (indentation, font type, size, style etc.). 
* Working with documents of various origin (statements of work, legal documents, technical reports, scientific papers) allowing flexible tuning for new domains. 
* Working with PDF documents containing a textual layer:
  * Support to automatically determine the correctness of the textual layer in PDF documents; 
  * Extract containing and formatting from PDF-documents with a textual layer using the developed interpreter of the virtual stack machine for printing graphics according to the format specification. 
* Extracting table data from DOC/DOCX, PDF, HTML, CSV and image formats:
  * Recognizing a physical structure and a cell text for complex multipage tables having explicit borders with the help of contour analysis. 
* Working with scanned documents (image formats and PDF without text layer):
  * Using Tesseract, an actively developed OCR engine from Google, together with image preprocessing methods. 
  * Utilizing modern machine learning approaches for detecting a document orientation, detecting single/multicolumn document page, detecting bold text and extracting hierarchical structure based on the classification of features extracted from document images.

## Impact
This project may be useful as a first step of automatic document analysis pipeline (e.g. before the NLP part).
Dedoc is in demand for information analytic systems, information leak monitoring systems, as well as for natural language processing systems.
The library is intended for application use by developers of systems for automatic analysis and structuring of electronic documents, including for further search in electronic documents. 

# Online-Documentation
Relevant documentation of the dedoc is available [here](https://dedoc.readthedocs.io/en/latest/)

# Installation instructions
****************************************
This project has REST Api and you can run it in Docker container.
Also, dedoc can be installed as a library via `pip`.
There are two ways to install and run dedoc as a web application or a library that are described below.


## Install and run dedoc using docker 

You should have [`git`](https://git-scm.com) and [`docker`](https://www.docker.com) installed for running dedoc by this method.
This method is more flexible because it doesn't depend on the operating system and other user's limitations,
still, the docker application should be installed and configured properly.

If you don't need to change the application configuration, you may use the built docker image as well.

## Work with dedoc as service

### 1. Pull the image
```shell
docker pull dedocproject/dedoc
```

### 2. Run the container
```shell
docker run -p 1231:1231 --rm dedocproject/dedoc python3 /dedoc_root/dedoc/main.py
```

Go to [dockerhub](https://hub.docker.com/r/dedocproject/dedoc) to get more information about available dedoc images.

If you need to change some application settings, you may update `config.py` according to your needs and re-build the image. 
You can build and run image:

### 1. Clone the repository
```shell
git clone https://github.com/ispras/dedoc
```

### 2. Go to the `dedoc` directory
```shell
cd dedoc
```

### 3. Build the image and run the application
```shell
docker-compose up --build
```

### 4. Run container with tests
```shell
test="true" docker-compose up --build
```

If you need to change some application settings, you may update `config.py` according to your needs and re-build the image.
For example, you can run dedoc on CUDA by setting `on_gpu` to `True` in `config.py`. 

To run Dedoc on CUDA with Docker use files from `docker_gpu` directory 
([CUDA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) 
should be installed on your machine):

```shell
cd docker_gpu
test="true" docker-compose up --build
```

## Install dedoc using pip

If you don't want to use docker for running the application, it's possible to run dedoc locally.
However, it isn't suitable for any operating system (`Ubuntu 20+` is recommended) and
there may be not enough machine's resources for its work.
You should have `python` (`python3.8`, `python3.9` are recommended) and `pip` installed.

### 1. Install necessary packages:
```shell
sudo apt-get install -y libreoffice djvulibre-bin unzip unrar
```

`libreoffice` and `djvulibre-bin` packages are used by converters (doc, odt to docx; xls, ods to xlsx; ppt, odp to pptx; djvu to pdf).
If you don't need converters, you can skip this step.
`unzip` and `unrar` packages are used in the process of extracting archives.

### 2. Install `Tesseract OCR 5` framework:
You can try any tutorial for this purpose or look [`here`](https://github.com/ispras/dedockerfiles/blob/master/dedoc_p3.9_base.Dockerfile)
to get the example of Tesseract installing for dedoc container or use next commands for building Tesseract OCR 5 from sources:

#### 2.1. Install compilers and libraries required by the Tesseract OCR:
```shell
sudo apt-get update
sudo apt-get install -y automake binutils-dev build-essential ca-certificates clang g++ g++-multilib gcc-multilib libcairo2 libffi-dev \
libgdk-pixbuf2.0-0 libglib2.0-dev libjpeg-dev libleptonica-dev libpango-1.0-0 libpango1.0-dev libpangocairo-1.0-0 libpng-dev libsm6 \
libtesseract-dev libtool libxext6 make pkg-config poppler-utils pstotext shared-mime-info software-properties-common swig zlib1g-dev
```
#### 2.2. Build Tesseract from sources:
```shell
sudo add-apt-repository -y ppa:alex-p/tesseract-ocr-devel
sudo apt-get update --allow-releaseinfo-change
sudo apt-get install -y tesseract-ocr tesseract-ocr-rus
git clone --depth 1 --branch 5.0.0-beta-20210916 https://github.com/tesseract-ocr/tesseract/
cd tesseract && ./autogen.sh && sudo ./configure && sudo make && sudo make install && sudo ldconfig && cd ..
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/
```

## Install the dedoc library via pip.

You need `torch~=1.11.0` and `torchvision~=0.12.0` installed. If you already have torch and torchvision in your environment:

```shell
pip install dedoc
```

Or you can install dedoc with torch and torchvision included:

```shell
pip install "dedoc[torch]"
```

## Install and run dedoc from sources

If you want to run dedoc as a service from sources, it's possible to run dedoc locally.
However, it is suitable not for all operating systems (`Ubuntu 20+` is recommended) and
there may be not enough machine's resources for its work.
You should have `python` (`python3.8`, `python3.9` are recommended) and `pip` installed.

### 1. Install necessary packages: according to instructions [install necessary packages](#1-Install-necessary-packages)

### 2. Build Tesseract from sources according to instructions [Install Tesseract OCR-5 framework](#2-Install-Tesseract-OCR-5-framework)

### 3. We recommend to install python's virtual environment (for example, via `virtualenvwrapper`)

Below are the instructions for installing the package `virtualenvwrapper`:

```shell
sudo pip3 install virtualenv virtualenvwrapper
mkdir ~/.virtualenvs
export WORKON_HOME=~/.virtualenvs
echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3.8" >> ~/.bashrc
echo ". /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc
source ~/.bashrc
mkvirtualenv dedoc_env
```

### 4. Install python's requirements and launch dedoc service on default port `1231`:

```shell
# clone dedoc project
git clone https://github.com/ispras/dedoc.git
cd dedoc
# check on your's python environment
workon dedoc_env
export PYTHONPATH=$PYTHONPATH:$(pwd)
pip install -r requirements.txt
pip install torch=1.11.0 torchvision==0.12.0 -f https://download.pytorch.org/whl/torch_stable.html
python dedoc/main.py -c ./dedoc/config.py
```
Now you can go to the `localhost:1231` and look at the docs and examples.

## Option: You can change the port of service:
You need to change environment `DOCREADER_PORT`

1. For local service launching on `your_port` (e.g. `1166`). Install ([installation instruction](#Install-and-run-dedoc-from-sources)) and launch with environment: 
```shell
DOCREADER_PORT=1166 python dedoc/main.py -c ./dedoc/config.py
```

2. For service launching in docker-container you need to change port value in `DOCREADER_PORT` env and field `ports` in `docker-compose.yml` file:
```yaml
    ...
    dedoc:
    ...
    ports:
      - your_port_number:your_port_number
    environment:
      DOCREADER_PORT: your_port_number
    ... 
    test:
    ...
    environment: 
      DOCREADER_PORT: your_port_number
``` 

Go [here](https://dedoc.readthedocs.io/en/latest/getting_started/installation.html) to get more details about dedoc installation.
