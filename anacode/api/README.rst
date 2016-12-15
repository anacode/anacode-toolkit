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


After you have output from our API you can use one of the writer classes
to store it.


.. code-block:: python

    >>> from anacode.api import writers
    >>> csv_writer = writers.CSVWriter()
    >>> csv_writer.init()
    >>> csv_writer.write_concepts(concepts_result)
    >>> csv_writer.write_absa(absa_result)
    >>> csv_writer.close()


If you want to analyze bigger list of content you may want to use bulk analyzer.
It can be used with multiple threads to speed up analysis (you have to have
paid account to have access to multiple concurrent requests) and save results.

.. code-block:: python

    >>> from anacode.api import client
    >>> from anacode.api import writers
    >>> data = [
    >>>     ['Lenovo', 'Samsung'],
    >>>     ['Volkswagen', 'Audi'],
    >>> ]
    >>> auth = '<username>', '<password>'
    >>> df_writer = writers.DataFrameWriter()
    >>> with client.analyzer(auth, df_writer, threads=2) as api:
    >>>     for texts in data:
    >>>         api.concepts(texts)
    >>>         api.absa(texts)
    >>> print(df_writer['concepts'])