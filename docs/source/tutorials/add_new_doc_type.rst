Adding support for a new document type to Dedoc
===============================================

Suppose you need to add support for a new type "newtype".
Several ways of document processing exist:

* **Converter** - you can write a converter from one document format to another;
* **Reader** - you can write special format-specific handler;
* **AttachmentExtractor** - if a document contains attachments, the attachment extractor can allow you to extract them.


General scheme of adding Converter
----------------------------------

When there is a parser for a document in a format to which another format is well converted, it's convenient to make a converter. For example, if we know how to parse documents in docx format, but we need to process documents in doc format, we can write a converter from doc to docx.

1. Implement ``NewtypeConverter`` class. This class must inherit
the abstract class :class:`~dedoc.converters.AbstractConverter` from ``dedoc/converters/concrete_converters/abstract_converter.py``.
You should call the constructor of the base class in the constructor of the current class.

.. code-block:: python

    from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter

    class NewtypeConverter(AbstractConverter):
       def __init__(self, config):
           super().__init__(config=config)

       def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
           pass  # some code here

       def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
            pass  # some code here

2. Implement converter methods to convert other formats to this format:

* :meth:`~dedoc.converters.AbstractConverter.can_convert` method checks if the new converter can process the file, for example, you can return True for the list of some specific file extensions.

* :meth:`~dedoc.converters.AbstractConverter.do_convert` method performs the required file conversion. Don't worry about the file name containing spaces or other unwanted characters because the file has been renamed by the manager.

3 Add the converter to manager config, see :ref:`adding_handlers_to_manager_config`.

General scheme of adding Reader
-------------------------------

1. Implement ``NewtypeReader`` class. This class must inherit the abstract class :class:`~dedoc.readers.base_reader.BaseReader`.

.. code-block:: python

    from dedoc.readers.base_reader import BaseReader

    class NewtypeReader(BaseReader):

        def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
            pass  # some code here

        def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
            pass  # some code here

2. You should implement reader methods according to specific file format processing.

* :meth:`~dedoc.readers.BaseReader.can_read` method checks if the given file can be processed. For processing the following information is required: the path to the file, file extension, mime and document type (for example, you can process only articles). It is better to make this method fast because it will be called frequently.
* :meth:`~dedoc.readers.BaseReader.read` method must form :class:`~dedoc.data_structures.unstructured_document.UnstructuredDocument` (document lines, tables and attachments).

3. Add the reader to manager config, see :ref:`adding_handlers_to_manager_config`.

General scheme of adding AttachmentExtractor
--------------------------------------------

1. Implement the class ``NewtypeAttachmentsExtractor``.
   This class must inherit the abstract class :class:`~dedoc.attachments_extractors.abstract_attachment_extractor.AbstractAttachmentsExtractor`.

