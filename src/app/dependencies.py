from typing import Callable

from fastapi import HTTPException

from src.core.manager.SqlMgr import SqlMgr
from src.core.model.resource import ResourcePredictGetIn, ResourcePredictRateIn
from src.core.model.task import TaskCreateIn, TaskGetIn
from src.core.model.user_key import (
    KeyCreateIn,
    KeyDeleteByOrderIdIn,
    KeyGetIn,
    KeyUpdateFrequencyIn,
    KeyUpdatePeriodIn,
    UserCreateIn,
    UserKeyCreateIn,
)
from src.utils.logger import logger

RequestIn = (
    ResourcePredictRateIn
    | ResourcePredictGetIn
    | TaskCreateIn
    | TaskGetIn
    | UserKeyCreateIn
    | UserCreateIn
    | KeyCreateIn
    | KeyDeleteByOrderIdIn
    | KeyGetIn
    | KeyUpdatePeriodIn
    | KeyUpdateFrequencyIn
)


def process_api_request(api_func: Callable, payload: RequestIn):
    sess = None
    try:
        sess = SqlMgr.create_session()
        response = api_func(sess, payload)
        sess.commit()
        return response
    except HTTPException as e:
        logger.error("error_code: %d, error_msg: %s", e.status_code, e.detail)
        sess.rollback()
        raise e
    finally:
        if sess:
            sess.close()
