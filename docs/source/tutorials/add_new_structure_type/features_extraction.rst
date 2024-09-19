.. _add_structure_type_features_extraction:

Features extraction
===================

According to the :ref:`description of the pipeline for structure extraction<classification_structure_extractor>`,
we should define how to extract feature matrix for a given document.
In feature matrix, each column represents one feature, each row corresponds one document line.
Thus, having a feature matrix for a document, we can feed it to the lines classifier and get lines' types.

To get a feature matrix for a certain document domain, one should implement a specific class --
an inheritor of the :class:`~dedoc.structure_extractors.feature_extractors.abstract_extractor.AbstractFeatureExtractor`.
This class contains a list of useful methods that can be tips for features extracting for a new domain.

The new custom domain-specific feature extractor should be an inheritor of the :class:`~dedoc.structure_extractors.feature_extractors.abstract_extractor.AbstractFeatureExtractor`
and, therefore, implement all its abstract methods. The most important method is
:meth:`~dedoc.structure_extractors.feature_extractors.abstract_extractor.AbstractFeatureExtractor.transform`,
that is utilized for transforming document lines into a feature matrix.

Example: implementation of a feature extractor for English articles
-------------------------------------------------------------------

In the :ref:`dataset creation tutorial<add_structure_type_dataset_creation>`,
we used an example domain of English articles.
Here we continue this example and implement ``ArticleFeatureExtractor``.

Let's implement the basic methods of the parent class:

    * :meth:`~dedoc.structure_extractors.feature_extractors.abstract_extractor.AbstractFeatureExtractor.parameters` --
      we don't plan to use any parameters in the ``__init__`` method, so an empty dictionary can be returned;

    * :meth:`~dedoc.structure_extractors.feature_extractors.abstract_extractor.AbstractFeatureExtractor.transform` --
      here we implement a basic scheme of features extraction from each document and their concatenation.

.. literalinclude:: ../../_static/code_examples/article_feature_extractor.py
    :language: python
    :lines: 30-42

To find the most suitable features for a feature extractor, it's better to look into the data first.
The example :download:`archive.zip <../../_static/add_new_structure_type/archive.zip>` with few articles
can suggest using specific regular expressions or keywords.
In our example, the dataset is too small to consider all possible variants adequately.
In real life, we recommend at least 30 various documents of the domain to be included to the training data.

From the given data, we can conclude frequently used keywords and patterns in named items and captions.
This forms some regular expressions and predefined lists of keywords:

.. literalinclude:: ../../_static/code_examples/article_feature_extractor.py
    :language: python
    :lines: 19-27

Let's implement a method that makes a feature vector for one document line.
We suggest the following groups of features to extract for each line:

    * **visual features** -- information about document formatting, e.g., spacing between two lines,
      font size and boldness, etc. Several methods of formatting extraction are available in
      the class :class:`~dedoc.structure_extractors.feature_extractors.abstract_extractor.AbstractFeatureExtractor`,
      that may be used in a custom feature extractor.

    * **textual features** -- features based on domain-specific regular expressions, keywords,
      and other information about the text.

    * **statistical features** -- some statistical information, e.g. line number in the document, its length, etc.

Let's implement the method that extracts the aforesaid groups of features:

.. literalinclude:: ../../_static/code_examples/article_feature_extractor.py
    :language: python
    :lines: 67-93

There are other potentially useful tips:

    * In documents of some domains, we may encounter numerated items.
      To add features related to the numeration, we can use the existing functionality:
      ``ListFeaturesExtractor`` class and :meth:`~dedoc.structure_extractors.feature_extractors.abstract_extractor.AbstractFeatureExtractor._list_features` method.

    * Values of some features may vary depending on the document, but their relative value can be important.
      For example, lines with a bigger font size may be important structure units.
      In this case, normalization can help, :meth:`~dedoc.structure_extractors.feature_extractors.abstract_extractor.AbstractFeatureExtractor._normalize_features` method.

    * We can use contextual nature of the data.
      For this purpose, we can add features of previous or next lines to the features of the current line.

To finish implementation of the feature extractor for articles, let's add a method of feature extraction for one document:

.. literalinclude:: ../../_static/code_examples/article_feature_extractor.py
    :language: python
    :lines: 44-65

The file with the feature extractor should be placed in ``dedoc/structure_extractors/feature_extractors``.
The resulting file with the feature extractor for English articles (our example) can be downloaded
:download:`here <../../_static/code_examples/article_feature_extractor.py>`.

Or you may copy the code below.

.. toggle::

    .. literalinclude:: ../../_static/code_examples/article_feature_extractor.py
        :language: python
