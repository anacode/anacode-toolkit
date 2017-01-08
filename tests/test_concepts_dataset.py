# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
import pandas as pd
from anacode.agg import aggregation as agg


@pytest.fixture
def frame_concepts():
    con_header = ['doc_id', 'text_order', 'concept', 'freq', 'relevance_score',
                  'concept_type']
    exp_header = ['doc_id', 'text_order', 'concept', 'expression']
    cons = pd.DataFrame([
        [0, 0, 'Lenovo', 1, 1.0, 'brand'],
        [0, 1, 'Samsung', 1, 1.0, 'brand'],
        [0, 1, 'Lenovo', 2, 1.0, 'brand'],
        [0, 1, 'VisualAppearance', 2, 1.0, 'feature'],
    ], columns=con_header)
    exps = pd.DataFrame([
        [0, 0, 'Lenovo', 'lenovo'],
        [0, 1, 'Samsung', 'samsung'],
    ], columns=exp_header)
    return {'concepts': cons, 'expressions': exps}


@pytest.fixture
def dataset(frame_concepts):
    return agg.ConceptsDataset(**frame_concepts)


@pytest.mark.parametrize('aggreg_func, args', [
    ('concept_frequency', ['lenovo']),
    ('most_common_concepts', []),
    ('least_common_concepts', []),
    ('co_occurring_concepts', ['lenovo']),
])
def test_empty_dataset_failure(aggreg_func, args):
    dataset = agg.ConceptsDataset(None, None)
    with pytest.raises(agg.NoRelevantData):
        func = getattr(dataset, aggreg_func)
        func(*args)


@pytest.mark.parametrize('concept,frequency', [
    ('Lenovo', [3]),
    ('Samsung', [1]),
    (['Lenovo', 'Samsung'], [3, 1]),
    ('NotHere', [0]),
    (['Lenovo', 'NotHere'], [3, 0]),
])
def test_concept_frequency(dataset, concept, frequency):
    assert (dataset.concept_frequency(concept) == frequency).all()


@pytest.mark.parametrize('concept,frequency', [
    ('Lenovo', [3.0/6.0]),
    ('Samsung', [1.0/6]),
    (['Lenovo', 'Samsung'], [3.0/6.0, 1.0/6.0]),
    ('NotHere', [0.0]),
    (['Lenovo', 'NotHere'], [3.0/6.0, 0.0]),
])
def test_concept_frequency_normalized(dataset, concept, frequency):
    result = dataset.concept_frequency(concept, normalize=True)
    assert (result == frequency).all()


@pytest.mark.parametrize('concept,frequency', [
    ('Lenovo', [3]),
    ('Samsung', [1]),
    (['Lenovo', 'Samsung'], [3, 1]),
    ('NotHere', [0]),
    (['Lenovo', 'NotHere'], [3, 0]),
])
def test_concept_frequency_brand(dataset, concept, frequency):
    result = dataset.concept_frequency(concept, concept_type='brand')
    assert (result == frequency).all()


@pytest.mark.parametrize('concept,frequency', [
    ('Lenovo', [3.0/4]),
    ('Samsung', [1.0/4]),
    (['Lenovo', 'Samsung'], [3.0/4, 1.0/4]),
    ('NotHere', [0.0]),
    (['Lenovo', 'NotHere'], [3.0/4, 0.0]),
])
def test_concept_frequency_brand_normalized(dataset, concept, frequency):
    result = dataset.concept_frequency(concept, 'brand', True)
    assert (result == frequency).all()


@pytest.mark.parametrize('args,concepts,counts', [
    ([1], ['Lenovo'], [3]),
    ([2], ['Lenovo', 'VisualAppearance'], [3, 2]),
    ([2, 'brand'], ['Lenovo', 'Samsung'], [3, 1])
])
def test_most_common_concepts(dataset, args, concepts, counts):
    result = dataset.most_common_concepts(*args)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == concepts
    assert (result.values == counts).all()


@pytest.mark.parametrize('args,concepts,freqs', [
    ([1], ['Lenovo'], [3.0/6]),
    ([2], ['Lenovo', 'VisualAppearance'], [3.0/6, 2.0/6]),
    ([2, 'brand'], ['Lenovo', 'Samsung'], [3.0/4, 1.0/4])
])
def test_most_common_concepts_normalized(dataset, args, concepts, freqs):
    result = dataset.most_common_concepts(*args, normalize=True)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == concepts
    assert (result.values == freqs).all()


@pytest.mark.parametrize('args,concepts, freqs', [
    ([1], ['Samsung'], [1]),
    ([2], ['Samsung', 'VisualAppearance'], [1, 2]),
    ([10, 'feature'], ['VisualAppearance'], [2])
])
def test_least_common_concepts(dataset, args, concepts, freqs):
    result = dataset.least_common_concepts(*args)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == concepts
    assert (result.values == freqs).all()


