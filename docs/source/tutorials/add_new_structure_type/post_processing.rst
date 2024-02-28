.. _add_structure_type_post_processing:

Lines post-processing
=====================

.. seealso::
    The :ref:`description <classification_structure_extractor>` of the whole pipeline for structure extraction using classification.
    Before post-processing, :ref:`add_structure_type_lines_classification` should be done.

The last step of the structure extraction pipeline is post-processing and filling lines' hierarchy levels.
For this purpose, one should implement a structure extractor -- an inheritor of the class :class:`~dedoc.structure_extractors.AbstractStructureExtractor`.

Classifiers of line types sometimes make mistakes, some lines can be split or merged -- all this may be done during post-processing.
A specific logic can be described during implementation of a method :meth:`~dedoc.structure_extractors.AbstractStructureExtractor.extract`.
The main purpose of a structure extractor is to fill ``hierarchy_level`` attribute of the :class:`~dedoc.data_structures.LineMetadata` class.
:ref:`add_structure_type_hierarchy_level` and documentation of the :class:`~dedoc.data_structures.HierarchyLevel` may help
in implementation of a custom structure extractor.


Example: implementation of a structure extractor for English articles
---------------------------------------------------------------------

In the :ref:`lines classification tutorial<add_structure_type_lines_classification>`,
we used an example domain of English articles and implemented ``ArticleLineTypeClassifier``.
Here we continue this example and implement ``ArticleStructureExtractor``.

In the ``__init__`` method of the class, let's initialize a classifier and define domain-specific keywords:

.. literalinclude:: ../../_static/code_examples/article_structure_extractor.py
    :language: python
    :lines: 19-24

Then we should define the :meth:`~dedoc.structure_extractors.AbstractStructureExtractor.extract` method and fill ``hierarchy_level``
attribute according to the following assumptions:

* `title` lines will be merged and form a document root;
* `named_item` lines are children of the root, they may be hierarchical if there is a numeration of article chapters;
* `author`, `affiliation`, `reference` are less important than `named_item` and `title` but more important the rest lines.

With the help of the :ref:`description <add_structure_type_hierarchy_level>` of hierarchy level peculiarities,
we decided to use the following values of ``level_1`` and ``level_2`` of :class:`~dedoc.data_structures.HierarchyLevel`:

* `title` → ``level_1=0, level_2=0``
* `named_item` → ``level_1=1,2, level_2=1,2,3...``
* `author`, `affiliation`, `reference` → ``level_1=3, level_2=1``
* other line types → ``level_1=None, level_2=None``

The implementation of the :meth:`~dedoc.structure_extractors.AbstractStructureExtractor.extract` method can be the following:

.. literalinclude:: ../../_static/code_examples/article_structure_extractor.py
    :language: python
    :lines: 26-49

.. note::
    In the example, we didn't fix any mistakes of the classifier in order to simplify the code.
    In reality, a lot of post-processing work should be done in order to get good results of structure parsing.

The whole code of the ``ArticleStructureExtractor`` can be found below.

The file with the structure extractor should be placed in ``dedoc/structure_extractors/concrete_structure_extractors``.
The resulting file with the structure extractor for English articles (our example) can be downloaded
:download:`here <../../_static/code_examples/article_structure_extractor.py>`.

Or you may copy the code below.

.. toggle::

    .. literalinclude:: ../../_static/code_examples/article_structure_extractor.py
        :language: python
