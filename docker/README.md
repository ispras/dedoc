

# How to change base image version for building dedoc using docker
## Change the DockerfileBaseimg file

This file is used for building an image with tesseract-ocr, libreoffice, secure pytorch and python tools in order to 
reduce time for its building in the main docker/Dockerfile

## Build the new baseimg image locally 

Run the command below from the project root

```shell
export VERSION_TAG=$(date '+%Y_%m_%d')
docker build -t dedocproject/baseimg:version_$VERSION_TAG -f docker/DockerfileBaseimg .
```

## Push the built image to the remote repository

The commands below allow to push the image to the [docker-hub](https://hub.docker.com).
You need login and password for this purpose. 

```shell
docker login -u dedocproject -p <password>
docker tag dedocproject/baseimg:version_$VERSION_TAG dedocproject/baseimg:latest
docker push dedocproject/baseimg:version_$VERSION_TAG
docker push dedocproject/baseimg:latest
```