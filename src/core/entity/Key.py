import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import backref, relationship

from src.core.entity.User import User
from src.core.manager.SqlMgr import SqlMgr


class Key(SqlMgr.base):
    __tablename__ = "keys"

    id = Column("id", Integer, primary_key=True)

    value = Column("value", String(36), unique=True)

    creation_date = Column("creation_date", DateTime, default=datetime.datetime.now)
    last_modified = Column(
        "last_modified",
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    )

    valid_from = Column("valid_from", DateTime, nullable=False, default=False)
    valid_to = Column("valid_to", DateTime, nullable=False, default=False)

    requests_left = Column("requests_left", Integer, nullable=False, default=0)

    user_id = Column("user_id", Integer, ForeignKey("users.id"))

    order_id = Column("order_id", String(15), nullable=False)

    # counter of key usage
    used = Column("used", BigInteger, nullable=False, default=0)

    # Use cascade='delete,all' to propagate the deletion of a User onto its Keys
    user = relationship(
        User, backref=backref("keys", uselist=True, cascade="delete,all")
    )

    # place an index on value
    Index("idx_col_value", "value")

    # place an index on value
    Index("idx_col_value_user_id_status", "value", "user_id", "status")
