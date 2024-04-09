.. _article_structure:

Article structure type (GROBID)
======================================

This structure type is used for scientific article analysis using `GROBID <https://github.com/kermitt2/grobid>`_ system.

We analyze the recognition results from GROBID. The following types of objects are included in the resulting tree:

    * Article's title;
    * Authors with their affiliations to organizations and emails;
    * Article's sections (for example `Abstract`, `Introduction`, .., `Conclusion` etc);
    * Tables and their content;
    * Bibliography;
    * References on tables and bibliography in the text of the article;

.. note::

    In case you use dedoc as a library. You should up GROBID service via Docker (or see `grobid install instruction <https://grobid.readthedocs.io/en/latest/Run-Grobid/>`_):

    .. code-block:: shell

        docker run --rm --init --ulimit core=0 -p 8070:8070 lfoppiano/grobid:0.8.0

Below is a description of the extracted data in the output tree (description of node):

    * **root**: node containing the text of the article title.

        There is only one root node in any document.
        It is obligatory for any document of diploma type.
        All other document lines are children of the root node.
        We take the title's text from GROBID's TEI-XML path tag ``<title>``:

        .. code-block:: XML

            <fileDesc>
                <titleStmt>
                    <title> Title's text </title> // -> node.paragraph_type="root"
                </fileDesc>
            </titleStmt>

    * **author**: author information.
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

        GROBID's TEI-XML ``<author>``'s affiliation information according the affiliation `description <https://grobid.readthedocs.io/en/latest/training/affiliation-address/>`_ :

        .. code-block:: XML

            <author>    // -> node.paragraph_type="author"
            ...
            <affiliation key="aff0"> // -> node.paragraph_type="author_affiliation"
                <orgname type="institution">École Normale Supérieure</orgname> // -> node.paragraph_type="org_name"
                <address>
                    <addrline>45 rue dUlm</addrline>
                    <postcode>75005</postcode>
                    <settlement>Paris</settlement>
                </address>
            </affiliation>

        The result of parsing the second author of the article:

        ..  example of "node_id": "0.1"

        .. literalinclude:: ../_static/json_format_examples/article_example.json
            :language: json
            :lines: 125-198


    * **bibliography** is the article's bibliography list which contains **bibliography_item** nodes.

        There is GROBID's TEI-XML <bibliography>'s item information description `here <https://grobid.readthedocs.io/en/latest/training/Bibliographical-references/>`_ .
        We parse GROBID's biblStruct and create bibliography item node. Example of GROBID's biblStruct:

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

    We set paragraph_type of the title according tag level in GROBID, according `title level's description <https://grobid.readthedocs.io/en/latest/training/Bibliographical-references/>`_:
        * for ``<title><level="a">`` set the ``parapgraph_type="title"`` for article title or chapter title (but not thesis, see below). Here "a" stands for analytics (a part of a monograph)
        * for ``<title><level="j">`` set the ``parapgraph_type="title_journal"`` for journal title
        * for ``<title><level="s">`` set the ``parapgraph_type="title_series"`` for series title (e.g. "Lecture Notes in Computer Science")
        * for ``<title><level="m">`` set the ``parapgraph_type="title_conference_proceedings"`` for non journal bibliographical item holding the cited article, e.g. conference proceedings title. Note if a book is cited, the title of the book is annotated with ``<title level="m">``

    We present bibliographymitem as the node with fields paragraph_type="bibliography_item" and unique id ``"uid"="uuid"``
    All bibliography_item nodes are children of the bibliography node.
    The example of the bibliography item parsing of the article in dedoc:

        .. example of "node_id": "0.20.5"

        .. literalinclude:: ../_static/json_format_examples/article_example.json
            :language: json
            :lines: 1745-1880


    * **Bibliography references**: We added bibliography references into annotations of the article's text.

        Text can contain references on bibliography_item nodes.
        (for example, "Authors in [5] describe an approach ...". Here "[5]" is the reference).
        We present the bibliography reference as the annotation with ``"name"="bibliography_ref"`` and value of bibliography item's uuid

        Example of bibliography reference in dedoc:
        There is a textual node with two bibliography references (with two annotations):

        .. example of "node_id": "0.15.0"

        .. literalinclude:: ../_static/json_format_examples/article_example.json
            :language: json
            :lines: 1085-1109

        In the example, the annotations reference two bibliography_item nodes:

        .. example of "node_id": "0.20.33"

        .. literalinclude:: ../_static/json_format_examples/article_example.json
            :language: json
            :lines: 4581-4593

        .. example of "node_id": "0.20.61"

        .. literalinclude:: ../_static/json_format_examples/article_example.json
            :language: json
            :lines: 7501-7513

    * **body**: node containing the rest of the document content.

        There is only one body node in any document.
        It is obligatory for any document of technical specification type.
        This is an auxiliary node with empty text, it is nested in the root node along with a table of contents (toc node).
        All of the rest document lines (except root and toc) are children of the body node.

    * **raw_text**: node referring to a simple document line.

        It has the least importance in the document tree hierarchy,
        so it is situated in the leaves of the tree.
        It is nested to the node corresponding the previous line with more important type.
