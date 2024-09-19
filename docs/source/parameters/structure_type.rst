.. _structure_type_parameters:

Structure type configuring
==========================

.. flat-table:: Parameters for structure type configuring
    :widths: 5 5 3 15 72
    :header-rows: 1
    :class: tight-table

    * - Parameter
      - Possible values
      - Default value
      - Where can be used
      - Description

    * - document_type
      - other, law, tz, diploma, article, fintoc
      - other
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.structure_extractors.StructureExtractorComposition.extract`
      - Type of the document structure according to specific domain.
        If you use default manager config for :class:`~dedoc.DedocManager`, then the following options are available:

            * **other** -- structure for document of any domain (:ref:`other_structure`).
              In this case, :class:`~dedoc.structure_extractors.DefaultStructureExtractor` is used.
            * **law** -- Russian laws (:ref:`law_structure`).
              In this case, :class:`~dedoc.structure_extractors.ClassifyingLawStructureExtractor` is used.
            * **tz** -- Russian technical specifications (:ref:`tz_structure`).
              In this case, :class:`~dedoc.structure_extractors.TzStructureExtractor` is used.
            * **diploma** -- Russian thesis (:ref:`diploma_structure`).
              In this case, :class:`~dedoc.structure_extractors.DiplomaStructureExtractor` is used.
            * **article**  -- scientific article (:ref:`article_structure`).
              In this case, :class:`~dedoc.readers.ArticleReader` and :class:`~dedoc.structure_extractors.ArticleStructureExtractor` are used.
            * **fintoc** -- English, French and Spanish financial prospects (:ref:`fintoc_structure`).
              In this case, :class:`~dedoc.structure_extractors.FintocStructureExtractor` is used.

        If you use your custom configuration, look to the documentation of :class:`~dedoc.structure_extractors.StructureExtractorComposition`

    * - patterns
      - list of patterns based on :class:`~dedoc.structure_extractors.patterns.abstract_pattern.AbstractPattern`,
        or list of patterns dicts, or list of dictionaries converted to string
      - None
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.structure_extractors.StructureExtractorComposition.extract`
        * :meth:`dedoc.structure_extractors.DefaultStructureExtractor.extract`
      - This parameter is used only by :class:`~dedoc.structure_extractors.DefaultStructureExtractor` (``document_type="other"``).
        Configuration of default document structure, please see :ref:`using_patterns` for more details.

    * - structure_type
      - tree, linear
      - tree
      - * :meth:`dedoc.DedocManager.parse`
        * :meth:`dedoc.structure_constructors.StructureConstructorComposition.construct`
      - The type of output document representation.
        If you use default manager config for :class:`~dedoc.DedocManager`, then the following options are available:

            * **tree** -- the document is represented as a hierarchical structure where nodes are document lines/paragraphs
              and child nodes have greater hierarchy level then parents according to the level found by structure extractor.
              In this case, :class:`~dedoc.structure_constructors.TreeConstructor` is used to construct structure.

            * **linear** -- the document is represented as a tree where the root is empty node,
              and all document lines are children of the root.
              In this case, :class:`~dedoc.structure_constructors.LinearConstructor` is used to construct structure.

        If you use your custom configuration, look to the documentation of :class:`~dedoc.structure_constructors.StructureConstructorComposition`
