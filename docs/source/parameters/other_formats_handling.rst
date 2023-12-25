.. _other_handling_parameters:

Other formats handling
======================

.. flat-table:: Parameters for other formats handling
    :widths: 5 5 3 15 72
    :header-rows: 1
    :class: tight-table

    * - Parameter
      - Possible values
      - Default value
      - Where can be used
      - Description

    * - delimiter
      - any string
      - None
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.CSVReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - A column separator for files in CSV and TSV format.
        By default "," (comma) is used for CSV and "\\t" (tabulation) for TSV.

    * - encoding
      - any string
      - None
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.CSVReader.read`, :meth:`dedoc.readers.RawTextReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - The encoding of documents of textual formats like TXT, CSV, TSV.
        Look `here <https://docs.python.org/3/library/codecs.html#encodings-and-unicode>`_ to get the list of possible values for the ``encoding`` parameter.
        By default the encoding of the document is detected automatically.

    * - handle_invisible_table
      - True, False
      - False
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.HtmlReader.read`, :meth:`dedoc.readers.EmailReader.read`, :meth:`dedoc.readers.MhtmlReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - Handle tables without visible borders as tables for HTML documents.
        By default tables without visible borders are parsed as usual textual lines.
