# -*- coding: utf-8 -*-
import os
import time
import requests
from multiprocessing.dummy import Pool
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from anacode import codes
from anacode.api import writers


ANACODE_API_URL = os.getenv('ANACODE_API_URL', 'https://api.anacode.de/')


def _analysis(call_endpoint, auth, max_retries=3, **kwargs):
    while True:
        try:
            res = requests.post(call_endpoint, auth=auth, json=kwargs)
        except requests.RequestException:
            if max_retries == 0:
                raise
            else:
                max_retries -= 1
                time.sleep(0.1)
        else:
            return res


class AnacodeClient(object):
    """Makes posting data to server for analysis simpler by keeping user's auth,
    url to Anacode API server and also knows paths for analysis calls.

    To find out more about specific api calls and their output format refer to
    https://api.anacode.de/api-docs/calls.html.

    """
    def __init__(self, auth, base_url=ANACODE_API_URL):
        """Default value for base_url is taken from environment variable
        ANACODE_API_URL if set otherwise 'https://api.anacode.de/' is used.

        :param auth: User's username and password
        :type auth: tuple
        :param base_url: Anacode API server URL
        :type base_url: str
        """
        self.auth = auth
        self.base_url = base_url

    def scrape(self, link):
        """Use Anacode API to scrape link web page and return result.

        :param link: URL that should be scraped
        :type link: str
        :return: dict --
        """
        url = urljoin(self.base_url, '/scrape/')
        res = _analysis(url, self.auth, url=link)
        return res.json()

    def categories(self, texts, taxonomy=None, depth=None):
        """Use Anacode API to find out topic probabilities for given texts. You
        can optionally specify what taxonomy to use - defaults to anacode - and
        maximum number of nested results you want where 1 means flat list.

        :param texts: List of texts to categorize
        :type texts: list
        :param taxonomy: Choose from anacode and iab
        :type taxonomy: str
        :param depth: Maximum number of nested subtopics
        :type depth: int
        :return: dict --
        """
        data = {'texts': texts}
        if taxonomy is not None:
            data['taxonomy'] = taxonomy
        if depth is not None:
            data['depth'] = depth
        url = urljoin(self.base_url, '/categories/')
        res = _analysis(url, self.auth, **data)
        return res.json()

    def concepts(self, texts):
        """Use Anacode API to find concepts in list of texts

        :param texts: List of texts to find concepts in
        :type texts: list
        :return: dict --
        """
        url = urljoin(self.base_url, '/concepts/')
        res = _analysis(url, self.auth, texts=texts)
        return res.json()

    def sentiment(self, texts):
        """Use Anacode API to analyze sentiment for texts in list

        :param texts: List of texts for sentiment analysis
        :type texts: list
        :return: dict --
        """
        url = urljoin(self.base_url, '/sentiment/')
        res = _analysis(url, self.auth, texts=texts)
        return res.json()

    def absa(self, texts, external_entity_data=None):
        """Use Anacode API to perform Aspect Based Sentiment Analysis for given
        list of texts.

        :param texts: List of texts to perform fine grained sentiment analysis
        :type texts: list
        :param external_entity_data: Ensure that found evaluations will have
         relations with entities specified here
        :type external_entity_data: dict
        :return: dict --
        """
        url = urljoin(self.base_url, '/absa/')
        data = {'texts': texts}
        if external_entity_data is not None:
            data['external_entity_data'] = external_entity_data
        res = _analysis(url, self.auth, **data)
        return res.json()

    def call(self, task):
        """Given tuple of Anacode API analysis code and arguments for this
        analysis this will call appropriate method out of scrape, categories,
        concepts, sentiment or absa and return it's result

        :param task: Task definition tuple - (analysis code, analysis args)
        :type task: tuple
        :return: dict --
        """
        call, args = task[0], task[1:]

        if call == codes.SCRAPE:
            return self.scrape(*args)
        if call == codes.CATEGORIES:
            return self.categories(*args)
        if call == codes.CONCEPTS:
            return self.concepts(*args)
        if call == codes.SENTIMENT:
            return self.sentiment(*args)
        if call == codes.ABSA:
            return self.absa(*args)


