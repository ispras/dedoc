.. _article_structure:

Article structure type (GROBID)
===============================

This structure type is used for scientific article analysis using `GROBID <https://github.com/kermitt2/grobid>`_ system.

    .. note::

        In case you use dedoc as a library or a separate Docker image (without docker-compose).
        If you want to use this structure extractor, you should run GROBID service via Docker (or see `grobid running instruction <https://grobid.readthedocs.io/en/latest/Run-Grobid/>`_).

        .. code-block:: shell

            docker run --rm --init --ulimit core=0 -p 8070:8070 lfoppiano/grobid:0.8.0

We analyze the recognition results from GROBID. The following types of objects are included in the resulting tree:

    * article's title;
    * authors with their affiliations to organizations and emails;
    * article's sections headers (for example `Abstract`, `Introduction`, .., `Conclusion` etc);
    * tables and their content;
    * bibliography;
    * references on tables and bibliography items.

There are the following line types in the article structure type:

    * ``root``;
    * ``author`` (includes ``author_first_name``, ``author_surname``, ``email``);
    * ``keywords`` (includes ``keyword``);
    * ``author_affiliation`` (includes ``org_name``, ``address``);
    * ``abstract``;
    * ``section``;
    * ``bibliography``;
    * ``bibliography_item`` (includes [``title`` | ``title_journal`` | ``title_series`` | ``title_conference_proceedings``], ``author``, ``biblScope_volume``, ``biblScope_pages``, ``DOI``, ``publisher``, ``date``);
    * ``raw_text``.


You can see the :download:`example  <../_static/structure_examples/article.pdf>` of the document of this structure type.
This page provides examples of this article analysis.

