.. _dedoc_api:

Using dedoc via API
===================

Dedoc can be used as a web application that runs on the ``localhost:1231``.
It's possible to change the port via ``config.py`` file (if you clone the repository and run dedoc as a docker container).

There are two ways to install and run dedoc as a web application:

1. :ref:`install_docker`.

2. :ref:`install_pypi`. After installing library using this method you can run the application via the following command:

    .. code-block:: bash

        dedoc -m main


Application usage
-----------------

Once you run the dedoc application, you can go to ``localhost:1231`` and
look to the main page with the information about dedoc.
From this page you can go to the upload page and manually choose settings for the file parsing.
Then you can get the result after pressing the ``upload`` button.

If you want to use the application in your program,
you can send requests e.g. using `requests <https://pypi.org/project/requests>`_ python library.
Post-requests should be sent to ``http://localhost:1231/upload``.

  .. code-block:: python

    import requests

    data = {
        "pdf_with_text_layer": "auto_tabby",
        "document_type": "diploma",
        "language": "rus",
        "need_pdf_table_analysis": "true",
        "need_header_footer_analysis": "false",
        "is_one_column_document": "true",
        "return_format": 'html'
    }
    with open(filename, 'rb') as file:
        files = {'file': (filename, file)}
        r = requests.post("http://localhost:1231/upload", files=files, data=data)
        result = r.content.decode('utf-8')

The ``data`` dictionary in the example contains some parameters to parse the given file.
They are described in the section :ref:`api_parameters`.

.. _api_parameters:

Api parameters description
--------------------------

.. _table_parameters:

.. flat-table:: Api parameters for files parsing via dedoc
    :widths: 10 5 5 80
    :header-rows: 1
    :class: tight-table

    * - Parameter
      - Values
      - Default value
      - Description

    * - :cspan:`3` **Type of document structure parsing**

    * - document_type
      - other, law, tz, diploma, article, fintoc
      - other
      - Type of the document structure according to specific domain.

        The following parameters are available:

            * **other** -- structure for document of any domain (:ref:`other_structure`);
            * **law** -- Russian laws (:ref:`law_structure`);
            * **tz** -- Russian technical specifications (:ref:`tz_structure`);
            * **diploma** -- Russian thesis (:ref:`diploma_structure`);
            * **article** -- scientific article (:ref:`article_structure`);
            * **fintoc** -- English, French and Spanish financial prospects (:ref:`fintoc_structure`).

        This type is used for choosing a specific structure extractor (and, in some cases, a specific reader).

    * - structure_type
      - tree, linear
      - tree
      - The type of output document representation:

            * **tree** -- the document is represented as a hierarchical structure where nodes are document lines/paragraphs and child nodes have greater hierarchy level then parents according to the level found by structure extractor;

            * **linear** -- the document is represented as a tree where the root is empty node, and all document lines are children of the root.

        This type is used for choosing a specific structure constructor after document structure extraction.

    * - return_format
      - json, pretty_json, html, plain_text, tree
      - json
      - The output format of the result data.
        The document structure from a structure constructor (see :class:`~dedoc.data_structures.ParsedDocument`)
        is transformed to one of the following formats:

        * **json** -- simple json structure got via recursive transformation of :class:`~dedoc.data_structures.ParsedDocument` into a dictionary, see :ref:`json_format` for examples;

        * **pretty_json** -- prettified by adding indentation to the aforesaid json structure;

        * **html** -- :class:`~dedoc.data_structures.ParsedDocument` is transformed into html file with styles and headers according to the extracted annotations and structure;

        * **plain_text** -- simple textual lines of the document;

        * **tree** -- simple document tree representation in html format (useful for structure visualization).

    * - :cspan:`3` **Attachments handling**

    * - with_attachments
      - true, false
      - false
      - The option to enable attached files extraction.
        Some documents can have attached files (attachments), e.g. images or videos.
        Dedoc allows to find attachments of the given file, get their metadata and save them in the directory where the given file is located.
        If the option is ``false``, all attached files will be ignored.

    * - need_content_analysis
      - true, false
      - false
      - The option to enable file's attachments parsing along with the given file.
        The content of the parsed attachments will be represented as :class:`~dedoc.data_structures.ParsedDocument`
        and saved in the specified return format in the ``attachments`` field (see :ref:`json_format` for examples).
        Use ``true`` value to enable this behaviour.

    * - recursion_deep_attachments
      - integer value >= 0
      - 10
      - If the attached files of the given file contain some attachments, they can also be extracted.
        The level of this recursion can be set via this parameter.

    * - return_base64
      - true, false
      - false
      - Attached files can be encoded in base64 and their contents will be saved instead of saving attached file on disk.
        The encoded contents will be saved in the attachment's metadata in the ``base64_encode`` field.
        Use ``true`` value to enable this behaviour.

    * - :cspan:`3` **Tables handling**

    * - need_pdf_table_analysis
      - true, false
      - true
      - This option is used for PDF documents which are images with text (PDF without a textual layer).
        It is also used for PDF documents when ``pdf_with_text_layer`` is ``true``, ``false``, ``auto`` or ``auto_tabby``.
        Since costly table recognition methods are used to get tables, you may need to use ``need_pdf_table_analysis=false``
        to increase parsing speed and get text without tables.
        If the document has a textual layer, it is recommended to use ``pdf_with_text_layer=tabby``,
        in this case tables will be parsed much easier and faster.

    * - orient_analysis_cells
      - true, false
      - false
      - This option is used for a table recognition in case of PDF documents without a textual layer
        (images, scanned documents or when ``pdf_with_text_layer`` is ``true``, ``false`` or ``auto``).
        When set to ``true``, it enables analysis of rotated cells in table headers.
        Use this option if you are sure that the cells of the table header are rotated.

    * - orient_cell_angle
      - 90, 270
      - 90
      - This option is used for a table recognition in case of PDF documents without a textual layer
        (images, scanned documents or when ``pdf_with_text_layer`` is ``true``, ``false`` or ``auto``).
        It is ignored when ``orient_analysis_cells=false``.
        The option is used to set orientation of cells in table headers:

            * **270** -- cells are rotated 90 degrees clockwise;
            * **90** -- cells are rotated 90 degrees counterclockwise (or 270 clockwise).

    * - :cspan:`3` **PDF handling**

    * - pdf_with_text_layer
      - true, false, tabby, auto, auto_tabby
      - auto_tabby
      - This option is used for choosing a specific reader of PDF documents.
        The following options are available:

            * **true** -- use this option if you are sure that the PDF file has a textual layer (its text is copiable).
              In this case tables will be parsed using table recognition method for documents without a textual layer
              (if you set ``need_pdf_table_analysis=false`` parsing will be faster but tables will be ignored).
              It is recommended to use ``pdf_with_text_layer=tabby`` instead of ``pdf_with_text_layer=true``,
              but you can try this option as well.

            * **false** -- this value forces to use PDF reader for scanned documents (images, PDF without a textual layer)
              even if the document has a textual layer (is copyable).
              It is highly recommended to use this option value if you are sure that documents for parsing
              are images or PDF without a textual layer, because this method is more costly in time and resources.

            * **tabby** -- use this option if you are sure that the PDF file has a textual layer (its text is copiable).
              This option value forces to use PDF reader for documents with a textual layer only,
              it also allows to extract tables easily and quickly.
              The method enabled by this option is much faster than the method enabled by ``pdf_with_text_layer=true``.

            * **auto** -- automatic detection of textual layer presence in the PDF document.
              If the document has a textual layer (is copyable), PDF document parsing works like with ``need_pdf_table_analysis=true``.
              If the document doesn't have a textual layer (it is an image, scanned document), PDF document parsing works like with ``need_pdf_table_analysis=false``.
              It is recommended to use ``pdf_with_text_layer=auto_tabby`` instead of ``pdf_with_text_layer=auto``,
              but you can try this option as well.

            * **auto_tabby** -- automatic detection of textual layer presence in the PDF document.
              If the document has a textual layer (is copyable), PDF document parsing works like with ``need_pdf_table_analysis=tabby``.
              If the document doesn't have a textual layer (it is an image, scanned document), PDF document parsing works like with ``need_pdf_table_analysis=false``.
              It is highly recommended to use this option value for any PDF document parsing.

    * - language
      - rus, eng, rus+eng, fra, spa
      - rus+eng
      - Language of the parsed PDF document without a textual layer. The following values are available:

            * **rus** -- Russian;
            * **eng** -- English;
            * **rus+eng** -- both Russian and English;
            * **fra** -- French (for fintoc structure type);
            * **spa** -- Spanish (for fintoc structure type).

    * - pages
      - :, start:, :end, start:end
      - :
      - If you need to read a part of the PDF document, you can use page slice to define the reading range.
        If the range is set like ``start_page:end_page``, document will be processed from ``start_page`` to ``end_page``
        (``start_page`` to ``end_page`` are included to the range).

            * using **:** means reading all document pages;
            * using empty ``end`` -- **start:** (e.g. 5:) means reading the document from ``start`` up to the end of the document;
            * using empty ``start`` -- **:end** (e.g. :5) means reading the document from the beginning up to the ``end`` page;
            * using **start:end** means reading document pages from ``start`` to ``end`` inclusively.

        If ``start`` > ``end`` or ``start`` > the number of pages in the document, the empty document will be returned.
        If ``end`` > the number of pages in the document, the document will be read up to its end.
        For example, if ``1:3`` is given, 1, 2 and 3 document pages will be processed.

    * - is_one_column_document
      - true, false, auto
      - auto
      - This option is used to set the number of columns if the PDF document is without a textual layer in case it's known beforehand.
        The following values are available:

            * **true** -- the document is single column;
            * **false** -- the document is multi-column (two columns parsing is supported);
            * **auto** -- automatic detection of the number of columns in the document.

        If you are not sure about the number of columns in the documents you need to parse, it is recommended to use ``auto``.

    * - document_orientation
      - auto, no_change
      - auto
      - This option is used to control document orientation analysis for PDF documents without a textual layer.
        The following values are available:

            * **auto** -- automatic detection of rotated document pages (rotation angle 0, 90, 180, 270 degrees) and rotation of document pages;
            * **no_change** -- parse document pages as they are without rotated pages detection.

        If you are sure that the documents you need to parse consist of vertical (not rotated) pages, you can use ``no_change``.

    * - need_header_footer_analysis
      - true, false
      - false
      - This option is used to **remove** headers and footers of PDF documents from the output result.
        If ``need_header_footer_analysis=false``, header and footer lines will present in the output as well as all other document lines.

    * - need_binarization
      - true, false
      - false
      - This option is used to clean background (binarize) for pages of PDF documents without a textual layer.
        If the document's background is heterogeneous, this option may help to improve the result of document text recognition.
        By default ``need_binarization=false`` because its usage may decrease the quality of the document page (and the recognised text on it).

    * - :cspan:`3` **Other formats handling**

    * - delimiter
      - any string
      - None
      - A column separator for files in CSV and TSV format.
        By default "," (comma) is used for CSV and "\\t" (tabulation) for TSV.

    * - encoding
      - any string
      - None
      - The encoding of documents of textual formats like TXT, CSV, TSV.
        Look `here <https://docs.python.org/3/library/codecs.html#encodings-and-unicode>`_ to get the list of possible values for the ``encoding`` parameter.
        By default the encoding of the document is detected automatically.

    * - handle_invisible_table
      - true, false
      - false
      - Handle tables without visible borders as tables for HTML documents.
        By default tables without visible borders are parsed as usual textual lines.
