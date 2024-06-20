.. _dedoc_installation:

Dedoc installation
==================

There are two ways to install and run dedoc as a web application or a library that are described below.

.. _install_docker:

Install and run dedoc using docker
----------------------------------

You should have `git <https://git-scm.com>`_ and `docker <https://www.docker.com>`_ installed for running dedoc by this method.
This method is more flexible because it doesn't depend on the operating system and other user's limitations,
still, the docker application should be installed and configured properly.

1. Clone the repository

  .. code-block:: bash

    git clone https://github.com/ispras/dedoc

2. Go to the `dedoc` directory

  .. code-block:: bash

    cd dedoc


3. Build the image and run the application

  .. code-block:: bash

    docker-compose up --build

If you need to change some application settings, you may update ``config.py`` according to your needs and re-build the image.

If you don't need to change the application configuration, you may use the built docker image as well.

1. Pull the image

  .. code-block:: bash

    docker pull dedocproject/dedoc

2. Run the container

  .. code-block:: bash

    docker run -p 1231:1231 --rm dedocproject/dedoc python3 /dedoc_root/dedoc/main.py

Go to `dockerhub <https://hub.docker.com/r/dedocproject/dedoc>`_ to get more information about available dedoc images.

.. _install_pypi:

Install dedoc using pip
-----------------------

If you don't want to use docker for running the application, it's possible to run dedoc locally.
However, it isn't suitable for any operating system (Ubuntu 20+ is recommended) and
there may be not enough machine's resources for its work.
You should have ``python`` (python3.8, python3.9 are recommended) and ``pip`` installed.

.. _install_packages:

1. Install necessary packages:
******************************

  .. code-block:: bash

    sudo apt-get install -y libreoffice djvulibre-bin unzip unrar

``libreoffice`` and ``djvulibre-bin`` packages are used by converters (doc, odt, rtf to docx; xls, ods to xlsx; ppt, odp to pptx; djvu to pdf).
If you don't need converters, you can skip this step.
``unzip`` and ``unrar`` packages are used in the process of extracting archives.

.. _install_tesseract:

2. Install `Tesseract OCR 5` framework.
***************************************
You can try any tutorial for this purpose or look `here <https://github.com/ispras/dedockerfiles/blob/master/dedoc_p3.9_base.Dockerfile>`_
to get the example of Tesseract installing for dedoc container or use next commands for building Tesseract OCR 5 from sources:

2.1. Install compilers and libraries required by the Tesseract OCR:

  .. code-block:: bash

    sudo apt-get update
    sudo apt-get install -y automake binutils-dev build-essential ca-certificates clang g++ g++-multilib gcc-multilib libcairo2 libffi-dev \
    libgdk-pixbuf2.0-0 libglib2.0-dev libjpeg-dev libleptonica-dev libpango-1.0-0 libpango1.0-dev libpangocairo-1.0-0 libpng-dev libsm6 \
    libtesseract-dev libtool libxext6 make pkg-config poppler-utils pstotext shared-mime-info software-properties-common swig zlib1g-dev

2.2. Build Tesseract from sources:

    .. code-block:: bash

       sudo add-apt-repository -y ppa:alex-p/tesseract-ocr-devel
       sudo apt-get update --allow-releaseinfo-change
       sudo apt-get install -y tesseract-ocr tesseract-ocr-rus
       git clone --depth 1 --branch 5.0.0-beta-20210916 https://github.com/tesseract-ocr/tesseract/
       cd tesseract && ./autogen.sh && sudo ./configure && sudo make && sudo make install && sudo ldconfig && cd ..
       export TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/

.. _install_library_via_pip:

3. Install the dedoc library via pip.
*************************************
You need ``torch~=1.11.0`` and ``torchvision~=0.12.0`` installed.
If you already have torch and torchvision in your environment:

  .. code-block:: bash

    pip install dedoc

Or you can install dedoc with torch and torchvision included:

  .. code-block:: bash

    pip install "dedoc[torch]"

Install and run dedoc from sources
----------------------------------

If you want to run dedoc as a service from sources. it's possible to run dedoc locally.
However, it isn't suitable for any operating system (Ubuntu 20+ is recommended) and
there may be not enough machine's resources for its work.
You should have ``python`` (python3.8, python3.9 are recommended) and ``pip`` installed.

1. Install necessary packages: according to instructions :ref:`install_packages`

2. Build Tesseract from sources according to instructions :ref:`install_tesseract`

3. We recommend to install python's virtual environment (for example, via ``virtualenvwrapper``)

Below are the instructions for installing the package ``virtualenvwrapper``:

  .. code-block:: bash

    sudo pip3 install virtualenv virtualenvwrapper
    mkdir ~/.virtualenvs
    export WORKON_HOME=~/.virtualenvs
    echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3.8" >> ~/.bashrc
    echo ". /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc
    source ~/.bashrc
    mkvirtualenv dedoc_env

4. Install python's requirements and launch dedoc service on default port ``1231``:

  .. code-block:: bash

    # clone dedoc project
    git clone https://github.com/ispras/dedoc.git
    cd dedoc
    # check on your's python environment
    workon dedoc_env
    export PYTHONPATH=$PYTHONPATH:$(pwd)
    pip install -r requirements.txt
    pip install torch==1.11.0 torchvision==0.12.0 -f https://download.pytorch.org/whl/torch_stable.html
    python dedoc/main.py -c ./dedoc/config.py


Install trusted torch (verified version)
----------------------------------------

You can install a trusted library ``torch`` (as a verified version of the library, verified by tools developed by the Ivannikov Institute for System Programming of the Russian Academy of Sciences).

First you need to install two required packages.:

    .. code-block:: bash

       sudo apt-get install -y mpich intel-mkl

Second you need to install torch and torchvision from built wheels:

For ``python3.8``:
  .. code-block:: bash

     pip install https://github.com/ispras/dedockerfiles/raw/master/wheels/torch-1.11.0a0+git137096a-cp38-cp38-linux_x86_64.whl
     pip install https://github.com/ispras/dedockerfiles/raw/master/wheels/torchvision-0.12.0a0%2B9b5a3fe-cp38-cp38-linux_x86_64.whl

For ``python3.9``:
  .. code-block:: bash

    pip install https://github.com/ispras/dedockerfiles/raw/master/wheels/torch-1.11.0a0+git137096a-cp39-cp39-linux_x86_64.whl
    pip install https://github.com/ispras/dedockerfiles/raw/master/wheels/torchvision-0.12.0a0%2B9b5a3fe-cp39-cp39-linux_x86_64.whl