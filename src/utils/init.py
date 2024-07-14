import os

from src.core.api.task_api import TaskApi
from src.core.app_enum import UserType
from src.core.manager.domain_query_mgr import DomainQueryMgr
from src.core.manager.feature_extract_mgr import FeatureExtractMgr
from src.core.manager.key_mgr import KeyMgr
from src.core.manager.resource_mgr import ResourceMgr
from src.core.manager.sql_mgr import SqlMgr
from src.core.manager.task_mgr import TaskMgr
from src.core.manager.tokenization_mgr import TokenizationMgr
from src.core.manager.user_mgr import UserMgr
from src.utils.logger import logger


def init_users(settings: dict):
    sess = SqlMgr.create_session()

    user_mgr = UserMgr(settings)
    key_mgr = KeyMgr(settings, user_mgr)

    # create admin user
    user = user_mgr.create_user(
        sess, "Dmitry", "Sagoyan", "contact@surfgate.app", UserType.ADMIN
    )

    # create key with period from today to +64 months
    key_mgr.create_key(
        sess, user.id, custom_key="621e5fe2-c930-426d-9863-a3aa6845ad71", months=64
    )

    # update the key just for a test to 3 months
    # key_mgr.update_key_period(key.value, valid_from=valid_from, months=3)

    user_mgr.create_user(sess, "Demo", "User", "demo@surfgate.app", UserType.CUSTOMER)

    sess.commit()
    sess.close()


def init_domainqueries(settings: dict):
    # import domain queries
    domainqueries_filename = settings["main"]["domainqueries_filename"]
    if not domainqueries_filename:
        return

    sess = SqlMgr.create_session()
    domainquery_mgr = DomainQueryMgr(settings)
    curr_dir = os.path.dirname(__file__)
    absolute_file_path = f"{curr_dir}/../data/{domainqueries_filename}.txt"
    domainquery_mgr.read_domainquery_from_file(sess, absolute_file_path)
    sess.commit()
    sess.close()


def init_resources(settings: dict, update: bool = False):
    feature_extract_mgr = FeatureExtractMgr(settings, TokenizationMgr(settings))
    resource_mgr = ResourceMgr(settings, feature_extract_mgr, DomainQueryMgr(settings))

    logger.info("Read data source files in mode: %s ", "update" if update else "init")

    sources = settings["model"]["train"]["sources"]
    sources = sources.split(",")
    sess = SqlMgr.create_session()
    curr_dir = os.path.dirname(__file__)
    for source in sources:
        source = source.strip()
        absolute_file_path = f"{curr_dir}/../data/{source}.txt"
        logger.info("Read data source file: %s", absolute_file_path)
        resource_mgr.read_resources_from_file(sess, absolute_file_path, update_resource=update)
    sess.commit()
    sess.close()

    if update:
        return

    logger.info("Analyse resources while extracting features")
    sess = SqlMgr.create_session()
    resource_mgr.analyse_resources(sess)
    sess.close()


def init_tasks(settings: dict) -> TaskApi:
    SqlMgr.init(settings, initial_table=False)

    app_token_mgr = TokenizationMgr(settings)
    app_feature_extract_mgr = FeatureExtractMgr(
        settings,
        app_token_mgr,
    )
    app_domainquery_mgr = DomainQueryMgr(settings)
    app_resource_mgr = ResourceMgr(
        settings, app_feature_extract_mgr, app_domainquery_mgr
    )
    app_user_mgr = UserMgr(settings)
    app_key_mgr = KeyMgr(settings, app_user_mgr)
    app_task_mgr = TaskMgr(settings, app_resource_mgr)

    task_api = TaskApi(settings, app_resource_mgr, app_key_mgr, app_task_mgr)
    return task_api
