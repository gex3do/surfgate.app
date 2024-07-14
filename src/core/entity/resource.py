import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text

from src.core.manager.sql_mgr import SqlMgr


class Resource(SqlMgr.base):
    __tablename__ = "resources"

    id = Column("id", Integer, primary_key=True)

    # [exp: text, url, image, video]
    value = Column("value", String(2000), unique=True)

    # [url, text, video, image]
    type = Column("type", String(10))

    # [ if is_propog = True, then the value above can be used to use like search
    is_propog = Column("is_propog", Boolean, nullable=False, default=False)

    # [english, german]
    lang = Column("lang", String(20))

    # [check, extracting, extracted, predicting, checked, declined, deleted]
    status = Column("status", String(20))

    status_reason_msg = Column("status_reason_msg", String(255))

    status_reason_code = Column("status_reason_code", String, default="")

    """
        Description of values:
        true_rate
        prediction_rate
        0 - between 0-12
        1 - between 13-17
        2 - after 18
    """

    # true value
    true_rate = Column("true_rate", Integer, nullable=True)

    # classifier value
    prediction_rate = Column("prediction_rate", Integer, nullable=True)

    creation_date = Column("creation_date", DateTime, default=datetime.datetime.now)

    last_modified = Column(
        "last_modified",
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
    )

    top_features = Column("top_features", Text, unique=False, nullable=True)

    # features = relationship("Feature", cascade="save-update, merge, delete")

    # place index on value
    Index("idx_col_value", "value")

    # place index on value and status
    Index("idx_col_value_status", "value", "status")

    # place index on value and status and is_propog
    Index("idx_col_value_status_propog", "value", "status", "is_propog")
