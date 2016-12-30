
Anacode aggregation library
***************************

This is the Python client library for `Anacode API <https://api.anacode.de>`_.
To get started you can check out READMEs in
`api <https://github.com/anacode/anacode-toolkit/tree/master/anacode/api>`_
and
`agg <https://github.com/anacode/anacode-toolkit/tree/master/anacode/agg>`_
subfolders that provide usage examples.

If you want to learn more about API calls please read their
`documentation <https://api.anacode.de/api-docs/>`_.


Installation
============

Library is published via PyPI so you can install it using pip:

.. code-block:: shell

    pip install anacode_toolkit

You can also clone it's repository and install from source using setup.py
script:

.. code-block:: shell

    git clone https://github.com/anacode/anacode-toolkit.git
    cd anacode-toolkit
    python setup.py install


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


License
=======

Licensed under `BSD-3-Clause <https://github.com/anacode/anacode-toolkit/blob/master/LICENSE.txt>`_.
