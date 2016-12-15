import pytest
from datetime import datetime
from freezegun import freeze_time
from anacode.api import writers


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


@pytest.fixture
def target(tmpdir):
    return tmpdir.mkdir('target')


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


@pytest.fixture
def csv_concepts(target, concepts):
    csv_writer = writers.CSVWriter(str(target))
    csv_writer.init()
    csv_writer.write_concepts(concepts)
    csv_writer.close()
    return csv_writer


class TestCsvWriterConcepts:
    def test_concepts_file_have_header(self, target, csv_concepts):
        contents = [f.basename for f in target.listdir()]
        assert 'concepts.csv' in contents
        file_lines = target.join('concepts.csv').readlines()
        header = file_lines[0].strip().split(',')
        assert header == ['doc_id', 'text_order', 'concept', 'freq',
                          'relevance_score', 'concept_type']

    def test_concepts_exprs_file_have_header(self, target, csv_concepts):
        contents = [f.basename for f in target.listdir()]
        assert 'concepts_expressions.csv' in contents
        file_lines = target.join('concepts_expressions.csv').readlines()
        header = file_lines[0].strip().split(',')
        assert header == ['doc_id', 'text_order', 'concept', 'expression']

    def test_write_concepts(self, target, csv_concepts):
        file_lines = target.join('concepts.csv').readlines()
        assert len(file_lines) == 3
        row1 = file_lines[1].strip().split(',')
        row2 = file_lines[2].strip().split(',')
        assert row1 == ['0', '0', 'Lenovo', '1', '1.0', 'brand']
        assert row2 == ['0', '1', 'Samsung', '1', '1.0', 'brand']

    def test_write_exprs(self, target, csv_concepts):
        file_lines = target.join('concepts_expressions.csv').readlines()
        assert len(file_lines) == 3
        row1 = file_lines[1].strip().split(',')
        row2 = file_lines[2].strip().split(',')
        assert row1 == ['0', '0', 'Lenovo', 'lenovo']
        assert row2 == ['0', '1', 'Samsung', 'samsung']


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


@pytest.fixture
def categories():
    return [
        [
            {'label': 'camera', 'probability': 0.44475978426332685},
            {'label': 'travel', 'probability': 0.2279223877672652},
            {'label': 'hr', 'probability': 0.09173477160494019},
            {'label': 'auto', 'probability': 0.06708061556120234},
            {'label': 'fashion', 'probability': 0.025414852323138004},
            {'label': 'finance', 'probability': 0.018507594185656784},
            {'label': 'food', 'probability': 0.010119412627783536},
            {'label': 'law', 'probability': 0.00965379302613669},
            {'label': 'education', 'probability': 0.009582090685450925},
            {'label': 'ce', 'probability': 0.009340358982552241},
            {'label': 'furniture', 'probability': 0.008684932567501653},
            {'label': 'internet', 'probability': 0.00778506882501582},
            {'label': 'babies', 'probability': 0.007096874411645032},
            {'label': 'fitness', 'probability': 0.0069576834053539675},
            {'label': 'health', 'probability': 0.006145046000728843},
            {'label': 'sports', 'probability': 0.006031221668762928},
            {'label': 'entertainment', 'probability': 0.005231272080964669},
            {'label': 'mobile', 'probability': 0.004967572280467443},
            {'label': 'beauty', 'probability': 0.00494888795526646},
            {'label': 'realestate', 'probability': 0.004493574861362339},
            {'label': 'energy', 'probability': 0.0040505145283132385},
            {'label': 'airline', 'probability': 0.003390457074009262},
            {'label': 'art', 'probability': 0.0028687491478624947},
            {'label': 'architecture', 'probability': 0.002822605573936816},
            {'label': 'music', 'probability': 0.0027084020379582676},
            {'label': 'hotel', 'probability': 0.002295792656008564},
            {'label': 'appliances', 'probability': 0.002193479986584827},
            {'label': 'books', 'probability': 0.001483402884988822},
            {'label': 'games', 'probability': 0.0010261026838245006},
            {'label': 'business', 'probability': 0.0007026983419913149}
        ],
        [
            {'label': 'games', 'probability': 0.39789969578523887},
            {'label': 'travel', 'probability': 0.11634739448945783},
            {'label': 'fashion', 'probability': 0.09168535069430538},
            {'label': 'law', 'probability': 0.04323751076891663},
            {'label': 'auto', 'probability': 0.041857526739422356},
            {'label': 'airline', 'probability': 0.035446480105636335},
            {'label': 'ce', 'probability': 0.03478883675405762},
            {'label': 'camera', 'probability': 0.02719330000509693},
            {'label': 'food', 'probability': 0.024219656311877134},
            {'label': 'finance', 'probability': 0.02301679246976262},
            {'label': 'education', 'probability': 0.022459608009340545},
            {'label': 'architecture', 'probability': 0.017837572573750626},
            {'label': 'beauty', 'probability': 0.015451481313075766},
            {'label': 'fitness', 'probability': 0.014332460323421978},
            {'label': 'babies', 'probability': 0.011144662880568099},
            {'label': 'health', 'probability': 0.010945923020829255},
            {'label': 'furniture', 'probability': 0.010466338721162467},
            {'label': 'hr', 'probability': 0.009210314423265968},
            {'label': 'mobile', 'probability': 0.008598212480182528},
            {'label': 'music', 'probability': 0.008036079511276282},
            {'label': 'internet', 'probability': 0.006370603094547427},
            {'label': 'hotel', 'probability': 0.005955447551681576},
            {'label': 'realestate', 'probability': 0.005121969573881132},
            {'label': 'entertainment', 'probability': 0.004570734302611687},
            {'label': 'energy', 'probability': 0.00424202672617446},
            {'label': 'appliances', 'probability': 0.004177990415535009},
            {'label': 'art', 'probability': 0.0021153603845123245},
            {'label': 'books', 'probability': 0.0013904052961039273},
            {'label': 'sports', 'probability': 0.0010192722188369773},
            {'label': 'business', 'probability': 0.0008609930554701703}
        ]
    ]


