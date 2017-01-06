# -*- coding: utf-8 -*-
import os
import logging
from itertools import chain

import numpy as np
import pandas as pd

from anacode import codes
from anacode.api import writers
from anacode.api.writers import CSV_FILES
from anacode.agg import plotting

from nltk.text import TextCollection, Text


class ApiCallDataset(object):
    """Base class for specific call data sets."""
    pass


class NoRelevantData(Exception):
    """Thrown when :class:`anacode.agg.aggregations.ApiCallDataset` does not
    have data needed to finish aggregation.
    """
    pass


class ConceptsDataset(ApiCallDataset):
    """Concept data sets container that provides easy aggregation and
    plotting capabilities.

    """
    def __init__(self, concepts, expressions):
        """Initialize instance by providing two concept relevant data frames.

        :param concepts: List of found concepts with metadata
        :type concepts: pandas.DataFrame
        :param expressions: List of expressions realizing found concepts
        :type expressions: pandas.DataFrame
        """
        self._concepts = concepts
        self._expressions = expressions

    def concept_frequency(self, concept, concept_type='', normalize=False):
        """Return occurrence count of input concept or concept list. Resulting
        list has concepts sorted just like they were in input if it was list or
        tuple.

        :param concept: name(s) of concept to count occurrences for
        :type concept: list, tuple, set or string
        :param concept_type: Limit concept counts only to concepts whose type
         starts with this string
        :type concept_type: str
        :param normalize: Returns relative counts of concepts in specified
         concept type
        :type normalize: bool
        :return: pandas.Series -- Concept names as index and their counts as
         values sorted as they were in input.
        """
        if self._concepts is None:
            raise NoRelevantData('Relevant concept data is not available!')

        if not isinstance(concept, (tuple, list, set)):
            concept = {concept}

        con = self._concepts
        con = con[con.concept_type.str.startswith(concept_type)]
        counts = con[con.concept.isin(concept)].groupby('concept')['freq'].sum()

        if isinstance(concept, (tuple, list)):
            counts = counts[concept]
        elif isinstance(concept, set):
            counts = counts[list(concept)]
        else:
            counts = counts[concept]

        result = counts.rename('Count').replace(np.nan, 0)
        result.index.name = 'Concept'

        if normalize:
            size = con.freq.sum()
            result = result.astype(float) / size
        else:
            result = result.astype(int)
        return result

    def most_common_concepts(self, n=15, concept_type='', normalize=False):
        """Counts concepts and returns n most occurring ones sorted by their
        count descending. Counted concepts can be filtered by their type.

        :param n: Maximum number of most common concepts to return
        :type n: int
        :param concept_type: Limit concept counts only to concepts whose type
         starts with this string
        :type concept_type: str
        :param normalize: Returns relative frequencies if normalize is True
        :type normalize: bool
        :return: pandas.Series -- Concept names as index and their counts as
         values sorted descending
        """
        if self._concepts is None:
            raise NoRelevantData('Relevant concept data is not available!')

        con = self._concepts
        con = con[con.concept_type.str.startswith(concept_type)]
        con_counts = con.groupby('concept').agg({'freq': 'sum'}).freq
        result = con_counts.rename('Count').sort_values(ascending=False)[:n]
        result.index.name = 'Concept'
        result._plot_id = codes.MOST_COMMON_CONCEPTS
        if normalize:
            result = result.astype(float) / con.freq.sum()
        return result

    def least_common_concepts(self, n=15, concept_type='', normalize=False):
        """Counts concepts and returns n least occurring ones sorted by their
        count ascending. Counted concepts can be filtered by their type.

        :param n: Maximum number of least common concepts to return
        :type n: int
        :param concept_type: Limit concept counts only to concepts whose type
         starts with this string
        :type concept_type: str
        :param normalize: Returns relative frequencies if normalize is True
        :type normalize: bool
        :return: pandas.Series -- Concept names as index and their counts as
         values sorted ascending
        """
        if self._concepts is None:
            raise NoRelevantData('Relevant concept data is not available!')

        con = self._concepts
        con = con[con.concept_type.str.startswith(concept_type)]
        con_counts = con.groupby('concept').agg({'freq': 'sum'}).freq
        result = con_counts.rename('Count').sort_values()[:n]
        result.index.name = 'Concept'
        result._plot_id = codes.LEAST_COMMON_CONCEPTS
        if normalize:
            result = result.astype(float) / con.freq.sum()
        return result

    def co_occurring_concepts(self, concept, n=15, concept_type=''):
        """Find n concepts co-occurring frequently in texts of this dataset with
        given concept, sorted descending. Co-occurring concepts can be
        filtered by their type.

        :param concept: Concept to inspect for co-occurring concepts
        :type concept: str
        :param n: Maximum count of returned concepts
        :type n: int
        :param concept_type: Limit co-occurring concept counts only to this type
         of concepts.
        :type concept_type: str
        :return: pandas.Series -- Co-occurring concept names as index and their
         counts as values sorted descending
        """
        if self._concepts is None:
            raise NoRelevantData('Relevant concept data is not available!')

        con = self._concepts

        identity_filter = con.concept.str.lower() == concept.lower()
        relevant_texts = con[identity_filter][['doc_id', 'text_order']]
        relevant_texts = relevant_texts.set_index(['doc_id', 'text_order'])

        type_filter = con.concept_type.str.startswith(concept_type)
        con = con[type_filter & (identity_filter == False)]
        con = relevant_texts.join(con.set_index(['doc_id', 'text_order']))

        con_counts = con.groupby('concept').agg({'freq': 'sum'}).freq
        con_counts = con_counts.rename('Count').sort_values(ascending=False)
        result = con_counts[:n].astype(int)
        result.index.name = 'Concept'
        result._concept = concept
        result._plot_id = codes.CO_OCCURING_CONCEPTS
        return result

    def nltk_textcollection(self, concept_type=''):
        """Wraps concepts of each represented documents into nltk.text.Text and
        returns these wrapped in nltk.text.TextCollection.

        :param concept_type: Limit gathered concepts only to this type of
         concepts
        :type concept_type: str
        :return: nltk.text.TextCollection -- TextCollection of represented
         documents
        """
        if self._concepts is None:
            raise NoRelevantData('Relevant concept data is not available!')

        con = self._concepts
        con = con[con.concept_type.str.startswith(concept_type)]

        texts = []
        docs_concepts = con.groupby(['doc_id', 'concept'])['freq'].sum()
        docs_concepts = docs_concepts.reset_index()
        for doc_id in self._concepts.doc_id.unique():
            concepts = docs_concepts[docs_concepts.doc_id == doc_id]
            concepts = concepts.set_index('concept')['freq']
            doc = chain.from_iterable([w] * c for w, c in concepts.iteritems())
            texts.append(Text(doc))

        return TextCollection(texts)

    def make_idf_filter(self, threshold, concept_type=''):
        """Generates concept filter based on idf value of concept in represented
        documents. This filter can be directly used as parameter for word_cloud
        call.

        :param threshold: Minimum IDF of concept that will pass the filter
        :type threshold: float
        :param concept_type: Limit co-occurring concept counts only to this type
         of concepts.
        :type concept_type: str
        :return: callable -- Function that can be used as idf_func in word_cloud
        """
        corpus = self.nltk_textcollection(concept_type)

        def idf_filter(word):
            """Computes idf of word in corpus and decides if word is important
            or not.

            :param word: Concept name to decide if bears significant meaning
            :type word: str
            :return: bool -- True if concept has meaning in text, False
             otherwise
            """
            return corpus.idf(word) >= threshold

        return idf_filter

    def word_cloud(self, path, size=(600, 350), background='white',
                   colormap_name='Accent', max_concepts=200, stopwords=None,
                   concept_type='', concept_filter=None, font=None):
        """Saves word cloud image to *path*. If *path* is not returns image as
        np.ndarray. On way to view np.ndarray resulting image is to use
        matplotlib's imshow method.

        :param path: Save plot to this file. Set to None if you want raw image
         np.ndarray of this plot as a return value
        :type path: str
        :param size: Size of plot in pixels
        :type size: tuple - pair - of ints
        :param background: Name of background color
        :type background: str
        :param colormap_name: Name of matplotlib colormap that will be used to
         sample random colors for concepts in plot
        :type colormap_name: str
        :param max_concepts: Maximum number of concepts that will be plotted
        :type max_concepts: int
        :param stopwords: Optionally set stopwords to use for the plot
        :type stopwords: iter
        :param concept_type: Limit concepts only to concepts whose type starts
         with this string
        :type concept_type: str
        :param concept_filter: If not None given callable needs to accept one
         string parameter that is concept name and evaluate it if it should pass
         the filter - callable returns True - or not - callable returns False.
         Only concepts that pass can be seen on resulting word cloud image
        :type concept_filter: callable
        :param font: Path to font that will be used
        :type font: str
        :return: numpy.ndarray or None -- Returns numpy.ndarray if no path to
         save was provided otherwise returns None.
        """
        if self._concepts is None:
            raise NoRelevantData('Relevant concept data is not available!')

        con = self._concepts
        con = con[con.concept_type.str.startswith(concept_type)]

        if concept_filter is not None:
            con = con[list(map(concept_filter, con.concept))]

        data = con.groupby('concept')['freq'].sum()
        data = data.sort_values().tail(max_concepts).reset_index()
        frequencies = [tuple(row.tolist()) for _, row in data.iterrows()]

        return plotting.word_cloud(frequencies, path, size, background,
                                   colormap_name, max_concepts, stopwords, font)


