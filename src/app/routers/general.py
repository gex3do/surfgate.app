from fastapi import APIRouter

from src.utils.settings import read_version


def get_router(settings: dict) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/",
        summary="project information",
        description="Provides information about the project (project name and version)",
        tags=["admin", "user"],
    )
    async def index():
        current_version = read_version()
        return "Project Name: {}<br />Version: {}".format(
            settings["app"]["display_name"], current_version
        )

    @router.get(
        "/health",
        summary="health check",
        description="Provides information about project health",
        tags=["admin", "user"],
    )
    async def health_check():
        return {"status": "ok"}

    return router
