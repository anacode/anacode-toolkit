import os
import csv
import datetime
import pandas as pd
from itertools import chain
from functools import partial



from anacode.api import codes


def backup(root, files):
    """Backs up `files` from `root` directory and return list of backed up
    file names. Backed up files will have datetime suffix appended to original
    file name.

    :param root: Absolute path to folder where files to backup are located
    :param files: Names of files that needs backing up
    :return: List of backed up file names
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
    'categories': ['doc_id', 'text_order', 'category', 'probability'],
    'concepts': ['doc_id', 'text_order', 'concept', 'freq',
                 'relevance_score', 'concept_type'],
    'concepts_expressions': ['doc_id', 'text_order', 'concept', 'expression'],
    'sentiments': ['doc_id', 'text_order', 'positive', 'negative'],
    'absa_entities': ['doc_id', 'text_order', 'entity_name', 'entity_type',
                      'surface_string', 'text_span'],
    'absa_normalized_texts': ['doc_id', 'text_order', 'normalized_text'],
    'absa_relations': ['doc_id', 'text_order', 'relation_id',
                       'opinion_holder', 'restriction', 'sentiment',
                       'is_external', 'surface_string', 'text_span'],
    'absa_relations_entities': ['doc_id', 'text_order', 'relation_id',
                                'entity_type', 'entity_name'],
    'absa_evaluations': ['doc_id', 'text_order', 'evaluation_id',
                         'sentiment', 'surface_string', 'text_span'],
    'absa_evaluations_entities': ['doc_id', 'text_order', 'evaluation_id',
                                  'entity_type', 'entity_name'],
}


# `anacode.agg.aggregations.ApiDataset.from_path` depends
# on ordering of files defined in values here
CSV_FILES = {
    'categories': ['categories.csv'],
    'concepts': ['concepts.csv', 'concepts_expressions.csv'],
    'sentiments': ['sentiment.csv'],
    'absa': [
        'absa_entities.csv', 'absa_normalized_texts.csv',
        'absa_relations.csv', 'absa_relations_entities.csv',
        'absa_evaluations.csv', 'absa_evaluations_entities.csv'
    ]
}


def categories_to_list(doc_id, analyzed):
    cat_list = []
    for text_order, text_analyzed in enumerate(analyzed):
        for result_dict in text_analyzed:
            row = [doc_id, text_order, result_dict.get('label'),
                   result_dict.get('probability')]
            cat_list.append(row)
    return {'categories': cat_list}


def concepts_to_list(doc_id, analyzed):
    con_list, exp_list = [], []
    for text_order, text_analyzed in enumerate(analyzed):
        for concept in text_analyzed:
            row = [doc_id, text_order, concept.get('concept'),
                   concept.get('freq'), concept.get('relevance_score'),
                   concept.get('type')]
            con_list.append(row)
            try:
                freq = int(concept.get('freq'))
            except ValueError:
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


class Writer:
    def __init__(self):
        self.ids = {'scrape': 0, 'category': 0, 'concept': 0,
                    'sentiment': 0, 'absa': 0}

    def _new_doc_id(self, call):
        current_id = self.ids[call]
        self.ids[call] += 1
        return current_id

    def write_row(self, call_type, call_result):
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

    def add_new_data_from_dict(self, new_data: dict):
        pass

    def write_scrape(self, scraped):
        pass

    def write_categories(self, analyzed):
        doc_id = self._new_doc_id('category')
        new_data = categories_to_list(doc_id, analyzed)
        self.add_new_data_from_dict(new_data)

    def write_concepts(self, analyzed):
        doc_id = self._new_doc_id('concept')
        new_data = concepts_to_list(doc_id, analyzed)
        self.add_new_data_from_dict(new_data)

    def write_sentiment(self, analyzed):
        doc_id = self._new_doc_id('sentiment')
        new_data = sentiments_to_list(doc_id, analyzed)
        self.add_new_data_from_dict(new_data)

    def write_absa(self, analyzed):
        doc_id = self._new_doc_id('absa')
        new_data = absa_to_list(doc_id, analyzed)
        self.add_new_data_from_dict(new_data)

    def write_bulk(self, results: iter):
        for call_type, call_result in results:
            self.write_row(call_type, call_result)

    def init(self):
        pass

    def close(self):
        pass


class DataFrameWriter(Writer):
    def __init__(self, frames: dict):
        super().__init__()
        self.frames = {} if frames is None else frames
        self._row_data = {}

    def init(self):
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
        for name, row in self._row_data.items():
            if len(row) > 0:
                self.frames[name] = pd.DataFrame(row, columns=HEADERS[name])
        self._row_data = {}

    def add_new_data_from_dict(self, new_data: dict):
        for name, row_list in new_data.items():
            self._row_data[name].extend(row_list)


class CSVWriter(Writer):
    def __init__(self, target_dir='.'):
        super().__init__()
        self.target_dir = os.path.abspath(os.path.expanduser(target_dir))
        self._files = {}
        self.csv = {}

    def _open_csv(self, csv_name):
        path = partial(os.path.join, self.target_dir)
        return open(path(csv_name), 'w', newline='')

    def init(self):
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

    def close(self):
        for name, file in self._files.items():
            try:
                file.close()
            except (IOError, AttributeError):
                print('Problem closing "{}"'.format(name))
        self._files = {}
        self.csv = {}

    def add_new_data_from_dict(self, new_data: dict):
        for name, row_list in new_data.items():
            self.csv[name].writerows(row_list)
