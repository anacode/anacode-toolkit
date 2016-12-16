You can call our rest api one by one using anacode.api.AnacodeClient class.

.. code-block:: python

    >>> from anacode.api import client
    >>> client = client.AnacodeClient(('<username>', '<password>'))
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
    >>>     ['轮毂还是挺喜欢的，依然不老',
    >>>      '外观保养的还算可以吧 PS门把手还带饰条的，当时已经很时尚了',
    >>>      '方方正正的后视镜，很大气吧 PS大灯也很犀利，没有一点泛黄的感觉哈',
    >>>      '后排的出风口，还有点烟器插座，人性化 PS中央扶手看起来很豪华',
    >>>      '还带灯的哦 PS后排这里也有出风口'],
    >>>     ['平时开百公里油耗15L，高速开百公里11L。',
    >>>      '操控一流，转向轻盈，刹车性能超好，有点人车合一的感觉！',
    >>>      '作为一辆王者之车，性价比还是挺高的！',
    >>>      '车内宽敞阔绰，载物空间丰富！'],
    >>> ]
    >>> auth = '<username>', '<password>'
    >>> df_writer = writers.DataFrameWriter()
    >>> with client.analyzer(auth, df_writer, threads=2) as api:
    >>>     for texts in data:
    >>>         api.concepts(texts)
    >>>         api.absa(texts)
    >>> print(df_writer.frames['concepts'])