Below is a description of nodes in the output tree:

    * **root**: node containing the text of the article title.

        There is only one root node in any document.
        It is obligatory for any document of article type.
        All other document lines are children of the root node.
        We take the title's text from GROBID's TEI-XML path tag <title>:

        .. code-block:: XML

            <fileDesc>
                <titleStmt>
                    <title> Title's text </title> // -> node.paragraph_type="root"
                </fileDesc>
            </titleStmt>

    * **author**: information about an author of the article.

        ``author`` nodes are children of the node ``root``. This type of node has subnodes.

        * ``author_first_name`` - <persname> tag in GROBID's output. The node doesn't have children nodes.
        * ``author_surname`` - <surname> tag in GROBID's output. The node doesn't have children nodes.
        * ``email`` - author's email, <email> tag in GROBID's output. The node doesn't have children nodes.
        * ``author_affiliation`` - author affiliation description.


        GROBID's TEI-XML <author>'s name information

        .. code-block:: XML

            <author>    // -> node.paragraph_type="author"
            <persname>
                <forename type="first">Sonia</forename> // -> node.paragraph_type="author_first_name"
                <surname>Belaïd</surname>               // -> node.paragraph_type="author_surname"
                <email></email>                         // -> node.paragraph_type="email"
            </persname>
            ...
            </author>

    * **author_affiliation**: Author's affiliation description.

        ``author_affiliation`` nodes are children of the node ``author``.
        This type of node has subnodes.

        * ``org_name`` - organization description, <orgname> tag in GROBID's output. The node doesn't have children nodes.
        * ``address`` - organization address, <address> tag in GROBID's output. The node doesn't have children nodes.

        GROBID's TEI-XML tag <author><affiliation> information according the affiliation `description <https://grobid.readthedocs.io/en/latest/training/affiliation-address/>`_ :

        .. code-block:: XML

            <author>    // -> node.paragraph_type="author"
            ...
            <affiliation key="aff2">        // -> node.paragraph_type="author_affiliation"
                <orgName type="department">ICTEAM/ELEN/Crypto Group</orgName>       // -> node.paragraph_type="org_name"
                <orgName type="institution">Université catholique de Louvain</orgName>
                <address>
                    <country key="BE">Belgium</country>
                </address>
            </affiliation>

        The result of parsing of the second author of the article:

        ..  example of "node_id": "0.1"

        .. literalinclude:: ../_static/json_format_examples/article_example.json
            :language: json
            :lines: 115-182

    * **keywords** node (if exist) is a child  node of the node ``root``.

        ``keywords`` node contains ``keyword`` nodes as children. Each ``keyword`` node contains the text of one key word item.

    * **abstract** is the article's abstract section (<abstract> tag in GROBID's output).

    * **section**: nodes of article sections (for example "Introduction", "Conclusion", "V Experiments ..." etc.). This type of node has a subnode ``raw_text``.

        ``section`` nodes are children of a node ``root`` and may me nested (e.g., section "2.1. Datasets" is nested to the section "2. Related work").

    * **bibliography** is the article's bibliography list which contains only ``bibliography_item`` nodes.

    * **bibliography_item** is the article's bibliography item description.

        ``bibliography_item`` nodes are children of the node ``bibliography``.
        This type of node has subnodes.

        * ``title`` or ``title_journal`` or ``title_series`` or ``title_conference_proceedings``- name of the bibliography item. The node doesn't have children nodes.
        * ``author`` - bibliography author name, <address> tag in GROBID's output. The node doesn't have children nodes.
        * ``biblScope_volume`` - volume name, <biblScope unit="volume">4</biblScope> tag in GROBID's output. The node doesn't have children nodes.
        * ``biblScope_pages`` - volume name, <biblScope unit="page" from="471" to="488" /> tag in GROBID's output. The node doesn't have children nodes.
        * ``DOI`` - bibliography DOI name, <idno> tag in GROBID's output. The node doesn't have children nodes.
        * ``publisher`` - bibliography DOI name, <publisher> tag in GROBID's output. The node doesn't have children nodes.
        * ``date`` - publication date, <date> tag in GROBID's output. The node doesn't have children nodes.



        There is GROBID's TEI-XML <bibliography>'s item information description `here <https://grobid.readthedocs.io/en/latest/training/Bibliographical-references/>`_ .
        We parse GROBID's biblStruct and create a ``bibliography_item`` node. Example of GROBID's biblStruct:

        .. code-block:: XML

            <listBibl>
                <biblStruct xml:id="b0">
                    <analytic>
                        <title level="a" type="main">Leakage-resilient symmetric encryption via re-keying</title>
                        <author>
                            <persName><forename type="first">Michel</forename><surname>Abdalla</surname></persName>
                        </author>
                        <author>
                            <persName><forename type="first">Sonia</forename><surname>Belaïd</surname></persName>
                        </author>
                        <author>
                            <persName><forename type="first">Pierre-Alain</forename><surname>Fouque</surname></persName>
                        </author>
                    </analytic>
                    <monogr>
                        <title level="m">Bertoni and Coron</title>
                        <imprint>
                            <biblScope unit="volume">4</biblScope>
                            <biblScope unit="page" from="471" to="488" />
                        </imprint>
                    </monogr>
                </biblStruct>
                <biblStruct xml:id="b1">

        We set paragraph_type of the title according the tag level in GROBID (see `title level's description <https://grobid.readthedocs.io/en/latest/training/Bibliographical-references/>`_):

        * For ``<title><level="a">`` set the ``paragraph_type="title"`` for article title or chapter title (but not thesis, see below). Here "a" stands for analytics (a part of a monograph).
        * For ``<title><level="j">`` set the ``paragraph_type="title_journal"`` for journal title.
        * For ``<title><level="s">`` set the ``paragraph_type="title_series"`` for series title (e.g. "Lecture Notes in Computer Science").
        * For ``<title><level="m">`` set the ``paragraph_type="title_conference_proceedings"`` for non journal bibliographical item holding the cited article, e.g. conference proceedings title. Note if a book is cited, the title of the book is annotated with ``<title level="m">``.

        We present a bibliography item as the node with fields ``paragraph_type="bibliography_item"`` and unique id ``uid="uuid"``.
        All ``bibliography_item`` nodes are children of the ``bibliography`` node.
        The example of the bibliography item parsing of the article in dedoc:

        .. example of "node_id": "0.12.5"

        .. literalinclude:: ../_static/json_format_examples/article_example.json
            :language: json
            :lines: 1591-1713


    * **bibliography references**: bibliography references in annotations of the article's text.

        Text can contain references on ``bibliography_item`` nodes.
        For example, "Authors in [5] describe an approach ...". Here "[5]" is the reference.
        We present the bibliography reference as the annotation with ``name="bibliography_ref"`` and value of bibliography item's uuid.
        See documentation of the class :class:`~dedoc.data_structures.ReferenceAnnotation` for more details.

        Example of a bibliography reference in dedoc is given below.
        There is a textual node with two bibliography references (with two annotations):

        .. example of "node_id": "0.10.0"

        .. literalinclude:: ../_static/json_format_examples/article_example.json
            :language: json
            :lines: 1038-1061

        In the example, the annotations reference two ``bibliography_item`` nodes:

        .. example of "node_id": "0.12.33"

        .. literalinclude:: ../_static/json_format_examples/article_example.json
            :language: json
            :lines: 4144-4153

        .. example of "node_id": "0.12.61"

        .. literalinclude:: ../_static/json_format_examples/article_example.json
            :language: json
            :lines: 6774-6783

    * **raw_text**: node referring to a simple document line.

        It has the least importance in the document tree hierarchy,
        so it is situated in the leaves of the tree.
        It is nested to the node corresponding the previous line with a more important type.
