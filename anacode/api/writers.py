# -*- coding: utf-8 -*-
import os
import csv
import datetime
import pandas as pd
from itertools import chain
from functools import partial

from anacode import codes

def backup(root, files):
    """Backs up `files` from `root` directory and return list of backed up
    file names. Backed up files will have datetime suffix appended to original
    file name.

    :param root: Absolute path to folder where files to backup are located
    :type root: str
    :param files: Names of files that needs backing up
    :type files: str
    :return: list -- List of backed up file names
    """
    backed_up = []
    join = os.path.join
    root_contents = os.listdir(root)
    dt_str = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
    for file_name in files:
        if file_name not in root_contents:
            continue
        new_name = file_name + '_' + dt_str
        os.rename(join(root, file_name), join(root, new_name))
        backed_up.append(new_name)
    return backed_up


HEADERS = {
    'categories': [u'doc_id', u'text_order', u'category', u'probability'],
    'concepts': [u'doc_id', u'text_order', u'concept', u'freq',
                 u'relevance_score', u'concept_type'],
    'concepts_expressions': [u'doc_id', u'text_order', u'concept',
                             u'expression'],
    'sentiments': [u'doc_id', u'text_order', u'positive', u'negative'],
    'absa_entities': [u'doc_id', u'text_order', u'entity_name', u'entity_type',
                      u'surface_string', u'text_span'],
    'absa_normalized_texts': [u'doc_id', u'text_order', u'normalized_text'],
    'absa_relations': [u'doc_id', u'text_order', u'relation_id',
                       u'opinion_holder', u'restriction', u'sentiment',
                       u'is_external', u'surface_string', u'text_span'],
    'absa_relations_entities': [u'doc_id', u'text_order', u'relation_id',
                                u'entity_type', u'entity_name'],
    'absa_evaluations': [u'doc_id', u'text_order', u'evaluation_id',
                         u'sentiment', u'surface_string', u'text_span'],
    'absa_evaluations_entities': [u'doc_id', u'text_order', u'evaluation_id',
                                  u'entity_type', u'entity_name'],
}


# `anacode.agg.aggregations.ApiDataset.from_path` depends
# on ordering of files defined in values here
CSV_FILES = {
    'categories': ['categories.csv'],
    'concepts': ['concepts.csv', 'concepts_expressions.csv'],
    'sentiments': ['sentiments.csv'],
    'absa': [
        'absa_entities.csv', 'absa_normalized_texts.csv',
        'absa_relations.csv', 'absa_relations_entities.csv',
        'absa_evaluations.csv', 'absa_evaluations_entities.csv'
    ]
}


def categories_to_list(doc_id, analyzed):
    """Converts categories response to flat list with doc_id included.

    :param doc_id: Will be inserted to each row as first element
    :param analyzed: Response json from anacode api for categories call
    :type analyzed: list
    :return: dict -- Dictionary with one key 'categories' pointing to flat list
     of categories
    """
    cat_list = []
    for text_order, text_analyzed in enumerate(analyzed):
        for result_dict in text_analyzed:
            row = [doc_id, text_order, result_dict.get('label'),
                   result_dict.get('probability')]
            cat_list.append(row)
    return {'categories': cat_list}


def concepts_to_list(doc_id, analyzed):
    """Converts concepts response to flat lists with doc_id included

    :param doc_id: Will be inserted to each row as first element
    :param analyzed: Response json from anacode api for concepts call
    :type analyzed: list
    :return: dict -- Dictionary with two keys: 'concepts' pointing to flat list
     of found concepts and their metadata and 'concepts_expressions' pointing to
     flat list of expressions realizing found concepts
    """
    con_list, exp_list = [], []
    for text_order, text_analyzed in enumerate(analyzed):
        for concept in text_analyzed:
            row = [doc_id, text_order, concept.get('concept'),
                   concept.get('freq'), concept.get('relevance_score'),
                   concept.get('type')]
            con_list.append(row)
            try:
                freq = int(concept.get('freq'))
            except (ValueError, TypeError):
                freq = 0
            for string, count in concept.get('expressions', {}).items():
                for _ in range(count):
                    freq -= 1
                    exp_list.append([doc_id, text_order,
                                     concept.get('concept'), string])
                for _ in range(freq):
                    exp_list.append([doc_id, text_order,
                                    concept.get('concept'), None])
    return {'concepts': con_list, 'concepts_expressions': exp_list}


