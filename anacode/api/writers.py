import os
import csv
import datetime
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


class CSVWriter:
    FILES = ['concepts.csv', 'concepts_expressions.csv',
             'sentiment.csv',
             'absa_entities.csv', 'absa_normalized_texts.csv',
             'absa_relations.csv', 'absa_relations_entities.csv',
             'absa_evaluations.csv', 'absa_evaluations_entities.csv']
    HEADERS = {
        'concepts': ['doc_id', 'concept', 'freq', 'relevance_score',
                     'concept_type'],
        'concepts_expr': ['doc_id', 'concept', 'expression'],
        'sentiment': ['doc_id', 'positive', 'negative'],

    }

    def __init__(self, target_dir='.'):
        self.ids = {'scrape': 0, 'category': 0, 'concept': 0,
                    'sentiment': 0, 'absa': 0}
        self.target_dir = os.path.abspath(os.path.expanduser(target_dir))
        self.files = {}

    def init(self) -> dict:
        self.close()
        backup(self.target_dir, self.FILES)

        path = partial(os.path.join, self.target_dir)
        opened_files = {
            'concepts': open(path('concepts.csv'), 'w', newline=''),
            'concepts_expr': open(path('concepts_expressions.csv'), 'w',
                                  newline=''),
            'sentiment': open(path('senfiment.csv'), 'w', newline=''),
        }
        excel = csv.get_dialect('excel')
        for name, fp in opened_files.items():
            headers = self.HEADERS[name]
            fp.write(','.join(headers))
            fp.write(excel.lineterminator)

        self.files = opened_files

    def close(self):
        for file in self.files.values():
            file.close()
        self.files = {}

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

    def write_bulk(self, results: iter):
        for call_type, call_result in results:
            self.write_row(call_type, call_result)

    def write_scrape(self, scraped):
        pass

    def write_categories(self, analyzed):
        doc_id = self.ids['category']
        self.ids['category'] += 1

    def write_concepts(self, analyzed):
        doc_id = self.ids['concept']
        self.ids['concept'] += 1

    def write_sentiment(self, analyzed):
        pass

    def write_absa(self, analyzed):
        pass
