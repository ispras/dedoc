Changelog
=========

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
