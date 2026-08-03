FROM dedocproject/dedoc_p3.10_base:version_2026_07_29
RUN apt-get install -y tesseract-ocr-rus

ENV PYTHONPATH "${PYTHONPATH}:/dedoc_root:/dedoc_root/tests:/dedoc_root/langchain"

COPY requirements.txt .
RUN pip3 install --no-cache-dir "langchain-community<1.0"
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir torch~=2.6.0 torchvision~=0.21.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip3 install --no-cache-dir transformers~=4.49.0

RUN mkdir /dedoc_root
COPY docs/source/_static/code_examples/langchain /dedoc_root/langchain
COPY dedoc /dedoc_root/dedoc
COPY VERSION /dedoc_root
RUN echo "__version__ = \"$(cat /dedoc_root/VERSION)\"" > /dedoc_root/dedoc/version.py
COPY tests /dedoc_root/tests

CMD [ "bash", "/dedoc_root/tests/run_tests_in_docker.sh" ]
