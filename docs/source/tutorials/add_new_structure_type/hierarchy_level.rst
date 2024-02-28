.. _add_structure_type_hierarchy_level:

Hierarchy level for document lines
==================================

According to the documentation of the class :class:`~dedoc.data_structures.HierarchyLevel`,
it defines the level of the document line :class:`~dedoc.data_structures.LineWithMeta`.
The lower is its value, the more important the line is.

Hierarchy level is used in the intermediate representation of the document :class:`~dedoc.data_structures.UnstructuredDocument`.
In this representation, document content is a flat list of lines.
Hierarchy level of each line adds some hierarchy to this flat list.

:class:`~dedoc.data_structures.LineMetadata` of :class:`~dedoc.data_structures.LineWithMeta` contains two types of hierarchy levels:

    * **tag_hierarchy_level** -- information extracted by readers using information provided by a specific format.
      When it is impossible to get such information, ``tag_hierarchy_level=HierarchyLevel.unknown``.
    * **hierarchy_level** -- information added by structure extractors according to some document domain.
      Hierarchy levels may be custom, but it is recommended to use :meth:`~dedoc.data_structures.HierarchyLevel.create_root` for
      the most important line (if any) and :meth:`~dedoc.data_structures.HierarchyLevel.create_raw_text` for the least important lines.

:class:`~dedoc.data_structures.HierarchyLevel` is used when a structure constructor (:class:`~dedoc.structure_constructors.AbstractStructureConstructor`)
converts :class:`~dedoc.data_structures.UnstructuredDocument` into :class:`~dedoc.data_structures.ParsedDocument`.
The class :class:`~dedoc.structure_constructors.TreeConstructor` compares hierarchy levels of lines, and based on the result,
builds a document tree: the less hierarchy level is, the closer the line will be to the document root, and vice versa.

Hierarchy level contains two levels: ``level_1`` and ``level_2``.
These levels can be filled freely by any integer or ``None`` value, levels will be compared by a tree constructor as tuples:

.. code-block:: python

    (first.level_1, first.level_2) < (second.level_1, second.level_2)

Thus, ``level_1`` defines a primary importance, e.g. for defining type of line:

* Document headings → ``level_1=1``
* Document list items → ``level_1=2``
* Other lines → ``level_1=None``

While ``level_2`` may be used to arrange lines of equal type such as nested lists or multi-level headings:

* `1. list item` → ``level_2=1``
* `1.1 nested list item` → ``level_2=2``
* `1.2 another nested item` → ``level_2=2``
* `1.2.1.1 more deeply nested item` → ``level_2=4``

or

* Heading 1 → ``level_2=1``
* Heading 2 → ``level_2=2``

Thus, when we meet lines `1. list item` with level=(2, 1) and `Heading 2` with level=(1, 2),
the heading line is more important, because (1, 2) < (2, 1).

Lines with ``None`` values are considered the least important, ``None`` is equal +∞ when we compare levels tuples.
For example, raw text lines (``HierarchyLevel.raw_text``) have ``level_1=None`` and ``level_2=None``, they become leaves in the document tree.

Another thing that a tree structure constructor does is lines merging into one tree node.
If ``can_be_multiline`` property is ``True``, it means that the line can be merged with other neighbor lines
that have equal hierarchy level (level_1, level_2) and type (line_type).
Also, for lines with type ``HierarchyLevel.list_item``, an empty parent node with type ``list`` will be created.

.. warning::
    Some details of a hierarchy level and tree structure constructor work may be changed in the future
