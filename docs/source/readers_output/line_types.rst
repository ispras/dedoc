.. _readers_line_types:

Types of textual lines
======================

Each reader returns :class:`~dedoc.data_structures.UnstructuredDocument` with textual lines.
Readers don't fill ``hierarchy_level`` metadata field (structure extractors do this), but they can fill ``hierarchy_level_tag`` with information about line types.
Below the readers are enlisted that can return non-empty ``hierarchy_level_tag`` in document lines metadata:

* `+` means that the reader can return lines of this type.
* `-` means that the reader doesn't return  lines of this type due to complexity of the task or lack of information provided by the format.

.. _table_line_types:

.. list-table:: Line types returned by each reader
   :widths: 20 20 20 20 20
   :class: tight-table

   * - **Reader**
     - **header**
     - **list_item**
     - **raw_text, unknown**
     - **key**

   * - :class:`~dedoc.readers.DocxReader`
     - `+`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.readers.HtmlReader`, :class:`~dedoc.readers.MhtmlReader`, :class:`~dedoc.readers.EmailReader`
     - `+`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.readers.RawTextReader`
     - `-`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.readers.JsonReader`
     - `-`
     - `+`
     - `+`
     - `+`

   * - :class:`~dedoc.readers.PdfImageReader`
     - `-`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.readers.PdfTabbyReader`
     - `+`
     - `+`
     - `+`
     - `-`

   * - :class:`~dedoc.readers.PdfTxtlayerReader`
     - `-`
     - `+`
     - `+`
     - `-`
