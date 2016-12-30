# -*- coding: utf-8 -*-
import pytest
import pandas as pd
from anacode.api import writers
from anacode.agg import aggregation as agg


@pytest.mark.parametrize('call_type,dataset_name,data', [
    ('categories', 'categories', pd.DataFrame([1])),
    ('concepts', 'concepts', pd.DataFrame([2])),
    ('concepts', 'concepts_expressions', pd.DataFrame([3])),
    ('sentiments', 'sentiments', pd.DataFrame([4])),
    ('absa', 'absa_entities', pd.DataFrame([5])),
    ('absa', 'absa_normalized_texts', pd.DataFrame([6])),
    ('absa', 'absa_relations', pd.DataFrame([7])),
    ('absa', 'absa_relations_entities', pd.DataFrame([8])),
    ('absa', 'absa_evaluations', pd.DataFrame([9])),
    ('absa', 'absa_evaluations_entities', pd.DataFrame([0])),
])
def test_init_correct_assignments(call_type, dataset_name, data):
    dataset = agg.DatasetLoader(**{dataset_name: data})
    has_dataset_name = 'has_' + call_type
    dataset_attr_name = '_' + dataset_name
    assert getattr(dataset, dataset_attr_name, None) is data
    assert getattr(dataset, has_dataset_name, False)


@pytest.mark.parametrize('call_type,dataset_name,data', [
    ('categories', 'categories', pd.DataFrame([1])),
    ('concepts', 'concepts', pd.DataFrame([2])),
    ('concepts', 'concepts_expressions', pd.DataFrame([3])),
    ('sentiments', 'sentiments', pd.DataFrame([4])),
    ('absa', 'absa_entities', pd.DataFrame([5])),
    ('absa', 'absa_normalized_texts', pd.DataFrame([6])),
    ('absa', 'absa_relations', pd.DataFrame([7])),
    ('absa', 'absa_relations_entities', pd.DataFrame([8])),
    ('absa', 'absa_evaluations', pd.DataFrame([9])),
    ('absa', 'absa_evaluations_entities', pd.DataFrame([0])),
])
def test_init_api_dataset_creation(call_type, dataset_name, data):
    dataset_class_map = {
        'concepts': agg.ConceptsDataset,
        'categories': agg.CategoriesDataset,
        'sentiments': agg.SentimentDataset,
        'absa': agg.ABSADataset,
    }
    dataset = agg.DatasetLoader(**{dataset_name: data})
    api_dataset = getattr(dataset, call_type)
    assert isinstance(api_dataset, dataset_class_map[call_type])


@pytest.mark.parametrize('call_type,dataset_name,data', [
    ('categories', 'categories', pd.DataFrame([1])),
    ('concepts', 'concepts', pd.DataFrame([2])),
    ('concepts', 'concepts_expressions', pd.DataFrame([3])),
    ('sentiments', 'sentiments', pd.DataFrame([4])),
    ('absa', 'absa_entities', pd.DataFrame([5])),
    ('absa', 'absa_normalized_texts', pd.DataFrame([6])),
    ('absa', 'absa_relations', pd.DataFrame([7])),
    ('absa', 'absa_relations_entities', pd.DataFrame([8])),
    ('absa', 'absa_evaluations', pd.DataFrame([9])),
    ('absa', 'absa_evaluations_entities', pd.DataFrame([0])),
])
def test_init_api_dataset_creation_failure(call_type, dataset_name, data):
    all_calls = {'categories', 'concepts', 'sentiments', 'absa'}
    dataset = agg.DatasetLoader(**{dataset_name: data})
    for call in all_calls - {call_type}:
        with pytest.raises(agg.NoRelevantData):
            getattr(dataset, call)


@pytest.fixture
def csv_writer(tmpdir, concepts, sentiments, categories, absa):
    target = tmpdir.mkdir('target')
    csv_writer = writers.CSVWriter(str(target))
    csv_writer.init()
    csv_writer.write_categories(categories)
    csv_writer.write_sentiment(sentiments)
    csv_writer.write_concepts(concepts)
    csv_writer.write_absa(absa)
    csv_writer.close()
    return csv_writer


