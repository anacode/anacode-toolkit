# -*- coding: utf-8 -*-
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
        [0, 1, 'VisualAppearance', 2, 1.0, 'feature_subjective'],
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
    ('Lenovo', 3),
    ('lenovo', 3),
    ('Samsung', 1),
    ('samsung', 1),
])
def test_concept_frequency(dataset, concept, frequency):
    assert dataset.concept_frequency(concept) == frequency


@pytest.mark.parametrize('args,concepts', [
    ([1], ['Lenovo']),
    ([2], ['Lenovo', 'VisualAppearance']),
    ([2, 'brand'], ['Lenovo', 'Samsung'])
])
def test_most_common_concepts(dataset, args, concepts):
    result = dataset.most_common_concepts(*args)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == concepts


@pytest.mark.parametrize('args,concepts', [
    ([1], ['Samsung']),
    ([2], ['Samsung', 'VisualAppearance']),
    ([10, 'feature_'], ['VisualAppearance'])
])
def test_least_common_concepts(dataset, args, concepts):
    result = dataset.least_common_concepts(*args)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == concepts


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
