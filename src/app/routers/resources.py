from fastapi import APIRouter, Response

from src.app.dependencies import process_api_request
from src.core.api.resource_api import ResourceApi
from src.core.model.resource import (
    ResourcePredictGetIn,
    ResourcePredictGetOrRateOut,
    ResourcePredictRateIn,
)


def get_router(resource_api: ResourceApi) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/Resource/predictResourceRate",
        summary="predicts resource and returns potential content violation rate",
        description="By passing the appropriate options, predicts resource and "
        "returns potential content violation rate",
        response_description="returns potential content violation rate",
        tags=["admin", "user"],
        response_model_exclude_none=True,
    )
    async def get_resource_rate_else_predict(
        data: ResourcePredictRateIn, response: Response
    ) -> ResourcePredictGetOrRateOut:
        res, status_code = process_api_request(
            resource_api.get_resource_rate_else_predict, data
        )
        response.status_code = status_code
        return res

    @router.post(
        "/Resource/getResourceRate",
        summary="returns potential content violation rate",
        description="By passing the appropriate options, returns potential content violation rate",
        response_description="returns potential content violation rate",
        tags=["admin", "user"],
        response_model_exclude_none=True,
    )
    async def get_resource_rate(
        data: ResourcePredictGetIn, response: Response
    ) -> ResourcePredictGetOrRateOut:
        res, status_code = process_api_request(resource_api.get_resource_rate, data)
        response.status_code = status_code
        return res

    return router
