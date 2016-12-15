What can this do?

 - most/least popular concepts
 - aggregate document sentiment
 - find co-occuring entities
 - best/worst rated features



 #. Are we ok asking user to join tables himself for some of agg functions?
 #.



To load parsed data in your working directory simply run `load` method. `load`
takes one optional positional argument that is path to folder with analyzed
data.

.. code-block:: python

    >>> from anacode.agg import load
    >>> data = load()


With analyzed data loaded like this you can do three things with this library.
You can filter documents you want to use, compute mean and std for quantitative
variables and count categorical variables. This library uses *pandas* internally
and you can get view of original pandas dataframe that corresponds to what you
did with our library any time by getting `dataframe` attribute.

Here is a list of resources that are supported by this framework:

- categories
- concepts
- concepts_expressions
- sentiment

To access these resources simply access them as attributes from loaded data.

.. code-block:: python

    >>> data.sentiment
    #Pandas dataframe representation of sentiment table:
    doc_id  positive    negative
    0       0.2         0.8
    1       0.9         0.1
    2       0.9         0.1


Trying to load dataset that is not in the folder will raise an error.

.. code-block:: python

    >>> data.categories
    ValueError: "categories.csv is not in /home/<username>/ folder"


To get statistics for quantitative variable you can call `stats` method and give
it name of column you want analyzed.

.. code-block:: python

    >>> data.sentiment.stats('positive')
    0.66666666666666663, 0.32998316455372217


To find most used concepts for the dataset you need to load concepts_expressions
data and count concept occurrences:

.. code-block:: python

    >>> data.concepts_expressions.count('concept')
    #Pandas dataframe representation of aggregated data
    concept                 count
    VisualAppearance        5
    BackSeats               23
    Battery                 1
    SteeringWheel           121


To analyze only certain part of data we supply you with `filter` method. It will
efficiently limit scope of operations that you use on returned object.

.. code-block:: python

    >>> data.concepts_expressions.filter(concept='VisualAppearance').\
    >>>     count('concept')
    #Pandas dataframe representation of aggregated data
    concept                 count
    VisualAppearance        5


So what's the difference?

.. code-block:: python

    >>> concepts[concepts['concept'] == 'VisualAppearance']['concept'].value_counts()
    >>> concepts.filter(concept='VisualAppearance').count('concept)

    >>> sentiment.stats()
    >>> sentiment.describe()


What about just "helper" functions, not a full blown library?

There can be a function for getting set of most common concepts.

.. code-block:: python

    >>> bmw7_features = review_concepts[bmw7 & features].groupby('concept').agg({'freq': 'sum'})
    >>> bmw7_popular_features_order = bmw7_features.sort_values(by='freq', ascending=False)[:15].index.tolist()
    >>> bmw7_popular_features = set(bmw7_popular_features_order)
    >>> bmw7_popular_features = most_common_concepts(review_concepts[bmw7 & features], 15)