def sentiments_to_list(doc_id, analyzed):
    """Converts sentiments response to flat lists with doc_id included

    :param doc_id: Will be inserted to each row as first element
    :param analyzed: Response json from anacode api for sentiment call
    :type analyzed: list
    :return: dict -- Dictionary with one key 'sentiments' pointing to flat list
     of sentiment probabilities
    """
    sen_list = []
    for text_order, sentiment in enumerate(analyzed):
        sentiment_map = {
            sentiment[0]['label']: sentiment[0]['probability'],
            sentiment[1]['label']: sentiment[1]['probability'],
        }
        row = [doc_id, text_order, sentiment_map['positive'],
               sentiment_map['negative']]
        sen_list.append(row)
    return {'sentiments': sen_list}


def _absa_entities_to_list(doc_id, order, entities):
    ent_list = []
    for entity_dict in entities:
        text_span = '-'.join(map(str, entity_dict['text']['span']))
        surface_string = entity_dict['text']['surface_string']
        for semantics in entity_dict['semantics']:
            row = [doc_id, order, semantics['value'], semantics['type'],
                   surface_string, text_span]
            ent_list.append(row)
    return ent_list


def _absa_normalized_text_to_list(doc_id, order, normalized_text):
    return [[doc_id, order, normalized_text]]


def _absa_relations_to_list(doc_id, order, relations):
    rel_list, ent_list = [], []
    for rel_index, rel in enumerate(relations):
        rel_row = [doc_id, order, rel_index,
                   rel['semantics']['opinion_holder'],
                   rel['semantics']['restriction'],
                   rel['semantics']['value'], rel['external_entity'],
                   rel['text']['surface_string'],
                   '-'.join(map(str, rel['text']['span']))]
        rel_list.append(rel_row)
        for ent in rel['semantics']['entity']:
            ent_row = [doc_id, order, rel_index, ent['type'], ent['value']]
            ent_list.append(ent_row)
    return rel_list, ent_list


def _absa_evaluations_to_list(doc_id, order, evaluations):
    eval_list, ent_list = [], []
    for eval_index, evaluation in enumerate(evaluations):
        eval_row = [doc_id, order, eval_index,
                    evaluation['semantics']['value'],
                    evaluation['text']['surface_string'],
                    '-'.join(map(str, evaluation['text']['span']))]
        eval_list.append(eval_row)
        for ent in evaluation['semantics']['entity']:
            ent_row = [doc_id, order, eval_index, ent['type'], ent['value']]
            ent_list.append(ent_row)
    return eval_list, ent_list


def absa_to_list(doc_id, analyzed):
    """Converts ABSA response to flat lists with doc_id included

    :param doc_id: Will be inserted to each row as first element
    :param analyzed: Response json from anacode api for ABSA call
    :type analyzed: list
    :return: dict -- Dictionary with six keys: 'absa_entities' pointing to flat
     list of found entities with metadata, 'absa_normalized_texts' pointing to
     flat list of normalized chinese texts, 'absa_relations' pointing to found
     entity relations with metadata, 'absa_relations_entities' pointing to flat
     list of entities that belong to absa relations, 'absa_evaluations'
     pointing to flat list of entity evaluations with metadata and
     'absa_evaluations_entities' specifying entities in absa_evaluations
    """
    absa = {
        'absa_entities': [],
        'absa_normalized_texts': [],
        'absa_relations': [],
        'absa_relations_entities': [],
        'absa_evaluations': [],
        'absa_evaluations_entities': []
    }
    for text_order, text_analyzed in enumerate(analyzed):
        entities = text_analyzed['entities']
        ents = _absa_entities_to_list(doc_id, text_order, entities)
        text = text_analyzed['normalized_text']
        texts = _absa_normalized_text_to_list(doc_id, text_order, text)
        relations = text_analyzed['relations']
        rels, rel_ents = _absa_relations_to_list(doc_id, text_order, relations)
        evaluations = text_analyzed['evaluations']
        evals, eval_ents = _absa_evaluations_to_list(doc_id, text_order,
                                                     evaluations)
        absa['absa_entities'].extend(ents)
        absa['absa_normalized_texts'].extend(texts)
        absa['absa_relations'].extend(rels)
        absa['absa_relations_entities'].extend(rel_ents)
        absa['absa_evaluations'].extend(evals)
        absa['absa_evaluations_entities'].extend(eval_ents)
    return absa


