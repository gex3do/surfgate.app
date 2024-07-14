from src.core.classifier.classifier import ClassifierType
from src.core.manager.resource_mgr import ResourceMgr


def get_classifier(settings: dict, resource_mgr: ResourceMgr):
    mode = settings["model"].get("mode", ClassifierType.TxClassifier.value)
    if mode == ClassifierType.TxClassifier.value:
        from src.core.classifier.tx_classifier import TxClassifier

        classifier = TxClassifier(settings, resource_mgr)
    elif mode == ClassifierType.DLTxClassifier.value:
        from src.core.classifier.dl_tx_classifier import DLTxClassifier

        classifier = DLTxClassifier(settings, resource_mgr)
    elif mode == ClassifierType.DLTxCNNClassifier.value:
        from src.core.classifier.dl_tx_cnn_classifier import DLTxCNNClassifier

        classifier = DLTxCNNClassifier(settings, resource_mgr)
    else:
        raise NotImplementedError(f"This training mode is not implemented: {mode}")
    return classifier
