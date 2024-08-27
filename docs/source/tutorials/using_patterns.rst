.. _using_patterns:

Configure structure extraction using patterns
=============================================

It is possible to configure structure type in Dedoc: option ``document_type`` in the ``parameters`` dictionary
(:ref:`api_parameters`, :ref:`structure_type_parameters`).
The default structure type (when ``document_type="other"``, see :ref:`other_structure`) allows to get a basic document structure which is fixed.
If you want to change this structure, e.g. names of line types (nodes) or their levels in the tree hierarchy, you can use structure patterns.

Use patterns in Dedoc library
-----------------------------

If you use Dedoc as a library, you can use existing pattern classes :ref:`dedoc_structure_extractors_patterns`
or implement your own custom pattern based on :class:`~dedoc.structure_extractors.patterns.abstract_pattern.AbstractPattern`.

Let's see some examples. First of all, we enlist all required imports:

.. literalinclude:: ../_static/code_examples/dedoc_using_patterns_tutorial.py
    :language: python
    :lines: 1-13

Using information from readers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assume we need to parse file :download:`with_tags.docx <../_static/code_examples/test_dir/with_tags.docx>`, which looks like follows:

.. _docx_with_tags_image:

.. figure:: ../_static/code_examples/test_dir/with_tags.png
    :width: 400

    DOCX document example



.. literalinclude:: ../_static/code_examples/dedoc_using_patterns_tutorial.py
    :language: python
    :lines: 18-28

.. literalinclude:: ../_static/code_examples/dedoc_using_patterns_tutorial.py
    :language: python
    :lines: 30-44


Using regular expressions
~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../_static/code_examples/dedoc_using_patterns_tutorial.py
    :language: python
    :lines: 47-51


.. literalinclude:: ../_static/code_examples/dedoc_using_patterns_tutorial.py
    :language: python
    :lines: 54-62


Practical example: get structured PDF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assume we need to parse file :download:`law.pdf <../_static/code_examples/test_dir/law.pdf>`, which looks like follows:

.. _pdf_law_image:

.. figure:: ../_static/code_examples/test_dir/law.png
    :width: 400

    PDF document example


.. literalinclude:: ../_static/code_examples/dedoc_using_patterns_tutorial.py
    :language: python
    :lines: 66-74


.. literalinclude:: ../_static/code_examples/dedoc_using_patterns_tutorial.py
    :language: python
    :lines: 76-83


.. literalinclude:: ../_static/code_examples/dedoc_using_patterns_tutorial.py
    :language: python
    :lines: 86-88


.. literalinclude:: ../_static/code_examples/dedoc_using_patterns_tutorial.py
    :language: python
    :lines: 91-110


.. literalinclude:: ../_static/code_examples/dedoc_using_patterns_tutorial.py
    :language: python
    :lines: 113-122

Conclusions
~~~~~~~~~~~



Use patterns in Dedoc API
-------------------------

.. code-block:: python

    import requests

    file_path = "test_dir/law.pdf"
    file_name = "law.pdf"
    patterns = [
        {"name": "regexp", "regexp": "^part\s+\d+$", "line_type": "part", "level_1": 1, "level_2": 1, "can_be_multiline": "false"},
        {"name": "regexp", "regexp": "^chapter\s+\d+$", "line_type": "chapter", "level_1": 1, "level_2": 2, "can_be_multiline": "false"},
        {"name": "dotted_list", "line_type": "point", "level_1": 2, "can_be_multiline": "false"},
        {"name": "regexp", "regexp": "^\(\d+\)\s", "line_type": "item", "level_1": 3, "level_2": 1, "can_be_multiline": "false"},
        {"name": "regexp", "regexp": "^\(\w\)\s", "line_type": "sub_item", "level_1": 3, "level_2": 2, "can_be_multiline": "false"}
    ]
    parameters = {"patterns": str(patterns)}

    with open(file_path, "rb") as file:
        files = {"file": (file_name, file)}
        r = requests.post("http://localhost:1231/upload", files=files, data=parameters)
