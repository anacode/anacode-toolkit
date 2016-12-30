# -*- coding: utf-8 -*-
import os
import random

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager

from PIL import Image
from wordcloud import WordCloud, STOPWORDS

from anacode import codes


def generate_color_func(colormap_name):
    """Creates color_func that picks random color from matplotlib's colormap
    *colormap_name* when called.

    :param colormap_name: Name of matplotlib's colormap
    :type colormap_name: str
    :return: callable -- color_func that returns random color from colormap
    """
    def color_func(word, font_size, position, orientation, random_state=None,
                   **kwargs):
        color = plt.get_cmap(colormap_name)(random.random())
        color = map(lambda val: int(round(val * 255)), color)
        return tuple(color)
    return color_func


def word_cloud(frequencies, path, size=(600, 400), background='white',
               colormap_name='Accent', max_concepts=200, stopwords=None,
               font=None):
    """Generates word cloud image from *frequencies* and stores it to *path*.
    If *path* is None, returns image as np.ndarray instead. One way to view
    resulting image is to use matplotlib's imshow method.

    :param frequencies: List of (word: str, frequency: int) pairs to plot
    :type frequencies: list
    :param path: Save plot to this file. Set to None if you want raw image
     np.ndarray of this plot as a return value
    :type path: str
    :param size: Size of plot in pixels as tuple (width: int, height: int)
    :type size: tuple
    :param background: Name of background color
    :type background: str
    :param colormap_name: Name of matplotlib colormap that will be used to
     sample random colors for concepts in plot
    :type colormap_name: str
    :param max_concepts: Maximum number of concepts that will be plotted
    :type max_concepts: int
    :param stopwords: Optionally set stopwords to use for the plot
    :type stopwords: iter
    :param font: Path to font that will be used
    :type font: str
    """
    if path is not None:
        for ext in Image.EXTENSION:
            if path.endswith(ext):
                break
        else:
            raise ValueError('Unsupported image file type: {}'.format(path))

    if stopwords is None:
        stopwords = STOPWORDS
    stopwords = set(w.lower() for w in stopwords)

    frequencies = [(word, freq) for word, freq in frequencies
                   if word.lower() not in stopwords]

    if font is not None and not os.path.isfile(font):
        font = matplotlib.font_manager.findfont(font)
    else:
        font = matplotlib.font_manager.findfont('')

    word_cloud = WordCloud(
        width=size[0], height=size[1], font_path=font,
        background_color=background, prefer_horizontal=0.8,
        color_func=generate_color_func(colormap_name), max_words=max_concepts,
    ).fit_words(frequencies)

    if path is not None:
        word_cloud.to_file(path)
    else:
        return np.asarray(word_cloud.to_image())


def plot(aggregation, color='dull green'):
    """Plots result from some of the aggregation results in form of horizontal
    bar chart.

    :param aggregation: Aggregation library result
    :type aggregation: pd.Series
    :param color: Seaborn named color for bars
    :type color: str
    :return: matplotlib.axes._subplots.AxesSubplot -- Axes for generated plot
    """
    if not hasattr(aggregation, '_plot_id'):
        raise ValueError('Aggregation needs to be pd.Series result from '
                         'aggregation library!')

    cat_name = aggregation.index.name
    val_name = aggregation.name
    agg = aggregation.reset_index()
    name = getattr(aggregation, '_entity', None) or \
           getattr(aggregation, '_concept', None)
    color = sns.xkcd_rgb.get(color, sns.xkcd_rgb['dull green'])
    plot_id = aggregation._plot_id

    plot = sns.barplot(x=val_name, y=cat_name, data=agg, color=color)
    plot.set_xlabel(val_name)
    if name is not None:
        plot.set_title('{} - {}'.format(plot_id, name), fontsize=14)
    else:
        plot.set_title(plot_id, fontsize=14)
    if val_name == 'Sentiment':
        plot.set_xticks(list(range(-5, 6, 1)))
    return plot
