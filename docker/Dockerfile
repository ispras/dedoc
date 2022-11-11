ARG REPOSITORY="docker.io"
FROM dedocproject/baseimg

ENV PYTHONPATH "${PYTHONPATH}:/dedoc_root"

ADD requirements.txt .
RUN python3.8 -m pip install pip==22.0.4 --upgrade && pip3.8 install -r requirements.txt
RUN pip3.8 install torch==1.11.0+cpu torchvision==0.12.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

RUN mkdir /dedoc_root
ADD dedoc /dedoc_root/dedoc
ADD resources /dedoc_root/resources
ADD tests /dedoc_root/tests
ADD VERSION /dedoc_root


CMD ["python3.8", "/dedoc_root/dedoc/main.py", "-c", "/dedoc_root/dedoc/config.py"]