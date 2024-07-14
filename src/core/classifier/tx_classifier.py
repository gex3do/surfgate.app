import os
import posixpath

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sqlalchemy.orm import Session

from src.core.classifier.classifier import Classifier
from src.core.manager.resource_mgr import ResourceMgr
from src.utils.logger import logger


class TxClassifier(Classifier):
    def __init__(self, settings: dict, res_mgr: ResourceMgr):
        Classifier.__init__(self, settings, res_mgr)

        self.vectorizer_dump_filename = posixpath.normpath(
            os.path.join(self.curr_dir, f"{self.target_dir}/tx_vectorizerDump.pkl")
        )

        self.model_dump_filename = posixpath.normpath(
            os.path.join(self.curr_dir, f"{self.target_dir}/tx_modelDump.pkl")
        )

    def train(self, sess: Session, save_model: bool = True):
        x_train, x_test, y_train, y_test = self._prepare_data(sess)

        # x_train (vectorized) and y_train labels
        x_test_tfidf = self._train_model(x_train, x_test, y_train)

        self._evaluate_model(x_test_tfidf, x_test, y_test, True)

        if save_model:
            self._save_model()

    def _train_model(self, x_train, x_test, y_train):
        """
        1. https://medium.com/all-things-ai/in-depth-parameter-tuning-for-svc-758215394769

        Some information about parameter C which is penalty (regulization)
        2. https://stats.stackexchange.com/questions/31066/what-is-the-influence-of-c-in-svms-with-linear-kernel
        """

        # Hyperparams different combinations
        self.train_pipe_elements.append(("svc", SVC()))
        self.train_pipe_parameters["svc__kernel"] = ["rbf"]
        self.train_pipe_parameters["svc__C"] = [120, 150, 160, 180]
        self.train_pipe_parameters["svc__gamma"] = [0.001, 0.005, 0.01, 0.05]
        # self.train_pipe_parameters["svc__C"] = [160]
        # self.train_pipe_parameters["svc__gamma"] = [0.005]
        pipeline = Pipeline(self.train_pipe_elements)
        gs = GridSearchCV(pipeline, self.train_pipe_parameters, n_jobs=3, cv=3)
        gs.fit(x_train, y_train)

        best_c = gs.best_params_["svc__C"]
        best_kernel = gs.best_params_["svc__kernel"]
        best_gamma = gs.best_params_["svc__gamma"]

        tfid_vect_params = {
            "ngram_range": gs.best_params_["tfidf__ngram_range"],
            "min_df": gs.best_params_["tfidf__min_df"],
            "max_df": gs.best_params_["tfidf__max_df"],
        }
        x_train_tfidf, x_test_tfidf = self._transform_data(
            x_train, x_test, tfid_vect_params
        )

        self.model = SVC(kernel=best_kernel, C=best_c, gamma=best_gamma)
        self.model.fit(x_train_tfidf, y_train)
        return x_test_tfidf

    def _evaluate_model(
        self, x_test_tfidf, x_test, y_test, evaluate_two_classes=False, show_print=False
    ):
        y_pred = self.model.predict(x_test_tfidf)
        accuracy = accuracy_score(y_test, y_pred) * 100

        logger.info("Accuracy: %.2f%%" % accuracy)

        if evaluate_two_classes is True:
            self.accuracy_for_2_classes(y_test, y_pred)
            self.evaluate_negative_prediction(x_test, y_pred, y_test, 2, 1)

        return accuracy

    @staticmethod
    def evaluate_negative_prediction(
        x_test, y_pred, y_test, label_value, prediction_value
    ):
        for input_prediction, prediction, label in zip(x_test, y_pred, y_test):
            if (
                prediction != label
                and label == label_value
                and prediction == prediction_value
            ):
                logger.info(
                    "%s has been classified as %s and should be %s",
                    input_prediction,
                    prediction,
                    label,
                )

    @staticmethod
    def accuracy_for_2_classes(y_test, y_pred):
        y_t = np.array(y_test)
        y_p = np.array(y_pred)

        # custom situation. transform class 1 to 0
        y_t[y_t == 1] = 0

        for i, item in enumerate(y_p):
            if item == 1 and y_t[i] == 0:
                y_p[i] = 0

        y_result = np.equal(y_t, y_p)
        unique, counts = np.unique(y_result, return_counts=True)
        y_result_grouped = dict(zip(unique, counts))
        accuracy_predictions = y_result_grouped[True] / len(y_t)

        logger.info("Quantity of True and False predicted")
        logger.info(y_result_grouped)
        logger.info("Total elements: {}".format(len(y_t)))
        logger.info("Accuracy with 2 classes: %s", round(accuracy_predictions, 2))

    def predict_resource(self, resource, show_top_features=False):
        logger.info("begin classifier predict_resource")

        y_pred = None
        top_features = None

        if resource.features:
            feature_tokens_str = Classifier.get_feature_tokens(resource.features)
            logger.info("Features found: %s", feature_tokens_str)
            x_test_transformed = self.vectorizer.transform([feature_tokens_str])
            if show_top_features:
                feature_names = self.vectorizer.get_feature_names_out()
                if top_features_pro_samples := Classifier.get_top_features_pro_samples(
                    feature_names, x_test_transformed
                ):
                    top_features = top_features_pro_samples[0]

            y_pred = self.model.predict(x_test_transformed)

        logger.info("end classifier predict_resource")
        return y_pred, top_features
