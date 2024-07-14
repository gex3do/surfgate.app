import json
from http import HTTPStatus
from typing import Any, Type

from src.core.entity.key import Key
from src.core.entity.user import User
from src.core.helper.rate import prediction_to_violation
from src.core.model.resource import ResourcePredictGetOrRateOut
from src.core.model.task import TaskCreateNotification, TaskCreateOut, TaskGetOut
from src.core.model.user_key import UserCreateOut, UserKeyCreateOut, UserKeyDeleteOut


class Responser:
    @staticmethod
    def create_resource_rate_status(
        resource, show_top_features=False
    ) -> (ResourcePredictGetOrRateOut, HTTPStatus):
        rate = prediction_to_violation(resource.prediction_rate)
        if show_top_features:
            top_features = (
                json.loads(resource.top_features) if resource.top_features else {}
            )
            return (
                ResourcePredictGetOrRateOut(result=rate, top_features=top_features),
                HTTPStatus.OK,
            )
        else:
            return (
                ResourcePredictGetOrRateOut(result=rate),
                HTTPStatus.OK,
            )

    @staticmethod
    def create_user_key_creation_status(
        key: Type[Key],
    ) -> (UserKeyCreateOut, HTTPStatus):
        return (
            UserKeyCreateOut(
                user_uuid=key.user.uuid,
                key=key.value,
                valid_from=str(key.valid_from),
                valid_to=str(key.valid_to),
                requests_left=key.requests_left,
            ),
            HTTPStatus.OK,
        )

    @staticmethod
    def create_user_creation_status(user: User) -> (UserCreateOut, HTTPStatus):
        return UserCreateOut(status="created", uuid=user.uuid), HTTPStatus.OK

    @staticmethod
    def create_user_key_delete_status() -> (UserKeyDeleteOut, HTTPStatus):
        return UserKeyDeleteOut(status="deleted"), HTTPStatus.OK

    @staticmethod
    def create_task_result(
        page_item: Any, stats: Any
    ) -> (TaskGetOut, HTTPStatus):
        return TaskGetOut(page=page_item, stats=stats), HTTPStatus.OK

    @staticmethod
    def create_task_creation_status(task) -> (TaskCreateOut, HTTPStatus):
        return TaskCreateOut(uuid=task.uuid), HTTPStatus.OK

    @staticmethod
    def create_task_notification(task) -> (TaskCreateNotification, HTTPStatus):
        return TaskCreateNotification(uuid=task.uuid, status=task.status), HTTPStatus.OK
