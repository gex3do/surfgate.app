import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

from src.core.entity.Resource import Resource
from src.core.manager.SqlMgr import SqlMgr


class Feature(SqlMgr.base):
    __tablename__ = "features"

    id = Column("id", Integer, primary_key=True)

    token = Column("token", String(2000))

    creation_date = Column("creation_date", DateTime, default=datetime.datetime.now)

    last_modified = Column(
        "last_modified",
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    )

    resource_id = Column("resource_id", Integer, ForeignKey("resources.id"))

    # Use cascade='delete,all' to propagate the deletion of a Resource onto its Features
    resource = relationship(
        Resource, backref=backref("features", uselist=True, cascade="delete,all")
    )
