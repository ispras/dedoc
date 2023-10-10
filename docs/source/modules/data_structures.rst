.. _dedoc_data_structures:

dedoc.data_structures
=====================

Main classes defining a document
--------------------------------

.. autoclass:: dedoc.data_structures.UnstructuredDocument
    :special-members: __init__

.. autoclass:: dedoc.data_structures.ParsedDocument
    :show-inheritance:
    :special-members: __init__
    :exclude-members: to_dict
    :members:

.. autoclass:: dedoc.data_structures.DocumentContent
    :show-inheritance:
    :special-members: __init__
    :exclude-members: to_dict
    :members:

.. autoclass:: dedoc.data_structures.DocumentMetadata
    :show-inheritance:
    :special-members: __init__
    :exclude-members: to_dict
    :members:

.. autoclass:: dedoc.data_structures.TreeNode
    :show-inheritance:
    :special-members: __init__
    :exclude-members: to_dict
    :members:

.. autoclass:: dedoc.data_structures.LineWithMeta
    :show-inheritance:
    :special-members: __init__
    :exclude-members: to_dict, get_api_dict
    :members:
    :undoc-members: line, uid, metadata, annotations

    .. automethod:: __len__
    .. automethod:: __getitem__
    .. automethod:: __add__

.. autoclass:: dedoc.data_structures.LineMetadata
    :show-inheritance:
    :special-members: __init__
    :exclude-members: to_dict
    :members:

.. autoclass:: dedoc.data_structures.HierarchyLevel
    :special-members: __init__, __eq__, __lt__
    :exclude-members: to_dict
    :members:

.. autoclass:: dedoc.data_structures.Table
    :show-inheritance:
    :special-members: __init__
    :exclude-members: to_dict
    :members:

.. autoclass:: dedoc.data_structures.TableMetadata
    :show-inheritance:
    :special-members: __init__
    :exclude-members: to_dict
    :members:

.. autoclass:: dedoc.data_structures.CellWithMeta
    :show-inheritance:
    :special-members: __init__
    :exclude-members: to_dict
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
    :special-members: __init__
    :members:

Annotations of the text lines
-----------------------------

.. autoclass:: dedoc.data_structures.Annotation
    :show-inheritance:
    :special-members: __init__

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
