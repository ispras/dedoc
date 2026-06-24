Changelog
=========

v2.7 (2026-06-24)
-----------------
Release note: `v2.7 <https://github.com/ispras/dedoc/releases/tag/v2.7>`_

* Added comments extraction from DOCX files.
  Extracted comments are stored in :class:`~dedoc.data_structures.LinkedTextAnnotation` of the commented line.
* Added attachment extraction (images) to :class:`~dedoc.readers.PdfImageReader` (for images and PDF without a textual layer).
* Small bug fix in :class:`~dedoc.readers.PdfTabbyReader`.
* Added notes/comments extraction from PDF (parameter ``extract_notes``) with linking to the commented text.
  Extracted comments are stored in :class:`~dedoc.data_structures.LinkedTextAnnotation` of the commented line.

v2.6.1 (2025-12-16)
-------------------
Release note: `v2.6.1 <https://github.com/ispras/dedoc/releases/tag/v2.6.1>`_

* Fixed some bugs in :class:`~dedoc.readers.DocxReader`.
* Replace outdated ``pylzma`` dependency by ``py7zr``.

v2.6 (2025-09-19)
-----------------
Release note: `v2.6 <https://github.com/ispras/dedoc/releases/tag/v2.6>`_

* Improved table merge algorithm (added check on table layout).
* Improved header footer analysis of :class:`~dedoc.readers.pdf_reader.utils.header_footers_analysis.HeaderFooterDetector`.
* Added header footer analysis support in :class:`~dedoc.readers.PdfTabbyReader`.
* Added header footer analysis info (parameter ``need_header_footer_analysis``) in documentation.
* Updated to python3.10.
* Updated to ubuntu22.04.
* Added :ref:`contributing` (project rules, how to build, how to develop) in documentation.

v2.5 (2025-09-05)
-----------------
Release note: `v2.5 <https://github.com/ispras/dedoc/releases/tag/v2.5>`_

* Added simple multilingual textual layer correctness classification based on letter percentage calculation (``textual_layer_classifier=letter``).
* Added a new parameter ``textual_layer_classifier = [simple, ml (default), letter]``.
* Removed parameter ``fast_textual_layer_detection``. Now it is a ``textual_layer_classifier=simple``.
* Fixed bug with ``table_type=table_wo_external_bounds``.
* Added parameter ``table_type`` and :class:`~dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer.TableRecognizer` info into documentation.

v2.4 (2025-07-28)
-----------------
Release note: `v2.4 <https://github.com/ispras/dedoc/releases/tag/v2.4>`_

* Upgrade ``PyPDF2`` to ``pypdf>4`` and fix bugs in attachments extraction from PDF files.
* Added ``each_page_textual_layer_detection`` parameter for textual layer detection on each page of PDF documents (for :class:`~dedoc.readers.PdfAutoReader`).
* Added ``ENABLE_CANCELLATION`` env variable for enabling/disabling parsing cancellation after client disconnection (enabled by default).
* Fixed location coordinates of attached images extracted by :class:`~dedoc.readers.PdfTabbyReader`.
* Added new reader :class:`~dedoc.readers.PdfBrokenEncodingReader` for PDF documents with textual layer but broken encoding (``pdf_with_text_layer=bad_encoding``).

v2.3.2 (2024-12-25)
-------------------
Release note: `v2.3.2 <https://github.com/ispras/dedoc/releases/tag/v2.3.2>`_

* Improve merging multi-page tables in :class:`~dedoc.readers.PdfTabbyReader`.
* Stop parsing after client disconnection (for API usage, see `issue 488 <https://github.com/ispras/dedoc/issues/488>`_).

v2.3.1 (2024-11-15)
-------------------
Release note: `v2.3.1 <https://github.com/ispras/dedoc/releases/tag/v2.3.1>`_

* Fix bug with bold lines in :class:`~dedoc.readers.DocxReader` (see `issue 479 <https://github.com/ispras/dedoc/issues/479>`_).
* Upgraded requirements.txt (beautifulsoup4 to 4.12.3 version).
* Added support for external grobid (added support env variable ``GROBID_AUTH_KEY`` for "Authorization" in request header).
* Added GOST (Russian government standard) frame recognition in :class:`~dedoc.readers.PdfTabbyReader` (``need_gost_frame_analysis`` parameter).
* Update documentation (added :ref:`gost_frame_handling`).

v2.3 (2024-09-19)
-----------------
Release note: `v2.3 <https://github.com/ispras/dedoc/releases/tag/v2.3>`_