@pytest.mark.parametrize('args,concepts, freqs', [
    ([1], ['Samsung'], [1.0/6]),
    ([2], ['Samsung', 'VisualAppearance'], [1.0/6, 2.0/6]),
    ([10, 'feature'], ['VisualAppearance'], [2.0/2])
])
def test_least_common_concepts_normalized(dataset, args, concepts, freqs):
    result = dataset.least_common_concepts(*args, normalize=True)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == concepts
    assert (result.values == freqs).all()


@pytest.mark.parametrize('args,concepts', [
    (['lenovo', 1], ['VisualAppearance']),
    (['Lenovo', 1], ['VisualAppearance']),
    (['Lenovo', 1, 'brand'], ['Samsung']),
    (['VisualAppearance', 2], ['Lenovo', 'Samsung']),
])
def test_co_occurring_concepts(dataset, args, concepts):
    result = dataset.co_occurring_concepts(*args)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == concepts


def test_pil_image_word_cloud_throws_no_error(dataset):
    word_cloud_image = dataset.word_cloud(None)
    assert isinstance(word_cloud_image, np.ndarray)


def test_word_cloud_save_throws_no_error(dataset, tmpdir):
    target = tmpdir.mkdir('target')
    cloud_path = os.path.join(str(target), 'test.png')
    dataset.word_cloud(cloud_path)
    assert os.path.isfile(cloud_path)


@pytest.fixture
def idf_dataset():
    con_header = ['doc_id', 'text_order', 'concept', 'freq', 'relevance_score',
                  'concept_type']
    concepts = pd.DataFrame([
        [0, 0, 'Lenovo', 1, 1.0, 'brand'],
        [0, 0, 'BMW', 1, 1.0, 'brand'],
        [1, 0, 'Samsung', 1, 1.0, 'brand'],
        [1, 0, 'Lenovo', 1, 1.0, 'brand'],
        [2, 0, 'Lenovo', 2, 1.0, 'brand'],
        [2, 1, 'VisualAppearance', 2, 1.0, 'feature'],
        [3, 0, 'VisualAppearance', 2, 1.0, 'feature'],
    ], columns=con_header)
    return agg.ConceptsDataset(concepts, None)


def test_text_collection_contain_appropriate_concepts(idf_dataset):
    corpus = idf_dataset.nltk_textcollection()
    assert 'Lenovo' in corpus
    assert 'BMW' in corpus
    assert 'Samsung' in corpus
    assert 'VisualAppearance' in corpus
    assert 'Wheel' not in corpus


def test_text_collection_creation_no_concept_in_doc(idf_dataset):
    corpus = idf_dataset.nltk_textcollection('brand')
    assert 'Lenovo' in corpus
    assert 'BMW' in corpus
    assert 'Samsung' in corpus
    assert 'VisualAppearance' not in corpus


def test_text_collection_idf_is_correct(idf_dataset):
    corpus = idf_dataset.nltk_textcollection()
    assert corpus.idf('Lenovo') < corpus.idf('Samsung')
    assert corpus.idf('Lenovo') < corpus.idf('BMW')
    assert corpus.idf('Lenovo') < corpus.idf('VisualAppearance')

    assert corpus.idf('Samsung') == corpus.idf('BMW')
    assert corpus.idf('VisualAppearance') < corpus.idf('Samsung')


@pytest.fixture
def idf_filter(idf_dataset):
    corpus = idf_dataset.nltk_textcollection()
    threshold = corpus.idf('VisualAppearance')
    return idf_dataset.make_idf_filter(threshold)


@pytest.mark.parametrize('word,result', [
    ('VisualAppearance', True),
    ('Lenovo', False),
    ('Samsung', True),
    ('BMW', True),
])
def test_concept_idf_filter(idf_filter, word, result):
    assert idf_filter(word) is result


@pytest.mark.parametrize('agg,args,name', [
    ('concept_frequency', ['lenovo'], 'Concept'),
    ('concept_frequency', ['lenovo', 'brand'], 'Brand'),
    ('concept_frequency', ['VisualAppearance', 'feature'], 'Feature'),
    ('most_common_concepts', [1], 'Concept'),
    ('most_common_concepts', [1, 'brand'], 'Brand'),
    ('most_common_concepts', [1, 'feature'], 'Feature'),
    ('least_common_concepts', [1], 'Concept'),
    ('least_common_concepts', [1, 'brand'], 'Brand'),
    ('least_common_concepts', [1, 'feature'], 'Feature'),
    ('co_occurring_concepts', ['Lenovo', 1], 'Concept'),
    ('co_occurring_concepts', ['Lenovo', 1, 'brand'], 'Brand'),
    ('co_occurring_concepts', ['BackSeats', 1, 'feature'], 'Feature'),
])
def test_concept_result_name(idf_dataset, agg, args, name):
    result = getattr(idf_dataset, agg)(*args)
    assert result.index.name == name
