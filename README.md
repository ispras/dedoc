# Dedoc

[![image](https://img.shields.io/pypi/pyversions/dedoc.svg)](https://pypi.python.org/pypi/dedoc)
[![GitHub release](https://img.shields.io/github/release/ispras/dedoc.svg)](https://github.com/ispras/dedoc/releases/)
[![PyPI version](https://badge.fury.io/py/dedoc.svg)](https://badge.fury.io/py/dedoc)
[![PyPI downloads](https://pepy.tech/badge/dedoc)](https://pepy.tech/project/dedoc)
[![Docker Hub](https://img.shields.io/docker/pulls/dedocproject/dedoc.svg)](https://hub.docker.com/r/dedocproject/dedoc/ "Docker Pulls")
[![License](http://img.shields.io/:license-apache-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)
[![Demo dedoc-readme.hf.space](https://img.shields.io/website-up-down-green-red/https/huggingface.co/spaces/dedoc/README.svg)](https://dedoc-readme.hf.space)
[![Documentation Status](https://readthedocs.org/projects/dedoc/badge/?version=latest)](https://dedoc.readthedocs.io/en/latest/?badge=latest)
[![CI tests](https://github.com/ispras/dedoc/workflows/CI/badge.svg)](https://github.com/ispras/dedoc/actions)

![Dedoc](https://github.com/ispras/dedoc/raw/master/dedoc_logo.png)

Dedoc is an open universal system for converting documents to a unified output format. 
It extracts a document’s logical structure and content: tables, text formatting and metadata. 
The document’s content is represented as a tree storing headings and lists of any level. 
Dedoc can be integrated in a document contents and structure analysis system as a separate module.

## Workflow

![Workflow](https://github.com/ispras/dedoc/raw/master/docs/source/_static/workflow.png)

Workflow description is given [`here`](https://dedoc.readthedocs.io/en/latest/?badge=latest#workflow)

## Features and advantages
Dedoc is implemented in Python and works with semi-structured data formats (DOC/DOCX, ODT, XLS/XLSX, CSV, TXT, JSON) and unstructured data formats like images (PNG, JPG etc.), archives (ZIP, RAR etc.), PDF and HTML formats. 
Document structure extraction is fully automatic regardless of input data type. 
Metadata and text formatting are also extracted automatically. 

In 2022, the system won a grant to support the development of promising AI projects from the [Innovation Assistance Foundation (Фонд содействия инновациям)](https://fasie.ru/).

## Dedoc provides:
* Extensibility due to flexible addition of new document formats and easy change of an output data format. 
* Support for extracting document structure out of nested documents having different formats. 
* Extracting various text formatting features (indentation, font type, size, style etc.). 
* Working with documents of various origin (statements of work, legal documents, technical reports, scientific papers) allowing flexible tuning for new domains. 
* Working with PDF documents containing a textual layer:
  * Support to automatically determine the correctness of the textual layer in PDF documents; 
  * Extract containing and formatting from PDF-documents with a textual layer using the developed interpreter of the virtual stack machine for printing graphics according to the format specification. 
* Extracting table data from DOC/DOCX, PDF, HTML, CSV and image formats:
  * Recognizing a physical structure and a cell text for complex multipage tables having explicit borders with the help of contour analysis. 
* Working with scanned documents (image formats and PDF without text layer):
  * Using Tesseract, an actively developed OCR engine from Google, together with image preprocessing methods. 
  * Utilizing modern machine learning approaches for detecting a document orientation, detecting single/multicolumn document page, detecting bold text and extracting hierarchical structure based on the classification of features extracted from document images.

## Document format description
The system processes different document formats. The main formats are listed below:

| Format group         | Description                                                                                                                                                                                                                                                                                                                                                                                                                                   |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Office formats       | DOCX, XLSX, PPTX and formats that can be converted to them. Handling of these formats is held by analysis of format inner representation and using specialized libraries ([python-docx](https://python-docx.readthedocs.io/en/latest/), [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/))                                                                                                                              |
| HTML, EML, MHTML     | HTML  documents  are  parsed  using  tags analysis,  HTML  handler  is  used  for  handling  documents  of  other  formats  in  this group                                                                                                                                                                                                                                                                                                    |
| TXT                  | Only raw textual content is analyzed                                                                                                                                                                                                                                                                                                                                                                                                          |
| Archives             | Attachments of the archive are analyzed                                                                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                  |
| PDF, document images | Copyable PDF documents (with a textual layer) can be handled using [pdfminer-six](https://pdfminersix.readthedocs.io/en/latest/) library or [tabby](https://github.com/sunveil/ispras_tbl_extr) software. Non-copyable PDF documents or images are handled using [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract), machine learning methods (including neural network methods) and [image processing methods](https://opencv.org/) |

## Examples of processed scanned documents
* Dedoc can only process scanned black and white documents, such as technical specifications, regulations, articles, etc.
<img src="https://github.com/ispras/dedoc/raw/master/docs/source/_static/doc_examples.png" alt="Document examples" style="width:800px;"/>

* In particular, dedoc recognizes tabular information only from tables with explicit boundaries. Here are examples of documents that can be processed by an dedoc's image handler:
<img src="https://github.com/ispras/dedoc/raw/master/docs/source/_static/example_table.jpg" alt="Table parsing example" style="width:600px;"/>

* The system also automatically detects and corrects the orientation of scanned documents

## Examples of structure extractors
<img src="https://github.com/ispras/dedoc/raw/master/docs/source/_static/str_ext_example_law.png" alt="Law structure example"/>
<img src="https://github.com/ispras/dedoc/raw/master/docs/source/_static/str_ext_example_tz.png" alt="Tz structure example"/>


## Impact
This project may be useful as a first step of an automatic document analysis pipeline (e.g. before the NLP part).
Dedoc is in demand for information analytic systems, information leak monitoring systems, as well as for natural language processing systems.
The library is intended for application use by developers of systems for automatic analysis and structuring of electronic documents, including for further search in electronic documents. 

# Documentation
Relevant documentation of dedoc is available [here](https://dedoc.readthedocs.io/en/latest/)

# Demo

* You can try [dedoc demo](https://dedoc-readme.hf.space)
* You can watch [video about dedoc](https://www.youtube.com/watch?v=ZUnPYV8rd9A)

![](https://github.com/ispras/dedoc/raw/master/docs/source/_static/web_interface.png)

![](https://github.com/ispras/dedoc/raw/master/docs/source/_static/dedoc_short.gif)

# Publications related to dedoc

* Article [ISPRAS@FinTOC-2022 shared task: Two-stage TOC generation model](https://aclanthology.org/2022.fnp-1.13.pdf) for the [FinTOC 2022 Shared Task](https://wp.lancs.ac.uk/cfie/fintoc2022/). We are the winners :smiley: :trophy:!
* Article on habr.com [Dedoc: как автоматически извлечь из текстового документа всё и даже немного больше](https://habr.com/ru/companies/isp_ras/articles/779390/) in Russian (2023)
* Article [Dedoc: A Universal System for Extracting Content and Logical Structure From Textual Documents](https://ieeexplore.ieee.org/abstract/document/10508151/) in English (2023)

# Installation instructions

This project has a REST api and you can run it in Docker container.
Also, dedoc can be installed as a library via `pip`.
There are two ways to install and run dedoc as a web application or a library that are described below.


## Install and run dedoc using docker 

You should have [`git`](https://git-scm.com) and [`docker`](https://www.docker.com) installed for running dedoc by this method.
This method is more flexible because it doesn't depend on the operating system and other user's limitations,
still, the docker application should be installed and configured properly.

If you don't need to change the application configuration, you may use the built docker image as well.

## Work with dedoc as service

### 1. Pull the image
```shell
docker pull dedocproject/dedoc
```

### 2. Run the container
```shell
docker run -p 1231:1231 --rm dedocproject/dedoc python3 /dedoc_root/dedoc/main.py
```

Go to [dockerhub](https://hub.docker.com/r/dedocproject/dedoc) to get more information about available dedoc images.

If you need to change some application settings, you may update `config.py` according to your needs and re-build the image. 
You can build and run image:

### 1. Clone the repository
```shell
git clone https://github.com/ispras/dedoc
```

### 2. Go to the `dedoc` directory
```shell
cd dedoc
```

### 3. Build the image and run the application
```shell
docker compose up --build
```

### 4. Run container with tests
```shell
test="true" docker compose up --build
```

If you need to change some application settings, you may update `config.py` according to your needs and re-build the image.


## Install dedoc using pip

If you don't want to use docker for running the application, it's possible to run dedoc locally.
However, it isn't suitable for any operating system (`Ubuntu 20+` is recommended) and
there may be not enough machine resources for its work.
You should have `python` (`python3.8`, `python3.9` are recommended) and `pip` installed.
Installation instructions via pip are available [here](https://dedoc.readthedocs.io/en/latest/getting_started/installation.html#install-dedoc-using-pip).

## Install and run dedoc from sources
You can also install and run dedoc locally from sources using [this](https://dedoc.readthedocs.io/en/latest/getting_started/installation.html#install-and-run-dedoc-from-sources) instruction.

