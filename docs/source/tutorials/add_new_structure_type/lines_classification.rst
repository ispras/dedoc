.. _add_structure_type_lines_classification:

Lines classification
====================

.. seealso::
    Training classifier is performed on the custom dataset described in :ref:`add_structure_type_dataset_creation`.
    Before classification, :ref:`add_structure_type_features_extraction` to feed the classifier should be done.

Here we describe two steps:
    1. Writing and running training script to get weights of a trained classifier.
    2. Adding a classifier class in code of Dedoc for further usage.

Classifier training
-------------------

Training a line classifier is quite typical, training scripts for different domains can be found in ``scripts/train``.
But during the process of adjusting the extracted features and classifier's hyperparameters
for enhancing classifier's accuracy, a lot of problems may be encountered.

There are several classes, that are used during training, in particular, for analysis of a training process:

* :class:`~scripts.train.trainers.data_loader.DataLoader` downloads data from cloud and transforms json-lines into Python classes.
* :class:`~scripts.train.trainers.dataset.LineClassifierDataset` represents dataset of document lines in form of a feature matrix.
* :class:`~scripts.train.trainers.base_sklearn_line_classifier.BaseClassifier` is a wrapper of `XGBClassifier <https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBClassifier>`_.
* :class:`~scripts.train.trainers.base_sklearn_line_classifier.BaseSklearnLineClassifierTrainer` -- base class for training :class:`~scripts.train.trainers.base_sklearn_line_classifier.BaseClassifier`.
* :class:`~scripts.train.trainers.xgboost_line_classifier_trainer.XGBoostLineClassifierTrainer` is a trainer for `XGBClassifier <https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBClassifier>`_ with ability to save importance of dataset features.
* :class:`~scripts.train.trainers.errors_saver.ErrorsSaver` is used for saving line classifier’s errors during training.

With this functionality, one may train classifiers of document lines,
analyse the most important features for classifiers,
visualize and analyse errors made by classifiers.
After the analysis, training data or feature extraction process may be changed
in order to improve classification results.

Example: training a classifier for English articles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To train a classifier for English articles, we will use the class :class:`~scripts.train.trainers.xgboost_line_classifier_trainer.XGBoostLineClassifierTrainer` --
please read the documentation of the class (and its base class) to learn its main parameters.

Below there is a code of trainer initialization and running a training process.
As a result, the trained classifier will be saved in ``classifier_path``,
its scores and importance of used features -- in ``path_scores`` and ``path_feature_importances`` correspondingly.

.. literalinclude:: ../../_static/code_examples/train_article_line_classifier.py
    :language: python
    :lines: 42-58


The ``label_transformer`` parameter allows to rename labels of the initial labeled data.
It may be useful when we want to merge two labels into one, or to ignore some labels completely -- in this case, the label_transformer should return ``None``.
In our example, let's ignore lines that have a label ``other``. The rest lines will have their labels unchanged.

.. literalinclude:: ../../_static/code_examples/train_article_line_classifier.py
    :language: python
    :lines: 11-17

We also need to do path configuration for saving resulting files:

.. literalinclude:: ../../_static/code_examples/train_article_line_classifier.py
    :language: python
    :lines: 20-31

Now we have almost everything we need, let's initialize the remaining parameters required by a trainer:

.. literalinclude:: ../../_static/code_examples/train_article_line_classifier.py
    :language: python
    :lines: 33-40

To run the script without errors, one should provide ``data_url`` parameter to download the training dataset.
Please, see training scripts in ``scripts/train`` where urls to the existing datasets are provided to get some examples.
Obtaining a training dataset is described in :ref:`add_structure_type_dataset_creation` in more details.

Thus, writing a training script is finished. The file with the script should be placed in the ``scripts/train`` directory.
The full training script may be downloaded :download:`here <../../_static/code_examples/train_article_line_classifier.py>`,
or you may copy the code below.

.. toggle::

    .. literalinclude:: ../../_static/code_examples/train_article_line_classifier.py
        :language: python


Classifier adding
-----------------

Since we trained a new classifier and saved its weights, we can use it in dedoc for inference.
Do do this, an inheritor of the :class:`~dedoc.structure_extractors.line_type_classifiers.abstract_pickled_classifier.AbstractPickledLineTypeClassifier` should be implemented.
In this class, the :meth:`~dedoc.structure_extractors.line_type_classifiers.abstract_line_type_classifier.AbstractLineTypeClassifier.predict` method is the most important part.
This method is used for classification of the list of input :class:`~dedoc.data_structures.LineWithMeta` related to one document.
As a result, the list of line types is obtained.

The commonplace pipeline in the :meth:`~dedoc.structure_extractors.line_type_classifiers.abstract_line_type_classifier.AbstractLineTypeClassifier.predict` method works as follows:

    * Forming a feature matrix for the input list of document lines using a feature extractor;
    * Calling a classifier's prediction method (classes probabilities also may be obtained);
    * If needed, some post-processing of probabilities can be done (optional).

Example: implementation of a line classifier for English articles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the :ref:`features extraction tutorial<add_structure_type_features_extraction>`,
we used an example domain of English articles and implemented ``ArticleFeatureExtractor``.
Here we continue this example and implement ``ArticleLineTypeClassifier``.

In the ``__init__`` method of the class, let's load classifier weights and initialize a feature extractor:

.. literalinclude:: ../../_static/code_examples/article_classifier.py
    :language: python
    :lines: 11-14

Let's implement the aforesaid commonplace pipeline in the ``predict`` method.

Forming a feature matrix:

.. literalinclude:: ../../_static/code_examples/article_classifier.py
    :language: python
    :lines: 20

Calling a classifier's prediction method:

.. literalinclude:: ../../_static/code_examples/article_classifier.py
    :language: python
    :lines: 21

Executing some custom post-processing of the predicted classes probabilities:

.. literalinclude:: ../../_static/code_examples/article_classifier.py
    :language: python
    :lines: 23-43

The file with the line classifier should be placed in ``dedoc/structure_extractors/line_type_classifiers``.
The resulting file with the classifier for English articles (our example) can be downloaded
:download:`here <../../_static/code_examples/article_classifier.py>`.

Or you may copy the code below.

.. toggle::

    .. literalinclude:: ../../_static/code_examples/article_classifier.py
        :language: python
