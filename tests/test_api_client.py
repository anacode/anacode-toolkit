import mock
import pytest
import requests
from urllib.parse import urljoin

from anacode.api import client
from anacode.api import codes


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
