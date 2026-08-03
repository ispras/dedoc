FROM dedocproject/dedoc_p3.10_base:version_2026_07_29
ARG LANGUAGES="rus"
RUN for lang in $LANGUAGES; do apt install -y tesseract-ocr-$(echo $lang | tr "_" "-"); done

ENV PYTHONPATH "${PYTHONPATH}:/dedoc_root"
ENV RESOURCES_PATH "/dedoc_root/resources"

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 -f https://download.pytorch.org/whl/torch_stable.html
RUN pip3 install --no-cache-dir transformers~=4.49.0

RUN mkdir /dedoc_root
RUN mkdir /dedoc_root/dedoc
COPY dedoc/config.py /dedoc_root/dedoc/config.py
COPY dedoc/download_models.py /dedoc_root/dedoc/download_models.py
RUN python3 /dedoc_root/dedoc/download_models.py

COPY dedoc /dedoc_root/dedoc
COPY VERSION /dedoc_root
RUN echo "__version__ = \"$(cat /dedoc_root/VERSION)\"" > /dedoc_root/dedoc/version.py

CMD ["python3", "/dedoc_root/dedoc/main.py"]
