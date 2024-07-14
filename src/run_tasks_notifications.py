#!/usr/bin/python

import argparse

from src.core.classifier.classifier import ClassifierType
from src.core.manager.sql_mgr import SqlMgr
from src.utils.init import init_tasks
from src.utils.logger import logger
from src.utils.settings import read_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", action="store", default="development.yaml")
    args = parser.parse_args()

    settings = read_settings(args.settings)
    task_api = init_tasks(settings)

    mode = settings["model"].get("mode", ClassifierType.TxClassifier.value)
    # initialize and load model
    if mode == ClassifierType.TxClassifier.value:
        from src.core.classifier.tx_classifier import TxClassifier

        classifier = TxClassifier(settings, task_api.resource_mgr)
    elif mode == ClassifierType.DLTxClassifier.value:
        from src.core.classifier.dl_tx_classifier import DLTxClassifier

        classifier = DLTxClassifier(settings, task_api.resource_mgr)
    elif mode == ClassifierType.DLTxCNNClassifier.value:
        from src.core.classifier.dl_tx_cnn_classifier import DLTxCNNClassifier

        classifier = DLTxCNNClassifier(settings, task_api.resource_mgr)
    else:
        logger.error(f"This training mode is not implemented: {mode}")
        raise NotImplementedError

    classifier.load_model()

    task_api.resource_mgr.classifier = classifier

    sess = SqlMgr.create_session()
    task_api.send_tasks_notifications(sess)
    sess.close()


if __name__ == "__main__":
    main()
