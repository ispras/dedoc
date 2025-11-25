ARG REPOSITORY="docker.io"
FROM dedocproject/dedoc_jammy_p3.10_base:version_2025_09_11

ENV PYTHONPATH "${PYTHONPATH}:/dedoc_root:/dedoc_root/tests:/dedoc_root/langchain"

COPY requirements.txt .
RUN pip3 install "langchain-community<1.0"
RUN pip3 install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y --fix-missing --no-install-recommends fontforge

RUN mkdir /dedoc_root
COPY docs/source/_static/code_examples/langchain /dedoc_root/langchain
COPY dedoc /dedoc_root/dedoc
COPY VERSION /dedoc_root
RUN echo "__version__ = \"$(cat /dedoc_root/VERSION)\"" > /dedoc_root/dedoc/version.py
COPY tests /dedoc_root/tests

CMD [ "bash", "/dedoc_root/tests/run_tests_in_docker.sh" ]
