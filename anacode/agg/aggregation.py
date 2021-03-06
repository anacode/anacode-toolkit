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


def _capitalize(string):
    return ''.join(map(lambda s: s.capitalize(), string.split('_')))


class ApiCallDataset(object):
    """Base class for specific call data sets."""
    pass


class NoRelevantData(Exception):
    """Thrown when :class:`anacode.agg.aggregations.ApiCallDataset` does not
    have data needed to finish aggregation.
    """
    pass


class ConceptsDataset(ApiCallDataset):
    """Concept dataset container with easy aggregation capabilities.
    """
    def __init__(self, concepts, surface_strings):
        """Initialize instance by providing the two dataframes required for concepts representation.

        :param concepts: List of found concepts with metadata
        :type concepts: pandas.DataFrame
        :param surface_strings: List of strings realizing found concepts
        :type surface_strings: pandas.DataFrame
        """
        self._concepts = concepts
        self._surface_strings = surface_strings
        if self._concepts is not None and 'concept_type' in self._concepts:
            self._concept_filter = set(self._concepts.concept_type.unique())
        else:
            self._concept_filter = set()
        self._concept_filter.add('')

    def concept_frequency(self, concept, concept_type='', normalize=False):
        """Return occurrence count of input concept or concept list. Resulting
        list has concepts sorted just like they were in input if it was list or
        tuple. Concepts that are not of *concept_type* or that are not in the
        dataset will always have zero count. Setting normalize will turn
        absolute counts into relative percentages.

        Specifying *concept_type* is intended to be used only with
        normalization. If used without *normalize* set it will have no effect
        except for concepts that do not have said type whose count will be zero.
        When used with *normalize* set percentages will reflect counts only
        within specified *concept_type* instead of the whole dataset.

        :param concept: name(s) of concept to count occurrences for
        :type concept: list, tuple, set or string
        :param concept_type: Limit result concepts counts only to concepts
         with this type
        :type concept_type: str
        :param normalize: Returns relative counts of concepts in specified
         concept type if set, otherwise returns absolute counts
        :type normalize: bool
        :return: pandas.Series -- Concept names as index and their counts as
         values sorted as they were in input.
        """
        if self._concepts is None:
            raise NoRelevantData('Relevant concept data is not available!')

        if concept_type not in self._concept_filter:
            msg = '"{}" not valid filter string'.format(concept_type)
            raise ValueError(msg)

        if not isinstance(concept, (tuple, list, set)):
            concept = {concept}

        con = self._concepts
        if concept_type:
            con = con[con.concept_type == concept_type]
        counts = con[con.concept.isin(concept)].groupby('concept')['freq'].sum()

        if isinstance(concept, (tuple, list)):
            counts = counts.reindex(concept)
        elif isinstance(concept, set):
            counts = counts.reindex(list(concept))
        else:
            counts = counts.reindex(concept)

        result = counts.rename('Count').replace(np.nan, 0)
        result.index.name = _capitalize(concept_type) or 'Concept'

        if normalize:
            size = con.freq.sum()
            result = result.astype(float) / size
        else:
            result = result.astype(int)
        result._plot_id = codes.CONCEPT_FREQUENCY
        return result

    def most_common_concepts(self, n=15, concept_type='', normalize=False):
        """Counts concepts and returns n most occurring ones sorted by their
        count descending. Counted concepts can be filtered by their type using
        *concept_type* and returned counts can be normalized with *normalize*.

        If both *concept_type* and *normalize* are specified concept ratios
        will be computed only from concept counts within given *concept_type*.

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

        if concept_type not in self._concept_filter:
            msg = '"{}" not valid filter string'.format(concept_type)
            raise ValueError(msg)

        con = self._concepts
        if concept_type:
            con = con[con.concept_type == concept_type]
        con_counts = con.groupby('concept').agg({'freq': 'sum'}).freq
        result = con_counts.rename('Count').sort_values(ascending=False)[:n]
        result.index.name = _capitalize(concept_type) or 'Concept'
        result._plot_id = codes.MOST_COMMON_CONCEPTS
        if normalize:
            result = result.astype(float) / con.freq.sum()
        return result

    def least_common_concepts(self, n=15, concept_type='', normalize=False):
        """Counts concepts and returns n least frequent ones sorted by their
        count ascending. Counted concepts can be filtered by their type using
        *concept_type* and returned counts can be normalized with *normalize*.

        If both *concept_type* and *normalize* are specified, concept ratios
        will be computed only from concept counts within given *concept_type*.

        :param n: Maximum number of concepts to return
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

        if concept_type not in self._concept_filter:
            msg = '"{}" not valid filter string'.format(concept_type)
            raise ValueError(msg)

        con = self._concepts
        if concept_type:
            con = con[con.concept_type == concept_type]
        con_counts = con.groupby('concept').agg({'freq': 'sum'}).freq
        result = con_counts.rename('Count').sort_values()[:n]
        result.index.name = _capitalize(concept_type) or 'Concept'
        result._plot_id = codes.LEAST_COMMON_CONCEPTS
        if normalize:
            result = result.astype(float) / con.freq.sum()
        return result

    def co_occurring_concepts(self, concept, n=15, concept_type=''):
        """Find *n* concepts co-occurring frequently in texts of this dataset
        with given *concept*, sorted by descending frequency. Co-occurring concepts can be
        filtered by their type.

        :param concept: Concept to inspect for co-occurring concepts
        :type concept: str
        :param n: Maximum number of returned co-occurring concepts
        :type n: int
        :param concept_type: Limit co-occurring concept counts only to this type
         of concepts.
        :type concept_type: str
        :return: pandas.Series -- Co-occurring concept names as index and their
         frequencies sorted by descending frequency
        """
        if self._concepts is None:
            raise NoRelevantData('Relevant concept data is not available!')

        if concept_type not in self._concept_filter:
            msg = '"{}" not valid filter string'.format(concept_type)
            raise ValueError(msg)

        con = self._concepts

        identity_filter = con.concept.str.lower() == concept.lower()
        relevant_texts = con[identity_filter][['doc_id', 'text_order']]
        relevant_texts = relevant_texts.set_index(['doc_id', 'text_order'])

        if relevant_texts.shape[0] != 0:
            if concept_type:
                type_filter = con.concept_type == concept_type
            else:
                type_filter = True
            con = con[type_filter & (identity_filter == False)]
            con = relevant_texts.join(con.set_index(['doc_id', 'text_order']))

            con_counts = con.groupby('concept').agg({'freq': 'sum'}).freq
            con_counts = con_counts.rename('Count').sort_values(ascending=False)
            result = con_counts[:n].astype(int)
        else:
            result = pd.Series([]).rename('Count')
        result.index.name = _capitalize(concept_type) or 'Concept'
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

        if concept_type not in self._concept_filter:
            msg = '"{}" not valid filter string'.format(concept_type)
            raise ValueError(msg)

        con = self._concepts
        if concept_type:
            con = con[con.concept_type == concept_type]

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
        """Generates concept filter based on idf values of concepts in represented
        documents. This filter can be directly used as parameter for
        concept_cloud call.

        :param threshold: Minimum IDF of concept that will pass the filter
        :type threshold: float
        :param concept_type: Limit co-occurring concept counts only to this type
         of concepts.
        :type concept_type: str
        :return: callable -- Function that can be used as idf_func in
         concept_cloud
        """
        corpus = self.nltk_textcollection(concept_type)

        def idf_filter(concept):
            """Computes IDF of concept in corpus and decides if the concept is relevant wrt the provided threshold.

            :param concept: Concept name for which to retrieve IDF
            :type concept: str
            :return: bool -- True if concept is relevant, else False
             otherwise
            """
            return corpus.idf(concept) >= threshold

        return idf_filter

    def make_time_series(self, concepts, date_info, delta, interval=None):
        """Creates DataFrame with counts for each *concepts* in every *delta*
        time tick that exists in *interval*. If you do not specify interval it
        will be computed from date_info to include all documents.

        In concepts dataset there is no information about document release date
        so you will have to provide this information externally as *date_info*.
        It needs to be a map object that has all document ids from concept's
        dataset as keys and they refer to datetime.date representing release
        date for the document.

        Result will include 0 counts for ticks where concepts were not
        mentioned. In each row there will also be start and stop times for that
        particular count. Counts from stop time are not included in the tick.

        :param concepts: List of concept names to make time series for
        :type concepts: list
        :param date_info: Keys need to be document ids in this dataset and
         values datetime.datetime or datetime.date objects
        :type date_info: dict
        :param delta: Time series tick size
        :param interval: (start, stop) where both values are datetimes or dates
        :type interval: tuple
        :return: pandas.DataFrame -- DataFrame with columns "Concept", "Count",
         "Start" and "Stop"
        """
        if self._concepts is None:
            raise NoRelevantData('Relevant concept data is not available!')

        if interval is None:
            interval = min(date_info.values()), max(date_info.values()) + delta

        tick_counts, ticks = [], []

        con = self._concepts
        con = con[con.concept.isin(concepts)]
        dates = pd.Series([date_info[doc_id] for doc_id in con.doc_id])

        last, stop = interval
        current = last + delta
        while last < stop:
            relevant = con[((dates >= last) & (dates < current)).tolist()]
            counts = relevant.groupby('concept').agg({'freq': 'sum'})['freq']
            concept_counts = [counts.get(c, 0) for c in concepts]
            tick_counts.append(concept_counts)
            ticks.append((last, current))

            last = current
            current = current + delta

        concept_frames = []
        concept_count_lists = list(zip(*tick_counts))
        ticks = list(zip(*ticks))
        for concept, counts in zip(concepts, concept_count_lists):
            count_df = pd.Series(counts, name='Count').reset_index()
            count_df['Concept'] = concept
            count_df['Start'] = ticks[0]
            count_df['Stop'] = ticks[1]
            concept_frames.append(count_df)

        retval = pd.concat(concept_frames)
        retval.reset_index(drop=True, inplace=True)
        retval.drop('index', axis=1, inplace=True)
        return retval

    def concept_frequencies(self, max_concepts=200, concept_type='',
                            concept_filter=None):
        """Returns pandas series with counts for all concepts from the dataset.

        To filter words that will be showed in the cloud you can use
        *concept_type* and *concept_filter*. The former is specific type of
        concepts that you only want to have present in the result and
        the latter is callable that takes concept name and returns bool
        to indicate whether given concept should pass the filter. You can set
        both at the same time. *concept_type* is applied first,
        *concept_filter* second.

        :param max_concepts: Maximum number of concepts that will be plotted
        :type max_concepts: int
        :param concept_type: Limit concepts only to concepts whose type starts
         with this string
        :type concept_type: str
        :param concept_filter: If not None given callable needs to accept one
         string parameter that is concept name and evaluate it if it should pass
         the filter - callable returns True - or not - callable returns False.
         Only concepts that pass can be seen on resulting concept cloud image
        :type concept_filter: callable
        :return: pandas.Series -- Concept names as index and their counts as
         values
        """
        if self._concepts is None:
            raise NoRelevantData('Relevant concept data is not available!')

        if concept_type not in self._concept_filter:
            msg = '"{}" not valid filter string'.format(concept_type)
            raise ValueError(msg)

        con = self._concepts
        if concept_type:
            con = con[con.concept_type == concept_type]

        if concept_filter is not None:
            con = con[list(map(concept_filter, con.concept))]

        data = con.groupby('concept')['freq'].sum()
        frequencies = data.sort_values().tail(max_concepts).reset_index()
        frequencies._plot_id = codes.CONCEPT_CLOUD
        frequencies.index.name = _capitalize(concept_type) or 'Concept'
        return frequencies


    def frequency_relevance(self, concepts=None, n=15, concept_type=''):
        if self._concepts is None:
            raise NoRelevantData('Relevant concept data is not available!')

        if concept_type not in self._concept_filter:
            msg = '"{}" not valid filter string'.format(concept_type)
            raise ValueError(msg)

        con = self._concepts
        if concept_type:
            con = con[con.concept_type == concept_type]
        if concepts:
            con = con[con.concept.isin(set(concepts))]

        agg = {'freq': 'sum', 'relevance_score': 'mean'}
        result = con.groupby('concept').agg(agg)
        if not concepts:
            result.sort_values('relevance_score', ascending=False, inplace=True)
            result = result.head(n)
        elif isinstance(concepts, (list, tuple)):
            result = result.reindex(concepts)
        result.rename(inplace=True, columns={'relevance_score': 'Relevance',
                                             'freq': 'Frequency'})
        result.index.name = _capitalize(concept_type) or 'Concept'
        result = result[result['Relevance'].isnull() == False]
        result._plot_id = codes.FREQUENCY_RELEVANCE
        return result

    def surface_forms(self, concept, n=15):
        """Find `n` random surface strings from analyzed text that were
        identified as `concept`.

        :param concept: Inspect this concept surface forms.
        :param n: Maximum number of unique surface forms returned
        :return: set -- Set with maximum of `n` surface forms of `concept`
        """
        if self._surface_strings is None:
            raise NoRelevantData('Relevant surface data is not available!')

        data = self._surface_strings
        data = data[data.concept.str.lower() == concept.lower()]
        surface_forms = list(data.surface_string.unique())
        return set(surface_forms[:n])


