
.. _intro:

Anacode Toolkit
***************

This library is a helper tool for users of
`Anacode API <https://api.anacode.de>`_ which is chinese natural language
processor. These are parts of working with Anacode API that this library
tries to make easier.

#. Abstracting away from HTTP protocol that is used by Anacode API. Also
   concurrent Anacode API querying is made simple. Concurrent querying is
   relevant only to users with paid account.
#. Give users easy way to convert analysis results in json format to flat
   table like data structures.
#. Provide *out-of-the-box* solution for common tasks that can be performed
   on API analysis results like finding the most discussed concept or ten best
   rated entities

First two goals are related to performing chinese text analysis with Anacode API
and :mod:`anacode.api` can help you with them. For performing tasks mentioned
in the last goal you can use :mod:`anacode.agg` to help you conceptually
simplify your code.


.. contents::
    :local:


Installation
~~~~~~~~~~~~

Library is published via PyPI and it's meant to work on python2.7 and
python3.3+. To install from PyPI simply use pip:

.. code-block:: shell

    pip install anacode

You can also clone it's repository and install from the source using setup.py
script:

.. code-block:: shell

    git clone https://github.com/anacode/anacode-toolkit.git
    cd anacode-toolkit
    python setup.py install


Using Anacode API and storing results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Querying API
------------

For http communication with Anacode API this library provides :mod:`anacode.api`
module. There is :class:`anacode.api.client.AnacodeClient` that can be used
to analyze chinese texts.

.. code-block:: python

    >>> from anacode.api import client
    >>> # base_url is optional
    >>> api = client.AnacodeClient(('username', 'password'),
    >>>                            base_url='https://api.anacode.de/')
    >>> # this will create an http request for you, sent it to appropriate
    >>> # endpoint, parse result and returns python dict
    >>> json_analysis = api.concepts(['储物空间少', '后备箱空间不小'])

There is also :class:`anacode.api.client.Analyzer` that performs bulk querying
potentially using multiple threads and saving results to either pandas's
DataFrames or csv files. It's however not intended for direct usage and there is
easy to use interface to it that's covered in :ref:`using-analyzer`.


Storing results
---------------

