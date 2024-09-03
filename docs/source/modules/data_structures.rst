.. _dedoc_data_structures:

dedoc.data_structures
=====================

Main classes defining a document
--------------------------------

.. autoclass:: dedoc.data_structures.UnstructuredDocument

.. autoclass:: dedoc.data_structures.ParsedDocument
    :show-inheritance:
    :members:

.. autoclass:: dedoc.data_structures.DocumentContent
    :show-inheritance:
    :members:

.. autoclass:: dedoc.data_structures.DocumentMetadata
    :show-inheritance:
    :members:

.. autoclass:: dedoc.data_structures.TreeNode
    :show-inheritance:
    :members:

.. autoclass:: dedoc.data_structures.LineWithMeta
    :show-inheritance:
    :special-members: __init__, __lt__
    :members:
    :undoc-members: set_line, set_metadata

    .. automethod:: __len__
    .. automethod:: __getitem__
    .. automethod:: __add__

.. autoclass:: dedoc.data_structures.LineMetadata
    :show-inheritance:
    :members:

.. autoclass:: dedoc.data_structures.HierarchyLevel
    :special-members: __eq__, __lt__
    :members:

.. autoclass:: dedoc.data_structures.Table
    :show-inheritance:
    :members:

.. autoclass:: dedoc.data_structures.TableMetadata
    :show-inheritance:
    :members:

.. autoclass:: dedoc.data_structures.CellWithMeta
    :show-inheritance:
    :members:


Helper classes
--------------

.. autoclass:: dedoc.data_structures.Serializable
    :members:

.. autoclass:: dedocutils.data_structures.BBox
     :special-members: __init__
     :exclude-members: to_dict
     :members:

     .. autoattribute:: x_top_left
     .. autoattribute:: y_top_left
     .. autoattribute:: x_bottom_right
     .. autoattribute:: y_bottom_right
     .. autoattribute:: width
     .. autoattribute:: height

.. autoclass:: dedoc.data_structures.AttachedFile
    :members:

.. _annotations:

Annotations of the text lines
-----------------------------

.. autoclass:: dedoc.data_structures.Annotation
    :show-inheritance:

Concrete annotations
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: dedoc.data_structures.AttachAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.TableAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.LinkedTextAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.ReferenceAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.BBoxAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.AlignmentAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.IndentationAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.SpacingAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.BoldAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.ItalicAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.UnderlinedAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.StrikeAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.SubscriptAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.SuperscriptAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.ColorAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.SizeAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.StyleAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name

.. autoclass:: dedoc.data_structures.ConfidenceAnnotation
    :show-inheritance:
    :special-members: __init__

    .. autoattribute:: name
