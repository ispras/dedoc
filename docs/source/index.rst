Dedoc: the system for document structure extraction
===================================================

.. image:: https://github.com/ispras/dedoc/raw/master/dedoc_logo.png
        :align: center

Dedoc is an open universal system for converting textual documents of different formats to a unified output representation.

Dedoc allows to extract the following data from the documents:
    * **Content** - textual lines of the document in the reading order;
    * **Annotations** of the lines - formatting of the text for its visual representation;
    * **Structure** - type of each document line and its level (importance) in the document hierarchy;
    * **Tables** - tables that are found in the document;
    * **Attachments** - files, attached to the document;
    * **Metadata** - some additional information about the file, e.g. creation date or the author.

Dedoc can be integrated in some system for document contents and structure analysis as a separate module.
Dedoc can be used as a python library, API service or a docker container.

Workflow
--------

The main workflow consists of the following stages:
    1. **Converting** document to one of the supported formats.
    There are some documents that can be easily converted to another well-known format, e.g. odt to docx.
    In this case we use converters to convert these documents to one common format in order to facilitate the subsequent reading.
    The list of supported document formats and which of them should be converted is shown in the table :ref:`table`.

    2. **Reading** the converted document to get intermediate representation of the document.
    This representation include document lines with annotations, tables, attachments and metadata.

    3. **Structure extraction** from the document.
    This stage includes line types and hierarchy levels identification.

    4. **Structure construction** of the output.
    The result document structure representation may vary and
    structure constructors may use the information about lines types and levels differently.
    For example, the tree of document lines may be built.

Reading documents using dedoc
-----------------------------

Dedoc allows to get the common intermediate representation for the documents of various formats.
The resulting output of any reader is a class :class:`~dedoc.data_structures.UnstructuredDocument`.

.. _table:

.. list-table:: Supported documents formats and the reader's output
   :widths: 40 25 10 10 15
   :header-rows: 1
   :class: tight-table

   * - Document format
     - Reader
     - Lines
     - Tables
     - Attachments

   * - zip, tar, tar.gz, rar, 7z
     - :class:`~dedoc.readers.ArchiveReader`
     - `-`
     - `-`
     - `+`

   * - csv, tsv
     - :class:`~dedoc.readers.CSVReader`
     - `-`
     - `+`
     - `-`

   * - docx
     - :class:`~dedoc.readers.DocxReader`
     - `+`
     - `+`
     - `+`

   * - doc, odt
     - convert to docx using :class:`~dedoc.converters.DocxConverter`
     - `+`
     - `+`
     - `+`

   * - xlsx
     - :class:`~dedoc.readers.ExcelReader`
     - `-`
     - `+`
     - `+`

   * - xls, ods
     - convert to xlsx using :class:`~dedoc.converters.ExcelConverter`
     - `-`
     - `+`
     - `+`

   * - pptx
     - :class:`~dedoc.readers.PptxReader`
     - `+`
     - `+`
     - `+`

   * - ppt, odp
     - convert to pptx using :class:`~dedoc.converters.PptxConverter`
     - `+`
     - `+`
     - `+`

   * - html, shtml
     - :class:`~dedoc.readers.HtmlReader`
     - `+`
     - `+`
     - `-`

   * - mhtml, mhtml.gz, mht, mht.gz
     - :class:`~dedoc.readers.MhtmlReader`
     - `+`
     - `+`
     - `+`

   * - json
     - :class:`~dedoc.readers.JsonReader`
     - `+`
     - `-`
     - `+`

   * - txt, txt.gz
     - :class:`~dedoc.readers.RawTextReader`
     - `+`
     - `-`
     - `-`

   * - xml
     - convert to txt using :class:`~dedoc.converters.TxtConverter`
     - `+`
     - `-`
     - `-`

   * - pdf (without textual layer), png
     - :class:`~dedoc.readers.PdfScanReader`
     - `+`
     - `+`
     - `-`

   * - pdf (with textual layer)
     - :class:`~dedoc.readers.TabbyPDFReader`
     - `+`
     - `+`
     - `+`

   * - bmp, dib, eps, gif, hdr, j2k, jfif, jp2, jpe, jpeg, jpg, pbm, pcx, pgm, pic, png, pnm, ppm, ras, sgi, sr, tiff, webp
     - convert to png using :class:`~dedoc.converters.PNGConverter`
     - `+`
     - `+`
     - `-`

   * - djvu
     - convert to pdf using :class:`~dedoc.converters.PDFConverter`
     - `+`
     - `+`
     - `+`

Structure extraction using dedoc
--------------------------------

Documentation will appear soon!

.. toctree::
   :maxdepth: 1
   :caption: Getting started:

   getting_started/installation
   getting_started/usage


.. toctree::
   :maxdepth: 1
   :caption: Dedoc usage

   dedoc_usage/api
   dedoc_usage/readers

.. toctree::
   :maxdepth: 1
   :caption: Package Reference

   modules/data_structures
   modules/converters
   modules/readers
   modules/attachments_extractors
   modules/metadata_extractors
   modules/structure_extractors
   modules/structure_constructors