* `Dedoc telegram chat <https://t.me/dedoc_chat>`_ created.
* Added ``patterns`` parameter for configuring default structure type (:ref:`using_patterns`).
* Added notebooks with Dedoc usage :ref:`table_notebooks` (see `issue 484 <https://github.com/ispras/dedoc/issues/484>`_).
* Fix bug ``OutOfMemoryError: Java heap space`` in :class:`~dedoc.readers.PdfTabbyReader` (see `issue 489 <https://github.com/ispras/dedoc/issues/489>`_).
* Fix bug with numeration in :class:`~dedoc.readers.DocxReader` (see `issue 494 <https://github.com/ispras/dedoc/issues/494>`_).
* Added GOST (Russian government standard) frame recognition in :class:`~dedoc.readers.PdfImageReader` and
  :class:`~dedoc.readers.PdfTxtlayerReader` (``need_gost_frame_analysis`` parameter).

v2.2.7 (2024-08-16)
-------------------
Release note: `v2.2.7 <https://github.com/ispras/dedoc/releases/tag/v2.2.7>`_

* Fix bugs with ``start``, ``end`` of :class:`~dedoc.data_structures.BBoxAnnotation` in :class:`~dedoc.readers.PdfTabbyReader`.
* Improve columns classification and orientation detection for PDF and images (``is_one_column_document`` and ``document_orientation`` parameters).
* Upgrade ``docker``: ``docker-compose`` is no longer supported, use ``docker compose`` instead.
* Fix bug of tables parsing in :class:`~dedoc.readers.DocxReader` (see `issue 478 <https://github.com/ispras/dedoc/issues/478>`_).
* Added simple textual layer detection in :class:`~dedoc.readers.PdfAutoReader` (``fast_textual_layer_detection`` parameter).
* Improve paragraph extraction from PDF documents and images.
* Retrain a classifier for diplomas (``document_type="diploma"``) on a new dataset.

v2.2.6 (2024-07-22)
-------------------
Release note: `v2.2.6 <https://github.com/ispras/dedoc/releases/tag/v2.2.6>`_

* Upgrade dependencies: ``numpy<2.0`` and ``dedoc-utils==0.3.7``.
* Since this version, ``dedoc`` is supported by `langchain <https://github.com/langchain-ai/langchain>`_ (langchain-community>=0.2.10).

v2.2.5 (2024-07-15)
-------------------
Release note: `v2.2.5 <https://github.com/ispras/dedoc/releases/tag/v2.2.5>`_

* Added internal functions and classes to support integration of Dedoc into `langchain <https://github.com/langchain-ai/langchain>`_
* Upgrade some dependencies, in particular, ``xgboost>=1.6.0``, ``pandas``, ``pdfminer.six``

v2.2.4 (2024-06-20)
-------------------
Release note: `v2.2.4 <https://github.com/ispras/dedoc/releases/tag/v2.2.4>`_

* Show page division and page numbers in the HTML output representation (API usage, ``return_format="html"``).
* Make imports from dedoc library faster.
* Added tutorial how to add a new language to dedoc (not finished entirely).
* Added additional page_id metadata for multi-page nodes (``structure_type="tree"`` in API, :class:`~dedoc.structure_constructors.TreeConstructor` in the library).
* Updated OCR and orientation/columns classification benchmarks.
* Minor edits of ``README.md``.
* Fixed empty cells handling in :class:`~dedoc.readers.CSVReader`.
* Fixed bounding boxes extraction for text in tables for :class:`~dedoc.readers.PdfTabbyReader`.

v2.2.3 (2024-06-05)
-------------------
Release note: `v2.2.3 <https://github.com/ispras/dedoc/releases/tag/v2.2.3>`_

* Show attached images and added ability to download attached files in the HTML output representation (API usage, ``return_format="html"``).
* Added hierarchy level information and annotations to :class:`~dedoc.readers.PptxReader`.

v2.2.2 (2024-05-21)
-------------------
Release note: `v2.2.2 <https://github.com/ispras/dedoc/releases/tag/v2.2.2>`_

* Added images extraction to :class:`~dedoc.readers.ArticleReader`.
* Added attachments and references to them in the HTML output representation (``return_format="html"``).
* Fixed functionality of parameter ``need_content_analysis``.
* Fixed :class:`~dedoc.readers.CSVReader` (exclude BOM character from the output).
* Added handling files with wrong extension or without extension to :class:`~dedoc.DedocManager` (detect file type by its content).
* Update ``README.md``.

v2.2.1 (2024-05-03)
-------------------
Release note: `v2.2.1 <https://github.com/ispras/dedoc/releases/tag/v2.2.1>`_

