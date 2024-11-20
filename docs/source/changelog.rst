Changelog
=========

v2.3.1 (2024-11-15)
-------------------
Release note: `v2.3.1 <https://github.com/ispras/dedoc/releases/tag/v2.3.1>`_

* Fix bug with bold lines in `DocxReader` (see `issue 479 <https://github.com/ispras/dedoc/issues/479>`_)
* Upgraded requirements.txt (beautifulsoup4 to 4.12.3 version)
* Added support for external grobid (added support parameter "Authorization")
* Added GOST (Russian government standard) frame recognition in `PdfTabbyReader` (`need_gost_frame_analysis` parameter)
* Update documentation (added GOST frame recognition)

v2.3 (2024-09-19)
-----------------
Release note: `v2.3 <https://github.com/ispras/dedoc/releases/tag/v2.3>`_

* `Dedoc telegram chat <https://t.me/dedoc_chat>`_ created.
* Added `patterns` parameter for configuring default structure type (:ref:`using_patterns`).
* Added notebooks with Dedoc usage :ref:`table_notebooks` (see `issue 484 <https://github.com/ispras/dedoc/issues/484>`_).
* Fix bug `OutOfMemoryError: Java heap space` in `PdfTabbyReader` (see `issue 489 <https://github.com/ispras/dedoc/issues/489>`_).
* Fix bug with numeration in `DocxReader` (see `issue 494 <https://github.com/ispras/dedoc/issues/494>`_).
* Added GOST (Russian government standard) frame recognition in `PdfImageReader` and `PdfTxtlayerReader` (`need_gost_frame_analysis` parameter).

v2.2.7 (2024-08-16)
-------------------
Release note: `v2.2.7 <https://github.com/ispras/dedoc/releases/tag/v2.2.7>`_

* Fix bugs with `start`, `end` of `BBoxAnnotation` in `PdfTabbyReader`.
* Improve columns classification and orientation detection for PDF and images (`is_one_column_document` and `document_orientation` parameters).
* Upgrade `docker`: `docker-compose` is no longer supported, use `docker compose` instead.
* Fix bug of tables parsing in `DocxReader` (see `issue 478 <https://github.com/ispras/dedoc/issues/478>`_).
* Added simple textual layer detection in `PdfAutoReader` (`fast_textual_layer_detection` parameter).
* Improve paragraph extraction from PDF documents and images.
* Retrain a classifier for diplomas (document_type="diploma") on a new dataset.

v2.2.6 (2024-07-22)
-------------------
Release note: `v2.2.6 <https://github.com/ispras/dedoc/releases/tag/v2.2.6>`_

* Upgrade dependencies: `numpy<2.0` and `dedoc-utils==0.3.7`.
* Since this version, `dedoc` is supported by `langchain <https://github.com/langchain-ai/langchain>`_ (langchain-community>=0.2.10).

v2.2.5 (2024-07-15)
-------------------
Release note: `v2.2.5 <https://github.com/ispras/dedoc/releases/tag/v2.2.5>`_

* Added internal functions and classes to support integration of Dedoc into `langchain <https://github.com/langchain-ai/langchain>`_
* Upgrade some dependencies, in particular, `xgboost>=1.6.0`, `pandas`, `pdfminer.six`

v2.2.4 (2024-06-20)
-------------------
Release note: `v2.2.4 <https://github.com/ispras/dedoc/releases/tag/v2.2.4>`_

* Show page division and page numbers in the HTML output representation (API usage, return_format="html").
* Make imports from dedoc library faster.
* Added tutorial how to add a new language to dedoc (not finished entirely).
* Added additional page_id metadata for multi-page nodes (structure_type="tree" in API, `TreeConstructor` in the library).
* Updated OCR and orientation/columns classification benchmarks.
* Minor edits of `README.md`.
* Fixed empty cells handling in `CSVReader`.
* Fixed bounding boxes extraction for text in tables for `PdfTabbyReader`.

v2.2.3 (2024-06-05)
-------------------
Release note: `v2.2.3 <https://github.com/ispras/dedoc/releases/tag/v2.2.3>`_

* Show attached images and added ability to download attached files in the HTML output representation (API usage, return_format="html").
* Added hierarchy level information and annotations to `PptxReader`.

v2.2.2 (2024-05-21)
-------------------
Release note: `v2.2.2 <https://github.com/ispras/dedoc/releases/tag/v2.2.2>`_

