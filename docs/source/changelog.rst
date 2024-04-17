Changelog
=========

v2.2 (2023-04-17)
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

* Update README.md.
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