@pytest.fixture
def csv_categories(target, categories):
    csv_writer = writers.CSVWriter(str(target))
    csv_writer.init()
    csv_writer.write_categories(categories)
    csv_writer.close()
    return csv_writer


class TestCsvWriterCategories:
    def test_write_categories_headers(self, target, csv_categories):
        contents = [f.basename for f in target.listdir()]
        assert 'categories.csv' in contents
        file_lines = target.join('categories.csv').readlines()
        header = file_lines[0].strip().split(',')
        assert header == ['doc_id', 'text_order', 'category', 'probability']

    def test_write_categories(self, target, csv_categories):
        file_lines = target.join('categories.csv').readlines()
        assert len(file_lines) == 30 + 30 + 1
        assert any(line.startswith('0,0,camera,0.444') for line in file_lines)
        assert any(line.startswith('0,0,music,0.002') for line in file_lines)
        assert any(line.startswith('0,1,law,0.043') for line in file_lines)


@pytest.fixture
def absa():
    return [{
        'entities': [
            {
                'semantics': [
                    {'type': 'feature_subjective', 'value': 'OperationQuality'}
                ],
                'text': {'span': [2, 4], 'surface_string': '性能'}
            }
        ],
        'evaluations': [
            {
                'semantics': {
                    'entity': [
                        {'type': 'feature_quantitative', 'value': 'Safety'}
                    ],
                    'value': 2.0
                },
                'text': {'span': [0, 2], 'surface_string': '安全'}
            },
            {
                'semantics': {
                    'entity': [
                        {'type': 'feature_subjective', 'value': 'VisualAppearance'}
                    ],
                    'value': 3.5
                },
                'text': {'span': [7, 10], 'surface_string': '很帅气'}
            }
        ],
        'normalized_text': '安全性能很好，很帅气。',
        'relations': [
            {
                'external_entity': False,
                'semantics': {
                    'entity': [
                        {'type': 'feature_quantitative', 'value': 'Safety'},
                        {'type': 'feature_subjective', 'value': 'OperationQuality'}
                    ],
                    'opinion_holder': None,
                    'restriction': None,
                    'value': 2.0
                },
                'text': {'span': [0, 4], 'surface_string': '安全性能'}
            }
        ]
    }]


@pytest.fixture
def csv_absa(target, absa):
    csv_writer = writers.CSVWriter(str(target))
    csv_writer.init()
    csv_writer.write_absa(absa)
    csv_writer.close()
    return csv_writer