@pytest.fixture
def data_folder(csv_writer):
    return csv_writer.target_dir


@pytest.mark.parametrize('dataset_name,shape', [
    ('_categories', (60, 4)),
    ('_sentiments', (2, 4)),
    ('_concepts', (2, 6)),
    ('_concepts_expressions', (2, 4)),
    ('_absa_entities', (1, 6)),
    ('_absa_normalized_texts', (1, 3)),
    ('_absa_relations', (1, 9)),
    ('_absa_relations_entities', (2, 5)),
    ('_absa_evaluations', (2, 6)),
    ('_absa_evaluations_entities', (2, 5))
])
def test_data_load_from_path(data_folder, dataset_name, shape):
    dataset_loader = agg.DatasetLoader.from_path(data_folder)
    dataset = getattr(dataset_loader, dataset_name)
    assert dataset is not None
    assert dataset.shape == shape


@pytest.fixture
def frame_writer(concepts, sentiments, categories, absa):
    frame_writer = writers.DataFrameWriter()
    frame_writer.init()
    frame_writer.write_categories(categories)
    frame_writer.write_sentiment(sentiments)
    frame_writer.write_concepts(concepts)
    frame_writer.write_absa(absa)
    frame_writer.close()
    return frame_writer


@pytest.mark.parametrize('dataset_name,shape', [
    ('_categories', (60, 4)),
    ('_sentiments', (2, 4)),
    ('_concepts', (2, 6)),
    ('_concepts_expressions', (2, 4)),
    ('_absa_entities', (1, 6)),
    ('_absa_normalized_texts', (1, 3)),
    ('_absa_relations', (1, 9)),
    ('_absa_relations_entities', (2, 5)),
    ('_absa_evaluations', (2, 6)),
    ('_absa_evaluations_entities', (2, 5))
])
def test_data_load_from_lists(concepts, sentiments, categories, absa,
                              dataset_name, shape):
    dataset_loader = agg.DatasetLoader.from_lists(
        [concepts], [categories], [sentiments], [absa]
    )
    dataset = getattr(dataset_loader, dataset_name)
    assert dataset is not None
    assert dataset.shape == shape


@pytest.mark.parametrize('dataset_name,shape', [
    ('_categories', (60, 4)),
    ('_sentiments', (2, 4)),
    ('_concepts', (2, 6)),
    ('_concepts_expressions', (2, 4)),
    ('_absa_entities', (1, 6)),
    ('_absa_normalized_texts', (1, 3)),
    ('_absa_relations', (1, 9)),
    ('_absa_relations_entities', (2, 5)),
    ('_absa_evaluations', (2, 6)),
    ('_absa_evaluations_entities', (2, 5))
])
def test_data_load_from_csv_writer(csv_writer, dataset_name, shape):
    dataset_loader = agg.DatasetLoader.from_writer(csv_writer)
    dataset = getattr(dataset_loader, dataset_name)
    assert dataset is not None
    assert dataset.shape == shape


@pytest.mark.parametrize('dataset_name,shape', [
    ('_categories', (60, 4)),
    ('_sentiments', (2, 4)),
    ('_concepts', (2, 6)),
    ('_concepts_expressions', (2, 4)),
    ('_absa_entities', (1, 6)),
    ('_absa_normalized_texts', (1, 3)),
    ('_absa_relations', (1, 9)),
    ('_absa_relations_entities', (2, 5)),
    ('_absa_evaluations', (2, 6)),
    ('_absa_evaluations_entities', (2, 5))
])
def test_data_load_from_frame_writer(frame_writer, dataset_name, shape):
    dataset_loader = agg.DatasetLoader.from_writer(frame_writer)
    dataset = getattr(dataset_loader, dataset_name)
    assert dataset is not None
    assert dataset.shape == shape
