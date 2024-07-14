import datetime

from sqlalchemy import Column, DateTime, Integer, String

from src.core.app_enum import UserStatus, UserType
from src.core.manager.sql_mgr import SqlMgr


class User(SqlMgr.base):
    __tablename__ = "users"

    id = Column("id", Integer, primary_key=True)

    uuid = Column("uuid", String(36), unique=True)

    firstname = Column("firstname", String(80))

    lastname = Column("lastname", String(80))

    email = Column("email", String(150), unique=True)

    password = Column("password", String(255))

    # activated, deactivated
    status = Column("status", String(30), default=UserStatus.ACTIVATED)

    # type [customer, moderator, admin]
    type = Column("type", String(30), default=UserType.CUSTOMER)

    creation_date = Column("creation_date", DateTime, default=datetime.datetime.now)

    last_modified = Column(
        "last_modified",
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    )