class Analyzer(object):
    """This class makes querying with multiple threads and storing in other
    formats then list of json-s simple.

    """
    def __init__(self, client, writer, threads=1, bulk_size=100):
        """

        :param client: Will be used to post analysis to anacode api
        :type client: :class:`anacode.api.client.AnacodeClient`
        :param writer: Needs to implement init, close and write_bulk methods
         from Writer interface
        :type writer: :class:`anacode.api.writers.Writer`
        :param threads: Number of concurrent threads to use, defaults to 1
        :type threads: int
        :param bulk_size: How often should writer's write_bulk method be
         invoked, defaults to 100
        :type bulk_size: int
        """
        self.client = client
        self.threads = threads
        self.task_queue = []
        self.analyzed = []
        self.analyzed_types = []
        self.bulk_size = bulk_size
        self.writer = writer

    def __enter__(self):
        self.writer.init()
        return self

    def __exit__(self, type, value, traceback):
        self.execute_tasks_and_store_output()
        self.writer.close()

    def should_start_analysis(self):
        """Checks how many tasks are in queue and returns boolean indicating
        whether analysis should be performed.

        :return: bool -- True if analysis should happen now, False otherwise
        """
        return len(self.task_queue) >= self.bulk_size

    def analyze_bulk(self):
        """Performs bulk analysis. Will use :class:`multiprocessing.dummy.Pool`
        to post data to anacode api if number of threads is more than one.

        Analysis results are not returned, but cached internally.
        """
        if self.threads > 1:
            pool = Pool(self.threads)
            results = pool.map(self.client.call, self.task_queue)
        else:
            results = list(map(self.client.call, self.task_queue))
        self.analyzed.extend(results)
        self.analyzed_types.extend([t[0] for t in self.task_queue])
        self.task_queue = []

    def flush_analysis_data(self):
        """Writes all cached analysis results using writer."""
        self.writer.write_bulk(zip(self.analyzed_types, self.analyzed))
        self.analyzed_types = []
        self.analyzed = []

    def execute_tasks_and_store_output(self):
        self.analyze_bulk()
        self.flush_analysis_data()

    def scrape(self, link):
        """Dummy clone for
        :meth:`anacode.api.client.AnacodeClient.scrape`
        """
        self.task_queue.append((codes.SCRAPE, link))
        if self.should_start_analysis():
            self.execute_tasks_and_store_output()

    def categories(self, texts, taxonomy=None, depth=None):
        """Dummy clone for
        :meth:`anacode.api.client.AnacodeClient.categories`
        """
        self.task_queue.append((codes.CATEGORIES, texts, taxonomy, depth))
        if self.should_start_analysis():
            self.execute_tasks_and_store_output()

    def concepts(self, texts):
        """Dummy clone for
        :meth:`anacode.api.client.AnacodeClient.concepts`
        """
        self.task_queue.append((codes.CONCEPTS, texts))
        if self.should_start_analysis():
            self.execute_tasks_and_store_output()

    def sentiment(self, texts):
        """Dummy clone for
        :meth:`anacode.api.client.AnacodeClient.sentiment`
        """
        self.task_queue.append((codes.SENTIMENT, texts))
        if self.should_start_analysis():
            self.execute_tasks_and_store_output()

    def absa(self, texts, external_entity_data=None):
        """Dummy clone for
        :meth:`anacode.api.client.AnacodeClient.absa`
        """
        self.task_queue.append((codes.ABSA, texts, external_entity_data))
        if self.should_start_analysis():
            self.execute_tasks_and_store_output()


def analyzer(auth, writer, threads=1, bulk_size=100, base_url=ANACODE_API_URL):
    """Convenient function for initializing bulk analyzer and potentially
    temporary writer instance as well.

    :param auth: (username, password) tuple
    :type auth: tuple
    :param threads: Number of threads to use for http communication with server
    :type threads: int
    :param writer: Writer instance that will store analysis results or path to
     folder where csv-s should be saved or dictionary where data frames should
     be stored
    :type writer: :class:`anacode.api.writers.Writer`
    :type writer: dict
    :type writer: str
    :param bulk_size:
    :type bulk_size: int
    :param base_url: Anacode API server URL
    :type base_url: str
    :return: :class:`anacode.api.client.Analyzer` -- Bulk analyzer instance
    """
    if hasattr(writer, 'init') and hasattr(writer, 'close') and \
            hasattr(writer, 'write_bulk'):
        pass
    elif isinstance(writer, str) and os.path.isdir(writer):
        writer = writers.CSVWriter(writer)
    elif isinstance(writer, dict):
        writer = writers.DataFrameWriter(writer)
    else:
        raise ValueError('Writer type not understood. Please use path to file, '
                         'dictionary or object implementing writers.Writer '
                         'interface.')
    client = AnacodeClient(auth, base_url)
    return Analyzer(client, writer, threads, bulk_size=bulk_size)
