import os
import pandas as pd
import logging

from anacode.api import writers
from anacode.api.writers import CSV_FILES


class ApiCallDataset:
    pass


class ConceptsDataset(ApiCallDataset):
    """Concept data sets container that provides easy aggregation and
    plotting capabilities.

    """
    def __init__(self, concepts: pd.DataFrame, expressions: pd.DataFrame):
        """Initialize instance by providing two concept relevant data frames.

        :param concepts: List of found concepts with metadata
        :type concepts: pandas.DataFrame
        :param expressions: List of expressions realizing found concepts
        :type expressions: pandas.DataFrame
        """
        self._concepts = concepts
        self._expressions = expressions

    def concept_frequency(self, concept: str):
        """Return count of concept occurrences in this dataset. It's case
        insensitive.

        :param concept: name of concept to count it's occurrences
        :type concept: str
        :return: int -- Number of concept occurences in dataset
        """
        con = self._concepts
        con = con[con.concept.str.lower() == concept.lower()]
        return con.freq.sum()

    def most_common_concepts(self, n=15, concept_type='') -> pd.Series:
        """Counts concepts and returns n most occurring ones sorted by their
        count descending. Counted concepts can be filtered by their type.

        :param n: Maximum number of most common concepts to return
        :type n: int
        :param concept_type: Limit concept counts only to concepts whose type
         starts with this string
        :type concept_type: str
        :return: pandas.Series -- Concept names as index and their counts as
         values sorted descending
        """
        con = self._concepts
        con = con[con.concept_type.str.startswith(concept_type)]
        con_counts = con.groupby('concept').agg({'freq': 'sum'}).freq
        return con_counts.rename('Count').sort_values(ascending=False)[:n]

    def least_common_concepts(self, n=15, concept_type='') -> pd.Series:
        """Counts concepts and returns n least occurring ones sorted by their
        count ascending. Counted concepts can be filtered by their type.

        :param n: Maximum number of least common concepts to return
        :type n: int
        :param concept_type: Limit concept counts only to concepts whose type
         starts with this string
        :type concept_type: str
        :return: pandas.Series -- Concept names as index and their counts as
         values sorted ascending
        """
        con = self._concepts
        con = con[con.concept_type.str.startswith(concept_type)]
        con_counts = con.groupby('concept').agg({'freq': 'sum'}).freq
        return con_counts.rename('Count').sort_values()[:n]

    def co_occurring_concepts(self, concept: str, n=15,
                              concept_type='') -> pd.Series:
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
        con = self._concepts

        identity_filter = con.concept.str.lower() == concept.lower()
        relevant_texts = con[identity_filter][['doc_id', 'text_order']]
        relevant_texts = relevant_texts.set_index(['doc_id', 'text_order'])

        type_filter = con.concept_type.str.startswith(concept_type)
        con = con[type_filter & (identity_filter == False)]
        con = relevant_texts.join(con.set_index(['doc_id', 'text_order']))

        con_counts = con.groupby('concept').agg({'freq': 'sum'}).freq
        con_counts = con_counts.rename('Count').sort_values(ascending=False)
        return con_counts[:n].astype(int)


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

    def main_topic(self) -> str:
        """Finds what topic is this dataset about. Does not support nested
        categories output.

        :return: str -- Name of main topic of all texts.
        """
        cat = self._categories
        all_cats = cat.groupby('category')['probability'].mean()
        return all_cats.sort_values(ascending=False)[0].index[0]


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
        sen = self._sentiments
        return sen.positive.mean()


class ABSADataset(ApiCallDataset):
    def __init__(self, entities, normalized_texts,
                 relations, relations_expressions,
                 evaluations, evaluations_expressions):
        self._entities = entities
        self._normalized_texts = normalized_texts
        self._relations = relations
        self._relations_expressions = relations_expressions
        self._evaluations = evaluations
        self._evaluations_expressions = evaluations_expressions

    def most_common_entities(self, n=15):
        pass

    def least_common_entities(self, n=15):
        pass

    def co_occurring_entities(self, entity: str) -> pd.Series:
        """

        :param entity:
        :type entity: str
        :return:
        """
        pass

    def relevant_entities(self):
        pass

    def best_rated_entities(self):
        pass

    def worst_rated_entities(self):
        pass

    def entity_texts(self):
        pass

    def feature_sentiment(self, feature):
        pass