class CategoriesDataset(ApiCallDataset):
    """Categories data set container that will provides easy aggregation
    capabilities.

    """
    def __init__(self, categories):
        """Initialize instance by providing categories data set.

        :param categories: List of document topic probabilities
        :type categories: pandas.DateFrame
        """
        self._categories = categories

    def main_topic(self):
        """Finds what topic is this dataset about. Does not support nested
        categories output.

        :return: str -- Name of main topic of all texts.
        """
        if self._categories is None:
            raise NoRelevantData('Relevant category data is not available!')

        cat = self._categories
        all_cats = cat.groupby('category')['probability'].mean()
        return all_cats.sort_values(ascending=False).index[0]


class SentimentDataset(ApiCallDataset):
    """Sentiments data set container that will provides easy aggregation
    capabilities.

    """
    def __init__(self, sentiments):
        """Initialize instance by providing sentiments data set.

        :param sentiments: List of document sentiment inclinations
        :type sentiments: pandas.DateFrame
        """
        self._sentiments = sentiments

    def average_sentiment(self):
        """Computes and returns average document sentiment. Result is a number
        from [0,1], where higher number means more positive sentiment.

        :return: float -- Average document sentiment
        """
        if self._sentiments is None:
            raise NoRelevantData('Relevant sentiment data is not available!')

        sen = self._sentiments
        return sen.positive.mean()


