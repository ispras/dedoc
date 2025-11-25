.. _check_documentation:

Check documentation
-------------------

1. To build automatic documentation, it is recommended to install the following dependencies:

    .. code-block:: bash

         pip install .[docs]

2. Documentation files should be located in the `docs/ <https://github.com/ispras/dedoc/blob/master/docs>`_ directory.
   Build documentation into HTML pages is done as follows:

    .. code-block:: bash

         python -m sphinx -T -E -W -b html -d docs/_build/doctrees -D language=en docs/source docs/_build

3. After building, the documentation can be checked locally, the main built page ``docs/_build/index.html`` can be opened in the browser.
