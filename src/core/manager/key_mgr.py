import uuid
from datetime import date, datetime

import datedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.core.app_enum import UserStatus, UserType
from src.core.app_error import AppError
from src.core.entity.key import Key
from src.core.entity.user import User
from src.core.manager.user_mgr import UserMgr
from src.utils.logger import logger


class KeyMgr:
    min_permission = {
        UserType.CUSTOMER: [
            UserType.CUSTOMER,
            UserType.MODERATOR,
            UserType.ADMIN,
        ],
        UserType.MODERATOR: [
            UserType.MODERATOR,
            UserType.ADMIN,
        ],
        UserType.ADMIN: [UserType.ADMIN],
    }

    def __init__(self, settings: dict, user_mgr: UserMgr):
        self.settings = settings
        self.user_mgr = user_mgr

    @staticmethod
    def get_key_by_value(sess: Session, value: str) -> Key | None:
        return sess.query(Key).filter(Key.value == value).first()

    @staticmethod
    def get_key_activated_user_by_val(sess: Session, user_key: str) -> Key | None:
        key = (
            sess.query(Key)
            .join(User)
            .filter(
                Key.value == user_key,
                Key.user_id == User.id,
                User.status == UserStatus.ACTIVATED,
            )
            .first()
        )
        return key

    @staticmethod
    def create_key(
        sess: Session,
        user_id: int,
        valid_from=None,
        custom_key=None,
        months=1,
        requests_left=0,
        order_id="",
    ):
        if valid_from:
            try:
                valid_from = datetime.strptime(valid_from, "%Y-%m-%d")
            except ValueError:
                raise

            valid_to = valid_from + datedelta.datedelta(months=months)
        else:
            valid_from = date.today()
            valid_to = valid_from + datedelta.datedelta(months=months)

        key_value = str(uuid.uuid4())
        if custom_key:
            key_value = custom_key

        key = Key(
            user_id=user_id,
            valid_from=valid_from,
            valid_to=valid_to,
            value=key_value,
            requests_left=requests_left,
            order_id=order_id,
        )

        sess.add(key)
        sess.flush()
        return key

    @staticmethod
    def delete_key_by_orderid(sess, user_id: int, order_id: str) -> bool:
        key = (
            sess.query(Key).join(User)
            .filter(
                Key.order_id == order_id,
                Key.user_id == user_id,
                User.status == UserStatus.ACTIVATED,
            )
            .first()
        )
        if key is None:
            return False

        sess.delete(key)
        sess.flush()
        return True

    @staticmethod
    def update_key_period(sess: Session, key: Key, months: int = 1) -> Key:
        key.valid_to = key.valid_to + datedelta.datedelta(months=months)
        sess.add(key)
        sess.flush()
        return key

    @staticmethod
    def update_key_frequency(
        sess: Session, key: Key, frequency: int = 1
    ) -> Key:
        key.requests_left = key.requests_left + frequency
        sess.add(key)
        sess.flush()
        return key

    @staticmethod
    def reduce_key_requests(sess: Session, key: Key) -> Key:
        if key.requests_left > 0:
            key.requests_left = key.requests_left - 1
        sess.add(key)
        sess.flush()
        return key

    @staticmethod
    def increase_key_requests(sess: Session, key: Key) -> Key:
        key.requests_left = key.requests_left + 1
        sess.add(key)
        sess.flush()
        return key

    def validate_key(self, sess: Session, user_key: str, permission: str):
        """
        Validate user key and provides results above it.

        Args:
            sess: SQL Alchemy Session
            user_key: key value
            permission: user permission

        Raises: HTTPException
        """
        key = self.get_key_activated_user_by_val(sess, user_key)

        if key is None:
            logger.error("Key has not been found: %s", key)
            raise AppError.key_not_found()

        if key.user.type not in self.min_permission[UserType(permission)]:
            logger.error(
                "Key was found, but has no enough "
                "permissions to do this operation: %s",
                key,
            )
            raise AppError.key_no_permissions()

        # the key exists and has enough permissions, now we need to check if it can be used further

        # 1. first check requests_left and if more than 0 , then allow but before reduce on 1
        if key.requests_left > 0:
            # reduce key usage
            self.reduce_key_requests(sess, key)
            return

        # 2. second check is date range
        now = datetime.now()

        if not key.valid_from or not key.valid_to:
            logger.error(
                "valid_form (%s) or valid_to (%s) of key %s is empty",
                key.valid_from,
                key.valid_to,
                key,
            )
            raise AppError.key_not_found()

        is_valid = key.valid_from <= now <= key.valid_to
        if not is_valid:
            raise AppError.key_expired()

        try:
            # update key usage frequency
            key.used = key.used + 1
            sess.add(key)
            sess.flush()
        except SQLAlchemyError:
            raise AppError.key_update()
