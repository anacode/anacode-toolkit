
.. _intro:

Anacode Toolkit
###############

This library is a helper tool for users of the
`Anacode Web&Text API <https://api.anacode.de>`_, a REST API for Chinese
web data collection and Natural Language Processing. The following operations are possible
with the library:

1. Abstraction of HTTP protocol that is used by Anacode Web&Text API. Besides,
   concurrent Anacode API querying is made simple (only relevant for users with paid account).
2. Conversion of JSON analysis results into flat table structures.
3. Common aggregation and selection tasks that can be performed
   on API analysis results, like finding the most discussed concepts or ten best-rated entities
4. Convenient plotting functions for aggregation results, ready to use in print documents.

The first two features are covered by the module :mod:`anacode.api`; 3. and 4. are covered by :mod:`anacode.agg`.


.. contents::
    :local:


Installation
************

The library is published via PyPI and works on python2.7 and
python3.3+. To install from PyPI simply use pip:

.. code-block:: shell

    pip install anacode

You can also clone its repository and install from source using the setup.py script:

.. code-block:: shell

    git clone https://github.com/anacode/anacode-toolkit.git
    cd anacode-toolkit
    python setup.py install


Using Anacode API and storing results (anacode.api)
***************************************************

Querying the API
================

The :mod:`anacode.api` module provides functionality for http communication with the Anacode Web&Text API.
The class :class:`anacode.api.client.AnacodeClient` can be used to analyze Chinese texts.

.. code-block:: python

    >>> from anacode.api import client
    >>> # base_url is optional
    >>> api = client.AnacodeClient(
    >>>     'token', base_url='https://api.anacode.de/')
    >>> # this will create an http request for you, send it to appropriate
    >>> # endpoint, parse the result and return it in a python dict
    >>> json_analysis = api.analyze(['储物空间少', '后备箱空间不小'], ['concepts'])

There is also a class :class:`anacode.api.client.Analyzer` to perform bulk querying. It can used
multiple threads and saves the results either to pandass
dataframes or csv files. However, it is not intended for direct usage - instead, please
use the interface to it that is covered in :ref:`using-analyzer`.


Storing results
===============

Since there is no analysis tool that can analyse arbitrary json schemas well,
the toolkit offers a simple way to convert lists of API json results to a standard SQL-like
data structure. There are two possibilities: you can convert your output to a
`pandas.DataFrames <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_
or store it to disk in csv files, making it ready to be input into various
data processing programs such as Excel. The JSON > CSV conversion code lives in
:mod:`anacode.api.writers`. You are not expected to use it directly, but here is
quick example how to load sentiment analysis results into memory as a dataframe.

.. code-block:: python

    >>> from anacode.api import writers
    >>> sentiment_json_output_0 = [
    >>>     [{"label": "negative", "probability": 0.7},
    >>>      {"label": "positive", "probability": 0.3}],
    >>>     [{"label": "negative", "probability": 0.8},
    >>>      {"label": "positive", "probability": 0.2}],
    >>> ]
    >>> sentiment_json_output_1 = [
    >>>     [{"label": "negative", "probability": 0.99},
    >>>      {"label": "positive", "probability": 0.01}]
    >>> ]
    >>> df_writer = writers.DataFrameWriter()
    >>> df_writer.init()
    >>> df_writer.write_sentiment(sentiment_json_output_0)
    >>> df_writer.write_sentiment(sentiment_json_output_1)
    >>> df_writer.close()
    >>> df_writer.frames['sentiments']

.. parsed-literal::

       doc_id  text_order  positive  negative
    0       0           0      0.3       0.7
    1       0           1      0.2       0.8
    2       1           0      0.01      0.99

The schemas of the tables are described in :ref:`analysed-schema`.

Both :class:`anacode.api.writers.DataFrameWriter` and
:class:`anacode.api.writers.CSVWriter` have the same interface. They
generate document ids (doc_id) incrementally and separately for analyze
and scrape. That means that document id gets incremented each time you
successfully receive an analysis/scrape result from API.


.. _using-analyzer:

Using analyzer
==============

If you want to analyze a larger number of texts and store
the analysis results to a csv file, you can use the
:func:`anacode.api.client.analyzer` function. It provides an easy interface to
bulk querying and storing results in a table-like data structure.

The following code snippet analyses categories and sentiment for all `documents`
in a single thread by bulks of size 100 and saves the resulting csv files to the folder
'ling'.

.. code-block:: python

    >>> from anacode.api import client
    >>> documents = [
    >>>     ['Chinese text 1', 'Chinese text 2'],
    >>>     ['...'],
    >>> ]
    >>> with client.analyzer('token', 'ling') as api:
    >>>     for document in documents:
    >>>         api.analyze(document, ['categories', 'sentiment'])


By contrast, below code snippet analyses categories and sentiment for all
`documents` in two threads by bulks of size 200 and saves the output as pandas
DataFrames to provided dictionary.

.. code-block:: python

    >>> from anacode.api.client import analyzer
    >>> documents = [
    >>>     ['Chinese text 1', 'Chinese text 2'],
    >>>     ['...'],
    >>> ]
    >>> output_dict = {}
    >>> with analyzer('token', output_dict, threads=2, bulk_size=200) as api:
    >>>     for document in documents:
    >>>         api.analyze(document, ['categories', 'sentiment'])
    >>> print(output_dict.keys())

.. parsed-literal::

    dict_keys(['concepts', 'concepts_surface_strings', 'sentiments'])


Aggregation framework (anacode.agg)
***********************************

Data loading
============

The Anacode Toolkit provides the :class:`anacode.agg.aggregation.DatasetLoader` for
loading analysed data from different formats:

#. Lists of json outputs

    If you just stored the raw json output of the Web\&Text API into a list of python dictionaries, you
    can use
    :func:`DatasetLoader.from_lists <anacode.agg.aggregation.DatasetLoader.from_lists>`
    to load them. This converts your lists into pandas dataframes.

    .. code-block:: python

        >>> from anacode.agg import DatasetLoader
        >>> absa_json_list = [ '...' ]
        >>> categories_json_list = [ '...' ]
        >>> dataset = DatasetLoader.from_lists(
        >>>     categories=categories_json_list,
        >>>     absa=absa_json_list,
        >>> )


#. Path to folder with csv files

    If you stored the analysis results in csv files (using
    :class:`anacode.api.writers.CSVWriter`), you can provide the path to
    their parent folder to
    :func:`DatasetLoader.from_path <anacode.agg.aggregation.DatasetLoader.from_path>`
    to load all available results. If you want to load older - backed up - csv
    files, you can use *backup_suffix* argument of the method to specify
    suffix of files to load.


#. From :class:`anacode.api.writers.Writer` instance

    If you used an instance of *Writer* (either *DataFrameWriter* or *CSVWriter*)
    to store the analysis results, you can pass a reference to it to the
    :func:`DatasetLoader.from_writer <anacode.agg.aggregation.DatasetLoader.from_writer>`
    class method.


#. From pandas.DataFrames

    You can also use *DatasetLoader*'s
    :func:`DatasetLoader.__init__ <anacode.agg.aggregation.DatasetLoader.__init__>`
    which simply takes *pandas.DataFrames* of analyzed data. See it's
    docstrings for more info on parameter names.


Accessing analysis data
=======================

There are two ways to access the analysis results from
:class:`DatasetLoader <anacode.agg.aggregation.DatasetLoader>`. First, you can access
*pandas.DataFrame* directly using
:func:`DatasetLoader.__getitem__ <anacode.agg.aggregation.DatasetLoader.__getitem__>`, as
follows: `absa_texts = dataset['absa_normalized_texts']`. The format of these
data frames is described below. Second, you can get higher-level access to the separate datasets via
:func:`DatasetLoader.categories <anacode.agg.aggregation.DatasetLoader.categories>`,
:func:`DatasetLoader.concepts <anacode.agg.aggregation.DatasetLoader.concepts>`,
:func:`DatasetLoader.sentiments <anacode.agg.aggregation.DatasetLoader.sentiments>` or
:func:`DatasetLoader.absa <anacode.agg.aggregation.DatasetLoader.absa>`.
The latter returns :class:`anacode.agg.aggregation.ApiCallDataset` instances
and actions you can perform with it will be explained in the next chapter.


Text order field
----------------

In `all calls documentation <https://api.anacode.de/api-docs/calls.html>`_
you can notice that they take not a single text for analysis but list of texts.
Every call also returns list of analysis, one for each text given. *text-order*
property in csv row defines index of analysis in this list that produced
the row. That means that you can use text-order column to match analysis results
to specific pieces of text that you sent to the API for analysis.

.. _analysed-schema:

Table schema
------------

In this section, we describe the table schema of the analysis results for each of the four calls.


Categories
""""""""""

**categories.csv**

categories.csv will contain one row per supported category name per text. You
can find out more about category classification in
`its documentation <https://api.anacode.de/api-docs/taxonomies.html>`_

- *doc_id* - document id generated incrementally
- *text_order* - index to original input text list
- *category* - category name
- *probability* - float in range <0.0, 1.0>

The probabilities for all categories for a given text sum up to 1.


Concepts
""""""""

**concepts.csv**

- *doc_id* - document id generated incrementally
- *text_order* - index to original input text list
- *concept* - name of concept
- *freq* - frequency of occurrences of this concept in the text
- *relevance_score* - relative relevance of the concept in this text
- *concept_type* - type of concept (cf. `here <https://api.anacode.de/api-docs/concept_types.html>`_ for list of available concept types)

**concept_surface_strings.csv**

concept_surface_strings.csv extends concepts.csv with surface strings that were
used in text that realize it’s concepts

- *doc_id* - document id generated incrementally
- *text_order* - index to original input text list
- *concept* - concept identified by anacode nlp
- *surface_string* - string found in original text that realizes this concept
- *text_span* - string index to original text where you can find this concept

Note that if concept is used multiple times in original text there will be
multiple rows with it in this file.


Sentiment
"""""""""

**sentiment.csv**

- *doc_id* - document id generated incrementally
- *text-order* - index to original input text list
- *positive* - probability that this post has positive sentiment
- *negative* - probability that this post has negative sentiment

Positive and negative probabilities sum up to 1.


ABSA
""""

**absa_entities.csv**

- *doc_id* - document id generated incrementally
- *text_order* - index to original input text list
- *entity_name* - name of the entity
- *entity_type* - type of the entity
- *surface_string* - string found in original text that realizes this entity
- *text_span* - string index in original text where surface_string can be found

**absa_normalized_text.csv**

- *doc_id* - document id generated incrementally
- *text_order* - index to original input text list
- *normalized_text* - text with normalized casing and whitespace

**absa_relations.csv**

- *doc_id* - document id generated incrementally
- *text_order* - index to original input text list
- *relation_id* - since the absa relation output can have multiple relations, we introduce relation_id as a foreign key
- *opinion_holder* - optional; if this field is null, the default opinion holder is the author himself
- *restriction* - optional; contextual restriction under which the evaluation applies
- *sentiment_value* - polarity of evaluation
- *is_external* - whether an external entity was defined for this relation
- *surface_string* - original text that generated this relation
- *text_span* - string index in original text where surface_string can be found

**absa_relations_entities.csv**

This table is extending absa_relations.csv by providing list of entities
connected to evaluations in it.

- *doc_id* - document id generated incrementally
- *text_order* - index to original input text list
- *relation_id* - foreign key to absa_relations
- *entity_type* -
- *entity_name* -

**absa_evaluations.csv**

- *doc_id* - document id generated incrementally
- *text_order* - index to original input text list
- *evaluation_id* - absa evaluations output can rate multiple entities, this
  serves as foreign key to them
- *sentiment_value* - numeric value how positive/negative statement is
- *surface_string* - original text that was used to get this evaluation
- *text_span* - string index in original text where surface_string can be found

**absa_evaluations_entities.csv**

- *doc_id* - document id generated incrementally
- *text_order* - index to original input text list
- *evaluation_id* - foreign key to absa_evaluations
- *entity_type* -
- *entity_name* -


Aggregations
============

The Anacode Toolkit provides set of common aggregations over the analysed
data. These are accessible from the four subclasses of
:class:`ApiCallDataset <anacode.agg.aggregation.ApiCallDataset>` -
:class:`CategoriesDataset <anacode.agg.aggregation.CategoriesDataset>`,
:class:`ConceptsDataset <anacode.agg.aggregation.ConceptsDataset>`,
:class:`SentimentDataset <anacode.agg.aggregation.SentimentDataset>` and
:class:`ABSADataset <anacode.agg.aggregation.ABSADataset>`. You can get any of those using
the corresponding properties of the class :class:`DatasetLoader <anacode.agg.aggregation.DatasetLoader>`
(:func:`categories <anacode.agg.aggregation.DatasetLoader.categories>`,
:func:`concepts <anacode.agg.aggregation.DatasetLoader.concepts>`,
:func:`sentiments <anacode.agg.aggregation.DatasetLoader.sentiments>` and
:func:`absa <anacode.agg.aggregation.DatasetLoader.absa>`).

Here is a list of aggregations and some other convenience methods with
descriptions and usage examples that can be performed for each api call dataset.


ConceptsDataset
---------------

.. _concept_frequency_agg:

- :func:`concept_frequency(concept, concept_type='', normalize=False) <anacode.agg.aggregation.ConceptsDataset.concept_frequency>`

  Concepts are returned in the same order as they were in input.

  .. code-block:: python

     >>> concept_list = ['CenterConsole', 'MercedesBenz',
     >>>                 'AcceleratorPedal']
     >>> concepts.concept_frequency(concept_list)

  .. parsed-literal::

     Concept
     CenterConsole       27
     MercedesBenz        91
     AcceleratorPedal    39
     Name: Count, dtype: int64

  Limiting concept_type may zero out counts:

  .. code-block:: python

     >>> concepts.concept_frequency(
     >>>     concept_list, concept_type='feature')

  .. parsed-literal::

     Feature
     CenterConsole       27
     MercedesBenz         0
     AcceleratorPedal    39
     Name: Count, dtype: int64

  The next two code samples demonstrate how percentages can change if concept_type
  filter changes.

  .. code-block:: python

     >>> concepts.concept_frequency(concept_list, normalize=True)

  .. parsed-literal::

     Concept
     CenterConsole       0.005560
     MercedesBenz        0.018740
     AcceleratorPedal    0.008031
     Name: Count, dtype: float64

  .. code-block:: python

     >>> concepts.concept_frequency(
     >>>     concept_list, concept_type='feature', normalize=True)

  .. parsed-literal::

     Feature
     CenterConsole       0.009174
     MercedesBenz        0.000000
     AcceleratorPedal    0.013252
     Name: Count, dtype: float64


- :func:`most_common_concepts(n=15, concept_type='', normalize=False) <anacode.agg.aggregation.ConceptsDataset.most_common_concepts>`

  .. code-block:: python

     >>> concepts.most_common_concepts(n=3)

  .. parsed-literal::

     Concept
     Automobile          533
     BMW                 381
     VisualAppearance    241
     Name: Count, dtype: int64

  Also read about :ref:`concept_frequency <concept_frequency_agg>` to see how
  concept_type and normalize can change output.

- :func:`least_common_concepts(n=15, concept_type='', normalize=False) <anacode.agg.aggregation.ConceptsDataset.least_common_concepts>`

  .. code-block:: python

     >>> concepts.least_common_concepts(n=3)

  .. parsed-literal::

     Concept
     30       1
     Lepow    1
     Lid      1
     Name: Concept, dtype: int64

  Also read about :ref:`concept_frequency <concept_frequency_agg>` to see how
  concept_type and normalize can change output.

- :func:`co_occurring_concepts(concept, n=15, concept_type='') <anacode.agg.aggregation.ConceptsDataset.co_occurring_concepts>`

  .. code-block:: python

     >>> concepts.co_occurring_concepts('VisualAppearance', n=5,
     >>>                                concept_type='feature')

  .. parsed-literal::

     Feature
     Interior    33
     Body        26
     Comfort     17
     Space       17
     RearEnd     16
     Name: Count, dtype: int64

  Also read about :ref:`concept_frequency <concept_frequency_agg>` to see how
  concept_type can change output.

- :func:`nltk_textcollection(concept_type='') <anacode.agg.aggregation.ConceptsDataset.nltk_textcollection>`

  Creates nltk.text.TextCollection containing concepts found by linguistic
  analysis.

- :func:`make_idf_filter(threshold, concept_type='') <anacode.agg.aggregation.ConceptsDataset.make_idf_filter>`

  Creates IDF filter from concepts found by linguistic analysis. You can read
  more about IDF filtering on many places, for your convenience we provide a link to
  `stanford webpage <http://nlp.stanford.edu/IR-book/html/htmledition/inverse-document-frequency-1.html>`_.

- :func:`make_time_series(concepts, date_info, delta, interval=None) <anacode.agg.aggregation.ConceptsDataset.make_time_series>`

  You will have to provide date_info dictionary to this function. The keys of date_info correspond to
  consecutive integers; the values correspond to :class:`datetime.date` objects:

  .. code-block:: python

     >>> print(date_info)

  .. parsed-literal::

     {0: datetime.date(2016, 1, 1),
      1: datetime.date(2016, 1, 2),
      2: datetime.date(2016, 1, 3),
      3: datetime.date(2016, 1, 4),
      4: datetime.date(2016, 1, 5),
      5: datetime.date(2016, 1, 6),
      ...
     }

  When you are using scraped data from Anacode in json format you can build
  the dictionary by looping over documents with date field, parsing it and storing
  it in dictionary under index of the document like this:

  .. code-block:: python

     >>> from datetime import datetime
     >>> date_info = {}
     >>> for index, doc in enumerate(scraped_json_data):
     >>>     if not doc['date']:
     >>>         continue
     >>>     date_info[index] = datetime.strptime(d['date'], '%Y-%m-%d')

  When you have date_info dictionary generating time series is simple. Keep in mind
  that resulting time series ticks include it's starting date and exclude ending date.
  So a tick who starts at *Start* and ends at *Stop* will include these:
  `Start <= concept's document time < Stop`.

  .. code-block:: python

     >>> concepts.make_time_series(['Body'], date_info,
     >>>                           timedelta(days=100))

  .. parsed-literal::

         Count   Concept     Start       Stop
     0   89      Body    2016-01-01  2016-04-10
     1   25      Body    2016-04-10  2016-07-19
     2   2       Body    2016-07-19  2016-10-27
     3   3       Body    2016-10-27  2017-02-04

  When you limit interval (start and stop of ticks) and you specify delta such
  that `start + K * delta = stop` cannot be solved the stop will stretch to the
  first following date for which the formula can be solved. For instance setting
  start to 2016-01-01 and stop to 2016-01-07 and delta to 4 days, stop will be
  changed to 2016-01-09.

  .. code-block:: python

     >>> concepts.make_time_series(['Body'], date_info,
     >>>                           timedelta(days=4),
     >>>                           (date(2016, 1, 1), date(2016, 1, 7)))

  .. parsed-literal::

         Count  Concept     Start      Stop
     0   3      Body     2016-01-01   2016-01-05
     1   2      Body     2016-01-05   2016-01-09

- :func:`concept_cloud(path, size=(600, 350), background='white', colormap_name='Accent', max_concepts=200, stopwords=None, concept_type='', concept_filter=None, font=None) <anacode.agg.aggregation.ConceptsDataset.concept_cloud>`

  This function generates a concept cloud image and stores it either to a file file or to a numpy
  ndarray. Here is simple example for generating an ndarray:

  .. code-block:: python

     >>> concept_cloud_img = concepts.concept_cloud(path=None)


CategoriesDataset
-----------------

- :func:`categories() <anacode.agg.aggregation.CategoriesDataset.categories>`

  You can check list of categories on
  `api.anacode.de webpage <https://api.anacode.de/api-docs/taxonomies.html>`_.
  Each category will be present in output.

  .. code-block:: python

     >>> categories.categories()

  .. parsed-literal::

           Probability
     auto  0.3155102
     hr    0.02371
           ...

- :func:`main_category() <anacode.agg.aggregation.CategoriesDataset.main_category>`

  .. code-block:: python

     >>> categories.main_category()

  .. parsed-literal::

     'auto'

SentimentsDataset
-----------------

- :func:`average_sentiment() <anacode.agg.aggregation.SentimentDataset.average_sentiment>`

  .. code-block:: python

     >>> sentiments.average_sentiment()

  .. parsed-literal::

     0.43487262467141063


ABSADataset
-----------

- :func:`entity_frequency(entity, entity_type='', normalize=False) <anacode.agg.aggregation.ABSADataset.entity_frequency>`

  .. code-block:: python

     >>> absa.entity_frequency(['Oil', 'Buying'])

  .. parsed-literal::

     Entity
     Oil       62
     Buying    80
     Name: Count, dtype: int64

  Also read about :ref:`concept_frequency <concept_frequency_agg>` to see how
  entity_type and normalize can change the output.

- :func:`most_common_entities(n=15, entity_type='', normalize=False) <anacode.agg.aggregation.ABSADataset.most_common_entities>`

  .. code-block:: python

     >>> absa.most_common_entities(n=2)

  .. parsed-literal::

     Entity
     Automobile    538
     BMW           384
     Name: Count, dtype: int64

  Also read about :ref:`concept_frequency <concept_frequency_agg>` to see how
  entity_type and normalize can change output.

- :func:`least_common_entities(n=15, entity_type='', normalize=False) <anacode.agg.aggregation.ABSADataset.least_common_entities>`

  .. code-block:: python

     >>> absa.least_common_entities(n=2)

  .. parsed-literal::

     Entity
     FashionStyle    1
     Room            1
     Name: entity_name, dtype: int64

  Also read about :ref:`concept_frequency <concept_frequency_agg>` to see how
  entity_type and normalize can change output.

- :func:`co_occurring_entities(entity, n=15, entity_type='') <anacode.agg.aggregation.ABSADataset.co_occurring_entities>`

  .. code-block:: python

     >>> absa.co_occurring_entities('Oil', n=5,
     >>>                            entity_type='feature_')

  .. parsed-literal::

     Feature
     FuelConsumption    32
     Power              28
     Acceleration       10
     Size                9
     Body                6
     Name: Count, dtype: int64

  Also read about :ref:`concept_frequency <concept_frequency_agg>` to see how
  entity_type can change output.


- :func:`best_rated_entities(n=15, entity_type='') <anacode.agg.aggregation.ABSADataset.best_rated_entities>`

  .. code-block:: python

     >>> absa.best_rated_entities(n=1)

  .. parsed-literal::

     Entity
     X5    9.0
     Name: Sentiment, dtype: float64

  Also read about :ref:`concept_frequency <concept_frequency_agg>` to see how
  entity_type can change output.

- :func:`worst_rated_entities(n=15, entity_type='') <anacode.agg.aggregation.ABSADataset.worst_rated_entities>`

  .. code-block:: python

     >>> absa.worst_rated_entities(n=2)

  .. parsed-literal::

     Entity
     Compartment   -4.0
     Black         -3.5
     Name: Sentiment, dtype: float64

  Also read about :ref:`concept_frequency <concept_frequency_agg>` to see how
  entity_type can change output.

- :func:`surface_strings(entity) <anacode.agg.aggregation.ABSADataset.surface_strings>`

  .. code-block:: python

     >>> absa.surface_strings('ShockAbsorption')

  .. parsed-literal::

     {'ShockAbsorption': ['减震效果也非常好',
                          '减震效果和隔音效果也很好',
                          '减震效果也很好']}

- :func:`entity_texts(entity) <anacode.agg.aggregation.ABSADataset.entity_texts>`

  .. code-block:: python

     >>> absa.entity_texts(['Room', 'FashionStyle'])

  .. parsed-literal::

     {'FashionStyle': ['外观很满意，外形稍显低调，但不缺乏时尚动感，整车的线条体现更是完整，看起来更为流畅，开眼角大灯我也比较喜欢，这车感觉就像一个穿着休闲西服的长腿欧巴，时而稳重，时而动感'],
      'Room': ['外观好看，室内舒适。']}

- :func:`entity_sentiment(entity) <anacode.agg.aggregation.ABSADataset.entity_sentiment>`

  .. code-block:: python

     >>> absa.entity_sentiment({'Oil', 'Seats', 'Room'})

  .. parsed-literal::

     Entity
     Oil      2.500000
     Room     2.000000
     Seats    2.469298
     Name: Sentiment, dtype: float64
