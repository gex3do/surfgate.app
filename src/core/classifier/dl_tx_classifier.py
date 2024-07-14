import os
import posixpath

import numpy as np
from keras import Sequential
from keras.api.layers import Dense, Dropout
from sklearn import logger, metrics
from sqlalchemy.orm import Session

from src.core.classifier.classifier import Classifier


class DLTxClassifier(Classifier):
    def __init__(self, settings, res_mgr):
        Classifier.__init__(self, settings, res_mgr)

        self.vectorizer_dump_filename = posixpath.normpath(
            os.path.join(self.curr_dir, f"{self.target_dir}/dltx_vectorizerDump.pkl")
        )

        self.model_dump_filename = posixpath.normpath(
            os.path.join(self.curr_dir, f"{self.target_dir}/dltx_modelDump.pkl")
        )

    @staticmethod
    def _build_model(shape, num_classes, dropout=0.7):
        nodes = 512
        num_layers = 2

        model = Sequential()
        model.add(Dense(nodes, input_dim=shape, activation="relu"))
        model.add(Dropout(dropout))

        for i in range(0, num_layers):
            model.add(Dense(nodes, activation="relu"))
            model.add(Dropout(dropout))

        model.add(Dense(num_classes, activation="softmax"))
        model.compile(
            loss="sparse_categorical_crossentropy",
            optimizer="adam",
            metrics=["accuracy"],
        )
        return model

    def train(self, sess: Session, save_model=True):
        # transform data to matrix
        x_train, x_test, y_train, y_test = self._prepare_data(sess)

        tfid_vect_params = {
            "min_df": 2,
            "max_df": 0.5,
            "ngram_range": (1, 2),
        }

        x_train_tfidf, x_test_tfidf = self._transform_data(
            x_train, x_test, tfid_vect_params
        )

        x_train_input = np.asarray(x_train_tfidf.toarray())
        y_train_input = np.asarray(y_train)

        x_test_input = np.asarray(x_test_tfidf.toarray())
        y_test_input = np.asarray(y_test)

        model = self._build_model(x_train_tfidf.shape[1], 3)
        model.fit(
            x_train_input,
            y_train_input,
            validation_data=(x_test_input, y_test_input),
            epochs=10,
            batch_size=128,
            verbose=2,
        )

        predict_x = model.predict(x_test_input)
        predicted = np.argmax(predict_x, axis=1)

        logger.info(metrics.classification_report(y_test, predicted))
        logger.info(metrics.accuracy_score(y_test, predicted))

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
                top_features_pro_samples = Classifier.get_top_features_pro_samples(
                    feature_names, x_test_transformed
                )
                top_features = top_features_pro_samples[0]

            x_test_tfidf_reshaped = np.expand_dims(x_test_transformed.toarray(), axis=2)
            y_pred = self.model.predict(x_test_tfidf_reshaped)

        logger.info("end classifier predict_resource")
        return y_pred, top_features
