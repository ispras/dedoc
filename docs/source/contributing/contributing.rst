.. _contributing:

Support and Contributing
========================

Support
-------
If you are stuck with a problem using Dedoc, please use our `Issues <https://github.com/ispras/dedoc/issues>`_ (recommended)
or `Dedoc Chat <https://t.me/dedoc_chat>`_. The developers are willing to help.

You can save time by following this procedure when reporting a problem:

    * Try to solve the problem on your own first. Read the documentation, including using the search feature, index and reference documentation.

    * Search the issue archives to see if someone else already had the same problem.

    * Before writing, try to create a minimal example that reproduces the problem (with the api parameters and files you used).
      You’ll get the fastest response if you can send just a handful of lines of code that show what isn’t working.


Contributing Rules
------------------

    * To add new features to the project repository yourself, you should follow
      the `general contributing rules of github <https://github.com/firstcontributions/first-contributions>`_.

      .. note::
          In your Pull Request, set `develop` as the target branch.

    * We recommend using `Pycharm IDE` and `virtualenv` package for development.

    * It is strongly recommended to use in development those versions of libraries that are already used in the project.
      Thus, it is necessary to avoid using an excessive number of libraries with the same functionality in the project.
      This leads to the growth of the dedoc library image.

    * We strongly recommend using the already used ML library `torch` in development. For example,
      using `tensorflow` library instead of `torch` is justified only in case of extreme necessity.

    * If you add new functionality to dedoc, be sure to add python `unittest` to test the added functionality
      (you can add api tests in `tests/api_tests <https://github.com/ispras/dedoc/blob/master/tests/api_tests>`_
      or unit tests in `tests/unit_tests <https://github.com/ispras/dedoc/blob/master/tests/unit_tests>`_).
      These tests are run automatically in the Continuous Integration pipeline.
      To run tests locally, you can use docker as described in the `README <https://github.com/ispras/dedoc/blob/master/README.md#4-run-container-with-tests>`_.

    * Before each commit, check the code style using the automatic checker using the `flake8` library.
      Instructions for using flake8 are provided in :ref:`using_flake8`.

    * We recommend setting up pre-commit for convenience and speeding up development according to the instructions :ref:`using_precommit` .
      This will run a style check of the changed code before each commit.

    * In case of any change in the online documentation of the project (for example, when adding a new api parameter),
      be sure to check locally that the changed documentation is successfully built and looks as expected.
      Building online documentation using `sphinx` is described here :ref:`check_documentation`.

.. toctree::
   :maxdepth: 1
   :hidden:

   using_flake8
   using_precommit
   check_documentation
