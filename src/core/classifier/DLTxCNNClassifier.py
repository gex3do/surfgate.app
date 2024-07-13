import os
import posixpath

import numpy as np
from keras import Sequential
from keras.api.layers import Conv1D, Dense, Dropout, Flatten, MaxPooling1D
from sklearn import metrics
from sqlalchemy.orm import Session

from src.core.classifier.Classifier import Classifier
from src.utils.logger import logger


class DLTxCNNClassifier(Classifier):
    def __init__(self, settings, res_mgr):
        Classifier.__init__(self, settings, res_mgr)

        self.vectorizer_dump_filename = posixpath.normpath(
            os.path.join(self.curr_dir, f"{self.target_dir}/dltxcnn_vectorizerDump.pkl")
        )

        self.model_dump_filename = posixpath.normpath(
            os.path.join(self.curr_dir, f"{self.target_dir}/dltxcnn_modelDump.pkl")
        )

    @staticmethod
    def __build_model(data_shape: tuple, num_classes):
        model = Sequential()

        # Layer 1
        model.add(
            Conv1D(
                filters=16,
                kernel_size=5,
                activation="relu",
                input_shape=data_shape[1:],
            )
        )
        model.add(MaxPooling1D(pool_size=6))

        model.add(Conv1D(filters=32, kernel_size=5, activation="relu"))
        model.add(MaxPooling1D(pool_size=6))

        # Dropout and flatten
        model.add(Flatten())
        model.add(Dense(64, activation="relu"))
        model.add(Dropout(0.5))

        model.add(Dense(num_classes, activation="softmax"))
        model.summary()

        model.compile(
            loss="sparse_categorical_crossentropy",
            optimizer="adadelta",
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

        x_train_tfidf_reshaped = np.expand_dims(x_train_input, axis=2)
        x_test_tfidf_reshaped = np.expand_dims(x_test_input, axis=2)

        self.model = self.__build_model(x_train_tfidf_reshaped.shape, 3)
        self.model.fit(
            x_train_tfidf_reshaped,
            y_train_input,
            validation_data=(x_test_input, y_test_input),
            epochs=12,
            batch_size=64,
            verbose=2,
        )

        predicted = self.model.predict(x_test_tfidf_reshaped)
        predicted_classes = np.argmax(predicted, axis=1)
        logger.info(metrics.classification_report(y_test, predicted_classes))
        logger.info(metrics.accuracy_score(y_test, predicted_classes))

        if save_model:
            self._save_model()

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
            predict_x = self.model.predict(x_test_tfidf_reshaped)
            y_pred = np.argmax(predict_x, axis=1)

        logger.info("end classifier predict_resource")
        return y_pred, top_features