class CategoriesDataset(ApiCallDataset):
    """Categories dataset container with easy aggregation
    capabilities.
    """
    def __init__(self, categories):
        """Initialize instance by providing categories data set.

        :param categories: List of document category probabilities
        :type categories: pandas.DataFrame
        """
        self._categories = categories

    def categories(self):
        """Aggregates categories across the whole dataset.

        :return: pandas.Series --
        """
        if self._categories is None:
            raise NoRelevantData('Relevant category data is not available!')

        cat = self._categories
        all_cats = cat.groupby('category')['probability'].mean()
        all_cats.sort_values(ascending=False, inplace=True)
        all_cats.rename('Probability', inplace=True)
        all_cats._plot_id = codes.AGGREGATED_CATEGORIES
        all_cats.index.name = 'Category'
        return all_cats

    def main_category(self):
        """Finds the main category of a dataset.

        :return: str -- Name of main category.
        """
        if self._categories is None:
            raise NoRelevantData('Relevant category data is not available!')

        cat = self._categories
        all_cats = cat.groupby('category')['probability'].mean()
        return all_cats.sort_values(ascending=False).index[0]


class SentimentDataset(ApiCallDataset):
    """Sentiment dataset container with easy aggregation
    capabilities.

    """
    def __init__(self, sentiments):
        """Initialize instance by providing sentiments data set.

        :param sentiments: List of document sentiment inclinations
        :type sentiments: pandas.DataFrame
        """
        self._sentiments = sentiments

    def average_sentiment(self):
        """Computes and returns average document sentiment. Result is a number
        from [-1,1], where higher number means more positive sentiment.

        :return: float -- Average document sentiment
        """
        if self._sentiments is None:
            raise NoRelevantData('Relevant sentiment data is not available!')

        sen = self._sentiments
        return sen.sentiment_value.mean()


