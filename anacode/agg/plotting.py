# -*- coding: utf-8 -*-
import re
import os
import random

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager

from io import StringIO
from anacode import codes

from wordcloud import WordCloud, STOPWORDS


def explode_capitalized(string):
    """Inserts spaces inside capitalized input string.

    :param string: Capitalized string
    :type string: str
    :return: str -- Capitalized string with spaces in it
    """
    result = StringIO()
    for segment in re.findall(r'([A-Z][a-z]*|[0-9]+)(\-?)', string):
        result.write(segment[0])
        result.write(segment[1])
        if len(segment[0]) > 1 and segment[1] != '-':
            result.write(' ')
    return result.getvalue().strip()


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


def chart_title(plot_id, series_index):
    """Replaces generic Concept or Entity strings from chart titles with more
    specific name if it was specified.

    :param plot_id: Automatic title for chart
    :param series_index: Aggregation's index column name
    :return: str -- New chart title
    """
    if series_index in {'Concept', 'Entity'}:
        return plot_id

    if 'Concept' in plot_id:
        if 'Concepts' in plot_id:
            return plot_id.replace('Concepts', series_index + 's')
        else:
            return plot_id.replace('Concept', series_index)

    if 'Entities' in plot_id:
        return plot_id.replace('Entities', series_index + 's')

    # For non concept and non absa aggregations
    return plot_id


def concept_cloud(aggregation, path=None, size=(600, 400), background='white',
                  colormap_name='Accent', max_concepts=200, stopwords=None,
                  font=None):
    """Generates concept cloud image from *frequencies* and stores it to *path*.
    If *path* is None, returns image as np.ndarray instead. One way to view
    resulting image is to use matplotlib's imshow method.

    :param frequencies: List of (concept: str, frequency: int) pairs to plot
    :type frequencies: list
    :param path: Save plot to this file. Set to None if you want raw image
     np.ndarray of this plot as a return value
    :type path: str
    :param size: Size of plot in pixels as tuple (width: int, height: int)
    :type size: tuple
    :param background: Name of background color
    :type background: matplotlib color definition
    :param colormap_name: Name of matplotlib colormap that will be used to
     sample random colors for concepts in plot
    :type colormap_name: str
    :param max_concepts: Maximum number of concepts that will be plotted
    :type max_concepts: int
    :param stopwords: Optionally set stopwords to use for the plot
    :type stopwords: iter
    :param font: Path to font that will be used
    :type font: str
    :return: matplotlib.axes._subplots.AxesSubplot -- Axes for generated plot or
     None if graph was saved to file
    """
    if not hasattr(aggregation, '_plot_id'):
        raise ValueError('Aggregation needs to be pd.Series result from '
                         'aggregation library!')
    allowed_results = {codes.CONCEPT_CLOUD}
    if aggregation._plot_id not in allowed_results:
        raise ValueError('concept cloud not available for this '
                         'aggregation result')

    if stopwords is None:
        stopwords = STOPWORDS
    stopwords = set(w.lower() for w in stopwords)

    frequencies = [tuple(row.tolist()) for _, row in aggregation.iterrows()]
    frequencies = {word: freq for word, freq in frequencies
                   if word.lower() not in stopwords}

    if font is not None and not os.path.isfile(font):
        font = matplotlib.font_manager.findfont(font)
    else:
        font = matplotlib.font_manager.findfont('')

    word_cloud = WordCloud(
        width=size[0], height=size[1], font_path=font,
        background_color=background, prefer_horizontal=0.8,
        color_func=generate_color_func(colormap_name), max_words=max_concepts,
    ).fit_words(frequencies)

    if path is None:
        nparray = np.asarray(word_cloud.to_image())
        fig, ax = plt.subplots()
        plt.imshow(nparray)
        plt.axis('off')
        return ax

    try:
        word_cloud.to_file(path)
    except KeyError:
        raise ValueError('Unsupported image file type: {}'.format(path))
    return


def piechart(aggregation, path=None, colors=None, category_count=6, explode=0,
             edgesize=0, edgecolor='#333333', perc_color='black',
             labeldistance=1.1):
    """Plots piechart with categories.

    :param aggregation: Aggregation library result
    :type aggregation: pd.Series
    :param path: If specified graph will be saved to this file instead of
     returning it as a result
    :type path: str
    :param colors: This will be passed to matplotlib.pyplot.piechart as colors
    :param category_count: How many categories to include in piecharm
    :type category_count: int
    :param explode: Size of whitespace between pie pieces
    :type explode: float
    :param edgesize: Pie's edge size, set to 0 for no edge
    :type edgesize: int
    :param edgecolor: Color of pie's edge
    :type edgecolor: matplotlib supported color
    :param perc_color: Controls color of percentages drawn inside piechart
    :type perc_color: matplotlib supported color
    :return: matplotlib.axes._subplots.AxesSubplot -- Axes for generated plot or
     None if graph was saved to file
    """
    if not hasattr(aggregation, '_plot_id'):
        raise ValueError('Aggregation needs to be pd.Series result from '
                         'aggregation library!')
    allowed_results = {codes.AGGREGATED_CATEGORIES}
    if aggregation._plot_id not in allowed_results:
        raise ValueError('piechart not available for this aggregation result')

    probabilities = aggregation.tolist()[:category_count]
    probabilities.append(sum(aggregation.tolist()[category_count:]))
    data_labels = aggregation.index.tolist()[:category_count]
    data_labels.append('Other')
    data_labels = list(map(lambda s: s.capitalize(), data_labels))
    data_labels = list(map(lambda s: {
        'Auto': 'Automotive', 'Hr': 'HR'
    }.get(s, s), data_labels))
    probabilities = list(reversed(probabilities))
    data_labels = list(reversed(data_labels))

    if colors is None:
        colors = sns.color_palette('hls', 7)[::-1]
        colors[0] = (0.7, 0.7, 0.7)

    fig, ax = plt.subplots()
    wedges, labels, percents = plt.pie(
        probabilities, labels=data_labels, autopct='%1.0f%%', colors=colors,
        explode=[explode] * len(probabilities), startangle=90,
       labeldistance=labeldistance,
    )
    automatic_chart_title = chart_title(aggregation._plot_id,
                                        aggregation.index.name)
    plt.title(automatic_chart_title + '\n\n', fontsize=14)

    for w in wedges:
        w.set_linewidth(edgesize)
        w.set_edgecolor(edgecolor)
    for l in labels:
        l.set_size(13)
    for t in percents:
        t.set_color(perc_color)

    plt.axis('equal')
    if path is None:
        return ax
    plt.savefig(path)


