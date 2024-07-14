from fastapi import APIRouter, Response

from src.app.dependencies import process_api_request
from src.core.api.user_api import UserApi
from src.core.model.user_key import (
    UserCreateIn,
    UserCreateOut,
    UserKeyCreateIn,
    UserKeyCreateOut,
)


def get_router(user_api: UserApi) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/User/createUserWithKey",
        summary="creates new user and generates license key for the user and returns generated license key",
        description="By passing the appropriate options, creates new user and generates license key for the "
        "user and returns generated license key ",
        response_description="returns generated license key",
        tags=["admin"],
        response_model_exclude_none=True,
    )
    async def create_user_with_key(
        data: UserKeyCreateIn, response: Response
    ) -> UserKeyCreateOut:
        res, status_code = process_api_request(user_api.create_user_with_key, data)
        response.status_code = status_code
        return res

    @router.post(
        "/User/createUser",
        summary="creates new user and returns the user creation status",
        description="By passing the appropriate options, creates new user and returns the user creation status",
        response_description="returns the user creation status",
        tags=["admin"],
        response_model_exclude_none=True,
    )
    async def create_user(data: UserCreateIn, response: Response) -> UserCreateOut:
        res, status_code = process_api_request(user_api.create_user, data)
        response.status_code = status_code
        return res

    return router