* Added ``fintoc`` structure type for parsing financial prospects according to the `FinTOC 2022 Shared task <https://wp.lancs.ac.uk/cfie/fintoc2022/>`_ (`FintocStructureExtractor`).
* Fixed small bugs in :class:`~dedoc.readers.ArticleReader`: colspan for tables, keywords, sections numbering, etc.
* Added references to nodes and fixed small bugs in the HTML output representation (``return_format="html"``).
* Removed ``other_fields`` from :class:`~dedoc.data_structures.LineMetadata` and :class:`~dedoc.data_structures.DocumentMetadata`.
* Update ``README.md``.

v2.2 (2024-04-17)
-----------------
Release note: `v2.2 <https://github.com/ispras/dedoc/releases/tag/v2.2>`_

* :class:`~dedoc.readers.PdfTabbyReader` improved: bugs fixes, speed increase of partial PDF extraction (with parameter ``pages``).
* Added benchmarks for evaluation of PDF readers performance.
* Added :class:`~dedoc.data_structures.ReferenceAnnotation` class.
* Fixed bug in ``can_read`` method for all readers.
* Added ``article`` structure type for parsing scientific articles using `GROBID <https://grobid.readthedocs.io>`_
  (:class:`~dedoc.readers.ArticleReader`, :class:`~dedoc.structure_extractors.ArticleStructureExtractor`).

v2.1.1 (2024-03-21)
-------------------
Release note: `v2.1.1 <https://github.com/ispras/dedoc/releases/tag/v2.1.1>`_

* Update ``README.md``.
* Update table and time benchmarks.
* Re-label line-classifier datasets (law, tz, diploma, paragraphs datasets).
* Update tasker creators (for the labeling system).
* Fix HTML table parsing.

v2.1 (2024-03-05)
-----------------
Release note: `v2.1 <https://github.com/ispras/dedoc/releases/tag/v2.1>`_

* Custom loggers deleted (the common logger is used for all dedoc classes).
* Do not change the document image if it has a correct orientation (orientation correction function changed).
* Use only :class:`~dedoc.readers.PdfTabbyReader` during detection of a textual layer in PDF files.
* Code related to the labeling mode refactored and removed from the library package (it is located in the separate directory).
* Added :class:`~dedoc.data_structures.BoldAnnotation` for words in :class:`~dedoc.readers.PdfImageReader`.
* More benchmarks are added: images of tables parsing, postprocessing of Tesseract OCR.
* Some fixes are made in a web-form of Dedoc.
* Tutorial how to add a new structure type to Dedoc added :ref:`add_structure_type`.
* Parsing of EML and HTML files fixed.


v2.0 (2023-12-25)
-----------------
Release note: `v2.0 <https://github.com/ispras/dedoc/releases/tag/v2.0>`_

* Fix table extraction from PDF using empty config (see `issue <https://github.com/ispras/dedoc/issues/373>`_).
* Add more benchmarks for Tesseract.
* Fix extension extraction for file names with several dots.
* Change names of some methods and their parameters for all main classes (attachments extractors, converters, readers, metadata extractors, structure extractors, structure constructors).
  Please look to the `Package reference` of `documentation <https://dedoc.readthedocs.io>`_ for more details.