class DatasetLoader:
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

        Data frames are expected to have format as if they were loaded from
        :class:`anacode.api.writers.CsvWriter` written csv file.

        :param concepts: Two `pandas.DataFrame` objects in a tuple or list.
         First one with concepts and second one with concept's expressions
        :type concepts: tuple of `pandas.DataFrame`
        :param categories: Categories `pandas.DataFrame`
        :type categories: `pandas.DataFrame`
        :param sentiments: Sentiments `pandas.DataFrame`
        :type sentiments: `pandas.DataFrame`
        :param absa:
        :type absa: tuple of `pandas.DataFrame`
        """
        self.has_categories = categories is not None
        self.has_concepts = concepts is not None and \
            concepts_expressions is not None
        self.has_sentiments = sentiments is not None
        self.has_absa = absa_entities is not None and \
            absa_normalized_texts is not None and \
            absa_relations is not None and \
            absa_relations_entities is not None and \
            absa_evaluations is not None and \
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

    @property
    def concepts(self) -> ConceptsDataset:
        """Creates new :class:`ConceptsDataset` if data is available.

        :return:
        """
        if self.has_concepts:
            return ConceptsDataset(self._concepts, self._concepts_expressions)
        else:
            raise ValueError('Concepts data not available!')

    @property
    def categories(self) -> CategoriesDataset:
        if self.has_categories:
            return CategoriesDataset(self._categories)
        else:
            raise ValueError('Categories data not available!')

    @property
    def sentiments(self) -> SentimentDataset:
        if self.has_sentiments:
            return SentimentDataset(self._sentiments)
        else:
            raise ValueError('Sentiment data is not available!')

    @property
    def absa(self) -> ABSADataset:
        if self.has_absa:
            return ABSADataset(
                self._absa_entities, self._absa_normalized_texts,
                self._absa_relations, self._absa_relations_entities,
                self._absa_evaluations, self._absa_evaluations_entities,
            )
        else:
            raise ValueError('ABSA data is not available!')

    @classmethod
    def from_path(cls, path: str):
        """Initializes ApiDataset from AnacodeAPI csv files present in given
        path. You could have obtained these by using
        :class:`anacode.api.writers.CsvWriter` to write your request results
        when you were querying AnacodeAPI.

        :param path: Path to folder where AnacodeAPI analysis is stored in csv
         files
        :type path: str
        :return: :class:`anacode.agg.aggregations.ApiDataset` -- ApiDataset
         with found csv files loaded into data frames
        """
        log = logging.getLogger(__name__)
        log.debug('Going to init ApiDataset from path %s', path)
        join = os.path.join
        path_contents = set(os.listdir(path))
        log.debug('Found files: %s', path_contents)
        kwargs = {}
        loaded = []

        for call, files in CSV_FILES.items():
            log.debug('"%s" call needs these files %s', call, files)
            if set(files).issubset(path_contents):
                frames = {}
                for file_name in files:
                    name = file_name[-4:]
                    if name.startswith('absa_'):
                        name = name[5:]
                    frames[name] = pd.read_csv(join(path, file_name))
                kwargs.update(frames)
                loaded.extend(files)
            else:
                kwargs[call] = None

        if len(loaded) == 0:
            raise ValueError('No relevant csv files in %s', path)
        else:
            log.info('Loaded %d csv files', len(loaded))
            log.debug('Loaded csv files are: %s', loaded)

        return cls(**kwargs)

    @classmethod
    def from_writer(cls, writer):
        """

        :param writer:
        :type writer: anacode.api.writers.Writer
        :return:
        """
        if isinstance(writer, writers.CSVWriter):
            return cls.from_path(writer.target_dir)
        elif isinstance(writer, writers.DataFrameWriter):
            return cls(**writer.frames)

    @classmethod
    def from_lists(cls, concepts=None, categories=None, sentiments=None,
                   absa=None):
        """

        :param concepts:
        :type concepts: list
        :param categories:
        :type categories: list
        :param sentiments:
        :type sentiments: list
        :param absa:
        :type absa: list
        :return: ApiDataset instance
        """
        concepts = concepts or []
        categories = categories or []
        sentiments = sentiments or []
        absa = absa or []

        frame_writer = writers.DataFrameWriter()
        for analyzed in concepts:
            frame_writer.write_concepts(analyzed)
        for analyzed in categories:
            frame_writer.write_categories(analyzed)
        for analyzed in sentiments:
            frame_writer.write_sentiment(analyzed)
        for analyzed in absa:
            frame_writer.write_absa(analyzed)

        return cls(**frame_writer.frames)
