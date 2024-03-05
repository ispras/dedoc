FROM python:3.8-alpine
RUN apk add git
RUN git clone https://github.com/dronperminov/ImageClassifier.git
RUN rm -r ImageClassifier/config.json ImageClassifier/tasks.json ImageClassifier/images/
RUN pip install -r ImageClassifier/requirements.txt
ADD . /ImageClassifier
WORKDIR /ImageClassifier
CMD python app.py
