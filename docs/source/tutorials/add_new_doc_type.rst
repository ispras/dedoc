Adding support for a new document type to Dedoc
===============================================

Suppose you need to add support for a new type "newtype".
Several ways of document processing exist:

* **Converter** - you can write a converter from one document format to another;\
* **Reader** - you can write special format-specific handler;
* **AttachmentExtractor** - if a document contains attachments, the attachment extractor can allow you to extract them.

General scheme of adding Converter
----------------------------------

When there is a parser for a document in a format to which another format is well converted, it's convenient to make a converter. For example, if we know how to parse documents in docx format, but we need to process documents in doc format, we can write a converter from doc to docx.

1. In :file:`dedoc/converters/concrete_converters` create file :file:`newtype_converter.py`
and implement the class :class:`NewtypeConverter` (it isn't necessary to create the class in this particular directory, you can use a different location). This class must inherit
the abstract class :class:`AbstractConverter` from :file:`dedoc/converters/concrete_converters/abstract_converter.py`.
You should call the constructor of the base class in the constructor of the current class.

.. code-block:: python

    from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter

    class NewtypeConverter(AbstractConverter):
       def __init__(self, config):
           super().__init__(config=config)


2. You should implement :meth:`can_convert()` and :meth:`do_convert()` methods to convert other formats to this format.

.. code-block:: python

    class NewtypeConverter(AbstractConverter):

       def __init__(self, config):
           super().__init__(config=config)

       def can_convert(self,
                       extension: str,
                       mime: str,
                       parameters: Optional[dict] = None) -> bool:
           pass  # some code here
       def do_convert(self,
                      tmp_dir: str,
                      filename: str,
                      extension: str) -> str:
            pass  # some code here

* :meth:`can_convert()` method checks if the new converter can process the file, for example, you can return True for the list of some specific file extensions.

* :meth:`do_convert()` method performs the required file conversion. Don't worry about the file name containing spaces or other unwanted characters because the file has been renamed by the manager.

3. Add the converter to :file:`dedoc/manager_config.py`.

   You should add :class:`NewtypeConverter()` in function :meth:`get_manager_config` to ``converter`` field of the dictionary along with other converters.

General scheme of adding Reader
-------------------------------

1. Add new package ``newtype_reader`` to ``dedoc/readers``, ``newtype`` is a new type which you need to add.
2. In ``dedoc/readers/newtype_reader`` create file :file:`newtype_reader.py` and implement class :class:`NewtypeReader`. This class must inherit the abstract class :class:`BaseReader` from :file:`dedoc/readers/base_reader.py`.

.. code-block:: python

    from dedoc.readers.base_reader import BaseReader

    class NewtypeReader(BaseReader):
        pass

3. You should implement :meth:`can_read()` and :meth:`read()` methods according to specific file format processing.

.. code-block:: python

    class NewtypeReader(BaseReader):

        def can_read(self,
                     path: str,
                     mime: str,
                     extension: str,
                     document_type: Optional[str],
                     parameters: Optional[dict] = None) -> bool:
            pass  # some code here

        def read(self,
                 path: str,
                 document_type: Optional[str] = None,
                 parameters: Optional[dict] = None) -> UnstructuredDocument:
            pass  # some code here


* :meth:`can_read()` method checks if the given file can be processed. For processing the following information is required: the path to the file, file extension, mime and document type (for example, you can process only articles). It is better to make this method fast because it will be called frequently.
* :meth:`read()` method must form :class:`UnstructuredDocument` (document lines, tables and attachments).

4. Add a new reader to :file:`dedoc/manager_config.py`.

   You should add :class:`NewtypeReader()` in function :meth:`get_manager_config` to ``reader`` field of the dictionary along with other readers.

General scheme of adding AttachmentExtractor
--------------------------------------------

1. In ``dedoc/attachments_extractors`` create file :file:``newtype_attachment_extractor.py`` and implement the class :class:`NewtypeAttachmentsExtractor`.
   This class must inherit the abstract class :class:`AbstractAttachmentsExtractor` from :file:`dedoc/attachments_extractors/abstract_attachment_extractor.py`.

.. code-block:: python

    from dedoc.attachment_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor

    class NewtypeAttachmentsExtractor(AbstractAttachmentsExtractor):
        pass


2. You should implement :meth:`get_attachments()` and :meth:`can_extract()` methods according to the specifics of extracting attachments for this format.

.. code-block:: python

    from typing import List
    from dedoc.data_structures.attached_file import AttachedFile

    class NewtypeAttachmentsExtractor(AbstractAttachmentsExtractor):
        def can_extract(self,
                        extension: str,
                        mime: str,
                        parameters: Optional[dict] = None) -> bool:
             pass # some code here



        def get_attachments(self,
                            tmpdir: str,
                            filename: str,
                            parameters: dict) -> List[AttachedFile]:
            pass  # some code here

* :meth:`can_extract()` method checks if the new extractor can process the file, for example, you can return True for the list of some specific file extensions.
* :meth:`get_attachments()` method should return a list of attachments that were extracted from the document: for each attachment :class:`AttachedFile` is returned, you can see its code in `dedoc/data_structures/attached_file.py`.


3. Add attachments extractor to the reader's code :file:`newtype_reader.py`.

   You should add line ``self.attachment_extractor = NewtypeAttachmentsExtractor()`` to the constructor of :class:`NewtypeReader` class
   and add attachments extraction to :meth:`read` method (see the example below).

Example of adding pdf/djvu handlers
-----------------------------------

Suppose we want to add the ability to handle pdf / djvu documents with a text layer.
We don't want to deal with two formats, because we can convert djvu to pdf.
The following steps are proposed:
1. Implementing the converter from djvu to pdf DjvuConverter.
2. Implementing of PdfAttachmentsExtractor.
3. Implementing of PdfReader.
4. Adding the implemented handlers to the manager config.

Let's describe each step in more detail.

Implementing the converter from djvu to pdf DjvuConverter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In ``dedoc/converters/concrete_converters`` create file :file:`djvu_converter.py` for :class:`DjvuConverter` implementing.

.. code-block:: python

    from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter

    class DjvuConverter(AbstractConverter):
        def __init__(self, config):
           super().__init__(config=config)

You should implement the following methods:

* :meth:`can_convert()`: return True if file extension is `.djvu`. You can see the file `dedoc/extensions.py` for more accurate work with extensions.
* :meth:`do_convert()`: use `ddjvu` utility and run it using ``os.system``. :meth:`_await_for_conversion()` method ensures that the converted file was saved.

.. literalinclude:: ../_static/code_examples/djvu_converter.py
    :language: python

Implementing of PdfAttachmentsExtractor
---------------------------------------

In ``dedoc/attachments_extractors`` create file :file:`pdf_attachment_extractor.py` for :class:`PdfAttachmentsExtractor` implementing.

.. code-block:: python

    from dedoc.attachment_extractors.abstract_attachment_extractor import AbstractAttachmentsExtractor

    class PdfAttachmentsExtractor(AbstractAttachmentsExtractor):
        pass


You should implement the following methods:

* :meth:`can_extract()`: use file extension or mime to check if we could read the given file. You can learn more about extensions and mime using file :file:`dedoc/extensions.py`
* :meth:`get_attachments()` : use information about file path and file name to extract attachments from the given file.

The method returns the list of :class:`AttachedFile` using :meth:`_content2attach_file` method.
This method is inherited from the abstract class, it makes the list of :class:`AttachedFile` from the list of tuples:
the name of the attached file and binary content of the file.

.. literalinclude:: ../_static/code_examples/pdf_attachment_extractor.py
    :language: python

Implementing of PdfReader
-------------------------

Add new package ``pdf_reader`` to ``dedoc/readers``.
In ``dedoc/readers/pdf_reader`` create file :file:`pdf_reader.py` for :class:`PdfReader` implementing.

.. code-block:: python

    from dedoc.readers.base_reader import BaseReader

    class PdfReader(BaseReader):
        pass


You should implement the following methods:
* :meth:`can_read()`: use file extension or mime to check if we could read the given file. You can learn more about extensions and mime using file :file:`dedoc/extensions.py`.
* :meth:`read()`: Returns document content :class:`UnstructuredDocument`, consisting of a list of document lines :class:`LineWithMeta`, tables :class:`Table` and attachments :class:`AttachedFile`.
For each line, you need to add its text, metadata, hierarchy level (if exists) and annotations (if exist).
For tables, you need to add a list of rows (each row is a list of table cells) and metadata.
You can use :ref:`dedoc_data_structures` to learn more about all the described structures.
We use PyPDF2 to extract the text and tabula to extract tables. They must be added to :file:`requirements.txt` of the project.
We use class :class:`PdfAttachmentsExtractor` for attachments extraction (it was mentioned before).
It must be added to the reader's constructor and used in :meth:`read` method.


.. literalinclude:: ../_static/code_examples/pdf_reader.py
    :language: python

Adding the implemented handlers to the manager config
-----------------------------------------------------

Let part of the contents of the file :file:`dedoc / manager_config.py` looks like this:

.. literalinclude:: ../_static/code_examples/manager_config_example.py
    :language: python

The imports of the classes described above should be added to the beginning of the file:

.. code-block:: python

    from dedoc.converters.concrete_converters.djvu_converter import DjvuConverter
    from dedoc.readers.pdf_reader.pdf_reader import PdfReader


Then you need to add classes to the dictionary in function :meth:`get_manager_config` as follows:

.. literalinclude:: ../_static/code_examples/get_manager_config_example_new_doctype.py
    :language: python
    :lines: 9-29

Adding support for a new document type is completed.
