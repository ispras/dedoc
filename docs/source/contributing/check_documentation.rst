.. _check_documentation:

Check documentation
-------------------

1. To build automatic documentation, it is recommended to install the following dependencies:

    .. code-block:: bash

         pip install .[docs]

2. Documentation files should be located in the `docs/ <https://github.com/ispras/dedoc/blob/master/docs>`_ directory,
   which must contain the `docs/source/conf.py <https://github.com/ispras/dedoc/blob/master/docs/source/conf.py>`_ (build settings)
   and `docs/source/index.rst <https://github.com/ispras/dedoc/blob/master/docs/source/index.rst>`_ (documentation main page) files.

3. Build documentation into HTML pages is done as follows:

    .. code-block:: bash

         python -m sphinx -T -E -W -b html -d docs/_build/doctrees -D language=en docs/source docs/_build
