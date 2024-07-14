import abc
import os
from enum import Enum

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
from sqlalchemy.orm import Session

from src.core.app_error import AppError
from src.core.manager.resource_mgr import ResourceMgr
from src.utils.logger import logger


class ClassifierType(Enum):
    TxClassifier = "tx"
    DLTxClassifier = "dltx"
    DLTxCNNClassifier = "dltxcnn"


class Classifier(abc.ABC):
    curr_dir = os.path.dirname(__file__)
    target_dir = "../../trained_data"

    random_state = np.random.RandomState(42)

    # these values are used for calculating proportions and balance the unbalanced dataset
    classes_pos = [0, 1]
    classes_neg = [2]

    # it will take 1 to 1 to positive, if more than one, then will take more negative
    proportion_neg_to_pos = 1

    train_pipe_elements = [("tfidf", TfidfVectorizer())]

    train_pipe_parameters = {
        "tfidf__min_df": (2, 3),
        "tfidf__max_df": (0.5, 0.6, 0.7),
        "tfidf__ngram_range": [(1, 2), (1, 3), (2, 3)],
        # "tfidf__min_df": (2,),
        # "tfidf__max_df": (0.5,),
        # "tfidf__ngram_range": [(1, 3),],
    }

    def __init__(self, settings: dict, res_mgr: ResourceMgr):
        self.settings = settings
        self.res_mgr = res_mgr

        self.model = None
        self.vectorizer = None

        self.vectorizer_dump_filename = None
        self.model_dump_filename = None

    @staticmethod
    def get_synonyms_lexicon(path):
        synonyms_lexicon = {}
        text_entries = [
            line.strip() for line in open(path, encoding="utf-8").readlines()
        ]
        for e in text_entries:
            e = e.split(" ")
            k = e[0]
            v = e[1: len(e)]
            synonyms_lexicon[k] = v
        return synonyms_lexicon

    def _prepare_data(self, sess: Session):
        resources = self.res_mgr.get_checked_with_truerate_resources(sess)
        docs_data, docs_target = self._prepare_resources_as_training_data(resources)
        return self._prepare_dataset(docs_data, docs_target)

    def _save_model(self):
        if not self.vectorizer or not self.model:
            raise AppError.prediction_illegal_state()

        with open(self.vectorizer_dump_filename, "wb") as f:
            joblib.dump(self.vectorizer, f, compress=6)

        with open(self.model_dump_filename, "wb") as f:
            joblib.dump(self.model, f, compress=6)

    def load_model(self):
        with open(self.vectorizer_dump_filename, "rb") as f:
            self.vectorizer = joblib.load(f)

        with open(self.model_dump_filename, "rb") as f:
            self.model = joblib.load(f)

        if self.model and self.vectorizer:
            logger.info("Model and vectorizer are loaded")
            return

        raise ValueError(
            "Something went wrong, cannot load either a model or a vectorizer"
        )

    def _evaluate_model(
            self, x_test_tfidf, x_test, y_test, evaluate_two_classes=False, show_print=False
    ):
        pass

    def _calculate_docs_propotions(self, docs_target):
        # check qty of pos and neg docs
        qty_docs_pos = 0
        qty_docs_neg = 0

        for y in docs_target:
            if y in self.classes_pos:
                qty_docs_pos = qty_docs_pos + 1
            else:
                qty_docs_neg = qty_docs_neg + 1

        ################
        # qty_docs_neg_pro = round(qty_docs_pos * self.proportion_neg_to_pos)

        # in case if calculated rate is more than negative docs
        # if qty_docs_neg_pro > qty_docs_neg:
        #    qty_docs_neg_pro = qty_docs_neg

        if qty_docs_neg > qty_docs_pos:
            qty_docs_neg = qty_docs_pos
        else:
            qty_docs_pos = qty_docs_neg

        ################
        return qty_docs_pos, qty_docs_neg

    @staticmethod
    def _prepare_resources_as_training_data(resources):
        docs_data = []  # np.memmap("/home/dim/test.mymemmap", mode="w+", shape=(,1))
        docs_target = []  # np.memmap("/home/dim/test.mymemmap", mode="w+")
        for resource in resources:
            if not resource.features:
                continue

            resource_tokens = Classifier.get_feature_tokens(resource.features)
            docs_data.append(resource_tokens)
            docs_target.append(resource.true_rate)

        return docs_data, docs_target

    def _generate_synonyms(self, docs_data, docs_target):
        docs_data, docs_target = shuffle(
            docs_data, docs_target, random_state=self.random_state
        )

        # text (data) augmentation method. Generate new sentences regarding synonym
        all_synonyms = Classifier.get_synonyms_lexicon("../data/ppdb-xl.txt")

        synonym_settings = self.settings["model"]["train"]["augmentation"]["synonym"]
        quit_after_found = synonym_settings["quit_after_found"]
        skip_after_not_found = synonym_settings["skip_after_not_found"]
        skip_word_shorter_than = synonym_settings["skip_word_shorter_than"]
        skip_after_unique_words = synonym_settings["skip_after_unique_words"]

        limit_qty = synonym_settings["limit_qty"]

        quit_after_counter = 0
        for x, y in zip(docs_data, docs_target):
            not_found_synonyms = 0
            data_words = x.split(" ")

            if len(data_words) < skip_word_shorter_than:
                # just skip short sentences, it doesn't make sense to create synonyms for short ones
                continue

            apply_synonyms = {}

            for word in data_words:
                if (
                        word.isnumeric()
                        or not_found_synonyms > skip_after_not_found
                        or len(apply_synonyms) > skip_after_unique_words
                ):
                    break

                # if word is already taken in consideration, skip and try next word
                if word in apply_synonyms.keys():
                    continue

                # synonyms found for the word
                synonyms = all_synonyms.get(word)

                if synonyms is None:
                    not_found_synonyms += 1
                    continue

                # reset counter if synonyms found and the word is new
                not_found_synonyms = 0

                # filter all synonyms so that the new word is not in the list of synonyms
                synonyms = [
                    synonym
                    for synonym in synonyms
                    if word not in synonym and not synonym.isnumeric()
                ]
                synonyms = synonyms[:limit_qty]
                if len(synonyms) == 0:
                    continue

                apply_synonyms[word] = synonyms

            if apply_synonyms:
                for apply_word, word_synonyms in apply_synonyms.items():
                    for apply_synonym in word_synonyms:
                        new_token = x.replace(apply_word, apply_synonym)

                        docs_data.append(new_token)
                        docs_target.append(y)
                        quit_after_counter += 1

            if quit_after_counter > quit_after_found:
                break

        return docs_data, docs_target

    def _prepare_dataset(self, docs_data, docs_target):
        if "augmentation" in self.settings["model"]["train"]:
            if (
                    "synonym" in self.settings["model"]["train"]["augmentation"]
                    and self.settings["model"]["train"]["augmentation"]["synonym"]["status"]
            ):
                docs_data, docs_target = self._generate_synonyms(docs_data, docs_target)

        qty_docs_pos_limit, qty_docs_neg_limit = self._calculate_docs_propotions(
            docs_target
        )

        qty_docs_pos = 0
        qty_docs_neg = 0

        docs_data_out = []
        docs_target_out = []

        for x, y in zip(docs_data, docs_target):
            # Add only resources in the main docs_data in case when it doesn't exceed the quantity
            # of neg+pos limits
            if (y in self.classes_pos and qty_docs_pos < qty_docs_pos_limit) or (
                    y in self.classes_neg and qty_docs_neg < qty_docs_neg_limit
            ):
                if y in self.classes_pos:
                    qty_docs_pos = qty_docs_pos + 1
                else:
                    qty_docs_neg = qty_docs_neg + 1

                docs_data_out.append(x)
                docs_target_out.append(y)

        logger.info("Quantity of positive docs: {}".format(qty_docs_pos))
        logger.info("Quantity of negative docs: {}".format(qty_docs_neg))
        logger.info("Quantity of total docs: {}".format(len(docs_data_out)))

        x_train, x_test, y_train, y_test = train_test_split(
            docs_data_out,
            docs_target_out,
            test_size=0.25,
            random_state=self.random_state,
            shuffle=True,
        )
        logger.info("Finished split operation")
        return x_train, x_test, y_train, y_test

    def _transform_data(self, x_train, x_test, tfid_vect_params):
        """
        max_df is used for removing terms that appear too frequently, also known as "corpus-specific stop words".
        For example:
        max_df = 0.50 means "ignore terms that appear in more than 50% of the docs".
        max_df = 25 means "ignore terms that appear in more than 25 docs".
        min_df = 0.01 means "ignore terms that appear in less than 1% of the docs".
        min_df = 5 means "ignore terms that appear in less than 5 docs".
        """
        self.vectorizer = TfidfVectorizer(**tfid_vect_params)
        x_train_tfidf = self.vectorizer.fit_transform(x_train)

        # feature_names = self.vectorizer.get_feature_names()
        # top_features = Classifier.get_top_features_pro_samples(
        #    feature_names, x_train_tfidf
        # )

        x_test_tfidf = self.vectorizer.transform(x_test)
        return x_train_tfidf, x_test_tfidf

    @staticmethod
    def get_top_features_pro_samples(feature_names, x_train_tfidf):
        x_data = x_train_tfidf.toarray()
        top_features = []
        rate_diff = None
        for x_row in x_data:
            top_features_with_tfids = {}
            tfids_top_indexes = np.argsort(x_row)[::-1][:25]
            for tfids_index in tfids_top_indexes:
                feature_rate = x_row[tfids_index]
                if feature_rate == 0.0:
                    continue

                if rate_diff is None:
                    rate_diff = round(1.00 - feature_rate, 2)
                    feature_rate = 1.00
                else:
                    feature_rate = round(feature_rate + rate_diff, 2)

                feature_name = feature_names[tfids_index]
                top_features_with_tfids[feature_name] = feature_rate

            if top_features_with_tfids:
                top_features.append(top_features_with_tfids)

        return top_features

    @staticmethod
    def get_feature_tokens(features: list) -> str:
        """
        Gets tokens like H1,H2,H3,TITLE, AHREF_VALUES from features of one resource and gives one the joined tokens back
        :param features: Features of the specific resource
        :return: Joined tokens from the given features of one specific resource
        """
        feature_tokens = [feature.token for feature in features]

        # All collected feature rows put in one string
        # Exp. page_title , header 1 , header 2 etc. in 1 sentence
        return " ".join(feature_tokens)

    @abc.abstractmethod
    def train(self, sess: Session, save_model=True):
        pass
