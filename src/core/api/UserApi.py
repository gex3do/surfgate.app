from sqlalchemy import exc
from sqlalchemy.orm.session import Session

from src.core.api.Responser import Responser
from src.core.AppEnum import UserType
from src.core.AppError import AppError
from src.core.manager import KeyMgr, ResourceMgr, UserMgr
from src.core.model.user_key import UserCreateIn, UserKeyCreateIn


class UserApi:
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
        self.months_default = 1

    def create_user(self, sess: Session, data: UserCreateIn):
        try:
            user = self.user_mgr.create_user(
                sess,
                data.firstname,
                data.lastname,
                data.email,
                UserType.CUSTOMER,
            )
        except exc.SQLAlchemyError as e:
            if e.code == "gkpj":
                raise AppError.user_email_already_exists()
            else:
                raise AppError.user_create()

        return Responser.create_user_creation_status(user)

    def create_user_with_key(self, sess: Session, data: UserKeyCreateIn):
        try:
            user = self.user_mgr.create_user(
                sess,
                data.firstname,
                data.lastname,
                data.email,
                UserType.CUSTOMER,
            )
        except exc.SQLAlchemyError as e:
            if e.code == "gkpj":
                raise AppError.user_email_already_exists()
            else:
                raise AppError.user_create()

        try:
            months = data.months
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