.. code-block:: python

    from typing import List
    from dedoc.data_structures.attached_file import AttachedFile
    from dedoc.attachments_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor

    class NewtypeAttachmentsExtractor(AbstractAttachmentsExtractor):
        def can_extract(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
             pass # some code here

        def get_attachments(self, tmpdir: str, filename: str, parameters: dict) -> List[AttachedFile]:
            pass  # some code here


2. You should implement methods according to the specifics of extracting attachments for this format.

* :meth:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor.can_extract()` method checks if the new extractor can process the file, for example, you can return True for the list of some specific file extensions.
* :meth:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor.get_attachments()` method should return a list of attachments that were extracted from the document: for each attachment :class:`~dedoc.data_structures.attached_file.AttachedFile` is returned, you can see its code in ``dedoc/data_structures/attached_file.py``.


3. Add attachments extractor to the reader's code.

   You should add line ``self.attachment_extractor = NewtypeAttachmentsExtractor()`` to the constructor of ``NewtypeReader`` class
   and add attachments extraction to ``read`` method:

.. code-block:: python

    class NewtypeReader(BaseReader):
        def __init__(self) -> None:
            self.attachment_extractor = PdfAttachmentsExtractor()

Example of adding pdf/djvu handlers
-----------------------------------

Suppose we want to add the ability to handle pdf/djvu documents with a text layer.
We don't want to deal with two formats, because we can convert djvu to pdf.
The following steps are proposed:

1. Implementing the converter from djvu to pdf DjvuConverter.
2. Implementing of PdfAttachmentsExtractor.
3. Implementing of PdfReader.
4. Adding the implemented handlers to the manager config.

Let's describe each step in more detail.

Implementing the converter from djvu to pdf DjvuConverter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Implement class ``DjvuConverter``.

.. literalinclude:: ../_static/code_examples/djvu_converter.py
    :language: python

You should implement the following methods:

* :meth:`~dedoc.converters.AbstractConverter.can_convert`: return True if file extension is `.djvu`. You can see the file ``dedoc/extensions.py`` for more accurate work with extensions.
* :meth:`~dedoc.converters.AbstractConverter.do_convert`: use `ddjvu` utility and run it using ``os.system``. ``._await_for_conversion()`` method ensures that the converted file was saved.


Implementing of PdfAttachmentsExtractor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Implement ``PdfAttachmentsExtractor``.

.. literalinclude:: ../_static/code_examples/pdf_attachment_extractor.py
    :language: python

You should implement the following methods:

* :meth:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor.can_extract()`: use file extension or mime to check if we could read the given file. You can learn more about extensions and mime using file ``dedoc/extensions.py``
* :meth:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor.get_attachments()` : use information about file path and file name to extract attachments from the given file.

The method returns the list of :class:`~dedoc.data_structures.attached_file.AttachedFile` using
:meth:`~dedoc.attachments_extractors.AbstractAttachmentsExtractor._content2attach_file` method.
This method is inherited from the abstract class, it makes the list of :class:`~dedoc.data_structures.attached_file.AttachedFile` from the list of tuples:
the name of the attached file and binary content of the file.


Implementing of PdfReader
^^^^^^^^^^^^^^^^^^^^^^^^^

Implement ``PdfReader``.

.. literalinclude:: ../_static/code_examples/pdf_reader.py
    :language: python

You should implement the following methods:

* :meth:`~dedoc.readers.BaseReader.can_read()`: use file extension or mime to check if we could read the given file. You can learn more about extensions and mime using file ``dedoc/extensions.py``.
* :meth:`~dedoc.readers.BaseReader.read()`: Returns document content :class:`~dedoc.data_structures.unstructured_document.UnstructuredDocument`, consisting of a list of document lines :class:`~dedoc.data_structures.line_with_meta.LineWithMeta`, tables :class:`~dedoc.data_structures.table.Table` and attachments :class:`~dedoc.data_structures.attached_file.AttachedFile`.

For each line, you need to add its text, metadata, hierarchy level (if exists) and annotations (if exist).
For tables, you need to add a list of rows (each row is a list of table cells) and metadata.
You can use :ref:`dedoc_data_structures` to learn more about all the described structures.
We use PyPDF2 to extract the text and tabula to extract tables. They must be added to ``requirements.txt`` of the project.
We use class ``PdfAttachmentsExtractor`` for attachments extraction (it was mentioned before).
It must be added to the reader's constructor and used in ``read`` method.


.. _adding_handlers_to_manager_config:

Adding the implemented handlers to the manager config
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All implemented document handlers are linked to dedoc in `dedoc/manager_config.py <https://github.com/ispras/dedoc/blob/develop/dedoc/manager_config.py>`_


You do not have to edit this file. Create your own ``manager_config`` with dedoc handlers you need and
your custom handlers directly in your code. Example of a manager config with the new handlers:

.. literalinclude:: ../_static/code_examples/dedoc_add_new_doc_type_tutorial.py
    :language: python
    :lines: 1-15, 44-55

Then create an object of :class:`~dedoc.DedocManager` and use :meth:`~dedoc.DedocManager.parse` method:

.. literalinclude:: ../_static/code_examples/dedoc_add_new_doc_type_tutorial.py
    :language: python
    :lines: 16-17, 57-58

Result is :class:`~dedoc.data_structures.ParsedDocument`:

.. literalinclude:: ../_static/code_examples/dedoc_add_new_doc_type_tutorial.py
    :language: python
    :lines: 60-61

Adding support for a new document type is completed.
