from src.core.manager.sql_mgr import SqlMgr
from src.utils.classifier import get_classifier
from src.utils.common import instantiate


def init_train(settings: dict):
    instances = instantiate(settings)

    sess = SqlMgr.create_session()
    classifier = get_classifier(settings, instances["resource_mgr"])
    classifier.train(sess, save_model=settings["model"]["train"]["save"])
    sess.close()