class Writer(object):
    """Base "abstract" class containing common methods that are expected to be
    needed by all implementations of Writer interface.

    Writer interface consists of init, close and write_bulk methods.

    """
    def __init__(self):
        self.ids = {'scrape': 0, 'category': 0, 'concept': 0,
                    'sentiment': 0, 'absa': 0}

    def _new_doc_id(self, call):
        current_id = self.ids[call]
        self.ids[call] += 1
        return current_id

    def write_row(self, call_type, call_result):
        """Decides what kind of data it got and calls appropriate write method.

        :param call_type: Library's ID of anacode call
        :type call_type: int
        :param call_result: JSON response from anacode api
        :type call_result: list
        """
        if call_type == codes.SCRAPE:
            self.write_scrape(call_result)
        if call_type == codes.CATEGORIES:
            self.write_categories(call_result)
        if call_type == codes.CONCEPTS:
            self.write_concepts(call_result)
        if call_type == codes.SENTIMENT:
            self.write_sentiment(call_result)
        if call_type == codes.ABSA:
            self.write_absa(call_result)

    def _add_new_data_from_dict(self, new_data):
        """Not implemented here!

        Write methods use this to submit new anacode data for storage.

        :param new_data: Dictionary, keys are data sets names and values are
         flat lists of rows
        :type new_data: dict
        """
        pass

    def write_scrape(self, scraped):
        pass

    def write_categories(self, analyzed):
        """Converts categories call response to flat lists and stores them using
        add_new_data_from_dict.

        :param analyzed: JSON categories response
        :type analyzed: list
        """
        doc_id = self._new_doc_id('category')
        new_data = categories_to_list(doc_id, analyzed)
        self._add_new_data_from_dict(new_data)

    def write_concepts(self, analyzed):
        """Converts concepts call response to flat lists and stores them using
        add_new_data_from_dict.

        :param analyzed: JSON concepts response
        :type analyzed: list
        """
        doc_id = self._new_doc_id('concept')
        new_data = concepts_to_list(doc_id, analyzed)
        self._add_new_data_from_dict(new_data)

    def write_sentiment(self, analyzed):
        """Converts sentiment call response to flat lists and stores them using
        add_new_data_from_dict.

        :param analyzed: JSON sentiment response
        :type analyzed: list
        """
        doc_id = self._new_doc_id('sentiment')
        new_data = sentiments_to_list(doc_id, analyzed)
        self._add_new_data_from_dict(new_data)

    def write_absa(self, analyzed):
        """Converts absa call response to flat lists and stores them using
        add_new_data_from_dict.

        :param analyzed: JSON absa response
        :type analyzed: list
        """
        doc_id = self._new_doc_id('absa')
        new_data = absa_to_list(doc_id, analyzed)
        self._add_new_data_from_dict(new_data)

    def write_bulk(self, results):
        """Stores multiple anacode api's JSON responses marked with call IDs.

        :param results: List of anacode responses with IDs of calls used
        :type results: list
        """
        for call_type, call_result in results:
            self.write_row(call_type, call_result)

    def init(self):
        """Not implemented here! Each subclass should decide what to do here."""
        pass

    def close(self):
        """Not implemented here! Each subclass should decide what to do here."""
        pass


