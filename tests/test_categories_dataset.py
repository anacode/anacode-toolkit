# -*- coding: utf-8 -*-
import pytest
import pandas as pd
from anacode.agg import aggregation as agg


@pytest.fixture
def frame_categories():
    cat_header = ['doc_id', 'text_order', 'category', 'probability']
    cats = pd.DataFrame([
        [0, 0, 'music', 0.1],
        [0, 0, 'law', 0.9],
        [0, 0, 'auto', 0.5],
        [0, 0, 'law', 0.5],
    ], columns=cat_header)
    return {'categories': cats}


@pytest.fixture
def dataset(frame_categories):
    return agg.CategoriesDataset(**frame_categories)


def test_empty_dataset_failure():
    dataset = agg.CategoriesDataset(None)
    with pytest.raises(agg.NoRelevantData):
        dataset.main_topic()


def test_main_topic(dataset):
    assert dataset.main_topic() == 'law'