* Added images extraction to `ArticleReader`.
* Added attachments and references to them in the HTML output representation (return_format="html").
* Fixed functionality of parameter `need_content_analysis`.
* Fixed `CSVReader` (exclude BOM character from the output).
* Added handling files with wrong extension or without extension to `DedocManager` (detect file type by its content).
* Update `README.md`.

v2.2.1 (2024-05-03)
-------------------
Release note: `v2.2.1 <https://github.com/ispras/dedoc/releases/tag/v2.2.1>`_

* Added `fintoc` structure type for parsing financial prospects according to the `FinTOC 2022 Shared task <https://wp.lancs.ac.uk/cfie/fintoc2022/>`_ (`FintocStructureExtractor`).
* Fixed small bugs in `ArticleReader`: colspan for tables, keywords, sections numbering, etc.
* Added references to nodes and fixed small bugs in the HTML output representation (return_format="html").
* Removed `other_fields` from `LineMetadata` and `DocumentMetadata`.
* Update `README.md`.

v2.2 (2024-04-17)
-----------------
Release note: `v2.2 <https://github.com/ispras/dedoc/releases/tag/v2.2>`_

* `PdfTabbyReader` improved: bugs fixes, speed increase of partial PDF extraction (with parameter `pages`).
* Added benchmarks for evaluation of PDF readers performance.
* Added `ReferenceAnnotation` class.
* Fixed bug in `can_read` method for all readers.
* Added `article` structure type for parsing scientific articles using `GROBID <https://grobid.readthedocs.io>`_ (`ArticleReader`, `ArticleStructureExtractor`).

v2.1.1 (2024-03-21)
-------------------
Release note: `v2.1.1 <https://github.com/ispras/dedoc/releases/tag/v2.1.1>`_

* Update `README.md`.
* Update table and time benchmarks.
* Re-label line-classifier datasets (law, tz, diploma, paragraphs datasets).
* Update tasker creators (for the labeling system).
* Fix HTML table parsing.

v2.1 (2024-03-05)
-----------------
Release note: `v2.1 <https://github.com/ispras/dedoc/releases/tag/v2.1>`_

* Custom loggers deleted (the common logger is used for all dedoc classes).
* Do not change the document image if it has a correct orientation (orientation correction function changed).
* Use only `PdfTabbyReader` during detection of a textual layer in PDF files.
* Code related to the labeling mode refactored and removed from the library package (it is located in the separate directory).
* Added `BoldAnnotation` for words in `PdfImageReader`.
* More benchmarks are added: images of tables parsing, postprocessing of Tesseract OCR.
* Some fixes are made in a web-form of Dedoc.
* Tutorial how to add a new structure type to Dedoc added.
* Parsing of EML and HTML files fixed.


v2.0 (2023-12-25)
-----------------
Release note: `v2.0 <https://github.com/ispras/dedoc/releases/tag/v2.0>`_

* Fix table extraction from PDF using empty config (see `issue <https://github.com/ispras/dedoc/issues/373>`_).
* Add more benchmarks for Tesseract.
* Fix extension extraction for file names with several dots.
* Change names of some methods and their parameters for all main classes (attachments extractors, converters, readers, metadata extractors, structure extractors, structure constructors).
  Please look to the `Package reference` of `documentation <https://dedoc.readthedocs.io>`_ for more details.
