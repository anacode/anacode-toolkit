# -*- coding: utf-8 -*-
import pytest
import pandas as pd
from anacode.agg import aggregation as agg


@pytest.fixture
def frame_absa():
    ent_header = ['doc_id', 'text_order', 'entity_name', 'entity_type',
                  'surface_string', 'text_span']
    ents = pd.DataFrame([
        [0, 0, 'Lenovo', 'brand', 'lenovo', '4-9'],
        [0, 1, 'VisualAppearance', 'feature_subjective', 'looks', '0-4'],
        [0, 1, 'Samsung', 'brand', 'samsung', '15-21'],
        [0, 1, 'Lenovo', 'brand', 'Lenovo', '154-159'],
        [0, 1, 'Lenovo', 'brand', 'Lenovo', '210-215'],
        [0, 1, 'VisualAppearance', 'feature_subjective', 'looks', '30-34'],
    ], columns=ent_header)
    texts_header = ['doc_id', 'text_order', 'normalized_text']
    texts = pd.DataFrame([
        [0, 0, 'Hey lenovo'],
        [0, 1, '安全性能很好，很帅气。'],
    ], columns=texts_header)
    rel_header = ['doc_id', 'text_order', 'relation_id', 'opinion_holder',
                  'restriction', 'sentiment', 'is_external', 'surface_string',
                  'text_span']
    rels = pd.DataFrame([], columns=rel_header)
    rel_ent_header = ['doc_id', 'text_order', 'relation_id',
                      'entity_type', 'entity_name']
    rel_entities = pd.DataFrame([], columns=rel_ent_header)
    eval_header = ['doc_id', 'text_order', 'evaluation_id', 'sentiment',
                   'surface_string', 'text_span']
    evals = pd.DataFrame([
        [0, 0, 0, 2.0, '安全', '0-2'],
        [0, 0, 1, 3.5, '很帅气', '7-10'],
        [0, 1, 0, 1.0, '安全', '0-2'],
        [0, 1, 1, 2.5, '很帅气', '7-10'],
    ], columns=eval_header)
    eval_ents_header = ['doc_id', 'text_order', 'evaluation_id', 'entity_type',
                        'entity_name']
    eval_entities = pd.DataFrame([
        [0, 0, 0, 'feature_quantitative', 'Safety'],
        [0, 0, 1, 'feature_subjective', 'VisualAppearance'],
        [0, 1, 0, 'feature_quantitative', 'Safety'],
        [0, 1, 1, 'feature_subjective', 'VisualAppearance']
    ], columns=eval_ents_header)
    return {
        'entities': ents, 'normalized_texts': texts,
        'relations': rels, 'relations_entities': rel_entities,
        'evaluations': evals, 'evaluations_entities': eval_entities
    }


@pytest.fixture
def dataset(frame_absa):
    return agg.ABSADataset(**frame_absa)


@pytest.mark.parametrize('aggreg_func, args', [
    ('most_common_entities', []),
    ('least_common_entities', []),
    ('co_occurring_entities', ['lenovo']),
    ('best_rated_entities', []),
    ('worst_rated_entities', []),
    ('entity_texts', ['lenovo']),
    ('entity_sentiment', ['lenovo']),
])
def test_empty_dataset_failure(aggreg_func, args):
    dataset = agg.ABSADataset(None, None, None, None, None, None)
    with pytest.raises(agg.NoRelevantData):
        func = getattr(dataset, aggreg_func)
        func(*args)


@pytest.mark.parametrize('args,entities', [
    ([1], ['Lenovo']),
    ([2], ['Lenovo', 'VisualAppearance']),
    ([2, 'brand'], ['Lenovo', 'Samsung'])
])
def test_most_common_concepts(dataset, args, entities):
    result = dataset.most_common_entities(*args)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == entities


@pytest.mark.parametrize('args,entities', [
    ([1], ['Samsung']),
    ([2], ['Samsung', 'VisualAppearance']),
    ([10, 'feature_'], ['VisualAppearance'])
])
def test_least_common_concepts(dataset, args, entities):
    result = dataset.least_common_entities(*args)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == entities


@pytest.mark.parametrize('args,entities', [
    (['lenovo', 1], ['VisualAppearance']),
    (['Lenovo', 1], ['VisualAppearance']),
    (['Lenovo', 1, 'brand'], ['Samsung']),
    (['VisualAppearance', 2], ['Lenovo', 'Samsung']),
])
def test_co_occurring_concepts(dataset, args, entities):
    result = dataset.co_occurring_entities(*args)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == entities


@pytest.mark.parametrize('args,entities', [
    ([1], ['VisualAppearance']),
    ([1, 'feature_quantitative'], ['Safety']),
    ([2], ['VisualAppearance', 'Safety'])
])
def test_best_rated_entities(dataset, args, entities):
    result = dataset.best_rated_entities(*args)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == entities


@pytest.mark.parametrize('args,entities', [
    ([1], ['Safety']),
    ([1, 'feature_subjective'], ['VisualAppearance']),
    ([2], ['Safety', 'VisualAppearance'])
])
def test_worst_rated_entities(dataset, args, entities):
    result = dataset.worst_rated_entities(*args)
    assert isinstance(result, pd.Series)
    assert result.index.tolist() == entities


@pytest.mark.parametrize('entity,texts', [
    ('Safety', []),
    ('VisualAppearance', ['安全性能很好，很帅气。']),
    ('visualappearance', ['安全性能很好，很帅气。']),
])
def test_entity_texts(dataset, entity, texts):
    result = dataset.entity_texts(entity)
    assert isinstance(result, list)
    assert result == texts


@pytest.mark.parametrize('entity,sentiment', [
    ('Safety', 1.5),
    ('safety', 1.5),
    ('VisualAppearance', 3.0),
])
def test_entity_sentiment(dataset, entity, sentiment):
    result = dataset.entity_sentiment(entity)
    assert result == sentiment