class TestCsvWriterAbsa:
    def test_absa_entities_headers(self, target, csv_absa):
        contents = [f.basename for f in target.listdir()]
        assert 'absa_entities.csv' in contents
        file_lines = target.join('absa_entities.csv').readlines()
        header = file_lines[0].strip().split(',')
        assert header == ['doc_id', 'text_order', 'entity_name', 'entity_type',
                          'surface_string', 'text_span']

    def test_absa_normalized_text_headers(self, target, csv_absa):
        contents = [f.basename for f in target.listdir()]
        assert 'absa_normalized_texts.csv' in contents
        file_lines = target.join('absa_normalized_texts.csv').readlines()
        header = file_lines[0].strip().split(',')
        assert header == ['doc_id', 'text_order', 'normalized_text']

    def test_absa_relations_headers(self, target, csv_absa):
        contents = [f.basename for f in target.listdir()]
        assert 'absa_relations.csv' in contents
        file_lines = target.join('absa_relations.csv').readlines()
        header = file_lines[0].strip().split(',')
        assert header == ['doc_id', 'text_order', 'relation_id',
                          'opinion_holder', 'restriction', 'sentiment',
                          'is_external', 'surface_string', 'text_span']

    def test_absa_rel_entities_headers(self, target, csv_absa):
        contents = [f.basename for f in target.listdir()]
        assert 'absa_relations_entities.csv' in contents
        file_lines = target.join('absa_relations_entities.csv').readlines()
        header = file_lines[0].strip().split(',')
        assert header == ['doc_id', 'text_order', 'relation_id',
                          'entity_type', 'entity_name']

    def test_absa_evaluations_headers(self, target, csv_absa):
        contents = [f.basename for f in target.listdir()]
        assert 'absa_evaluations.csv' in contents
        file_lines = target.join('absa_evaluations.csv').readlines()
        header = file_lines[0].strip().split(',')
        assert header == ['doc_id', 'text_order', 'evaluation_id',
                          'sentiment', 'surface_string', 'text_span']

    def test_absa_eval_entities_headers(self, target, csv_absa):
        contents = [f.basename for f in target.listdir()]
        assert 'absa_evaluations_entities.csv' in contents
        file_lines = target.join('absa_evaluations_entities.csv').readlines()
        header = file_lines[0].strip().split(',')
        assert header == ['doc_id', 'text_order', 'evaluation_id',
                          'entity_type', 'entity_name']

    def test_write_absa_entities(self, target, csv_absa):
        file_lines = target.join('absa_entities.csv').readlines()
        assert len(file_lines) == 2
        entity = file_lines[1].strip().split(',')
        assert entity == ['0', '0', 'OperationQuality', 'feature_subjective',
                          '性能', '2-4']

    def test_write_absa_normalized_texts(self, target, csv_absa):
        file_lines = target.join('absa_normalized_texts.csv').readlines()
        assert len(file_lines) == 2
        entity = file_lines[1].strip().split(',')
        assert entity == ['0', '0', '安全性能很好，很帅气。']

    def test_write_absa_relations(self, target, csv_absa):
        file_lines = target.join('absa_relations.csv').readlines()
        assert len(file_lines) == 2
        relation = file_lines[1].strip().split(',')
        assert relation == ['0', '0', '0', '', '', '2.0', 'False',
                            '安全性能', '0-4']

    def test_write_absa_relation_entities(self, target, csv_absa):
        file_lines = target.join('absa_relations_entities.csv').readlines()
        assert len(file_lines) == 3
        entity1 = file_lines[1].strip().split(',')
        entity2 = file_lines[2].strip().split(',')
        assert entity1 == ['0', '0', '0', 'feature_quantitative', 'Safety']
        assert entity2 == ['0', '0', '0', 'feature_subjective',
                           'OperationQuality']

    def test_write_evaluations(self, target, csv_absa):
        file_lines = target.join('absa_evaluations.csv').readlines()
        assert len(file_lines) == 3
        eval1 = file_lines[1].strip().split(',')
        eval2 = file_lines[2].strip().split(',')
        assert eval1 == ['0', '0', '0', '2.0', '安全', '0-2']
        assert eval2 == ['0', '0', '1', '3.5', '很帅气', '7-10']

    def test_write_evaluations_entities(self, target, csv_absa):
        file_lines = target.join('absa_evaluations_entities.csv').readlines()
        assert len(file_lines) == 3
        entity1 = file_lines[1].strip().split(',')
        entity2 = file_lines[2].strip().split(',')
        assert entity1 == ['0', '0', '0', 'feature_quantitative', 'Safety']
        assert entity2 == ['0', '0', '1', 'feature_subjective',
                           'VisualAppearance']