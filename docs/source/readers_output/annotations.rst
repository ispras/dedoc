.. _readers_annotations:

Text annotations
================

Below the readers are enlisted that can return non-empty list of annotations for document lines:

* `+` means that the reader can return the annotation.
* `-` means that the reader doesn't return the annotation due to complexity of the task or lack of information provided by the format.

.. _table_annotations:

.. list-table:: Annotations returned by each reader
   :widths: 20 10 10 10 10 10 10 10
   :class: tight-table

   * - **Annotation**
     - :class:`~dedoc.readers.DocxReader`
     - :class:`~dedoc.readers.HtmlReader`, :class:`~dedoc.readers.MhtmlReader`, :class:`~dedoc.readers.EmailReader`
     - :class:`~dedoc.readers.RawTextReader`
     - :class:`~dedoc.readers.PdfImageReader`
     - :class:`~dedoc.readers.PdfTabbyReader`
     - :class:`~dedoc.readers.PdfTxtlayerReader`
     - :class:`~dedoc.readers.ArticleReader`

   * - :class:`~dedoc.data_structures.AttachAnnotation`
     - `+`
     - `-`
     - `-`
     - `-`
     - `-`
     - `+`
     - `+`

   * - :class:`~dedoc.data_structures.TableAnnotation`
     - `+`
     - `-`
     - `-`
     - `+`
     - `+`
     - `+`
     - `+`

   * - :class:`~dedoc.data_structures.LinkedTextAnnotation`
     - `+`
     - `+`
     - `-`
     - `-`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.data_structures.BBoxAnnotation`
     - `-`
     - `-`
     - `-`
     - `+`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.data_structures.AlignmentAnnotation`
     - `+`
     - `+`
     - `-`
     - `-`
     - `-`
     - `-`
     - `-`

   * - :class:`~dedoc.data_structures.IndentationAnnotation`
     - `+`
     - `-`
     - `+`
     - `+`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.data_structures.SpacingAnnotation`
     - `+`
     - `-`
     - `+`
     - `+`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.data_structures.BoldAnnotation`
     - `+`
     - `+`
     - `-`
     - `+`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.data_structures.ItalicAnnotation`
     - `+`
     - `+`
     - `-`
     - `-`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.data_structures.UnderlinedAnnotation`
     - `+`
     - `+`
     - `-`
     - `-`
     - `-`
     - `-`
     - `-`

   * - :class:`~dedoc.data_structures.StrikeAnnotation`
     - `+`
     - `+`
     - `-`
     - `-`
     - `-`
     - `-`
     - `-`

   * - :class:`~dedoc.data_structures.SubscriptAnnotation`
     - `+`
     - `+`
     - `-`
     - `-`
     - `-`
     - `-`
     - `-`

   * - :class:`~dedoc.data_structures.SuperscriptAnnotation`
     - `+`
     - `+`
     - `-`
     - `-`
     - `-`
     - `-`
     - `-`

   * - :class:`~dedoc.data_structures.ColorAnnotation`
     - `-`
     - `-`
     - `-`
     - `+`
     - `-`
     - `+`
     - `-`

   * - :class:`~dedoc.data_structures.SizeAnnotation`
     - `+`
     - `+`
     - `-`
     - `+`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.data_structures.StyleAnnotation`
     - `+`
     - `+`
     - `-`
     - `-`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.data_structures.ConfidenceAnnotation`
     - `-`
     - `-`
     - `-`
     - `+`
     - `-`
     - `-`
     - `-`

   * - :class:`~dedoc.data_structures.ReferenceAnnotation`
     - `-`
     - `-`
     - `-`
     - `-`
     - `-`
     - `-`
     - `+`
