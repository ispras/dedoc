ARG REPOSITORY="docker.io"
FROM dedocproject/dedoc_p3.9_base:version_2023_08_28

ENV PYTHONPATH "${PYTHONPATH}:/dedoc_root"
ENV RESOURCES_PATH "/dedoc_root/resources"

ADD requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN mkdir /dedoc_root
RUN mkdir /dedoc_root/dedoc
ADD dedoc/config.py /dedoc_root/dedoc/config.py
ADD dedoc/download_models.py /dedoc_root/dedoc/download_models.py
RUN python3 /dedoc_root/dedoc/download_models.py

ADD dedoc /dedoc_root/dedoc
ADD VERSION /dedoc_root
RUN echo "__version__ = \"$(cat /dedoc_root/VERSION)\"" > /dedoc_root/dedoc/version.py

ADD tests /dedoc_root/tests
ADD resources /dedoc_root/resources

CMD ["python3", "/dedoc_root/dedoc/main.py", "-c", "/dedoc_root/dedoc/config.py"]
