.. _dedoc_api_schema:

API schema
==========

The output json format has a strict schema: serialized :class:`~dedoc.api.schema.ParsedDocument` is returned.
Json schema of the output is also available during dedoc application running on ``http://localhost:1231/docs``.

.. autoclass:: dedoc.api.schema.ParsedDocument

.. autoclass:: dedoc.api.schema.DocumentContent

.. autoclass:: dedoc.api.schema.DocumentMetadata

.. autoclass:: dedoc.api.schema.TreeNode

.. autoclass:: dedoc.api.schema.LineWithMeta

.. autoclass:: dedoc.api.schema.LineMetadata

.. autoclass:: dedoc.api.schema.Table

.. autoclass:: dedoc.api.schema.TableMetadata

.. autoclass:: dedoc.api.schema.CellWithMeta

.. autoclass:: dedoc.api.schema.Annotation
