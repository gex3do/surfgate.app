from fastapi import APIRouter, Response

from src.app.dependencies import process_api_request
from src.core.api.KeyApi import KeyApi
from src.core.model.user_key import (
    KeyCreateIn,
    KeyCreateOut,
    KeyDeleteByOrderIdIn,
    KeyGetIn,
    KeyUpdateFrequencyIn,
    KeyUpdatePeriodIn,
    UserKeyCreateOut,
    UserKeyDeleteOut,
)


def get_router(key_api: KeyApi) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/Key/createKey",
        summary="creates a new key for the user and returns generated license key",
        description="By passing the appropriate options, creates a new key for the user and returns generated "
        "license key",
        response_description="returns generated license key",
        tags=["admin"],
        response_model_exclude_none=True,
    )
    async def create_key(data: KeyCreateIn, response: Response) -> KeyCreateOut:
        res, status_code = process_api_request(key_api.create_key, data)
        response.status_code = status_code
        return res

    @router.post(
        "/Key/deleteKeyByOrderId",
        summary="deletes key by order id and customer id",
        description=" By passing the appropriate options, deletes key and returns the deletion status",
        response_description="returns key deletion status",
        tags=["admin"],
        response_model_exclude_none=True,
    )
    async def delete_key_by_orderid(
        data: KeyDeleteByOrderIdIn, response: Response
    ) -> UserKeyDeleteOut:
        res, status_code = process_api_request(key_api.delete_key_by_orderid, data)
        response.status_code = status_code
        return res

    @router.post(
        "/Key/getKey",
        summary="get license key information and returns it",
        description="By passing the appropriate options, get license key information and returns it",
        response_description="returns license key information",
        tags=["admin", "user"],
        response_model_exclude_none=True,
    )
    async def get_key(data: KeyGetIn, response: Response) -> UserKeyCreateOut:
        res, status_code = process_api_request(key_api.get_key, data)
        response.status_code = status_code
        return res

    @router.post(
        "/Key/updateKeyPeriod",
        summary="update license key period by given license key and returns updated license key",
        description="By passing the appropriate options, update license key period by "
        "given license key and returns updated license key",
        response_description="returns updated license key",
        tags=["admin"],
        response_model_exclude_none=True,
    )
    async def update_key_period(
        data: KeyUpdatePeriodIn, response: Response
    ) -> UserKeyCreateOut:
        res, status_code = process_api_request(key_api.update_key_period, data)
        response.status_code = status_code
        return res

    @router.post(
        "/Key/updateKeyFrequency",
        summary="update license key frequency (requests_left) by given license key and returns updated license key",
        description="By passing the appropriate options, update license key frequency (requests_left) by given "
        "license key and returns updated license key",
        response_description="returns updated license key",
        tags=["admin"],
        response_model_exclude_none=True,
    )
    async def update_key_frequency(
        data: KeyUpdateFrequencyIn, response: Response
    ) -> UserKeyCreateOut:
        res, status_code = process_api_request(key_api.update_key_frequency, data)
        response.status_code = status_code
        return res

    return router