class ABSADataset(ApiCallDataset):
    """ABSA data set container that will provides easy aggregation and plotting
    capabilities.

    """
    def __init__(self, entities, normalized_texts,
                 relations, relations_entities,
                 evaluations, evaluations_entities):
        """Initialize instance by providing all absa data sets.

        :param entities: List of entities used in texts
        :type entities: pandas.DataFrame
        :param normalized_texts: List of chinese normalized texts
        :type normalized_texts: pandas.DataFrame
        :param relations: List of relations with metadata
        :type relations: pandas.DataFrame
        :param relations_entities: List of entities used in relations
        :type relations_entities: pandas.DataFrame
        :param evaluations: List of entity evaluations
        :type evaluations: pandas.DataFrame
        :param evaluations_entities: List of entities used in evaluations
        :type evaluations_entities: pandas.DataFrame
        """
        self._entities = entities
        self._normalized_texts = normalized_texts
        self._relations = relations
        self._relations_entities = relations_entities
        self._evaluations = evaluations
        self._evaluations_entities = evaluations_entities

    def entity_frequency(self, entity, entity_type='', normalize=False):
        """Return occurrence count of input entity or entity list. Resulting
        list has entities sorted just like they were in input if it was list or
        tuple.

        :param entity: Entity name or tuple/list/set of entity names
        :type entity: tuple, list, set or str
        :param entity_type: Optional filter for entity type to consider
        :type entity_type: str
        :param normalize: Returns relative frequencies if normalize is True
        :type normalize: bool
        :return: pandas.Series -- Entity names as index entity frequencies as
         values sorted as input if it was tuple or list
        """
        if self._entities is None:
            raise NoRelevantData('Relevant entities data is not available!')

        if not isinstance(entity, (tuple, list, set)):
            entity = {entity}

        ents = self._entities
        ents = ents[ents.entity_type.str.startswith(entity_type)]
        counts = ents['entity_name'].value_counts(normalize=normalize)

        if isinstance(entity, (tuple, list)):
            counts = counts[entity]
        elif isinstance(entity, set):
            counts = counts[list(entity)]
        else:
            counts = counts[entity]

        result = counts.rename('Count').replace(np.nan, 0)
        result.index.name = 'Entity'
        if not normalize:
            result = result.astype(int)
        return result

    def most_common_entities(self, n=15, entity_type='', normalize=False):
        """Counts entities and returns n most occurring ones sorted by their
        count descending. Counted entities can be filtered by their type.

        :param n: Maximum number of most common entities to return
        :type n: int
        :param entity_type: Limit entities counts only to entities whose type
         starts with this string
        :type entity_type: str
        :param normalize: Returns relative frequencies if normalize is True
        :type normalize: bool
        :return: pandas.Series -- Entity names as index and their counts as
         values sorted descending
        """
        if self._entities is None:
            raise NoRelevantData('Relevant entity data is not available!')

        ent = self._entities
        ent = ent[ent.entity_type.str.startswith(entity_type)]
        result = ent['entity_name'].value_counts(normalize=normalize)[:n]
        result._plot_id = codes.MOST_COMMON_ENTITIES
        result.index.name = 'Entity'
        return result.rename('Count')

    def least_common_entities(self, n=15, entity_type='', normalize=False):
        """Counts entities and returns n least occurring ones sorted by their
        count ascending. Counted entities can be filtered by their type.

        :param n: Maximum number of least common entities to return
        :type n: int
        :param entity_type: Limit entities counts only to entities whose type
         starts with this string
        :type entity_type: str
        :param normalize: Returns relative frequencies if normalize is True
        :type normalize: bool
        :return: pandas.Series -- Entity names as index and their counts as
         values sorted descending
        """
        if self._entities is None:
            raise NoRelevantData('Relevant entity data is not available!')

        ent = self._entities
        ent = ent[ent.entity_type.str.startswith(entity_type)]['entity_name']
        result = ent.value_counts(normalize=normalize, ascending=True)[:n]
        result._plot_id = codes.LEAST_COMMON_ENTITIES
        result.index.name = 'Entity'
        return result

    def co_occurring_entities(self, entity, n=15, entity_type=''):
        """Find n entities co-occurring frequently in texts of this dataset with
        given entity, sorted descending. Co-occurring entities can be
        filtered by their type.

        :param entity: Concept to inspect for co-occurring concepts
        :type entity: str
        :param n: Maximum count of returned concepts
        :type n: int
        :param entity_type: Limit co-occurring concept counts only to this type
         of concepts.
        :type entity_type: str
        :return: pandas.Series -- Co-occurring concept names as index and their
         counts as values sorted descending
        """
        if self._entities is None:
            raise NoRelevantData('Relevant entity data is not available!')

        ent, doc_txt = self._entities, ['doc_id', 'text_order']
        entity_filter = ent.entity_name.str.lower() == entity.lower()
        docs = ent[entity_filter][doc_txt].drop_duplicates()
        if docs.shape[0] == 0:
            return pd.Series([]).rename('Count')

        docs = docs.set_index(doc_txt)
        type_filter = ent.entity_type.str.startswith(entity_type)
        ent = ent[type_filter & (entity_filter == False)].set_index(doc_txt)
        result = docs.join(ent, how='inner')
        if result.shape[0] == 0:
            return pd.Series([]).rename('Count')

        result = result.groupby('entity_name').size().rename('Count')
        result = result.sort_values(ascending=False)[:n]
        result._plot_id = codes.CO_OCCURING_ENTITIES
        result._entity = entity
        result.index.name = 'Entity'
        return result

    def best_rated_entities(self, n=15, entity_type=''):
        """Find top n rated entities in this dataset sorted descending by their
        mean rating.

        :param n: Maximum count of returned entities
        :type n: int
        :param entity_type: Optional filter for entity type to consider
        :type entity_type: str
        :return: pandas.Series -- Best rated entities in this dataset as
         index and their ratings as values sorted descending
        """
        if self._relations is None or self._relations_entities is None:
            raise NoRelevantData('Relevant relation data is not available!')

        idx = ['doc_id', 'text_order', 'relation_id']
        rels, ents = self._relations, self._relations_entities
        rels = rels[rels.sentiment.abs() < 100]
        ent_evals = rels.set_index(idx).join(ents.set_index(idx)).reset_index()
        ent_evals = ent_evals[ent_evals.entity_type.str.startswith(entity_type)]
        mean_evals = ent_evals.groupby('entity_name').agg({'sentiment': 'mean'})
        mean_evals = mean_evals.sentiment.rename('Sentiment')
        result = mean_evals.sort_values(ascending=False)[:n]
        result._plot_id = codes.BEST_RATED_ENTITIES
        result.index.name = 'Entity'
        return result

    def worst_rated_entities(self, n=15, entity_type=''):
        """Find n worst rated entities in this dataset sorted ascending by their
        mean rating.

        :param n: Maximum count of returned entities
        :type n: int
        :param entity_type: Optional filter for entity type to consider
        :type entity_type: str
        :return: pandas.DataFrame -- Worst rated entities in this dataset as
         index and their ratings as values sorted ascending
        """
        if self._relations is None or self._relations_entities is None:
            raise NoRelevantData('Relevant relation data is not available!')

        idx = ['doc_id', 'text_order', 'relation_id']
        rels, ents = self._relations, self._relations_entities
        rels = rels[rels.sentiment.abs() < 100]
        ent_evals = rels.set_index(idx).join(ents.set_index(idx)).reset_index()
        ent_evals = ent_evals[ent_evals.entity_type.str.startswith(entity_type)]
        mean_evals = ent_evals.groupby('entity_name').agg({'sentiment': 'mean'})
        mean_evals = mean_evals.sentiment.rename('Sentiment')
        result = mean_evals.sort_values()[:n]
        result._plot_id = codes.WORST_RATED_ENTITIES
        result.index.name = 'Entity'
        return result

    def entity_texts(self, entity):
        """Returns dict of entities to list of normalized texts where entity is
        mentioned

        :param entity: Name of entities to find in normalized texts
        :type entity: tuple, list, set or str
        :return: dict -- Map where keys are concept names and values are lists
         of normalized strings
        """
        if self._entities is None or self._normalized_texts is None:
            raise NoRelevantData('Relevant entity data is not available!')

        if not isinstance(entity, (tuple, list, set)):
            entity = {entity}

        col_filter = ['doc_id', 'text_order', 'entity_name']
        ent, texts = self._entities[col_filter], self._normalized_texts
        ent = ent[ent.entity_name.isin(entity)].drop_duplicates()
        ent_texts = pd.merge(ent, texts, on=['doc_id', 'text_order'])
        grp = ent_texts.groupby('entity_name')['normalized_text']

        result = {key: [] for key in entity}
        result.update({
            entity_name: grp.get_group(entity_name).tolist()
            for entity_name in grp.groups
        })
        return result

    def entity_sentiment(self, entity):
        """Computes and return mean rating for given entity or entities if list,
        tuple or set is given. If input is list or tuple result Series is sorted
        as input was.

        :param entity: Name(s) of entity(ies) to compute mean sentiment for
        :type entity: tuple, list, set or str
        :return: pandas.Series -- Mean ratings for entities, np.nan if entity
         was not rated. Entity names are in index and their sentiments are
         values
        """
        if self._relations is None or self._relations_entities is None:
            raise NoRelevantData('Relevant relation data is not available!')

        idx = ['doc_id', 'text_order', 'relation_id']
        rels, ents = self._relations, self._relations_entities
        rels = rels[rels.sentiment.abs() < 100]
        all_ent_evals = pd.merge(rels, ents, on=idx)

        if not isinstance(entity, (tuple, list, set)):
            entity = {entity}

        entity_filter = all_ent_evals.entity_name.isin(set(entity))
        entity_evals = all_ent_evals[entity_filter]

        means = entity_evals.groupby('entity_name')['sentiment'].mean()
        return means[list(entity)]