Since there is no analysis tool that can analyse arbitrary json schema well
there is a simple way to convert list of json results from our API to sql-like
data structure. There are two possibilities: you can convert output to
`pandas.DataFrames <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_
or store it to disk in csv files. There is a lot of software that can work with
csv files out of the box. One of the notable ones that are used for data
analysis is Excel. JSON -> CSV conversion code lives in
:mod:`anacode.api.writers`. You are not expected to use it directly, but here is
quick example how to load sentiment analysis results to memory as DataFrame.

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

Table "schema" for format that is used to store analysis result is described
in more detail in :ref:`analysed-schema`.

Both :class:`anacode.api.writers.DataFrameWriter` and
:class:`anacode.api.writers.CSVWriter` have the same interface and they both
generate doc_id incrementally and separately for each API call. That means that
you are expected to save exactly the same amount of call results from the calls
that you choose to store in order for `doc_id` to properly connect results
from different calls. It also means that it does not matter whether you first
save 10 sentiment results and then 10 absa results or you save 10 times
1 sentiment and 1 absa result.


.. _using-analyzer:

Using analyzer
--------------

If you have more than just a few texts you want to analyse and you wish to store
analysis results in csv file, you want to use
:func:`anacode.api.client.analyzer` function. It provides easy interface to
bulk querying and storing results in table like data structure.

Following code snippet would analyse categories and absa for all `documents`
in single thread by bulks of size 100 and save resulting CSV files to folder
'ling'.

.. code-block:: python

    >>> from anacode.api import client
    >>> documents = [
    >>>     ['Chinese text 1', 'Chinese text 2'],
    >>>     ['...'],
    >>> ]
    >>> with client.analyzer(('username', 'password'), 'ling') as api:
    >>>     for document in documents:
    >>>         api.categories(document)
    >>>         api.absa(document)


This code snippet would analyse concepts and general sentiment for all
`documents` in two threads by bulks of size 200 and save output as pandas
DataFrames to provided dictionary.

.. code-block:: python

    >>> from anacode.api.client import analyzer
    >>> documents = [
    >>>     ['Chinese text 1', 'Chinese text 2'],
    >>>     ['...'],
    >>> ]
    >>> auth = 'username', 'password'
    >>> output_dict = {}
    >>> with analyzer(auth, output_dict, threads=2, bulk_size=200) as api:
    >>>     for document in documents:
    >>>         api.concepts(document)
    >>>         api.sentiment(document)
    >>> print(output_dict.keys())

.. parsed-literal::

    dict_keys(['concepts', 'concepts_expressions', 'sentiments'])


Aggregation framework
~~~~~~~~~~~~~~~~~~~~~

Data loading
------------

Library provides class :class:`anacode.agg.aggregation.DatasetLoader` for
loading analysed data. After performing analysis there are more options how you
can have your data stored. Here is an exhaustive list of ways how and what
formats can *DatasetLoader* use to load Anacode API analysis data. Every one
of them results in properly initialized *DatasetLoader* instance.

#. Lists of json api output

    If you stored raw json output of API into list of python dictionaries you
    can use
    :func:`DatasetLoader.from_lists <anacode.agg.aggregation.DatasetLoader.from_lists>`
    to load them. This converts your lists into pandas DataFrames internally
    using :class:`anacode.api.writers.DataFrameWriter`.

    .. code-block:: python

        >>> from anacode.agg import DatasetLoader
        >>> absa_json_list = [ '...' ]
        >>> categories_json_list = [ '...' ]
        >>> dataset = DatasetLoader.from_lists(
        >>>     categories=categories_json_list,
        >>>     absa=absa_json_list,
        >>> )


#. Path to folder with csv files

    When you stored analysis results in a csv files (using
    :class:`anacode.api.writers.CSVWriter`) you can provide path to
    their parent folder to
    :func:`DatasetLoader.from_path <anacode.agg.aggregation.DatasetLoader.from_path>`
    to load all available analysis data.


#. From :class:`anacode.api.writers.Writer` instance

    If you used instance of *Writer* (either *DataFrameWriter* or *CSVWriter*)
    to store the analysis output you can pass reference to it to
    :func:`DatasetLoader.from_writer <anacode.agg.aggregation.DatasetLoader.from_writer>`
    class method.


#. Directly from pandas.DataFrames

    You can also use *DatasetLoader*'s
    :func:`DatasetLoader.__init__ <anacode.agg.aggregation.DatasetLoader.__init__>`
    which simply takes *pandas.DataFrames* of analyzed data. See it's
    docstrings for more info on parameter names.


Accessing analysis data
-----------------------

There are two possible ways to get to output of text analysis from
:class:`DatasetLoader <anacode.agg.aggregation.DatasetLoader>`. You can either
access *pandas.DataFrame* directly using
:func:`DatasetLoader.__getitem__ <anacode.agg.aggregation.DatasetLoader.__getitem__>`
like this: `absa_texts = dataset['absa_normalized_texts']`. Format of these
data frames is described below. If you want higher level access you can access
separate call datasets via
:func:`DatasetLoader.categories <anacode.agg.aggregation.DatasetLoader.categories>`,
:func:`DatasetLoader.concepts <anacode.agg.aggregation.DatasetLoader.concepts>`,
:func:`DatasetLoader.sentiments <anacode.agg.aggregation.DatasetLoader.sentiments>` or
:func:`DatasetLoader.absa <anacode.agg.aggregation.DatasetLoader.absa>`.
The latter returns :class:`<anacode.agg.aggregation.ApiCallDataset>` instances
and actions you can perform with it will be explained in the next chapter.

.. _analysed-schema:

Table schema
''''''''''''

Here are lists of columns for each analysis output table with short
descriptions:

**categories.csv**

categories.csv will contain one row per supported category name per text. You
can find out more about category classification in
`it's documentation <https://api.anacode.de/api-docs/taxonomies.html>`_

- *doc_id* - id of review from reviews.csv
- *text_order* - specific text identifier
- *category* - category name
- *probability* - float from <0.0, 1.0> interval

**concepts.csv**

- *doc_id* - id of review from reviews.csv
- *concept* - concept identified by anacode nlp
- *freq* - frequency of occurrences of this concept in the text
- *relevance_score* - relative relevance of the concept in this text
- *concept_type* -

**concept_expressions.csv**

concept_expressions.csv extends concepts.csv with expressions that were used
in text that realize it’s concepts.

- *doc_id* - id of review from reviews.csv
- *concept* - concept identified by anacode nlp
- *expression* - expression found in original text that realizes this concept

Note that if expression is used multiple times in original text there will be
multiple rows with it in this file.

**sentiment.csv**

- *doc_id* - id of review from reviews.csv
- *positive* - probability that this post has positive sentiment
- *negative* - probability that this post has negative sentiment

Note that positive + negative = 1.

**absa_entities.csv**

- *doc_id* - id of review from reviews.csv
- *text_order* - specific text identifier; API returns separate output for
  every text it gets and we called it with list of texts so this makes sure
  that different text outputs from one posts can be matched together
- *entity_name* -
- *entity_type* -
- *surface_string* - expression found in original text that realizes this entity
- *text_span* - string index in original text where surface_string can be found

**absa_normalized_text.csv**

- *doc_id* - id of review from reviews.csv
- *text_order* - specific text identifier
- *normalized_text* - text with normalized casing and whitespace

**absa_relations.csv**

