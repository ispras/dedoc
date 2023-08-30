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

If you need to change some application settings, you may update `config.py` according to your needs and re-build the image.

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
You should have `python` (python3.8+ is recommended) and `pip` installed.


1. Install `libreoffice` and `djvulibre-bin` packages:

  .. code-block:: bash

    sudo apt-get install -y libreoffice djvulibre-bin

These packages are used by converters (doc, odt to docx; xls, ods to xlsx; ppt, odp to pptx; djvu to pdf).
If you don't need converters, you can skip this step.


2. Install `Tesseract OCR 5` framework.
You can try any tutorial for this purpose or look `here <https://github.com/ispras/dedockerfiles/blob/master/dedoc_p3.9_base.Dockerfile>`_
to get the example of Tesseract installing for dedoc container.


3. Install the dedoc library via pip.
To fulfil all the library requirements, you should have `torch~=1.11.0` and `torchvision~=0.12.0` installed.
You can install suitable for you versions of these libraries and install dedoc using pip command:

  .. code-block:: bash

    pip install dedoc

Or you can install dedoc with torch and torchvision included:

  .. code-block:: bash

    pip install "dedoc[torch]"
