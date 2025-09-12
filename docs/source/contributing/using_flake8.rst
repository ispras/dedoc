.. _using_flake8:

Using Flake8 (Linting)
----------------------

To check Python code for compliance with all style standards, you can use the automatic checking tool `flake8`.
Flake8 checks code according to configuration file `.flake8 <https://github.com/ispras/dedoc/blob/master/.flake8>`_.

    1. Install all requirements for `flake8` package:

    .. code-block:: bash

         pip3 install .[lint]

    2. Run `flake8` package:

    .. code-block:: bash

         flake8 .
