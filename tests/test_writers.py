import pytest
from datetime import datetime
from freezegun import freeze_time
from anacode.api import writers


@pytest.fixture
def concepts():
    return [
        [
            {
                'concept': 'Lenovo',
                'expressions': {'lenovo': 1},
                'freq': 1,
                'relevance_score': 1.0,
                'type': 'brand'
            },
        ],
    ]


@freeze_time(datetime(2016, 12, 6, 18, 0, 6))
class TestBackup:
    def test_backup_works(self, tmpdir):
        target = tmpdir.mkdir('target')
        target.join('concepts.csv').write('content')
        writers.backup(str(target), ['concepts.csv'])
        contents = [f.basename for f in target.listdir()]
        assert 'concepts.csv' not in contents
        assert 'concepts.csv_20161206180006' in contents

    def test_backup_returns_files(self, tmpdir):
        target = tmpdir.mkdir('target')
        target.join('concepts.csv').write('content')
        backed_up = writers.backup(str(target), ['concepts.csv'])
        assert backed_up == ['concepts.csv_20161206180006']

    def test_no_file_no_backup(self, tmpdir):
        target = tmpdir.mkdir('target')
        target.join('concepts.csv').write('content')
        backed_up = writers.backup(str(target), ['nofile.csv'])
        contents = [f.basename for f in target.listdir()]
        assert len(backed_up) == 0
        assert contents == ['concepts.csv']


class TestCsvWriter:
    def test_can_init_in_file(self):
        csv_writer = writers.CSVWriter('/tmp/test')
        assert csv_writer.target_dir == '/tmp/test'

    def test_concepts_file_have_header(self, tmpdir, concepts):
        target = tmpdir.mkdir('target')
        csv_writer = writers.CSVWriter(str(target))
        csv_writer.init()
        csv_writer.write_concepts(concepts)
        csv_writer.close()
        contents = [f.basename for f in target.listdir()]
        assert 'concepts.csv' in contents
        header = target.join('concepts.csv').readlines()[0].strip()
        assert 'doc_id' in header
        assert 'concept' in header
        assert 'freq' in header
        assert 'relevance_score' in header
        assert 'concept_type' in header

    def test_can_write_concepts(self, tmpdir, concepts):
        target = tmpdir.mkdir('target')
        csv_writer = writers.CSVWriter(str(target))
        csv_writer.init()
        csv_writer.write_concepts(concepts)
        csv_writer.close()
        contents = [f.basename for f in target.listdir()]
        assert 'concepts.csv' in contents
        file_lines = target.join('concepts.csv').readlines()
        assert len(file_lines) == 2
        row = file_lines[1].strip().split(',')
        assert row[0] == '0'
        assert row[1] == 'Lenovo'
        assert row[2] == '1'
        assert row[3] == '1.0'
        assert row[4] == 'brand'
