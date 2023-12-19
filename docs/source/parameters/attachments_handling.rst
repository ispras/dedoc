.. _attachments_handling_parameters:

Attachments handling
====================

.. flat-table:: Parameters for attachments handling
    :widths: 5 5 3 15 72
    :header-rows: 1
    :class: tight-table

    * - Parameter
      - Possible values
      - Default value
      - Where can be used
      - Description

    * - with_attachments
      - True, False
      - False
      - * :meth:`dedoc.DedocManager.parse`,
        * method :meth:`~dedoc.readers.BaseReader.read` of inheritors of :class:`~dedoc.readers.BaseReader`
      - The option to enable attached files extraction.
        If the option is ``False``, all attached files will be ignored.

    * - need_content_analysis
      - True, False
      - False
      - :meth:`dedoc.DedocManager.parse`
      - The option to enable file's attachments parsing along with the given file.
        The content of the parsed attachments will be represented as :class:`~dedoc.data_structures.ParsedDocument`.
        Use ``True`` value to enable this behaviour.

    * - recursion_deep_attachments
      - integer value >= 0
      - 10
      - :meth:`dedoc.DedocManager.parse`
      - If the attached files of the given file contain some attachments, they can also be extracted.
        The level of this recursion can be set via this parameter.

    * - return_base64
      - True, False
      - False
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.extract` for inheritors of :class:`~dedoc.metadata_extractors.AbstractMetadataExtractor`
      - Attached files can be encoded in base64 and their contents will be saved instead of saving attached file on disk.
        The encoded contents will be saved in the attachment's metadata in the ``base64_encode`` field.
        Use ``True`` value to enable this behaviour.

    * - attachments_dir
      - optional string with a valid path
      - None
      - * :meth:`dedoc.DedocManager.parse`
        * method :meth:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor.extract` of inheritors of :class:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor`
        * method :meth:`~dedoc.readers.BaseReader.read` of inheritors of :class:`~dedoc.readers.BaseReader`
      - The path to the directory where document's attached files can be saved.
        By default, attachments are saved into the directory where the given file is located.
