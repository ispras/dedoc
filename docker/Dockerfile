ARG REPOSITORY="docker.io"
FROM dedocproject/baseimg

ENV PYTHONPATH "${PYTHONPATH}:/dedoc_root"

ADD requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir /dedoc_root
ADD dedoc /dedoc_root/dedoc
ADD resources /dedoc_root/resources
ADD tests /dedoc_root/tests
ADD VERSION /dedoc_root

CMD ["python3", "/dedoc_root/dedoc/main.py", "-c", "/dedoc_root/dedoc/config.py"]