ARG REPOSITORY="docker.io"
FROM dedocproject/dedoc_p3.9_base:version_2023_08_28

ENV PYTHONPATH "${PYTHONPATH}:/dedoc_root:/dedoc_root/tests:/dedoc_root/langchain"

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install "langchain-community<1.0"

RUN mkdir /dedoc_root
COPY docs/source/_static/code_examples/langchain /dedoc_root/langchain
COPY dedoc /dedoc_root/dedoc
COPY VERSION /dedoc_root
RUN echo "__version__ = \"$(cat /dedoc_root/VERSION)\"" > /dedoc_root/dedoc/version.py
COPY tests /dedoc_root/tests

CMD [ "bash", "/dedoc_root/tests/run_tests_in_docker.sh" ]
