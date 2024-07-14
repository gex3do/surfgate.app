from sqlalchemy import Column, Index, Integer, String

from src.core.manager.sql_mgr import SqlMgr


class DomainQuery(SqlMgr.base):
    __tablename__ = "domainqueries"

    id = Column("id", Integer, primary_key=True)

    name = Column("name", String(80), unique=True)

    # [for google = qa, for rambler = query]
    query_key = Column("query_key", String(50))

    value = Column("value", String(80))

    # place a unique index on name
    Index("idx_col_name", "name")
