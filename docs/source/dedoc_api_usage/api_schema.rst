.. _dedoc_api_schema:

API schema
==========

The output json format has a strict schema: serialized :class:`~dedoc.api.schema.ParsedDocument` is returned.
Json schema of the output is also available during dedoc application running on ``http://localhost:1231/docs``.

.. autoclass:: dedoc.api.schema.ParsedDocument

    .. autoattribute:: content
    .. autoattribute:: metadata
    .. autoattribute:: version
    .. autoattribute:: warnings
    .. autoattribute:: attachments

.. autoclass:: dedoc.api.schema.DocumentContent

    .. autoattribute:: structure
    .. autoattribute:: tables

.. autoclass:: dedoc.api.schema.DocumentMetadata

    .. autoattribute:: uid
    .. autoattribute:: file_name
    .. autoattribute:: temporary_file_name
    .. autoattribute:: size
    .. autoattribute:: modified_time
    .. autoattribute:: created_time
    .. autoattribute:: access_time
    .. autoattribute:: file_type
    .. autoattribute:: other_fields

.. autoclass:: dedoc.api.schema.TreeNode

    .. autoattribute:: node_id
    .. autoattribute:: text
    .. autoattribute:: annotations
    .. autoattribute:: metadata
    .. autoattribute:: subparagraphs

.. autoclass:: dedoc.api.schema.LineWithMeta

    .. autoattribute:: text
    .. autoattribute:: annotations

.. autoclass:: dedoc.api.schema.LineMetadata

    .. autoattribute:: paragraph_type
    .. autoattribute:: page_id
    .. autoattribute:: line_id
    .. autoattribute:: other_fields

.. autoclass:: dedoc.api.schema.Table

    .. autoattribute:: cells
    .. autoattribute:: metadata

.. autoclass:: dedoc.api.schema.TableMetadata

    .. autoattribute:: page_id
    .. autoattribute:: uid
    .. autoattribute:: rotated_angle
    .. autoattribute:: title

.. autoclass:: dedoc.api.schema.CellWithMeta

    .. autoattribute:: lines
    .. autoattribute:: rowspan
    .. autoattribute:: colspan
    .. autoattribute:: invisible

.. autoclass:: dedoc.api.schema.Annotation

    .. autoattribute:: start
    .. autoattribute:: end
    .. autoattribute:: name
    .. autoattribute:: value
