ARG REPOSITORY="docker.io"
from dedocproject/baseimg

ENV PYTHONPATH ":/dedoc/:/dedoc/src/"

ADD requirements.txt .
RUN python3.8 -m pip install pip==22.0.4 --upgrade && pip3.8 install -r requirements.txt
RUN pip3.8 install torch==1.11.0+cpu torchvision==0.12.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

RUN mkdir /dedoc
ADD src /dedoc/src
ADD resources /dedoc/resources/
ADD test/run_tests_in_docker.sh .
ADD dedoc/config.py /dedoc/
ADD VERSION /dedoc/


CMD ["python3.8", "/dedoc/src/main.py", "-c", "/dedoc/config.py"]