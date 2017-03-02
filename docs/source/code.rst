Library Docstrings
##################

Anacode library consists of two parts. One is for using api and another is for
working with api analysis.

.. contents::
    :local:

anacode.api
***********

..  automodule:: anacode.api

Writers
=======

..  autoclass:: anacode.api.writers.Writer
    :members:

..  autoclass:: anacode.api.writers.CSVWriter
    :members: __init__

..  autoclass:: anacode.api.writers.DataFrameWriter
    :members: __init__

Querying
========

..  autoclass:: anacode.api.client.AnacodeClient
    :members:
    :special-members: __init__

..  autoclass:: anacode.api.client.Analyzer
    :members:
    :special-members: __init__

..  automodule:: anacode.api.client
    :members: analyzer


anacode.agg
***********

..  automodule:: anacode.agg
    :members:

Dataset loader
==============

..  autoclass:: anacode.agg.aggregation.DatasetLoader
    :members:
    :special-members: __init__, __getitem__

API Datasets
============

..  autoclass:: anacode.agg.aggregation.ApiCallDataset

..  autoclass:: anacode.agg.aggregation.CategoriesDataset
    :members:
    :special-members: __init__

..  autoclass:: anacode.agg.aggregation.ConceptsDataset
    :members:
    :special-members: __init__

..  autoclass:: anacode.agg.aggregation.SentimentDataset
    :members:
    :special-members: __init__

..  autoclass:: anacode.agg.aggregation.ABSADataset
    :members:
    :special-members: __init__


anacode.agg.plotting
********************

..  automodule:: anacode.agg.plotting
    :members: barhchart, piechart, concept_cloud