- *doc_id* - id of review from reviews.csv
- *text_order* - specific text identifier
- *relation_id* - absa relation output can have multiple relations, this serves as foreign key to them
- *opinion_holder* - optional; if this field is null, the default opinion holder is the author himself
- *restriction* - optional; contextual restriction under which the evaluation applies
- *sentiment* - polarity of evaluation
- *is_external* - whether external data was defined for this relation
- *surface_string* - original text that generated this relation
- *text_span* - string index in original text where surface_string can be found

**absa_relations_entities.csv**

This table is extending absa_relations.csv by providing list of entities
connected to evaluations in it.

- *doc_id* - id of review from reviews.csv
- *text_order* - specific text identifier
- *relation_id* - foreign key to absa_relations
- *entity_type* -
- *entity_name* -

**absa_evaluations.csv**

- *doc_id* - id of review from reviews.csv
- *text_order* - specific text identifier
- *evaluation_id* - absa evaluations output can rate multiple entities, this
  serves as foreign key to them
- *sentiment* - numeric value how positive/negative statement is
- *surface_string* - original text that was used to get this evaluation
- *text_span* - string index in original text where surface_string can be found

**absa_evaluations_entities.csv**

- *doc_id* - id of review from reviews.csv
- *text_order* - specific text identifier
- *evaluation_id* - foreign key to absa_evaluations
- *entity_type* -
- *entity_name* -


Aggregations
------------

Library provides set of functions to perform common aggregations over analysis
data. These are accessible from four subclasses of
:class:`ApiCallDataset <anacode.agg.aggregation.ApiCallDataset>` -
:class:`CategoriesDataset <anacode.agg.aggregation.CategoriesDataset>`,
:class:`ConceptsDataset <anacode.agg.aggregation.ConceptsDataset>`,
:class:`SentimentDataset <anacode.agg.aggregation.SentimentDataset>` and
:class:`ABSADataset <anacode.agg.aggregation.ABSADataset>`. To get any of those
you can use properties of :class:`DatasetLoader <anacode.agg.aggregation.DatasetLoader>`:
:func:`categories <anacode.agg.aggregation.DatasetLoader.categories>`,
:func:`concepts <anacode.agg.aggregation.DatasetLoader.concepts>`,
:func:`sentiments <anacode.agg.aggregation.DatasetLoader.sentiments>` and
:func:`absa <anacode.agg.aggregation.DatasetLoader.absa>`.

Here is an exhaustive list of aggregations (list also include some
non-aggregation methods) with usage examples that can be performed for
each api call dataset.


ConceptsDataset
'''''''''''''''

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

  Next two code samples demonstrate how percentages can change if concept_type
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
- :func:`make_idf_filter(threshold, concept_type='') <anacode.agg.aggregation.ConceptsDataset.make_idf_filter>`
- :func:`make_time_series(concepts, date_info, delta, interval=None) <anacode.agg.aggregation.ConceptsDataset.make_time_series>`

  You will have to provide date_info dictionary to this function to make it
  work. How to construct this dictionary depends on your data format so this
  library cannot help you with it, but here is how it should look:

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

  When you have your date_info generating time series is simple. Keep in mind
  that Stop time counts are not included in the total tick counts reported
  in the column, that is concepts counts that are included are
  `Start <= concept time < Stop`.

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

- :func:`word_cloud(path, size=(600, 350), background='white', colormap_name='Accent', max_concepts=200, stopwords=None, concept_type='', concept_filter=None, font=None) <anacode.agg.aggregation.ConceptsDataset.word_cloud>`

    You can use this to generate word cloud image to either file or to numpy
    ndarray - check doc strings for more info. Here is simple example
    of generating ndarray.

  .. code-block:: python

     >>> word_cloud_img = concepts.word_cloud(path=None)


CategoriesDataset
'''''''''''''''''

- :func:`main_topic() <anacode.agg.aggregation.CategoriesDataset.main_topic>`

  .. code-block:: python

     >>> categories.main_topic()

  .. parsed-literal::

     'auto'

SentimentsDataset
'''''''''''''''''

- :func:`average_sentiment() <anacode.agg.aggregation.SentimentDataset.average_sentiment>`

  .. code-block:: python

     >>> sentiments.average_sentiment()

  .. parsed-literal::

     0.43487262467141063


ABSADataset
'''''''''''

- :func:`entity_frequency(entity, entity_type='', normalize=False) <anacode.agg.aggregation.ABSADataset.entity_frequency>`

  See

  .. code-block:: python

     >>> absa.entity_frequency(['Oil', 'Buying'])

  .. parsed-literal::

     Entity
     Oil       62
     Buying    80
     Name: Count, dtype: int64

  Also read about :ref:`concept_frequency <concept_frequency_agg>` to see how
  entity_type and normalize can change output.

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