class ABSADataset(ApiCallDataset):
    """ABSA data set container that will provides easy aggregation
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
        tuple. Entities whose entity_type does not start with given one or that
        are not in the dataset will always have zero count. Setting normalize
        will turn absolute counts into relative percentages.

        Specifying *entity_type* is intended to be used only with
        normalization. If used without *normalize* set it will have no effect
        except for possible before mentioned zeroing. When used with *normalize*
        set result percentages will reflect counts only within specified
        *concept_type* instead of the whole dataset.

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
            counts = counts.reindex(entity)
        elif isinstance(entity, set):
            counts = counts.reindex(list(entity))
        else:
            counts = counts.reindex(entity)

        result = counts.rename('Count').replace(np.nan, 0)
        result.index.name = _capitalize(entity_type) or 'Entity'
        if not normalize:
            result = result.astype(int)
        result._plot_id = codes.ENTITY_FREQUENCY
        return result

    def most_common_entities(self, n=15, entity_type='', normalize=False):
        """Counts entities and returns n most occurring ones sorted by their
        count descending. Counted entities can be filtered by their type using
        *entity_type* and returned counts can be normalized with *normalize*.

        If both *entity_type* and *normalize* are specified entity ratios
        will be computed only from entity counts within given *entity_type*.

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
        result = result.rename('Count')
        result._plot_id = codes.MOST_COMMON_ENTITIES
        result.index.name = _capitalize(entity_type) or 'Entity'
        return result

    def least_common_entities(self, n=15, entity_type='', normalize=False):
        """Counts entities and returns n least frequent ones sorted by their
        count ascending. Counted entities can be filtered by their type using
        *entity_type* and returned counts can be normalized with *normalize*.

        If both *entity_type* and *normalize* are specified entity ratios
        will be computed only from entity counts within given *entity_type*.

        :param n: Maximum number of least frequent entities to return
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
        result.index.name = _capitalize(entity_type) or 'Entity'
        return result

    def co_occurring_entities(self, entity, n=15, entity_type=''):
        """Find *n* entities co-occurring frequently in texts of this dataset
        with given entity, sorted descending. Co-occurring entities can be
        filtered by their type.

        :param entity: Entity to inspect for co-occurring entities
        :type entity: str
        :param n: Maximum count of returned entities
        :type n: int
        :param entity_type: Limit co-occurring entity counts only to this type
         of entities.
        :type entity_type: str
        :return: pandas.Series -- Co-occurring entity names as index and their
         counts as values sorted descending
        """
        if self._entities is None:
            raise NoRelevantData('Relevant entity data is not available!')

        index_name = _capitalize(entity_type) or 'Entity'

        ent, doc_txt = self._entities, ['doc_id', 'text_order']
        entity_filter = ent.entity_name.str.lower() == entity.lower()
        docs = ent[entity_filter][doc_txt].drop_duplicates()
        if docs.shape[0] == 0:
            result = pd.Series([]).rename('Count')
            result.index.name = index_name
            return result

        docs = docs.set_index(doc_txt)
        type_filter = ent.entity_type.str.startswith(entity_type)
        ent = ent[type_filter & (entity_filter == False)].set_index(doc_txt)
        result = docs.join(ent, how='inner')
        if result.shape[0] == 0:
            result = pd.Series([]).rename('Count')
            result.index.name = index_name
            return result

        result = result.groupby('entity_name').size().rename('Count')
        result = result.sort_values(ascending=False)[:n]
        result._plot_id = codes.CO_OCCURING_ENTITIES
        result._entity = entity
        result.index.name = index_name
        return result

    def best_rated_entities(self, n=15, entity_type=''):
        """Find top *n* rated entities in this dataset sorted descending
        by their mean rating.

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
        rels = rels[rels.sentiment_value.abs() < 100]
        ent_evals = pd.merge(rels, ents, 'inner', on=idx)
        ent_evals = ent_evals[ent_evals.entity_type.str.startswith(entity_type)]
        agg = {'sentiment_value': 'mean'}
        mean_evals = ent_evals.groupby('entity_name').agg(agg)
        mean_evals = mean_evals.sentiment_value.rename('Sentiment')
        result = mean_evals.sort_values(ascending=False)[:n]
        result._plot_id = codes.BEST_RATED_ENTITIES
        result.index.name = _capitalize(entity_type) or 'Entity'
        return result

    def worst_rated_entities(self, n=15, entity_type=''):
        """Find *n* worst rated entities in this dataset sorted ascending
        by their mean rating.

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
        rels = rels[rels.sentiment_value.abs() < 100]
        ent_evals = rels.set_index(idx).join(ents.set_index(idx)).reset_index()
        ent_evals = ent_evals[ent_evals.entity_type.str.startswith(entity_type)]
        agg = {'sentiment_value': 'mean'}
        mean_evals = ent_evals.groupby('entity_name').agg(agg)
        mean_evals = mean_evals.sentiment_value.rename('Sentiment')
        result = mean_evals.sort_values()[:n]
        result._plot_id = codes.WORST_RATED_ENTITIES
        result.index.name = _capitalize(entity_type) or 'Entity'
        return result

    def surface_strings(self, entity):
        """Returns list of surface strings for each entity specified in *entity*
        as a dictionary.

        :param entity: Name of entities to find in normalized texts
        :type entity: tuple, list, set or str
        :return: dict -- Map where keys are entity names and values are lists
         of normalized strings
        """
        if self._relations is None or self._relations_entities is None:
            raise NoRelevantData('Relevant relation data is not available!')

        if not isinstance(entity, (tuple, list, set)):
            entity = {entity}

        idx = ['doc_id', 'text_order', 'relation_id', 'entity_name']
        rels, ents = self._relations, self._relations_entities
        ents = ents[ents.entity_name.isin(entity)][idx].drop_duplicates()
        grp = pd.merge(rels, ents, on=idx[:3]).groupby('entity_name')

        result = {key: [] for key in entity}
        result.update({
            entity_name: grp.get_group(entity_name)['surface_string'].tolist()
            for entity_name in grp.groups
        })
        return result

    def entity_texts(self, entity):
        """Returns list of normalized texts where each *entity* can be found
        as a dictionary.

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
        rels = rels[rels.sentiment_value.abs() < 100]
        all_ent_evals = pd.merge(rels, ents, on=idx)

        if not isinstance(entity, (tuple, list, set)):
            entity = {entity}

        entity_filter = all_ent_evals.entity_name.isin(set(entity))
        entity_evals = all_ent_evals[entity_filter]

        means = entity_evals.groupby('entity_name')['sentiment_value'].mean()
        means.index.name = 'Entity'
        result = means.reindex(list(entity)).rename('Sentiment')
        result._plot_id = codes.ENTITY_SENTIMENT
        return result


