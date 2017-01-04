You can use aggregations to find "basic" insights about your text data.

Data loading is done using `anacode.agg.DatasetLoader`. You can load data
either directly with `pandas.DataFrame` instances given to constructor or
you can make use of convenient functions to load data from python lists, folder
with appropriate csv-s or from `anacode.api.writers.Writer` instance.


To load data from csv-s in working directory you can use `from_path` method of
`anacode.agg.DatasetLoader`.

..  code-block:: python

    >>> from anacode.agg import DatasetLoader
    >>> data = DatasetLoader.from_path('.')


To load data directly from list of outputs from AnacodeAPI, you can use
`from_lists` method and pass it lists for concepts, categories, sentiments and
absa dictionaries.


..  code-block:: python

    >>> from anacode.agg import DatasetLoader
    >>> data = DatasetLoader.from_lists(concepts=concepts_list, absa=absa_list)


Once you have loaded analyzed dataset you can analyze specific call results.
For example you can find 10 most commonly used concepts in your dataset.

.. code-block:: python

    >>> data.concepts.most_common_concepts(n=10)


To visualize these 10 most common concepts as a horizontal bar chart you can use
`plotting.plot` method:

.. code-block:: python

    >>> from anacode.agg import plotting
    >>> common_concepts = data.concepts.most_common_concepts(n=10)
    >>> plotting.plot(common_concepts)


Here is list of all possible analysis you can do with this library. Those that
can be visualized are marked with asterix:

- concepts:
    - concept_frequency
    - most_common_concepts *
    - least_common_concepts *
    - co_occurring_concepts *
- categories:
    - main_topic
- sentiments:
    - average_sentiment
- absa:
    - most_common_entities *
    - least_common_entities *
    - co_occurring_entities *
    - best_rated_entities *
    - worst_rated_entities *
    - entity_texts
    - entity_sentiment


If you want to access underlying pandas DataFrame objects, you can do so by
subscripting DatasetLoader instance with "categories", "concepts",
"concepts_expressions", "sentiments", "absa_entities", "absa_normalized_texts",
"absa_relations", "absa_relations_entities", "absa_evaluations" and
"absa_evaluations_entities" strings like this:

.. code-block:: python

    >>> relation_entities = dataset['absa_relations_entities']