def barhchart(aggregation, path=None, color='dull green', title=None):
    """Plots result from aggregation output in form of horizontal bar chart.

    :param aggregation: anacode.agg aggregation result
    :type aggregation: pd.Series
    :param path: If specified graph will be saved to this file instead of
     returning it as a result
    :type path: str
    :param color: seaborn named color for bars
    :type color: str
    :param title: Title of chart; set to None for automatic title, empty string for no title
    :type title: str
    :return: matplotlib.axes._subplots.AxesSubplot -- Axes for generated plot or
     None if graph was saved to file
    """
    if not hasattr(aggregation, '_plot_id'):
        raise ValueError('Aggregation needs to be pd.Series result from '
                         'aggregation library!')

    cat_name = aggregation.index.name
    val_name = aggregation.name
    agg = aggregation.reset_index()
    name = getattr(aggregation, '_entity', None) or \
           getattr(aggregation, '_concept', None)
    if not re.match(r'#\d{6}', color):
        color = sns.xkcd_rgb.get(color, sns.xkcd_rgb['dull green'])
    plot_id = aggregation._plot_id

    exploded = agg[cat_name].map(explode_capitalized).rename('exploded')
    agg = pd.concat([agg, exploded], axis=1)

    plot = sns.barplot(x=val_name, y='exploded', data=agg, color=color)
    plot.set_xlabel(val_name)
    plot.set_ylabel(explode_capitalized(cat_name))
    if title != '':
        if title is not None:
            plot.set_title(title, fontsize=14)
        elif name is not None:
            automatic_chart_title = chart_title(aggregation._plot_id,
                                                aggregation.index.name)
            plot.set_title('{} - {}'.format(automatic_chart_title,
                                            explode_capitalized(name)),
                           fontsize=14)
        else:
            automatic_chart_title = chart_title(aggregation._plot_id,
                                                aggregation.index.name)
            plot.set_title(automatic_chart_title, fontsize=14)

    if val_name == 'Sentiment':
        plot.set_xticks(np.arange(-1.0, 1.2, 0.2))

    plt.tight_layout()
    if path is None:
        return plot
    plt.savefig(path)


def frequency_relevance_chart(aggregation, path=None,
                              bar_color='#f4a582', line_color='#404040'):
    if not hasattr(aggregation, '_plot_id'):
        raise ValueError('Aggregation needs to be pd.Series result from '
                         'aggregation library!')

    aggregation = aggregation.reset_index()
    fig, ax = plt.subplots(figsize=(10, 9))
    ax2 = ax.twiny()
    ax2.xaxis.grid(False)
    sns.barplot(x='Frequency', y='Concept', data=aggregation, color=bar_color,
                ax=ax)
    sns.pointplot(x='Relevance', y='Concept', data=aggregation, color=line_color,
                  scale=0.5, linestyles='-',
                  ax=ax2, label='Relevance')
    ax.set_xlim((0, aggregation['Frequency'].max() + 1))
    ax2.set_xlim((0.0, 1.1))
    ax.set_ylabel('Concept')
    ax.set_xlabel('Frequency')
    ax2.set_xlabel('Relevance')
    plt.legend(handles=[
        mpatches.Patch(color=bar_color, label='Frequency'),
        mlines.Line2D([], [], color=line_color, marker='.', markersize=12,
                      label='Relevance')
    ], loc='lower right')

    plt.tight_layout()

    if path is None:
        return plot
    plt.savefig(path)



def plot(aggregation, path=None, **kwargs):
    """Plots aggregation result. This is convenience method that will choose
    chart type based on result type.

    :param aggregation: Aggregation library result
    :type aggregation: pd.Series
    :param path: If specified graph will be saved to this file instead of
     returning it as a result
    :type path: str
    :return: matplotlib.axes._subplots.AxesSubplot -- Axes for generated plot or
     None if graph was saved to file
    """
    if not hasattr(aggregation, '_plot_id'):
        raise ValueError('Aggregation needs to be pd.Series result from '
                         'aggregation library!')
    chart_type = {
        codes.AGGREGATED_CATEGORIES: 'piechart',
        codes.CONCEPT_CLOUD: 'concept_cloud',
    }.get(aggregation._plot_id, 'barhchart')

    if chart_type == 'piechart':
        return piechart(aggregation, path=path, **kwargs)
    if chart_type == 'concept_cloud':
        return concept_cloud(aggregation, path=path, **kwargs)
    if chart_type == 'barhchart':
        return barhchart(aggregation, path=path, **kwargs)
