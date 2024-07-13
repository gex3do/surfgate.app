import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    LargeBinary,
    String,
)

from src.core.AppEnum import TaskStatus
from src.core.manager.SqlMgr import SqlMgr


class Task(SqlMgr.base):
    __tablename__ = "tasks"

    id = Column("id", Integer, primary_key=True)

    uuid = Column("uuid", String(36), unique=True)

    # [exp: text, url, image, video]
    value = Column("value", String(2000))

    # [english, german]
    lang = Column("lang", String(20))

    # [exp: http://surfgate.app/return_url
    return_url = Column("return_url", String(200))

    # [check, extracting, extracted, predicting, checked, declined, deleted]
    status = Column("status", String(20), default=TaskStatus.CHECK)

    status_reason_msg = Column("status_reason_msg", String(255))

    creation_date = Column("creation_date", DateTime, default=datetime.datetime.now)

    last_modified = Column(
        "last_modified",
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    )

    maxdepth = Column("maxdepth", Integer, default=1)

    # counter of task get usage
    used = Column("used", BigInteger, nullable=False, default=0)

    # json data
    data = Column("data", LargeBinary, nullable=True)

    recheck = Column("recheck", Boolean, default=False)

    notified = Column("notified", Integer, nullable=False, default=0)

    notification_done = Column("notification_done", Boolean, default=False)
