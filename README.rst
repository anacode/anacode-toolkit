
Anacode aggregation library
***************************

This is the Python client library for `Anacode API <https://api.anacode.de>`_.
To get started you can check out READMEs in *api* and *agg* subfolders that
provide usage samples.


Installation
============

Library is published via PyPI so you can install it using pip:

.. code-block:: shell

    pip install anacode_toolkit


Python Version
==============

Currently we run tests against Python 2.7.12 and Python 3.5.2, but library
should work with Python 2.7+ and Python 3.3+ versions as well.


Dependencies
============

Library dependencies are:

* requests
* numpy
* pandas
* matplotlib
* seaborn
* wordcloud
* pillow

Test dependencies:

* pytest
* mock
* pytest-mock
* freezegun