* Add :class:`~dedoc.data_structures.AttachAnnotation` and :class:`~dedoc.data_structures.TableAnnotation` to PPTX (see `discussion <https://github.com/ispras/dedoc/discussions/386>`_).
* Fix bugs in DOCX handling (see issues `378 <https://github.com/ispras/dedoc/issues/378>`_, `379 <https://github.com/ispras/dedoc/issues/379>`_

v1.1.1 (2023-11-24)
-------------------
Release note: `v1.1.1 <https://github.com/ispras/dedoc/releases/tag/v1.1.1>`_

* Use older ``pydantic`` version for improving compatibility with other libraries.
* Add support for RTF format (:class:`~dedoc.converters.DocxConverter`).
* Fix bug in handling files' names with dots and spaces.
* Fix bug in non-integer values of text formatting in :class:`~dedoc.readers.DocxReader`.
* Add support of ``on_gpu`` parameter in ``config``.
* Add attached images extraction for :class:`~dedoc.readers.PdfTabbyReader`.
* Fix partial file reading for :class:`~dedoc.readers.PdfTabbyReader`.
* Add tutorial how to create dedoc's basic data structures.
* Fix ``attachments_dir`` parameter for readers and attachments extractors.

v1.1.0 (2023-10-24)
-------------------
Release note: `v1.1.0 <https://github.com/ispras/dedoc/releases/tag/v1.1.0>`_

* Add :class:`~dedoc.data_structures.BBoxAnnotation` to table cells for :class:`~dedoc.readers.PdfTabbyReader`.
* Fix swagger, add api schema classes, remove ``to_dict`` method from :class:`~dedoc.data_structures.ParsedDocument`.
* Improve parsing PDF by :class:`~dedoc.readers.PdfTxtlayerReader`, add benchmarks.
* Fix :class:`~dedoc.data_structures.BBoxAnnotation` extraction for tables in :class:`~dedoc.readers.PdfImageReader` using ``table_type=split_last_column`` parameter.
* Change base method of metadata extractors, rename it to ``extract_metadata``.
* Unify :class:`~dedoc.data_structures.BBoxAnnotation` extraction for all PDF readers - return only words bboxes.
* Increase timeout value for all converters.

v1.0 (2023-10-10)
-----------------
Release note: `v1.0 <https://github.com/ispras/dedoc/releases/tag/v1.0>`_

* Remove ``is_one_column_document_list`` parameter.
* Add tutorial about support for a new document type to the documentation.
* Improve textual layer correctness classifier.
* Improve orientation and columns classifier.
* Change table's output structure - added `CellWithMeta` instead of a textual string.
* Add :class:`~dedoc.data_structures.BBoxAnnotation` to table cells for :class:`~dedoc.readers.PdfTxtlayerReader` and :class:`~dedoc.readers.PdfImageReader`.
* Add :class:`~dedoc.data_structures.ConfidenceAnnotation` to table cells for :class:`~dedoc.readers.PdfImageReader`.
* Remove ``insert_table`` parameter.
* Added information about table and page rotation to the table and document metadata respectively.
* Use `dedoc-utils <https://pypi.org/project/dedoc-utils>`_ library for document images preprocessing.
* Change web interface, fix online-examples of document processing.
* Add comparison operator to :class:`~dedoc.data_structures.LineWithMeta`.

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

* Add bbox annotations in :class:`~dedoc.readers.PdfTabbyReader`.
* Add bbox annotations for words in :class:`~dedoc.readers.PdfTxtlayerReader`.
* Add an option ``plain_text`` to the ``return_format`` parameter.
* Reduce size of the dedoc base image, move dockerfiles to the `separate repository <https://github.com/ispras/dedockerfiles>`_.
* Refactor script for tesseract benchmarking.
* Make fixed dedoc dependencies as ranges.
* Add table cell properties in :class:`~dedoc.readers.PdfTabbyReader`.

v0.11.0 (2023-08-22)
--------------------
Release note: `v0.11.0 <https://github.com/ispras/dedoc/releases/tag/v0.11.0>`_

* Rename exceptions classes.
* Update style tests.
* Change :class:`~dedoc.data_structures.ConfidenceAnnotation` value range to ``[0, 1]``.
* Add bbox annotations for words in :class:`~dedoc.readers.PdfImageReader`.

v0.10.0 (2023-08-01)
--------------------
Release note: `v0.10.0 <https://github.com/ispras/dedoc/releases/tag/v0.10.0>`_

* Add :class:`~dedoc.data_structures.ConfidenceAnnotation` annotation for :class:`~dedoc.readers.PdfImageReader`.
* Remove version parameter from metadata extractors, structure constructors and parsed document methods.
* Add version file and version resolving for the library.
* Add recursive handling of attachments.
* Add parameter for saving attachments in a custom directory.
* Remove dedoc threaded manager.
* Improve :class:`~dedoc.readers.PdfAutoReader`.
* Add temporary file name to :class:`~dedoc.data_structures.DocumentMetadata`.

v0.9.2 (2023-07-18)
-------------------
Release note: `v0.9.2 <https://github.com/ispras/dedoc/releases/tag/v0.9.2>`_

* Fix bug for diplomas with ``insert_table=true``.
* Fix logging in PDF slicing.
* Make :class:`~dedoc.readers.PdfAutoReader` faster.
* Update bold classifier.
* Tests Refactoring.
* Fix bug in models downloading inside docker container.

v0.9.1 (2023-07-05)
-------------------
Release note: `v0.9.1 <https://github.com/ispras/dedoc/releases/tag/v0.9.1>`_

* Fixed bug with :class:`~dedoc.data_structures.AttachAnnotation` in docx: its value is equal attachment uid instead of file name.


v0.9 (2023-06-26)
-----------------
Release note: `v0.9 <https://github.com/ispras/dedoc/releases/tag/v0.9>`_

* Publication of the first version of dedoc library.
