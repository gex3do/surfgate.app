from sqlalchemy import exc
from sqlalchemy.orm.session import Session

from src.core.api.responser import Responser
from src.core.app_error import AppError
from src.core.manager.key_mgr import KeyMgr
from src.core.manager.resource_mgr import ResourceMgr
from src.core.manager.user_mgr import UserMgr
from src.core.model.user_key import (
    KeyCreateIn,
    KeyDeleteByOrderIdIn,
    KeyGetIn,
    KeyGetOut,
    KeyUpdateFrequencyIn,
    KeyUpdatePeriodIn,
)
from src.utils.logger import logger


class KeyApi:
    def __init__(
        self,
        settings: dict,
        resource_mgr: ResourceMgr,
        user_mgr: UserMgr,
        key_mgr: KeyMgr,
    ):
        self.settings = settings
        self.resource_mgr = resource_mgr
        self.user_mgr = user_mgr
        self.key_mgr = key_mgr
        self.requests_left_default = 0

    def get_key(self, sess: Session, data: KeyGetIn) -> KeyGetOut:
        key = self.key_mgr.get_key_by_value(sess, str(data.key))

        if not key:
            raise AppError.key_not_found()

        return Responser.create_user_key_creation_status(key)

    def create_key(self, sess: Session, data: KeyCreateIn):
        try:
            months = data.months

            user = self.user_mgr.get_user_by_uuid(sess, data.user_uuid)
            if not user:
                raise AppError.user_not_found()

            requests_left = self.requests_left_default

            if data.demo:
                months = 0
                requests_left = self.settings["main"]["demo"]["requests_left_pro_key"]

            key = self.key_mgr.create_key(
                sess,
                user.id,
                months=months,
                requests_left=requests_left,
                order_id=data.order_id,
            )

        except exc.SQLAlchemyError as e:
            if e.code == "gkpj":
                raise AppError.key_already_exists()
            else:
                raise AppError.key_create()

        return Responser.create_user_key_creation_status(key)

    def delete_key_by_orderid(self, sess: Session, data: KeyDeleteByOrderIdIn):
        try:
            user = self.user_mgr.get_user_by_uuid(sess, data.user_uuid)

            if not user:
                raise AppError.user_not_found()

            self.key_mgr.delete_key_by_orderid(sess, data.user_uuid, data.order_id)

        except exc.SQLAlchemyError as e:
            logger.error("key cannot be deleted by order-id: %s. Error occurred: %s", data.order_id, str(e))
            raise AppError.key_delete()

        return Responser.create_user_key_delete_status()

    def update_key_period(self, sess: Session, data: dict):
        try:
            val = data["value"]
            key = self.key_mgr.get_key_by_value(sess, val)

            if not key:
                raise AppError.key_not_found()

            months = data["months"]

            self.key_mgr.update_key_period(sess, key.value, months=months)

        except exc.SQLAlchemyError:
            raise AppError.key_update()

        return Responser.create_user_key_creation_status(key)

    def update_key_frequency(self, sess: Session, data: dict):
        try:
            val = data["value"]
            key = self.key_mgr.get_key_by_value(sess, val)

            if not key:
                raise AppError.key_not_found()

            frequency = data["frequency"]

            self.key_mgr.update_key_frequency(sess, key, frequency)

        except exc.SQLAlchemyError:
            raise AppError.key_update()

        return Responser.create_user_key_creation_status(key)
