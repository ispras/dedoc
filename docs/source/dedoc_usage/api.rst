Using dedoc via API
===================

Dedoc can be used as a web application that runs on the `localhost:1231`.
It's possible to change the port via `config.py` file (if you clone the repository and run dedoc as a docker container).

There are two ways to install and run dedoc as a web application that are described below.


Run dedoc in a docker container
-------------------------------

You should have `git <https://git-scm.com>`_ and `docker <https://www.docker.com>`_ installed for running dedoc by this method.
This method is more flexible because it doesn't depend on the operating system and other user's limitations,
still, the docker application should be installed and configured properly.

1. Clone the repository

  .. code-block:: bash

    git clone https://github.com/ispras/dedoc

2. Go to the `dedoc` directory

  .. code-block:: bash

    cd dedoc


3. Build the image and run the application

  .. code-block:: bash

    docker-compose up --build


Run dedoc as a PyPI library
---------------------------

If you don't want to use docker for running the application,
it's possible to run dedoc locally.
However, it isn't suitable for any operating system (Ubuntu 20+ is recommended) and
there may be not enough machine's resources for its work.
You should have `python` (python3.8+ is recommended) and `pip` installed.

1. Install the dedoc library via pip

  .. code-block:: bash

    pip install dedoc


2. Run the application

  .. code-block:: bash

    dedoc -m main


Application usage
-----------------

Once you run the dedoc application, you can go to `localhost:1231` and
look to the main page with the information about dedoc.
From this page you can go to the upload page and manually choose settings for the file parsing.
Then you can get the result after pressing the `upload` button.

If you want to use the application in your program,
you can send requests e.g. using `requests <https://pypi.org/project/requests>`_ python library.
Post-requests should be sent to `http://localhost:1231/upload`.

  .. code-block:: python

    data = {
        "pdf_with_text_layer": "auto_tabby",
        "document_type": "diploma",
        "language": "rus",
        "need_pdf_table_analysis": "true",
        "need_header_footer_analysis": "false",
        "is_one_column_document": "true",
        "return_format": 'html'
    }
    with open(filename, 'rb') as file:
        files = {'file': (filename, file)}
        r = requests.post("http://localhost:1231/upload", files=files, data=data)
        result = r.content.decode('utf-8')

The `data` dictionary in the example contains some parameters to parse the given file.
They are described in the section :ref:`api_parameters`.

.. _api_parameters:

Api parameters description
--------------------------

.. _table_parameters:

.. list-table:: Api parameters for files parsing via dedoc
    :widths: 15 15 10 60
    :header-rows: 1
    :class: tight-table

    * - Parameter
      - Values
      - Default value
      - Description

    * - document_type
      - other, law, tz, diploma
      - other
      - Type of the document structure according to specific domain.

        The following parameters are available:

            * other -- structure for document of any domain (:ref:`other_structure`);
            * law -- russian laws (:ref:`law_structure`);
            * tz -- russian technical specifications (:ref:`tz_structure`);
            * diploma -- russian thesis (:ref:`diploma_structure`).

        This type is used for choosing a specific structure extractor after document reading.

    * - structure_type
      - tree, linear
      - tree
      - The type of output document representation:

            * tree -- the document is represented as a hierarchical structure where nodes are document lines/paragraphs and child nodes have greater hierarchy level then parents according to the level found by structure constructor;

            * linear -- the document is represented as a tree where the root is empty node, and all document lines are children of the root.

        This type is used for choosing a specific structure constructor after document structure extraction.

    * - return_format
      - json, pretty_json, html, tree
      - json
      -

    * - with_attachments
      - true, false
      - false
      -

    * - need_content_analysis
      - true, false
      - false
      -

    * - recursion_deep_attachments
      - integer value >= 0
      - 10
      -

    * - return_base64
      - true, false
      - false
      -

    * - insert_table
      - true, false
      - false
      -

    * - need_pdf_table_analysis
      - true, false
      - false
      -

    * - table_type
      -
      -
      -

    * - orient_analysis_cells
      - true, false
      - false
      -

    * - orient_cell_angle
      - 90, 270
      - 90
      -

    * - pdf_with_text_layer
      - true, false, tabby, auto, auto_tabby
      - auto_tabby
      -

    * - language
      - rus, eng, rus+eng
      - rus+eng
      -

    * - pages
      - :, start:, :end, start:end
      - :
      -

    * - is_one_column_document
      - true, false, auto
      - auto
      -

    * - document_orientation
      - auto, no_change
      - auto
      -

    * - need_header_footer_analysis
      - true, false
      - false
      -

    * - need_binarization
      - true, false
      - false
      -

    * - delimiter
      -
      -
      -

    * - encoding
      -
      -
      -

    * - html_fields
      -
      -
      -

    * - handle_invisible_table
      - true, false
      - false
      -
