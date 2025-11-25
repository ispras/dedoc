ARG REPOSITORY="docker.io"
FROM dedocproject/dedoc_jammy_p3.10_base:version_2025_09_11

ENV PYTHONPATH "${PYTHONPATH}:/labeling_root:/labeling_root/labeling"
ENV RESOURCES_PATH "/labeling_root/resources"

ADD requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install Jinja2==3.1.2

RUN mkdir /labeling_root
RUN mkdir /labeling_root/dedoc
ADD dedoc/config.py /labeling_root/dedoc/config.py
ADD dedoc/download_models.py /labeling_root/dedoc/download_models.py
RUN python3 /labeling_root/dedoc/download_models.py

ADD dedoc /labeling_root/dedoc
ADD VERSION /labeling_root
RUN echo "__version__ = \"$(cat /labeling_root/VERSION)\"" > /labeling_root/dedoc/version.py

ADD labeling /labeling_root/labeling

CMD ["python3", "/labeling_root/labeling/train_dataset/main.py"]
