#!/usr/bin/python

import argparse

from src.core.classifier.Classifier import ClassifierType
from src.core.manager.SqlMgr import SqlMgr
from src.utils.init import init_tasks
from src.utils.logger import logger
from src.utils.settings import read_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", action="store", default="development.yaml")
    args = parser.parse_args()

    # read settings
    settings = read_settings(args.settings)

    task_api = init_tasks(settings)

    mode = settings["model"].get("mode", ClassifierType.TxClassifier.value)
    # initialize and load model
    if mode == ClassifierType.TxClassifier.value:
        from src.core.classifier.TxClassifier import TxClassifier

        classifier = TxClassifier(settings, task_api.resource_mgr)
    elif mode == ClassifierType.DLTxClassifier.value:
        from src.core.classifier.DLTxClassifier import DLTxClassifier

        classifier = DLTxClassifier(settings, task_api.resource_mgr)
    elif mode == ClassifierType.DLTxCNNClassifier.value:
        from src.core.classifier.DLTxCNNClassifier import DLTxCNNClassifier

        classifier = DLTxCNNClassifier(settings, task_api.resource_mgr)
    else:
        logger.error(f"This training mode is not implemented: {mode}")
        raise NotImplementedError

    classifier.load_model()

    task_api.resource_mgr.classifier = classifier

    sess = SqlMgr.create_session()
    task_api.predict_tasks_resources(sess)
    sess.close()


if __name__ == "__main__":
    main()
