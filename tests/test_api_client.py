# -*- coding: utf-8 -*-
import time
import mock
import pytest
import requests

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from anacode.api import client
from anacode.api import codes
from anacode.api import writers


def empty_response(*args, **kwargs):
    resp = requests.Response()
    resp._content = b'{}'
    resp.status_code = 200
    return resp


def empty_json(*args, **kwargs):
    return {}


@pytest.fixture
def auth():
    return 'user1', 'pass2'


@pytest.fixture
def api(auth):
    return client.AnacodeClient(auth)


@mock.patch('requests.post', empty_response)
def test_scrape_call(api, auth, mocker):
    mocker.spy(requests, 'post')
    api.scrape('http://chinese.portal.com.ch')
    assert requests.post.call_count == 1
    requests.post.assert_called_once_with(
        urljoin(client.ANACODE_API_URL, 'scrape/'),
        auth=auth, json={'url': 'http://chinese.portal.com.ch'})


@pytest.mark.parametrize('kwargs', [
    {},
    {'depth': 0},
    {'taxonomy': 'iab'},
    {'depth': 2, 'taxonomy': 'anacode'},
])
@mock.patch('requests.post', empty_response)
def test_categories_call(api, auth, mocker, kwargs):
    mocker.spy(requests, 'post')
    api.categories(['安全性能很好，很帅气。'], **kwargs)
    assert requests.post.call_count == 1
    json_data = {'texts': ['安全性能很好，很帅气。']}
    json_data.update(kwargs)
    requests.post.assert_called_once_with(
        urljoin(client.ANACODE_API_URL, 'categories/'),
        auth=auth, json=json_data)


@mock.patch('requests.post', empty_response)
def test_sentiment_call(api, auth, mocker):
    mocker.spy(requests, 'post')
    api.sentiment(['安全性能很好，很帅气。'])
    assert requests.post.call_count == 1
    requests.post.assert_called_once_with(
        urljoin(client.ANACODE_API_URL, 'sentiment/'),
        auth=auth, json={'texts': ['安全性能很好，很帅气。']})


@mock.patch('requests.post', empty_response)
def test_concepts_call(api, auth, mocker):
    mocker.spy(requests, 'post')
    api.concepts(['安全性能很好，很帅气。'])
    assert requests.post.call_count == 1
    requests.post.assert_called_once_with(
        urljoin(client.ANACODE_API_URL, 'concepts/'),
        auth=auth, json={'texts': ['安全性能很好，很帅气。']})


@mock.patch('requests.post', empty_response)
def test_absa_call(api, auth, mocker):
    mocker.spy(requests, 'post')
    api.absa(['安全性能很好，很帅气。'])
    assert requests.post.call_count == 1
    requests.post.assert_called_once_with(
        urljoin(client.ANACODE_API_URL, 'absa/'),
        auth=auth, json={'texts': ['安全性能很好，很帅气。']})


@pytest.mark.parametrize('code, call', [
    (codes.SCRAPE, 'scrape'),
    (codes.CATEGORIES, 'categories'),
    (codes.SENTIMENT, 'sentiment'),
    (codes.CONCEPTS, 'concepts'),
    (codes.ABSA, 'absa'),
])
def test_proper_method_call(api, code, call, mocker):
    text = ['安全性能很好，很帅气。']
    mock.patch('anacode.api.client.AnacodeClient.' + call, empty_json)
    mocker.spy(api, call)
    api.call((code, text))
    getattr(api, call).assert_called_once_with(text)


@pytest.mark.parametrize('call', [
    'categories', 'sentiment', 'scrape', 'absa', 'concepts',
])
@pytest.mark.parametrize('count,call_count', [
    (0, 0), (5, 0), (9, 0), (10, 1), (11, 1), (19, 1), (20, 2),
])
def test_should_start_analysis(api, mocker, call, count, call_count):
    text = ['安全性能很好，很帅气。']
    writer = writers.DataFrameWriter()
    writer.init()

    to_mock = 'anacode.api.client.AnacodeClient.' + call
    mock.patch(to_mock, empty_json)

    analyzer = client.Analyzer(api, writer, bulk_size=10)
    mocker.spy(analyzer, 'execute_tasks_and_store_output')

    for _ in range(count):
        analyzer.categories(text)

    assert analyzer.execute_tasks_and_store_output.call_count == call_count


@pytest.mark.parametrize('call, args', [
    ('categories', ([], )),
    ('sentiment', ([], )),
    ('scrape', ([], )),
    ('absa', ([], )),
    ('concepts', ([], )),
])
def test_analysis_execution(api, mocker, call, args):
    text = ['安全性能很好，很帅气。']
    writer = writers.DataFrameWriter()
    writer.init()

    to_mock = 'anacode.api.client.AnacodeClient.' + call
    mock.patch(to_mock, empty_json)
    mocker.spy(api, call)

    analyzer = client.Analyzer(api, writer, bulk_size=10)
    for _ in range(4):
        getattr(analyzer, call)(*args)

    analyzer.execute_tasks_and_store_output()
    assert getattr(api, call).call_count == 4


def time_consuming(*args, **kwargs):
    time.sleep(0.1)
    return {}


@mock.patch('anacode.api.client.AnacodeClient.categories', time_consuming)
def test_parallel_queries(api, mocker):
    text = ['安全性能很好，很帅气。']
    writer = writers.DataFrameWriter()
    writer.init()

    mocker.spy(api, 'categories')
    analyzer = client.Analyzer(api, writer, threads=4, bulk_size=4)

    start = time.time()
    with analyzer:
        for _ in range(4):
            analyzer.categories(text)
    stop = time.time()
    duration = stop - start
    assert abs(duration - 0.1) < 0.1
