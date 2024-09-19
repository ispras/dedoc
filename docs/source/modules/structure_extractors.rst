.. _dedoc_structure_extractors:

dedoc.structure_extractors
==========================

.. autoclass:: dedoc.structure_extractors.AbstractStructureExtractor
    :special-members: __init__
    :members:

.. autoclass:: dedoc.structure_extractors.StructureExtractorComposition
    :show-inheritance:
    :special-members: __init__
    :members:

.. autoclass:: dedoc.structure_extractors.DefaultStructureExtractor
    :show-inheritance:
    :members:

    .. autoattribute:: document_type

.. autoclass:: dedoc.structure_extractors.AbstractLawStructureExtractor
    :show-inheritance:
    :members:

.. autoclass:: dedoc.structure_extractors.ClassifyingLawStructureExtractor
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: document_type

.. autoclass:: dedoc.structure_extractors.LawStructureExtractor
    :show-inheritance:
    :members:

    .. autoattribute:: document_type

.. autoclass:: dedoc.structure_extractors.FoivLawStructureExtractor
    :show-inheritance:
    :members:

    .. autoattribute:: document_type

.. autoclass:: dedoc.structure_extractors.DiplomaStructureExtractor
    :show-inheritance:
    :members:

    .. autoattribute:: document_type

.. autoclass:: dedoc.structure_extractors.TzStructureExtractor
    :show-inheritance:
    :members:

    .. autoattribute:: document_type

.. autoclass:: dedoc.structure_extractors.ArticleStructureExtractor
    :show-inheritance:
    :members:

    .. autoattribute:: document_type

.. autoclass:: dedoc.structure_extractors.FintocStructureExtractor
    :show-inheritance:
    :members:

    .. autoattribute:: document_type


.. _dedoc_structure_extractors_patterns:

Patterns for :class:`~dedoc.structure_extractors.DefaultStructureExtractor`
---------------------------------------------------------------------------

Structure patterns are used for a more flexible configuring of lines types and levels during structure extraction step.
They are useful only for :class:`~dedoc.structure_extractors.DefaultStructureExtractor` (in API when "document_type"="other").
Please see :ref:`using_patterns` to get examples of patterns usage.


.. autoclass:: dedoc.structure_extractors.patterns.abstract_pattern.AbstractPattern
    :special-members: __init__
    :members:

    .. autoattribute:: _name

.. autoclass:: dedoc.structure_extractors.patterns.pattern_composition.PatternComposition
    :special-members: __init__
    :members:

.. autoclass:: dedoc.structure_extractors.patterns.RegexpPattern
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: _name

.. autoclass:: dedoc.structure_extractors.patterns.StartWordPattern
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: _name

.. autoclass:: dedoc.structure_extractors.patterns.TagPattern
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: _name

.. autoclass:: dedoc.structure_extractors.patterns.BracketListPattern
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: _name

.. autoclass:: dedoc.structure_extractors.patterns.BracketRomanListPattern
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: _name

.. autoclass:: dedoc.structure_extractors.patterns.BulletListPattern
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: _name

.. autoclass:: dedoc.structure_extractors.patterns.DottedListPattern
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: _name

.. autoclass:: dedoc.structure_extractors.patterns.LetterListPattern
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: _name

.. autoclass:: dedoc.structure_extractors.patterns.RomanListPattern
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: _name

.. autoclass:: dedoc.structure_extractors.patterns.TagHeaderPattern
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: _name

.. autoclass:: dedoc.structure_extractors.patterns.TagListPattern
    :show-inheritance:
    :special-members: __init__
    :members:

    .. autoattribute:: _name