class DataFrameWriter(Writer):
    """Capable of writing anacode api output into pandas.DataFrame instances."""
    def __init__(self, frames=None):
        """Initializes dictionary of result frames. Alternatively uses given
        frames dict for storage.

        :param frames: Might be specified to use this instead of new dict
        :type frames: dict
        """
        super(DataFrameWriter, self).__init__()
        self.frames = {} if frames is None else frames
        self._row_data = {}

    def init(self):
        """Initialized empty lists for each possible data frame."""
        self._row_data = {
            'categories': [],
            'concepts': [],
            'concepts_expressions': [],
            'sentiments': [],
            'absa_entities': [],
            'absa_normalized_texts': [],
            'absa_relations': [],
            'absa_relations_entities': [],
            'absa_evaluations': [],
            'absa_evaluations_entities': [],
        }

    def close(self):
        """Creates pandas data frames to self.frames dict and clears internal
        state.
        """
        for name, row in self._row_data.items():
            if len(row) > 0:
                self.frames[name] = pd.DataFrame(row, columns=HEADERS[name])
        self._row_data = {}

    def _add_new_data_from_dict(self, new_data):
        """Stores anacode api result converted to flat lists.

        :param new_data: Anacode api result
        :param new_data: list
        """
        for name, row_list in new_data.items():
            self._row_data[name].extend(row_list)


class CSVWriter(Writer):
    def __init__(self, target_dir='.'):
        """Initializes Writer to store anancode api analysis in target_dir in
        csv files.

        :param target_dir: Path to file where to store csv-s
        :type target_dir: str
        """
        super(CSVWriter, self).__init__()
        self.target_dir = os.path.abspath(os.path.expanduser(target_dir))
        self._files = {}
        self.csv = {}

    def _open_csv(self, csv_name):
        path = partial(os.path.join, self.target_dir)
        try:
            return open(path(csv_name), 'w', newline='')
        except TypeError:
            return open(path(csv_name), 'wb')

    def init(self):
        """Opens all csv files for writing and write headers to them."""
        self.close()
        backup(self.target_dir, chain.from_iterable(CSV_FILES.values()))

        self._files = {
            'categories': self._open_csv('categories.csv'),
            'concepts': self._open_csv('concepts.csv'),
            'concepts_expressions': self._open_csv('concepts_expressions.csv'),
            'sentiments': self._open_csv('sentiments.csv'),
            'absa_entities': self._open_csv('absa_entities.csv'),
            'absa_normalized_texts': self._open_csv(
                'absa_normalized_texts.csv'
            ),
            'absa_relations': self._open_csv('absa_relations.csv'),
            'absa_relations_entities': self._open_csv(
                'absa_relations_entities.csv'
            ),
            'absa_evaluations': self._open_csv('absa_evaluations.csv'),
            'absa_evaluations_entities': self._open_csv(
                'absa_evaluations_entities.csv'
            ),
        }
        self.csv = {name: csv.writer(fp) for name, fp in self._files.items()}
        for name, writer in self.csv.items():
            writer.writerow(HEADERS[name])

    def _csv_has_content(self, csv_path):
        if not os.path.isfile(csv_path):
            return False

        with open(csv_path) as fp:
            for line_count, line in enumerate(fp):
                if line_count == 1:
                    return True
        return False

    def close(self):
        """Closes all csv files and removes empty ones."""
        for name, file in self._files.items():
            try:
                file.close()
            except (IOError, AttributeError):
                print('Problem closing "{}"'.format(name))

        for file_list in CSV_FILES.values():
            for file_name in file_list:
                path = os.path.join(self.target_dir, file_name)
                if os.path.isfile(path) and not self._csv_has_content(path):
                    os.unlink(path)

        self._files = {}
        self.csv = {}

    def _add_new_data_from_dict(self, new_data):
        """Stores anacode api result converted to flat lists.

        :param new_data: Anacode api result
        :param new_data: list
        """
        for name, row_list in new_data.items():
            self.csv[name].writerows(row_list)
