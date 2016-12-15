You can call our rest api one by one using anacode.api.AnacodeClient class.

.. code-block:: python

    >>> from anacode.api import client
    >>> client = client.AnacodeClient('<username>', '<password>')
    >>> concepts_result = client.concepts(texts=['Samsung'])
    >>> print(concepts_result)
    Output of concepts call
    >>> absa_result = client.absa(texts=['Lenovo'])
    >>> print(absa_result)
    Output of absa call


After you have output from our API you can use one of writer class to store it.


.. code-block:: python

    >>> from anacode.api import writers
    >>> csv_writer = writers.CSVWriter()
    >>> csv_writer.init()
    >>> csv_writer.write_concepts(concepts_result)
    >>> csv_writer.write_absa(absa_result)
    >>> csv_writer.close()


If you want to analyze not just a string but a big list content you want to use
AnacodeClient's analyzer method. You can use it with multiple threads to speed
up analysis (you have to have paid account to have access to multiple threads)
and save results to appropriate csv files automatically.

.. code-block:: python

    >>> from anacode.api import client
    >>> from anacode.api import writers
    >>> data = [
    >>>     ['Lenovo', 'Samsung'],
    >>>     ['Volkswagen', 'Audi'],
    >>> ]
    >>> client = client.AnacodeClient('<username>', '<password>')
    >>> csv_writer = writers.CSVWriter()
    >>> with client.analyzer(threads=2, csv_writer) as analyzer:
    >>>     for texts in data:
    >>>         analyzer.concepts(texts)
    >>>         analyzer.absa(texts)