# Dedoc

[![Documentation Status](https://readthedocs.org/projects/dedoc/badge/?version=latest)](https://dedoc.readthedocs.io/en/latest/?badge=latest)

![Dedoc](https://github.com/ispras/dedoc/raw/master/dedoc_logo.png)

Dedoc is an open universal system for converting documents to a unified output format. It extracts a document’s logical structure and content, its tables, text formatting and metadata. The document’s content is represented as a tree storing headings and lists of any level. Dedoc can be integrated in a document contents and structure analysis system as a separate module.

## Features and advantages
Dedoc is implemented in Python and works with semi-structured data formats (DOC/DOCX, ODT, XLS/XLSX, CSV, TXT, JSON) and none-structured data formats like images (PNG, JPG etc.), archives (ZIP, RAR etc.), PDF and HTML formats. Document structure extraction is fully automatic regardless of input data type. Metadata and text formatting is also extracted automatically. 

In 2022, the system won a grant to support the development of promising AI projects from the [Innovation Assistance Foundation (Фонд содействия инновациям)](https://fasie.ru/).

## Dedoc provides:
* Extensibility due to a flexible addition of new document formats and to an easy change of an output data format. 
* Support for extracting document structure out of nested documents having different formats. 
* Extracting various text formatting features (indentation, font type, size, style etc.). 
* Working with documents of various origin (statements of work, legal documents, technical reports, scientific papers) allowing flexible tuning for new domains. 
* Working with PDF documents containinng a text layer:
  * Support to automatically determine the correctness of the text layer in PDF documents; 
  * Extract containing and formatting from PDF-documents with a text layer using the developed interpreter of the virtual stack machine for printing graphics according to the format specification. 
Extracting table data from DOC/DOCX, PDF, HTML, CSV and image formats:
  * Recognizing a physical structure and a cell text for complex multipage tables having explicit borders with the help of contour analysis. 
* Working with scanned documents (image formats and PDF without text layer):
  * Using Tesseract, an actively developed OCR engine from Google, together with image preprocessing methods. 
  * Utilizing modern machine learning approaches for detecting a document orientation, detecting single/multicolumn document page, detecting bold text and extracting hierarchical structure based on the classification of features extracted from document images.


This project may be useful as a first step of automatic document analysis pipeline (e.g. before the NLP part)

This project has REST Api and you can run it in Docker container
To read full Dedoc documentation run the project and go to localhost:1231.
 

## Run the project
How to build and run the project

Ensure you have Git and Docker installed
 
Clone the project 
```bash
git clone https://github.com/ispras/dedoc.git

cd dedoc/
```
 
Ensure you have Docker installed.
Start 'Dedoc' on the port 1231:
 ```bash
docker-compose up --build
```

Start Dedoc with tests:
 ```bash
 tests="true" docker-compose up --build
 ```

Now you can go to the localhost:1231 and look at the docs and examples.

You can change the port and host in the config file 'dedoc/config.py'