class DatasetLoader(object):
    """Meant for loading analysed data obtained via AnacodeAPI from various
    formats.

    """
    def __init__(self, concepts=None, concepts_expressions=None,
                 categories=None, sentiments=None,
                 absa_entities=None, absa_normalized_texts=None,
                 absa_relations=None, absa_relations_entities=None,
                 absa_evaluations=None, absa_evaluations_entities=None):
        """Will construct DatasetLoader instance that is aware of what data is
        available to it. Raises ValueError if no data was given.

        Data frames are expected to have format that corresponds to format that
        :class:`anacode.api.writers.Writer` would write.

        :param concepts: List of found concepts with metadata
        :type concepts: pandas.DataFrame
        :param concepts_expressions: List of expressions realizing concepts
        :type concepts_expressions: pandas.DataFrame
        :param categories: List of document topic probabilities
        :type categories: pandas.DateFrame
        :param sentiments: List of document sentiment inclinations
        :type sentiments: pandas.DateFrame
        :param absa_entities: List of entities used in texts
        :type absa_entities: pandas.DataFrame
        :param absa_normalized_texts: List of chinese normalized texts
        :type absa_normalized_texts: pandas.DataFrame
        :param absa_relations: List of relations with metadata
        :type absa_relations: pandas.DataFrame
        :param absa_relations_entities: List of entities used in relations
        :type absa_relations_entities: pandas.DataFrame
        :param absa_evaluations: List of entity evaluations
        :type absa_evaluations: pandas.DataFrame
        :param absa_evaluations_entities: List of entities used in evaluations
        :type absa_evaluations_entities: pandas.DataFrame
        """
        self.has_categories = categories is not None
        self.has_concepts = concepts is not None or \
            concepts_expressions is not None
        self.has_sentiments = sentiments is not None
        self.has_absa = absa_entities is not None or \
            absa_normalized_texts is not None or \
            absa_relations is not None or \
            absa_relations_entities is not None or \
            absa_evaluations is not None or \
            absa_evaluations_entities is not None

        if not (self.has_categories or self.has_concepts or
                self.has_sentiments or self.has_absa):
            raise ValueError('No data provided. Please provide at least one '
                             'valid argument')

        if self.has_categories:
            self._categories = categories
        else:
            self._categories = None

        if self.has_concepts:
            self._concepts = concepts
            self._concepts_expressions = concepts_expressions
        else:
            self._concepts = self._concepts_expressions = None

        if self.has_sentiments:
            self._sentiments = sentiments
        else:
            self._sentiments = None

        if self.has_absa:
            self._absa_entities = absa_entities
            self._absa_normalized_texts = absa_normalized_texts
            self._absa_relations = absa_relations
            self._absa_relations_entities = absa_relations_entities
            self._absa_evaluations = absa_evaluations
            self._absa_evaluations_entities = absa_evaluations_entities
        else:
            self._absa_entities = self._absa_normalized_texts = None
            self._absa_relations = self._absa_relations_entities = None
            self._absa_evaluations = self._absa_evaluations_entities = None

    def __getitem__(self, item):
        dataset_map = {
            'categories': self._categories,
            'concepts': self._concepts,
            'concepts_expressions': self._concepts_expressions,
            'sentiments': self._sentiments,
            'absa_entities': self._absa_entities,
            'absa_normalized_texts': self._absa_normalized_texts,
            'absa_relations': self._absa_relations,
            'absa_relations_entities': self._absa_relations_entities,
            'absa_evaluations': self._absa_evaluations,
            'absa_evaluations_entities': self._absa_evaluations_entities,
        }
        if item not in dataset_map:
            raise KeyError('Don\'t recognize "{}" dataset'.format(item))
        return dataset_map[item]

    def remove_concepts(self, concepts):
        """Remove given concepts from dataset if they are present.

        :param concepts: These concepts will be removed from dataset
        :type concepts: iterable
        """
        con = self._concepts
        if con is None:
            return

        concepts = set(concepts)
        self._concepts = con[con.concept.isin(concepts) == False]

    @property
    def concepts(self):
        """Creates new ConceptsDataset if data is available.

        :return: :class:`anacode.agg.aggregations.ConceptsDataset` --
        """
        if self.has_concepts:
            return ConceptsDataset(self._concepts, self._concepts_expressions)
        else:
            raise NoRelevantData('Concepts data not available!')

    @property
    def categories(self):
        """Creates new CategoriesDataset if data is available.

        :return: :class:`anacode.agg.aggregations.CategoriesDataset` --
        """
        if self.has_categories:
            return CategoriesDataset(self._categories)
        else:
            raise NoRelevantData('Categories data not available!')

    @property
    def sentiments(self):
        """Creates new SentimentDataset if data is available.

        :return: :class:`anacode.agg.aggregations.SentimentDataset` --
        """
        if self.has_sentiments:
            return SentimentDataset(self._sentiments)
        else:
            raise NoRelevantData('Sentiment data is not available!')

    @property
    def absa(self):
        """Creates new ABSADataset if data is available.

        :return: :class:`anacode.agg.aggregations.ABSADataset` --
        """
        if self.has_absa:
            return ABSADataset(
                self._absa_entities, self._absa_normalized_texts,
                self._absa_relations, self._absa_relations_entities,
                self._absa_evaluations, self._absa_evaluations_entities,
            )
        else:
            raise NoRelevantData('ABSA data is not available!')

    @classmethod
    def from_path(cls, path):
        """Initializes DatasetLoader from AnacodeAPI csv files present in given
        path. You could have obtained these by using
        :class:`anacode.api.writers.CSVWriter` to write your request results
        when you were querying AnacodeAPI.

        :param path: Path to folder where AnacodeAPI analysis is stored in csv
         files
        :type path: str
        :return: :class:`anacode.agg.DatasetLoader` -- DatasetLoader with found
         csv files loaded into data frames
        """
        log = logging.getLogger(__name__)
        log.debug('Going to init ApiDataset from path %s', path)
        join = os.path.join
        path_contents = set(os.listdir(path))
        log.debug('Found files: %s', path_contents)
        kwargs = {}
        loaded = []

        for call, files in CSV_FILES.items():
            for file_name in files:
                name = file_name[:-4]
                file_path = join(path, file_name)
                if os.path.isfile(file_path):
                    kwargs[name] = pd.read_csv(file_path)
                    loaded.append(name)
                else:
                    kwargs[name] = None

        if len(loaded) == 0:
            raise ValueError('No relevant csv files in %s', path)
        else:
            log.info('Loaded %d csv files', len(loaded))
            log.debug('Loaded csv files are: %s', loaded)

        return cls(**kwargs)

    @classmethod
    def from_writer(cls, writer):
        """Initializes DatasetLoader from writer instance that was used to store
        anacode analysis. Accepts both
        :class:`anacode.api.writers.DataFrameWriter` and
        :class:`anacode.api.writers.CSVWriter`.

        :param writer: Writer that was used by
         :class:`anacode.api.client.Analyzer` to store analysis
        :type writer: anacode.api.writers.Writer
        :return: :class:`anacode.agg.DatasetLoader` -- DatasetLoader with
         available data frames loaded
        """
        if isinstance(writer, writers.CSVWriter):
            return cls.from_path(writer.target_dir)
        elif isinstance(writer, writers.DataFrameWriter):
            return cls(**writer.frames)
        else:
            raise ValueError('{} class not supported'.format(type(writer)))

    @classmethod
    def from_lists(cls, concepts=None, categories=None, sentiments=None,
                   absa=None):
        """Initializes DatasetLoader from list of json-s that anacode api calls
        return.

        :param concepts: List of concept analysis json-s
        :type concepts: list
        :param categories: List of categories analysis json-s
        :type categories: list
        :param sentiments: List of sentiment analysis json-s
        :type sentiments: list
        :param absa: List of ABSA analysis json-s
        :type absa: list
        :return: :class:`anacode.agg.DatasetLoader` -- DatasetLoader with
         available analysis data loaded
        """
        concepts = concepts or []
        categories = categories or []
        sentiments = sentiments or []
        absa = absa or []

        frame_writer = writers.DataFrameWriter()
        frame_writer.init()
        for analyzed in concepts:
            frame_writer.write_concepts(analyzed)
        for analyzed in categories:
            frame_writer.write_categories(analyzed)
        for analyzed in sentiments:
            frame_writer.write_sentiment(analyzed)
        for analyzed in absa:
            frame_writer.write_absa(analyzed)
        frame_writer.close()

        return cls(**frame_writer.frames)

    def filter(self, document_ids):
        """Creates new DatasetLoader instance using data only from documents
        with ids in *document_ids*.

        :param document_ids: Iterable with document ids. Cannot be empty.
        :type document_ids: iterable
        :return: DatasetLoader -- New DatasetLoader instance with data only from
         desired documents
        """
        document_ids = set(document_ids)
        if len(document_ids) == 0:
            raise ValueError('Can\'t use empty filter')

        def f(frame):
            if frame is None:
                return None
            return frame[frame.doc_id.isin(document_ids)]

        return DatasetLoader(
            concepts=f(self._concepts),
            concepts_expressions=f(self._concepts_expressions),
            categories=f(self._categories), sentiments=f(self._sentiments),
            absa_entities=f(self._absa_entities),
            absa_normalized_texts=f(self._absa_normalized_texts),
            absa_evaluations=f(self._absa_evaluations),
            absa_evaluations_entities=f(self._absa_evaluations_entities),
            absa_relations=f(self._absa_relations),
            absa_relations_entities=f(self._absa_relations_entities),
        )
