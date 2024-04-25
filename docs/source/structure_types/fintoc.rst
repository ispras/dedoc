.. _fintoc_structure:

FinTOC structure type
=====================

This structure type is used for analysis of English, French and Spanish financial prospects in PDF format
according to the `FinTOC 2022 Shared task <https://wp.lancs.ac.uk/cfie/fintoc2022/>`_.
You can see the :download:`example  <../_static/structure_examples/fintoc.pdf>` of the document of this structure type.

According to the FinTOC 2022 Shared task, there were two subtasks to be solved:

    * **Title detection (TD)** -- selection from all lines of the document only those that should be included in the table of contents.
    * **Table of contents (TOC) generation** -- identification nesting depths of selected titles.

Based on these tasks, we propose the FinTOC structure type with **header** and **raw_text** node types.
The detailed description of each node type:

    * **header** -- title nodes (from the title detection task). Titles can be nested, so their depth is determined according to the
      TOC generation task. **header** nodes can have other **header** nodes or **raw_text** nodes as children nodes.
    * **raw_text** -- non-title nodes. Unlike forming the result of TOC generation task,
      we add non-title lines in the result document tree. **raw_text** node refers to a simple document line.
      It has the least importance in the document tree hierarchy, so it is situated in the leaves of the tree.
      It is nested to the node corresponding the previous line with more important type.


The documents for the FinTOC 2022 Shared task are PDF files with a textual layer,
so it is recommended to use :class:`~dedoc.readers.PdfTxtlayerReader` or :class:`~dedoc.readers.PdfTabbyReader` for their parsing
(``pdf_with_text_layer="true"`` or ``pdf_with_text_layer="tabby"`` in the :ref:`API parameters <table_parameters>`).

.. note::

    During structure extraction step, we use classifiers trained on data extracted by :class:`~dedoc.readers.PdfTxtlayerReader` --
    usage of :class:`~dedoc.readers.PdfTxtlayerReader` or ``pdf_with_text_layer="true"`` is more preferable.

The training dataset contains English, French, and Spanish documents, so three language options are available ("en", "fr", "sp").
It is possible to set document's language using ``language`` option in parameters (e.g., ``parameters={"language": "en"}``).

To obtain FinTOC structure, we use our method described in `our article <https://aclanthology.org/2022.fnp-1.13.pdf>`_
(winners of FinTOC 2022 Shared task!).
The results of our method for different languages and readers are given in the :ref:`table below <fintoc_results_table>`
(they slightly changed since the competition finished).
The name of each experiment consists of the reader type ("tabby" -- :class:`~dedoc.readers.PdfTabbyReader`,
"txt_layer" -- :class:`~dedoc.readers.PdfTxtlayerReader`)
and the document's language ("en" -- English, "fr" -- French, "sp" -- Spanish).
As in the FinTOC 2022 Shared task, we use two metrics for results evaluation (metrics from the `article <https://aclanthology.org/2022.fnp-1.12.pdf>`_):
**TD** -- F1 measure for the title detection task, **TOC** -- harmonic mean of Inex F1 score and Inex level accuracy for the TOC generation task.

.. _fintoc_results_table:

.. list-table:: The results from 3-fold cross-validation on the FinTOC 2022 training dataset
   :widths: 20 10 10 10 10 10 10 10 10
   :header-rows: 1

   * - Name
     - TD 0
     - TD 1
     - TD 2
     - TD mean
     - TOC 0
     - TOC 1
     - TOC 2
     - TOC mean
   * - **en_tabby**
     - 0.811
     - 0.833
     - 0.864
     - **0.836**
     - 56.5
     - 58.0
     - 64.9
     - **59.8**
   * - **en_txt_layer**
     - 0.821
     - 0.853
     - 0.833
     - **0.836**
     - 57.8
     - 62.1
     - 57.8
     - **59.2**
   * - **fr_tabby**
     - 0.753
     - 0.744
     - 0.782
     - **0.759**
     - 51.2
     - 47.9
     - 51.5
     - **50.2**
   * - **fr_txt_layer**
     - 0.740
     - 0.794
     - 0.766
     - **0.767**
     - 45.6
     - 52.2
     - 50.1
     - **49.3**
   * - **sp_tabby**
     - 0.606
     - 0.622
     - 0.599
     - **0.609**
     - 37.1
     - 43.6
     - 43.4
     - **41.3**
   * - **sp_txt_layer**
     - 0.629
     - 0.667
     - 0.446
     - **0.581**
     - 46.4
     - 48.8
     - 30.7
     - **41.9**

.. seealso::

    Please see our article `ISPRAS@FinTOC-2022 shared task: Two-stage TOC generation model <https://aclanthology.org/2022.fnp-1.13.pdf>`_
    to get more information about the FinTOC 2022 Shared task and our method of solving it.
    We will be grateful, if you cite our work (see citation in BibTeX format below).

.. code-block:: RST

    @inproceedings{bogatenkova-etal-2022-ispras,
        title = "{ISPRAS}@{F}in{TOC}-2022 Shared Task: Two-stage {TOC} Generation Model",
        author = "Bogatenkova, Anastasiia  and
          Belyaeva, Oksana Vladimirovna  and
          Perminov, Andrew Igorevich  and
          Kozlov, Ilya Sergeevich",
        editor = "El-Haj, Mahmoud  and
          Rayson, Paul  and
          Zmandar, Nadhem",
        booktitle = "Proceedings of the 4th Financial Narrative Processing Workshop @LREC2022",
        month = jun,
        year = "2022",
        address = "Marseille, France",
        publisher = "European Language Resources Association",
        url = "https://aclanthology.org/2022.fnp-1.13",
        pages = "89--94"
    }
