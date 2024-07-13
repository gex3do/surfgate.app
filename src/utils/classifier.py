from src.core.classifier.Classifier import ClassifierType
from src.core.manager.ResourceMgr import ResourceMgr


def get_classifier(settings: dict, resource_mgr: ResourceMgr):
    mode = settings["model"].get("mode", ClassifierType.TxClassifier.value)
    if mode == ClassifierType.TxClassifier.value:
        from src.core.classifier.TxClassifier import TxClassifier

        classifier = TxClassifier(settings, resource_mgr)
    elif mode == ClassifierType.DLTxClassifier.value:
        from src.core.classifier.DLTxClassifier import DLTxClassifier

        classifier = DLTxClassifier(settings, resource_mgr)
    elif mode == ClassifierType.DLTxCNNClassifier.value:
        from src.core.classifier.DLTxCNNClassifier import DLTxCNNClassifier

        classifier = DLTxCNNClassifier(settings, resource_mgr)
    else:
        raise NotImplementedError(f"This training mode is not implemented: {mode}")
    return classifier
