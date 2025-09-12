.. _using_precommit:

Using Pre-commit
----------------

In addition to running the style check yourself, it is possible to configure a `precommit-hook <https://pre-commit.com>`_,
which will run the style check before committing (`git commit`). The `pre-commit` is configured in
the `.pre-commit-config.yaml <https://github.com/ispras/dedoc/blob/master/.pre-commit-config.yaml>`_ configuration file.

1. You will need to install the dependency `pre-commit` and set up the hook:

    .. code-block:: bash

        pip3 install pre-commit
        pre-commit install

2. Check the hook (or do `git commit`):

    .. code-block:: bash

        pre-commit run --all

.. seealso::
    If you want to commit without checking the tests, you need to add the option `--no-verify`

    .. code-block:: bash

        git commit -m "your message" --no-verify
