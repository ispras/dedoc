Creating Dedoc Document from basic data structures in code
==========================================================

Let's dig inside Dedoc data structures and build Dedoc document from scratch. During this tutorial you will learn:

* How to use data structures of Dedoc to store text, structure, tables, annotations, metadata, attachments
* What is Dedoc unified output representation of document
* How document structure is defined

Raw document content is stored in :class:`~dedoc.data_structures.UnstructuredDocument`. This is de facto
a container with lists of data strucutres objects:

* list of :class:`~dedoc.data_structures.Table`
* list of text lines :class:`~dedoc.data_structures.LineWithMeta`
* list of attachments :class:`~dedoc.data_structures.AttachedFile`
* dict with metadata

Order of data structures in lists doesn't matter. All document hierarchy and structure is held inside the data structures.


LineWithMeta
------------

Basic block of Dedoc document is :class:`~dedoc.data_structures.LineWithMeta`:

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 4-5

To specify hierarchy you should use :class:`~dedoc.data_structures.HierarchyLevel` class:

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 7-11

Hierarchy level compares by tuple (``level_1``, ``level_2``): lesser values are closer to the root of the tree.
``level_1`` is primary hierarchy dimension that defines type of line:

* `root` is ``level_1`` = 0
* `header` is ``level_1`` = 1

etc.

``level_2`` is a dimension through lines of equal type such as nested lists:

* `1.` is ``level_2`` = 1
* `1.1` is ``level_2`` = 2
* `2.6` is ``level_2`` = 2
* `3.4.5.1` is ``level_2`` = 4

Some parts of the document (for example title) may take more than one line. To union them set ``can_be_multiline``
to `True` and then and copy ``level_1``, ``level_2`` and ``line_type`` from the first line to others.

Define metadata with :class:`~dedoc.data_structures.LineMetadata`:

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 14

Also there is an option to add some :ref:`annotations`:

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 15-18

Now you can create new :class:`~dedoc.data_structures.LineMetadata` with hierarchy level, metadata and annotations:

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 20


Table
-----

Imagine you have table like this:

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 22-25

Main block of tables is :class:`~dedoc.data_structures.CellWithMeta`. To create table, you should
make list of lists of :class:`~dedoc.data_structures.CellWithMeta`.

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 27-34

Table also has some metadata, let's assume that our table is on the first page.
Use :class:`~dedoc.data_structures.TableMetadata`:

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 36

Finally, create :class:`~dedoc.data_structures.Table`:

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 36

AttachedFile
------------

Also we can attach some files: TODO что такое uid

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 39

Unstructured Document
---------------------

Now we are ready to create :class:`~dedoc.data_structures.UnstructuredDocument` object:

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 41

There is an option to add file metadata to document:

.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 43-45

Parsed Document
---------------

There are several ways how the structure of document can be represented. In this tutorial
we will utilize :class:`~dedoc.structure_constructors.TreeConstructor` that
returns document tree from unstrucutred document:


.. literalinclude:: ../_static/code_examples/dedoc_creating_dedoc_document.py
    :language: python
    :lines: 47-51


Great job! You just created your first document in Dedoc format from scratch!


