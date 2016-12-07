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


@pytest.fixture
def longer_concepts():
    return [
        [
            {
                'concept': 'Lenovo',
                'expressions': {'lenovo': 1},
                'freq': 1,
                'relevance_score': 1.0,
                'type': 'brand'
            }
        ],
        [
            {
                'concept': 'Samsung',
                'expressions': {'samsung': 1},
                'freq': 1,
                'relevance_score': 1.0,
                'type': 'brand'
            }
        ]
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


def test_csvwriter_init_with_directory():
    csv_writer = writers.CSVWriter('/tmp/test')
    assert csv_writer.target_dir == '/tmp/test'


class TestCsvWriterConcepts:
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
        assert 'text_order' in header
        assert 'concept' in header
        assert 'freq' in header
        assert 'relevance_score' in header
        assert 'concept_type' in header

    def test_concepts_exprs_file_have_header(self, tmpdir, concepts):
        target = tmpdir.mkdir('target')
        csv_writer = writers.CSVWriter(str(target))
        csv_writer.init()
        csv_writer.write_concepts(concepts)
        csv_writer.close()
        contents = [f.basename for f in target.listdir()]
        assert 'concepts_expressions.csv' in contents
        header = target.join('concepts_expressions.csv').readlines()[0].strip()
        assert 'doc_id' in header
        assert 'text_order' in header
        assert 'concept' in header
        assert 'expression' in header

    def test_write_concepts(self, tmpdir, concepts):
        target = tmpdir.mkdir('target')
        csv_writer = writers.CSVWriter(str(target))
        csv_writer.init()
        csv_writer.write_concepts(concepts)
        csv_writer.close()
        file_lines = target.join('concepts.csv').readlines()
        assert len(file_lines) == 2
        row = file_lines[1].strip().split(',')
        assert row[0] == '0'
        assert row[1] == '0'
        assert row[2] == 'Lenovo'
        assert row[3] == '1'
        assert row[4] == '1.0'
        assert row[5] == 'brand'

    def test_write_exprs(self, tmpdir, concepts):
        target = tmpdir.mkdir('target')
        csv_writer = writers.CSVWriter(str(target))
        csv_writer.init()
        csv_writer.write_concepts(concepts)
        csv_writer.close()
        file_lines = target.join('concepts_expressions.csv').readlines()
        assert len(file_lines) == 2
        row = file_lines[1].strip().split(',')
        assert row[0] == '0'
        assert row[1] == '0'
        assert row[2] == 'Lenovo'
        assert row[3] == 'lenovo'

    def test_write_contents_from_multiple_texts(self, tmpdir, longer_concepts):
        target = tmpdir.mkdir('target')
        csv_writer = writers.CSVWriter(str(target))
        csv_writer.init()
        csv_writer.write_concepts(longer_concepts)
        csv_writer.close()
        file_lines = target.join('concepts.csv').readlines()
        assert len(file_lines) == 3
        row1 = file_lines[1].strip().split(',')
        assert row1[1] == '0'
        assert row1[2] == 'Lenovo'
        row2 = file_lines[2].strip().split(',')
        assert row2[1] == '1'
        assert row2[2] == 'Samsung'

    def test_write_exprs_from_multiple_texts(self, tmpdir, longer_concepts):
        target = tmpdir.mkdir('target')
        csv_writer = writers.CSVWriter(str(target))
        csv_writer.init()
        csv_writer.write_concepts(longer_concepts)
        csv_writer.close()
        file_lines = target.join('concepts_expressions.csv').readlines()
        assert len(file_lines) == 3
        row1 = file_lines[1].strip().split(',')
        assert row1[1] == '0'
        assert row1[2] == 'Lenovo'
        assert row1[3] == 'lenovo'
        row2 = file_lines[2].strip().split(',')
        assert row2[1] == '1'
        assert row2[2] == 'Samsung'
        assert row2[3] == 'samsung'


@pytest.fixture
def sentiments():
    return [
        [
            {'label': 'negative', 'probability': 0.7299562892999195},
            {'label': 'positive', 'probability': 0.2700437107000805}
        ],
        [
            {'label': 'negative', 'probability': 0.6668725094407698},
            {'label': 'positive', 'probability': 0.3331274905592302}
        ]
    ]


class TestCsvWriterSentiment:
    def test_write_sentiment_headers(self, tmpdir, sentiments):
        target = tmpdir.mkdir('target')
        csv_writer = writers.CSVWriter(str(target))
        csv_writer.init()
        csv_writer.write_sentiment(sentiments)
        csv_writer.close()
        contents = [f.basename for f in target.listdir()]
        assert 'sentiments.csv' in contents
        header = target.join('sentiments.csv').readlines()[0].strip()
        assert 'doc_id' in header
        assert 'text_order' in header
        assert 'positive' in header
        assert 'negative' in header

    def test_write_sentiment_values(self, tmpdir, sentiments):
        target = tmpdir.mkdir('target')
        csv_writer = writers.CSVWriter(str(target))
        csv_writer.init()
        csv_writer.write_sentiment(sentiments)
        csv_writer.close()
        file_lines = target.join('sentiments.csv').readlines()
        assert len(file_lines) == 3
        row1 = file_lines[1].strip().split(',')
        assert row1[0] == '0'
        assert row1[1] == '0'
        assert row1[2].startswith('0.27')
        assert row1[3].startswith('0.72')
        row2 = file_lines[2].strip().split(',')
        assert row2[0] == '0'
        assert row2[1] == '1'
        assert row2[2].startswith('0.33')
        assert row2[3].startswith('0.66')


