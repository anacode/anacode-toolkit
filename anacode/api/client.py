# -*- coding: utf-8 -*-
import os
import time
import json
import requests
from multiprocessing.dummy import Pool
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from anacode import codes
from anacode.api import writers


MAX_REQUEST_BYTES_SIZE = 1000 ** 2
ANACODE_API_URL = os.getenv('ANACODE_API_URL', 'https://api.anacode.de/')


def _analysis(call_endpoint, auth, max_retries=3, **kwargs):
    headers = {'Authorization': 'Token %s' % auth,
               'Accept': 'application/json'}
    while True:
        try:
            res = requests.post(call_endpoint, headers=headers, json=kwargs)
        except requests.RequestException:
            if max_retries == 0:
                raise
            else:
                max_retries -= 1
                time.sleep(0.1)
        else:
            return res


def optimal_requests(data, analyses, max_size=MAX_REQUEST_BYTES_SIZE):
    """Yields text lists from `data` that will fit into maximum request size.
    Will not reorder texts - they will be send to server in order they appear
    in `data`. You also need to provide list of `analyses` that you will be
    calling on returned texts so that final json size may be computed properly.
    
    :param data: Iterable with chinese texts
    :param analyses: List of analyses to perform. Can only have 'concepts',
     'categories', 'sentiment' and 'absa' values.
    :param max_size: Request body maximum size. Json with encoded text and 
     analysis list has to fit into this size.
    :return: Generator yielding lists of chinese texts
    """
    analyses = set(analyses)
    extra = analyses - {'concepts', 'categories', 'sentiment', 'absa'}
    if len(extra) > 0:
        raise ValueError('No support for {} analyses'.format(', '.join(extra)))
    analyses = list(analyses)

    json_temp = json.dumps({'text': ['%%mark%%'], 'analyses': analyses})
    start, stop = json_temp.split('"%%mark%%"')
    empty_length = len(start) + len(stop)

    result = []
    length = empty_length
    for text in data:
        new_string = json.dumps(text)
        current_diff = max_size - length
        if current_diff < len(new_string) + 1:
            yield result
            result = []
            length = empty_length

        length += len(new_string) + 1
        result.append(text)

    if result:
        yield result


class AnacodeClient(object):
    """Makes posting data to server for analysis simpler by storing user's auth,
    the URL of the Anacode API server and paths for analysis calls.

    To find out more about specific API calls and analyses and their output format, please refer to
    https://api.anacode.de/api-docs/calls.html.

    """
    def __init__(self, auth, base_url=ANACODE_API_URL):
        """Default value for base_url is taken from environment variable
        ANACODE_API_URL if set; otherwise, 'https://api.anacode.de/' is used.

        :param auth: User's token
        :type auth: str
        :param base_url: Anacode API server URL
        :type base_url: str
        """
        self.auth = auth
        self.base_url = base_url

    def scrape(self, link):
        """Use Anacode API's scrape call to scrape page from Web URL and return result.

        :param link: URL that should be scraped
        :type link: str
        :return: dict --
        """
        url = urljoin(self.base_url, '/scrape/')
        res = _analysis(url, self.auth, url=link)
        return res.json()

    def analyze(self, texts, analyses, external_entity_data=None,
                single_document=False):
        """Use Anacode API to perform specified linguistic analysis on texts.
        Please consult https://api.anacode.de/api-docs/calls.html for more
        details and better understanding of parameters.

        :param texts: List of texts to analyze
        :param analyses: List of analysss to perform. Can contain 'categories',
         'concepts', 'sentiment' and 'absa'
        :param external_entity_data: Provide additional entities to relate to
         sentiment evaluation.
        :param single_document: Makes API treat texts as paragraphs of one
         document instead of treating them as separate documents
        :type single_document: bool
        :return: dict --
        """
        url = urljoin(self.base_url, '/analyze/')
        data = {'texts': texts, 'analyses': analyses}
        if external_entity_data is not None:
            data['absa'] = {'external_entity_data': external_entity_data}
        if single_document:
            data['single_document'] = True
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
        if call == codes.ANALYZE:
            return self.analyze(*args)


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

    def analyze(self, texts, analyses, external_entity_data=None,
                single_document=False):
        """Dummy clone for
        :meth:`anacode.api.client.AnacodeClient.analyze`"""
        self.task_queue.append((codes.ANALYZE, texts, analyses,
                                external_entity_data, single_document))
        if self.should_start_analysis():
            self.execute_tasks_and_store_output()


def analyzer(auth, writer, threads=1, bulk_size=100, base_url=ANACODE_API_URL):
    """Convenient function for initializing bulk analyzer and potentially
    temporary writer instance as well.

    :param auth: User's token string
    :type auth: str
    :param threads: Number of threads to use for https communication with server
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
