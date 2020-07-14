# Dedoc

## About
This project called Dedoc and it purpose is 
* Extract text and it metadata from various types of document (what was written in document and how it 
was written)  
* Retrieve logical structure of the document (build tree Title -> section -> subsection and so on) 
*  Extract useful document metadata and attachments.
* Provide a framework that allows you to add new types of documents to the analysis

This project may be useful as a first step of automated  document analysis pipeline (before the NLP part for example)

This project use Rest Api and can work in docker container.  
You may see online  documentation by running the project. 
 

## Run the project
How to build and run the project

Clone the project 
```bash
git clone https://gitlab.at.ispras.ru/Ilya/dedoc_project.git

cd dedoc_project/
```
 
 Ensure that you install docker on your system and
 
 ```bash
docker build . -t dedoc_container
docker run -p 1231:1231 --rm dedoc_container:latest python3 /dedoc/main.py
```

Now you may go to  localhost:1231 and look at docs and examples. 

You may change port and host in config file (dedoc/config.py). 