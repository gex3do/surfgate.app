from fastapi import APIRouter, Response

from src.app.dependencies import process_api_request
from src.core.api.task_api import TaskApi
from src.core.model.task import TaskCreateIn, TaskCreateOut, TaskGetIn, TaskGetOut


def get_router(task_api: TaskApi) -> APIRouter:
    router = APIRouter()

    @router.post(
        "/Task/getTask",
        summary="get processed task by task uuid",
        description="By passing the appropriate options, returns processed task related "
        "pages and statistics",
        response_description="returns processed task related pages and statistics",
        tags=["admin", "user"],
        response_model_exclude_none=True,
    )
    async def get_task(data: TaskGetIn, response: Response) -> TaskGetOut:
        res, status_code = process_api_request(task_api.get_task, data)
        response.status_code = status_code
        return res

    @router.post(
        "/Task/createTask",
        summary="creates task in tasks queue for a given URL resource and returns the task uuid",
        description=" By passing the appropriate options, creates task in tasks queue for "
        "a given URL resource and returns the task uuid",
        response_description="returns created task uuid",
        tags=["admin", "user"],
        response_model_exclude_none=True,
    )
    async def create_task(data: TaskCreateIn, response: Response) -> TaskCreateOut:
        res, status_code = process_api_request(task_api.create_task, data)
        response.status_code = status_code
        return res

    return router