class DatasetLoader(object):
    """Loads analysed data obtained via Anacode API from various formats.
    """
    def __init__(self, concepts=None, concepts_surface_strings=None,
                 categories=None, sentiments=None,
                 absa_entities=None, absa_normalized_texts=None,
                 absa_relations=None, absa_relations_entities=None,
                 absa_evaluations=None, absa_evaluations_entities=None):
        """Will construct DatasetLoader instance that is aware of what data is
        available to it. Raises ValueError if no data was provided.

        Data frames are expected to have format that corresponds to format that
        :class:`anacode.api.writers.Writer` would write.

        :param concepts: List of found concepts with metadata
        :type concepts: pandas.DataFrame
        :param concepts_surface_strings: List of strings realizing concepts
        :type concepts_surface_strings: pandas.DataFrame
        :param categories: List of document category probabilities
        :type categories: pandas.DataFrame
        :param sentiments: List of document sentiment polarities
        :type sentiments: pandas.DataFrame
        :param absa_entities: List of absa entities used in texts
        :type absa_entities: pandas.DataFrame
        :param absa_normalized_texts: List of Chinese normalized strings identified and analyzed by absa
        :type absa_normalized_texts: pandas.DataFrame
        :param absa_relations: List of absa relations with metadata
        :type absa_relations: pandas.DataFrame
        :param absa_relations_entities: List of absa entities used in relations
        :type absa_relations_entities: pandas.DataFrame
        :param absa_evaluations: List of absa evaluations
        :type absa_evaluations: pandas.DataFrame
        :param absa_evaluations_entities: List of absa entities used in evaluations
        :type absa_evaluations_entities: pandas.DataFrame
        """
        self.has_categories = categories is not None
        self.has_concepts = concepts is not None or \
            concepts_surface_strings is not None
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
            self._concepts_surface_strings = concepts_surface_strings
        else:
            self._concepts = self._concepts_surface_strings = None

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
        """If item is the name of linguistic dataset known to DatasetLoader,
        it will return the corresponding dataset. If the dataset is not found,
        None is returned. If item is not recognized, a KeyError is thrown.

        :param item: possible values: categories, concepts,
         concepts_surface_strings, sentiments, absa_entities,
         absa_normalized_texts, absa_relations, absa_relations_entities,
         absa_evaluations, absa_evaluations_entities
        :type item: str
        :return: pandas.DataFrame -- DataFrame with requested data if found, else None
        """
        dataset_map = {
            'categories': self._categories,
            'concepts': self._concepts,
            'concepts_surface_strings': self._concepts_surface_strings,
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
        exp = self._concepts_surface_strings
        concepts = set(concepts)
        if con is not None:
            self._concepts = con[con.concept.isin(concepts) == False]
        if exp is not None:
            exp = exp[exp.concept.isin(concepts) == False]
            self._concepts_surface_strings = exp

    @property
    def concepts(self):
        """Creates new ConceptsDataset if data is available.

        :return: :class:`anacode.agg.aggregations.ConceptsDataset` --
        """
        if self.has_concepts:
            return ConceptsDataset(self._concepts,
                                   self._concepts_surface_strings)
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
    def from_path(cls, path, backup_suffix=''):
        """Initializes DatasetLoader from AnacodeAPI csv files present in given
        path. You could have obtained these by using
        :class:`anacode.api.writers.CSVWriter` to write your request results
        when you were querying AnacodeAPI.

        :param path: Path to folder where AnacodeAPI analysis is stored in csv
         files
        :type path: str
        :param backup_suffix: If you want to load older dataset from file that
         has been backed up by toolkit, use this to specify suffix of file names
        :type backup_suffix: str
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
                if backup_suffix:
                    file_name = '%s_%s' % (file_name, backup_suffix)
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
    def from_api_result(cls, result):
        """Initializes DatasetLoader from API JSON output. Works with both
        single analysis result and with list of analyses results.

        :param result: Either single API JSON analysis dict or list of them
        :return: :class:`anacode.agg.DatasetLoader` -- DatasetLoader with
         available analysis data loaded
        """
        frame_writer = writers.DataFrameWriter()
        frame_writer.init()
        if isinstance(result, list):
            for analysis in result:
                frame_writer.write_analysis(analysis)
        else:
            frame_writer.write_analysis(result)
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
            concepts_surface_strings=f(self._concepts_surface_strings),
            categories=f(self._categories), sentiments=f(self._sentiments),
            absa_entities=f(self._absa_entities),
            absa_normalized_texts=f(self._absa_normalized_texts),
            absa_evaluations=f(self._absa_evaluations),
            absa_evaluations_entities=f(self._absa_evaluations_entities),
            absa_relations=f(self._absa_relations),
            absa_relations_entities=f(self._absa_relations_entities),
        )
