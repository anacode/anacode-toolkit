# -*- coding: utf-8 -*-
import mock
import pytest
import pandas as pd
from matplotlib.axes import Axes
from anacode.agg import aggregation as agg
from anacode.agg import plotting as plt


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
        dataset.main_category()


def test_main_topic(dataset):
    assert dataset.main_category() == 'law'


def test_categories(dataset):
    cats = dataset.categories()
    assert cats.tolist() == [0.7, 0.5, 0.1]
    assert cats.index.tolist() == ['law', 'auto', 'music']


def test_categories_direct_plot(dataset):
    plot = plt.piechart(dataset.categories())
    assert isinstance(plot, Axes)


def test_categories_plot(dataset):
    with mock.patch.object(plt, 'piechart') as obj:
        plot = plt.plot(dataset.categories())
    obj.assert_called_once()
