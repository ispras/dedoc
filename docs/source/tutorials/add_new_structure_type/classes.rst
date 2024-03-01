Main classes related to the structure extraction via lines classification
=========================================================================

Here described the main classes used for features extraction from textual lines,
line classifier training and classifier usage for lines' types prediction.

Features extraction
-------------------

.. autoclass:: dedoc.structure_extractors.feature_extractors.abstract_extractor.AbstractFeatureExtractor
    :members:
    :private-members:

Training utilities
------------------

.. autoclass:: scripts.train.trainers.data_loader.DataLoader
    :members:
    :special-members: __init__

.. autoclass:: scripts.train.trainers.dataset.LineClassifierDataset
    :members:
    :special-members: __init__

.. autoclass:: scripts.train.trainers.base_sklearn_line_classifier.BaseClassifier
    :show-inheritance:
    :members:

.. autoclass:: scripts.train.trainers.base_sklearn_line_classifier.BaseSklearnLineClassifierTrainer
    :members:
    :private-members:
    :special-members: __init__

.. autoclass:: scripts.train.trainers.xgboost_line_classifier_trainer.XGBoostLineClassifierTrainer
    :show-inheritance:
    :members:
    :private-members:

.. autoclass:: scripts.train.trainers.errors_saver.ErrorsSaver
    :members:

Classification
--------------

.. autoclass:: dedoc.structure_extractors.line_type_classifiers.abstract_line_type_classifier.AbstractLineTypeClassifier
    :members:

.. autoclass:: dedoc.structure_extractors.line_type_classifiers.abstract_pickled_classifier.AbstractPickledLineTypeClassifier
    :show-inheritance:
    :members:
