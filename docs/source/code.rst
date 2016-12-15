Anacode Library Overview
************************

This library has three main goals.

 #. Help it's users to concurrently analyze their data with multiple http
    requests at the same time leveraging python's own :mod:`threading` module.
 #. Give users easy way to convert analysis results in json format to flat
    sql-like data structures.
 #. Provide *out-of-the-box* solutions for common analysis that can be done
    on analysis results.

First two goals are related to getting the data that you can perform analysis
on and this library helps you achieve this with it's :mod:`anacode.api` module.
Simple analysis tools are provided in :mod:`anacode.agg` module.


.. toctree::

    anacode_api
    anacode_agg
