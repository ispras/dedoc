ARG REPOSITORY="docker.io"
FROM dedocproject/dedoc_p3.9_base:version_2023_08_28

ENV PYTHONPATH "${PYTHONPATH}:/dedoc_root"
ENV RESOURCES_PATH "/dedoc_root/resources"


ADD requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 -f https://download.pytorch.org/whl/torch_stable.html


RUN mkdir /dedoc_root
ADD dedoc /dedoc_root/dedoc
ADD docker_gpu/config_on_gpu.py /dedoc_root/dedoc/config.py
RUN python3 /dedoc_root/dedoc/download_models.py


ADD VERSION /dedoc_root
RUN echo "__version__ = \"$(cat /dedoc_root/VERSION)\"" > /dedoc_root/dedoc/version.py

ADD tests /dedoc_root/tests
ADD resources /dedoc_root/resources

CMD ["python3", "/dedoc_root/dedoc/main.py", "-c", "/dedoc_root/dedoc/config.py"]
