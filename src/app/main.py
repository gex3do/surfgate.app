import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from textwrap import dedent
from typing import Annotated, Dict

import uvicorn
from fastapi import Depends, FastAPI, Header, Request
from starlette.middleware.cors import CORSMiddleware

from src.app.routers import general, keys, resources, tasks, users
from src.core.api.key_api import KeyApi
from src.core.api.meta_tags import tags_metadata
from src.core.api.permissions import min_permissions
from src.core.api.resource_api import ResourceApi
from src.core.api.task_api import TaskApi
from src.core.api.user_api import UserApi
from src.core.app_error import AppError
from src.core.manager.key_mgr import KeyMgr
from src.core.manager.sql_mgr import SqlMgr
from src.core.manager.task_mgr import TaskMgr
from src.core.manager.user_mgr import UserMgr
from src.utils.classifier import get_classifier
from src.utils.common import instantiate
from src.utils.settings import read_version


def start_server(settings: dict) -> None:
    current_version = read_version()
    SqlMgr.init(settings, initial_table=False)

    instances = instantiate(settings)

    resource_mgr = instances["resource_mgr"]
    user_mgr = UserMgr(settings)
    key_mgr = KeyMgr(settings, user_mgr)
    task_mgr = TaskMgr(settings, resource_mgr)

    classifier = get_classifier(settings, resource_mgr)
    classifier.load_model()
    resource_mgr.classifier = classifier

    resource_api = ResourceApi(settings, resource_mgr, key_mgr)
    task_api = TaskApi(settings, resource_mgr, key_mgr, task_mgr)
    user_api = UserApi(settings, resource_mgr, user_mgr, key_mgr)
    key_api = KeyApi(settings, resource_mgr, user_mgr, key_mgr)

    limits = settings["main"]["limits"]

    @dataclass
    class Client:
        last_seen: time
        count: int

    clients: Dict[str, Client] = {}

    async def rate_limiter(request: Request):
        def cleanup():
            remove = set()
            for h, c in clients.items():
                if datetime.now() > c.last_seen + timedelta(seconds=limits["reset_after_seconds"]):
                    remove.add(h)
            for h in remove:
                del clients[h]

        # TODO this should be run separately every X time,
        #   either in cronjob or some other thread/async
        cleanup()

        client_host = request.client.host
        client = clients.get(client_host, None)
        if not client:
            clients[client_host] = Client(datetime.now(), 1)
            return

        if client.count > limits["connections_per_user"]:
            raise AppError.too_many_requests()

        client.count += 1
        client.last_seen = datetime.now()

    async def verify_key(request: Request, user_key: Annotated[str, Header()]):
        sess = None
        try:
            sess = SqlMgr.create_session()
            key_mgr.validate_key(sess, user_key, min_permissions[request.url.path])
        finally:
            if sess:
                sess.commit()
                sess.close()

    app = FastAPI(
        title="surfgate.app",
        description=dedent(
            """
                The surfgate.app API provides endpoints you connect to using your web-service user license key.
                These endpoints represent actions like evaluating and/or getting already
                evaluated potential content violation rates.
            """
        ),
        summary="surfgate.app application",
        version=current_version,
        terms_of_service="https://surfgate.app/terms/",
        contact={
            "name": "Dmitry Sagoyan",
            "url": "https://surfgate.app",
            "email": "contact@surfgate.app",
        },
        dependencies=[Depends(rate_limiter), Depends(verify_key)],
        openapi_tags=tags_metadata,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(general.get_router(settings))
    app.include_router(resources.get_router(resource_api))
    app.include_router(users.get_router(user_api))
    app.include_router(tasks.get_router(task_api))
    app.include_router(keys.get_router(key_api))

    host = settings["app"]["host"]
    port = int(settings["app"]["port"])

    uvicorn.run(app, host=host, port=port)
