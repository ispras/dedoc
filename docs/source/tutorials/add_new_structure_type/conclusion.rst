.. _add_structure_type_conclusion:

Adding implemented extractor to the main pipeline
=================================================

.. seealso::
    Before doing this step, implementation of a structure extractor should be done.
    :ref:`Here <add_structure_type>` there is an instruction how to add a new structure extractor.

All implemented document handlers are linked in `dedoc/manager_config.py <https://github.com/ispras/dedoc/blob/master/dedoc/manager_config.py>`_
You may edit this file or create your own ``manager_config`` with dedoc handlers you need and
your custom handlers directly in your code.

Let's consider an example.
In the :ref:`tutorial<add_structure_type_post_processing>` about structure extractor implementation,
we implemented the class ``ArticleStructureExtractor`` for handling English scientific articles in PDF format.
Example of a manager config with PDF handlers and the implemented structure extractor:

.. literalinclude:: ../../_static/code_examples/dedoc_add_new_structure_type_tutorial.py
    :language: python

After initialization of ``manager``, it can be used for document parsing,
``document_type`` parameter is equal to the ``ArticleStructureExtractor.document_type`` attribute.

.. code-block:: python

    result = manager.parse(file_path=file_path, parameters={"document_type": "article"})