* Add `AttachAnnotation` and `TableAnnotation` to `PPTX` (see `discussion <https://github.com/ispras/dedoc/discussions/386>`_).
* Fix bugs in `DOCX` handling (see issues `378 <https://github.com/ispras/dedoc/issues/378>`_, `379 <https://github.com/ispras/dedoc/issues/379>`_

v1.1.1 (2023-11-24)
-------------------
Release note: `v1.1.1 <https://github.com/ispras/dedoc/releases/tag/v1.1.1>`_

* Use older `pydantic` version for improving compatibility with other libraries.
* Add support for `RTF` format.
* Fix bug in handling files' names with dots and spaces.
* Fix bug in non-integer values of text formatting in `DocxReader`.
* Add support of `on_gpu` parameter in `config`.
* Add attached images extraction for `PdfTabbyReader`.
* Fix partial file reading for `PdfTabbyReader`.
* Add tutorial how to create dedoc's basic data structures.
* Fix `attachments_dir` parameter for readers and attachments extractors.

v1.1.0 (2023-10-24)
-------------------
Release note: `v1.1.0 <https://github.com/ispras/dedoc/releases/tag/v1.1.0>`_

* Add `BBoxAnnotation` to table cells for `PdfTabbyReader`.
* Fix swagger, add api schema classes, remove `to_dict` method from `ParsedDocument`.
* Improve parsing PDF by `PdfTxtlayerReader`, add benchmarks.
* Fix `BBoxAnnotation` extraction for tables in `PdfImageReader` using `table_type=split_last_column` parameter.
* Change base method of metadata extractors, rename it to `extract_metadata`.
* Unify `BBoxAnnotation` extraction for all PDF readers - return only words bboxes.
* Increase timeout value for all converters.

v1.0 (2023-10-10)
-----------------
Release note: `v1.0 <https://github.com/ispras/dedoc/releases/tag/v1.0>`_

* Remove `is_one_column_document_list` parameter.
* Add tutorial about support for a new document type to the documentation.
* Improve textual layer correctness classifier.
* Improve orientation and columns classifier.
* Change table's output structure - added `CellWithMeta` instead of a textual string.
* Add `BBoxAnnotation` to table cells for `PdfTxtlayerReader` and `PdfImageReader`.
* Add `ConfidenceAnnotation` to table cells for `PdfImageReader`.
* Remove `insert_table` parameter.
* Added information about table and page rotation to the table and document metadata respectively.
* Use `dedoc-utils <https://pypi.org/project/dedoc-utils>`_ library for document images preprocessing.
* Change web interface, fix online-examples of document processing.
* Add comparison operator to `LineWithMeta`.

v0.11.2 (2023-09-06)
--------------------
Release note: `v0.11.2 <https://github.com/ispras/dedoc/releases/tag/v0.11.2>`_

* Remove plexus-utils-1.1.jar.
* Update installation documentation.
* Add documentation for Tesseract OCR installation.
* Add documentation for annotations.
* Add documentation for secure torch.
* Fix examples.

v0.11.1 (2023-08-30)
--------------------
Release note: `v0.11.1 <https://github.com/ispras/dedoc/releases/tag/v0.11.1>`_

* Add bbox annotations in `PdfTabbyReader`.
* Add bbox annotations for words in `PdfTxtlayerReader`.
* Add an option `plain_text` to the `return_format` parameter.
* Reduce size of the dedoc base image, move dockerfiles to the `separate repository <https://github.com/ispras/dedockerfiles>`_.
* Refactor script for tesseract benchmarking.
* Make fixed dedoc dependencies as ranges.
* Add table cell properties in `PdfTabbyReader`.

v0.11.0 (2023-08-22)
--------------------
Release note: `v0.11.0 <https://github.com/ispras/dedoc/releases/tag/v0.11.0>`_

* Rename exceptions classes.
* Update style tests.
* Change `ConfidenceAnnotation` value range to `[0, 1]`.
* Add bbox annotations for words in `PdfImageReader`.

v0.10.0 (2023-08-01)
--------------------
Release note: `v0.10.0 <https://github.com/ispras/dedoc/releases/tag/v0.10.0>`_

* Add ConfidenceAnnotation annotation for PdfImageReader.
* Remove version parameter from metadata extractors, structure constructors and parsed document methods.
* Add version file and version resolving for the library.
* Add recursive handling of attachments.
* Add parameter for saving attachments in a custom directory.
* Remove dedoc threaded manager.
* Improve PdfAutoReader.
* Add temporary file name to DocumentMetadata.

v0.9.2 (2023-07-18)
-------------------
Release note: `v0.9.2 <https://github.com/ispras/dedoc/releases/tag/v0.9.2>`_

* Fix bug for diplomas with `insert_table=true`.
* Fix logging in PDF slicing.
* Make PdfAutoReader faster.
* Update bold classifier.
* Tests Refactoring.
* Fix bug in models downloading inside docker container.

v0.9.1 (2023-07-05)
-------------------
Release note: `v0.9.1 <https://github.com/ispras/dedoc/releases/tag/v0.9.1>`_

* Fixed bug with `AttachAnnotation` in docx: its value is equal attachment uid instead of file name.


v0.9 (2023-06-26)
-----------------
Release note: `v0.9 <https://github.com/ispras/dedoc/releases/tag/v0.9>`_

* Publication of the first version of dedoc library.
