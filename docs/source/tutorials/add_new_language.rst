.. _add_language:

Adding support for a new language to Dedoc
==========================================

By default, dedoc supports handling Russian and English languages.
The most important part of language support is OCR (for images, PDF).
If you don't need parse images and PDF files, you don't need to do anything.

To parse images with a new language, additional Tesseract language packages should be installed.
The list of languages supported by Tesseract are enlisted `here <https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html>`_ (see **Languages** section).

.. seealso::
    The instruction with Tesseract installation can be found :ref:`here <install_tesseract>`.

.. warning::
    Not all languages are fully supported by dedoc even with installed Tesseract packages. The more detailed information will appear soon.


Add new language in docker
--------------------------

Similar to the :ref:`installation tutorial <dedoc_installation>`, beforehand one should clone the dedoc repository and go to the `dedoc` directory:

.. code-block:: bash

    git clone https://github.com/ispras/dedoc
    cd dedoc

Then one should decide, which languages should be supported, and look for them in the
`list of supported languages <https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html>`_ (**Languages** section).
For each language, ``LangCode`` is used to configure it.
For example, if we need to add French and Spanish, we should use ``fra`` and ``spa`` language codes.


Using docker build
******************

For passing the list of languages while building docker image, the ``LANGUAGES`` argument is used.
Languages should be enlisted in string and separated by spaces.
For example, for adding French and Spanish we should use the following command:

.. code-block:: bash

    docker build --build-arg LANGUAGES="fra spa" .

One may also choose a tag for an image, e.g. ``dedocproject/dedoc_multilang:latest``, and run the container:

.. code-block:: bash

    docker build -t dedocproject/dedoc_multilang:latest --build-arg LANGUAGES="fra spa" .
    docker run -p 1231:1231 --rm dedocproject/dedoc_multilang python3 /dedoc_root/dedoc/main.py


Using docker-compose
********************

For passing the list of languages while building docker image, the ``LANGUAGES`` argument is used in the ``docker-compose.yml`` file.
Languages should be enlisted in string and separated by spaces.
For example, for adding French and Spanish we should add the following lines to the ``docker-compose.yml`` file:

.. code-block:: yaml
    :emphasize-lines: 8-9

    version: '2.4'

    services:
      dedoc:
        mem_limit: 16G
        build:
          context: .
          args:
            LANGUAGES: "fra spa"
        restart: always
        tty: true
        ports:
          - 1231:1231
        environment:
          DOCREADER_PORT: 1231
          GROBID_HOST: "grobid"
          GROBID_PORT: 8070

Then, the service can be run with the following command:

.. code-block:: bash

    docker-compose up --build


Add new language locally
------------------------

Suppose Tesseract OCR 5 is already installed on the computer (or see :ref:`instruction <install_tesseract>`).
For each language, the following command should be executed (``lang`` is one language code):

.. code-block:: bash

    apt install -y tesseract-ocr-$lang

For example, for adding French and Spanish we should use the following commands:

.. code-block:: bash

    apt install -y tesseract-ocr-fra
    apt install -y tesseract-ocr-spa

Or we can install all packages with one command using ``LANGUAGES`` variable:

.. code-block:: bash

    export LANGUAGES="fra spa"
    for lang in $LANGUAGES; do apt install -y tesseract-ocr-$lang; done

Then the dedoc library can be used with new languages or dedoc API can be run locally (see :ref:`instruction <install_library_via_pip>`) for more details.
