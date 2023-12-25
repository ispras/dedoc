.. _pdf_handling_parameters:

PDF and images handling
=======================

.. flat-table:: Parameters for PDF and images handling
    :widths: 5 5 3 15 72
    :header-rows: 1
    :class: tight-table

    * - Parameter
      - Possible values
      - Default value
      - Where can be used
      - Description

    * - pdf_with_text_layer
      - true, false, tabby, auto, auto_tabby
      - auto_tabby
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.PdfAutoReader.can_read`, :meth:`dedoc.readers.PdfTxtlayerReader.can_read`, :meth:`dedoc.readers.PdfTabbyReader.can_read`
        * :meth:`dedoc.readers.PdfAutoReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - This option is used for choosing a specific reader of PDF documents for :class:`dedoc.DedocManager` or :class:`dedoc.readers.ReaderComposition`.
        For readers, the option is used to check if the reader is able to parse the file.
        The following options are available:

            * **true** -- parsing PDF files with a textual layer (text is copiable).
              This option is used to choose :class:`dedoc.readers.PdfTxtlayerReader` for parsing.

            * **false** -- parsing scanned documents (images, PDF without a textual layer)
              even if the document has a textual layer (is copyable).
              This option is used to choose :class:`dedoc.readers.PdfImageReader` for parsing.
              Note: :class:`dedoc.readers.PdfImageReader` doesn't check the option because it can handle both scanned and copyable documents.

            * **tabby** -- parsing PDF files with a textual layer (text is copiable).
              This option is used to choose :class:`dedoc.readers.PdfTabbyReader` for parsing.

            * **auto** -- automatic detection of textual layer presence in the PDF document.
              This option is used to choose :class:`dedoc.readers.PdfAutoReader` for parsing.
              If the document has a textual layer (is copyable), :class:`dedoc.readers.PdfTxtlayerReader` will be used for parsing.
              If the document doesn't have a textual layer (it is an image, scanned document), :class:`dedoc.readers.PdfImageReader` will be used.


            * **auto_tabby** -- automatic detection of textual layer presence in the PDF document.
              This option is used to choose :class:`dedoc.readers.PdfAutoReader` for parsing.
              If the document has a textual layer (is copyable), :class:`dedoc.readers.PdfTabbyReader` will be used for parsing.
              If the document doesn't have a textual layer (it is an image, scanned document), :class:`dedoc.readers.PdfImageReader` will be used.
              It is highly recommended to use this option value for any PDF document parsing.

    * - language
      - rus, eng, rus+eng
      - rus+eng
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.PdfAutoReader.read`, :meth:`dedoc.readers.PdfImageReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - Language of the document without a textual layer. The following values are available:

            * **rus** -- Russian;
            * **eng** -- English;
            * **rus+eng** -- both Russian and English.

    * - pages
      - :, start:, :end, start:end
      - :
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.PdfAutoReader.read`, :meth:`dedoc.readers.PdfTxtlayerReader.read`, :meth:`dedoc.readers.PdfTabbyReader.read`, :meth:`dedoc.readers.PdfImageReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
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
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.PdfAutoReader.read`, :meth:`dedoc.readers.PdfImageReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - This option is used to set the number of columns if the PDF document is without a textual layer in case it's known beforehand.
        The following values are available:

            * **true** -- the document is single column;
            * **false** -- the document is multi-column (two columns parsing is supported);
            * **auto** -- automatic detection of the number of columns in the document.

        If you are not sure about the number of columns in the documents you need to parse, it is recommended to use ``auto``.

    * - document_orientation
      - auto, no_change
      - auto
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.PdfAutoReader.read`, :meth:`dedoc.readers.PdfImageReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - This option is used to control document orientation analysis for PDF documents without a textual layer.
        The following values are available:

            * **auto** -- automatic detection of rotated document pages (rotation angle 0, 90, 180, 270 degrees) and rotation of document pages;
            * **no_change** -- parse document pages as they are without rotated pages detection.

        If you are sure that the documents you need to parse consist of vertical (not rotated) pages, you can use ``no_change``.

    * - need_header_footer_analysis
      - True, False
      - False
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.PdfAutoReader.read`, :meth:`dedoc.readers.PdfTxtlayerReader.read`, :meth:`dedoc.readers.PdfImageReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - This option is used to **remove** headers and footers of PDF documents from the output result.
        If ``need_header_footer_analysis=False``, header and footer lines will present in the output as well as all other document lines.

    * - need_binarization
      - True, False
      - False
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.PdfAutoReader.read`, :meth:`dedoc.readers.PdfImageReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - This option is used to clean background (binarize) for pages of PDF documents without a textual layer.
        If the document's background is heterogeneous, this option may help to improve the result of document text recognition.
        By default ``need_binarization=False`` because its usage may decrease the quality of the document page (and the recognised text on it).

    * - need_pdf_table_analysis
      - True, False
      - True
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.PdfAutoReader.read`, :meth:`dedoc.readers.PdfTxtlayerReader.read`, :meth:`dedoc.readers.PdfImageReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - This option is used to enable table recognition for PDF documents or images.
        The table recognition method is used in :class:`dedoc.readers.PdfImageReader` and :class:`dedoc.readers.PdfTxtlayerReader`.
        If the document has a textual layer, it is recommended to use :class:`dedoc.readers.PdfTabbyReader`,
        in this case tables will be parsed much easier and faster.

    * - orient_analysis_cells
      - True, False
      - False
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.PdfAutoReader.read`, :meth:`dedoc.readers.PdfTxtlayerReader.read`, :meth:`dedoc.readers.PdfImageReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - This option is used for a table recognition for PDF documents or images.
        It is ignored when ``need_pdf_table_analysis=False``.
        When set to ``True``, it enables analysis of rotated cells in table headers.
        Use this option if you are sure that the cells of the table header are rotated.

    * - orient_cell_angle
      - 90, 270
      - 90
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.readers.PdfAutoReader.read`, :meth:`dedoc.readers.PdfTxtlayerReader.read`, :meth:`dedoc.readers.PdfImageReader.read`
        * :meth:`dedoc.readers.ReaderComposition.read`
      - This option is used for a table recognition for PDF documents or images.
        It is ignored when ``need_pdf_table_analysis=False`` or ``orient_analysis_cells=False``.
        The option is used to set orientation of cells in table headers:

            * **270** -- cells are rotated 90 degrees clockwise;
            * **90** -- cells are rotated 90 degrees counterclockwise (or 270 clockwise).
