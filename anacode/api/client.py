import os
import time
import requests
from urllib.parse import urljoin
from multiprocessing.dummy import Pool

from anacode.api import writers
from anacode.api import codes


ANACODE_API_URL = os.getenv('ANACODE_API_URL', 'https://api.anacode.de/')


def analysis(call_endpoint, auth, max_retries=3, **kwargs):
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


class _Analyzer:
    def __init__(self, client: AnacodeClient, threads, writer, bulk_size=100):
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
        return self.task_queue >= self.bulk_size

    def analyze_bulk(self):
        if self.threads > 1:
            pool = Pool(self.threads)
            results = pool.map(self.client.call, self.task_queue)
        else:
            results = list(map(self.client.call, self.task_queue))
        self.analyzed.extend(results)
        self.analyzed_types.extend([t[0] for t in self.task_queue])
        self.task_queue = []

    def flush_analysis_data(self):
        self.writer.write_bulk(zip(self.analyzed_types, self.analyzed))
        self.analyzed_types = []
        self.analyzed = []

    def execute_tasks_and_store_output(self):
        self.analyze_bulk()
        self.flush_analysis_data()

    def scrape(self, link):
        self.task_queue.append((codes.SCRAPE, link))
        if self.should_start_analysis():
            self.execute_tasks_and_store_output()

    def categories(self, texts, taxonomy, depth):
        self.task_queue.append((codes.CATEGORIES, texts, taxonomy, depth))
        if self.should_start_analysis():
            self.execute_tasks_and_store_output()

    def concepts(self, texts):
        self.task_queue.append((codes.CONCEPTS, texts))
        if self.should_start_analysis():
            self.execute_tasks_and_store_output()

    def sentiment(self, texts):
        self.task_queue.append((codes.SENTIMENT, texts))
        if self.should_start_analysis():
            self.execute_tasks_and_store_output()

    def absa(self, texts):
        self.task_queue.append((codes.ABSA, texts))
        if self.should_start_analysis():
            self.execute_tasks_and_store_output()


class AnacodeClient:
    def __init__(self, username, password, base_url=ANACODE_API_URL):
        self.auth = (username, password)
        self.base_url = base_url

    def scrape(self, link):
        url = urljoin(self.base_url, '/scrape/')
        res = analysis(url, self.auth, url=link)
        return res.json()

    def categories(self, texts, taxonomy, depth):
        data = {texts: texts}
        if taxonomy is not None:
            data['taxonomy'] = taxonomy
        if depth is not None:
            data['depth'] = depth
        url = urljoin(self.base_url, '/categories/')
        res = analysis(url, self.auth, **data)
        return res.json()

    def concepts(self, texts):
        url = urljoin(self.base_url, '/concepts/')
        res = analysis(url, self.auth, texts=texts)
        return res.json()

    def sentiment(self, texts):
        url = urljoin(self.base_url, '/sentiment/')
        res = analysis(url, self.auth, texts=texts)
        return res.json()

    def absa(self, texts):
        url = urljoin(self.base_url, '/absa/')
        res = analysis(url, self.auth, texts=texts)
        return res.json()

    def call(self, task: tuple):
        call, args = task[0], task[1:]

        if call == AnacodeClient.SCRAPE:
            return self.scrape(*args)
        if call == AnacodeClient.CATEGORIES:
            return self.categories(*args)
        if call == AnacodeClient.CONCEPTS:
            return self.concepts(*args)
        if call == AnacodeClient.SENTIMENT:
            return self.sentiment(*args)
        if call == AnacodeClient.ABSA:
            return self.absa(*args)

    def analyzer(self, threads=1, writer=None):
        if writer is None:
            writer = writers.CSVWriter('.')
        return _Analyzer(self, threads, writer)
