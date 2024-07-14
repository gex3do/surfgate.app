import codecs
import os
import posixpath

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from src.utils.logger import logger


class SqlMgr:
    base = declarative_base()

    engine = None
    session_factory = None

    db_settings = None
    conn_str = None

    tables_list = [
        "users",
        "keys",
        "features",
        "resources",
        "domainqueries",
        "tasks",
    ]

    @classmethod
    def create_session(cls):
        return cls.session_factory()

    @classmethod
    def init(cls, settings: dict, initial_table: bool = None):
        cls.db_settings = settings["main"]["database"]

        if initial_table is None:
            initial_table = cls.db_settings["initial_database"]

        cls.engine = create_engine(
            cls.db_settings["configuration"]["connection_string"],
            pool_size=cls.db_settings["configuration"]["pool_size"],
            max_overflow=cls.db_settings["configuration"]["max_overflow"],
            pool_timeout=cls.db_settings["configuration"]["pool_timeout"],
            echo=cls.db_settings["configuration"]["echo"],
        )

        if initial_table:
            logger.info("Drop tables")
            cls.base.metadata.drop_all(cls.engine)

            logger.info("Recreate tables after drop")
            cls.base.metadata.create_all(cls.engine)

        cls.session_factory = sessionmaker(bind=cls.engine)

        username = cls.db_settings["configuration"]["username"]
        dbname = cls.db_settings["configuration"]["dbname"]
        host = cls.db_settings["configuration"]["host"]
        password = cls.db_settings["configuration"]["password"]

        cls.conn_str = (
            f"host='{host}' user='{username}' dbname='{dbname}' password='{password}' "
        )

    @classmethod
    def restore_records(cls):

        backup_filename = "../../{}/{}".format(
            cls.db_settings["restore_dir"], cls.db_settings["restore_filename"]
        )

        backup_file = posixpath.normpath(
            os.path.join(os.path.dirname(__file__), backup_filename)
        )

        if not os.path.isfile(backup_file):
            raise IOError("Backup file (%s) was not found" % backup_file)

        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(cls.conn_str)
            cursor = conn.cursor()

            commit_after_reached = 40
            counter = 0
            with codecs.open(backup_file, "r", "UTF-8") as fp:
                with tqdm(total=len(fp.readlines())) as pbar:
                    fp.seek(0)
                    while True:
                        pbar.update(1)
                        sql_line = fp.readline()
                        if not sql_line:
                            if counter != 0:
                                conn.commit()
                            break

                        sql_line = sql_line.strip()
                        if sql_contains_insert(sql_line):
                            cursor.execute(sql_line)
                            counter = counter + 1
                            if counter > commit_after_reached:
                                counter = 0
                                conn.commit()

            # Update sequence id to start from scratch
            for table in cls.tables_list:
                cursor.execute(f"SELECT max(id) FROM {table}")
                res = cursor.fetchone()

                # check if id column exists
                if res[0]:
                    latest_id = res[0]
                    cursor.execute(
                        f"SELECT pg_catalog.setval('public.{table}_id_seq', {latest_id}, true)"
                    )
                    conn.commit()
        except Exception as e:
            logger.error(e)
        finally:
            # Close communication with the database
            cursor.close()

            conn.close()


INSERT_FEATURES = "INSERT INTO public.features"
INSERT_RESOURCES = "INSERT INTO public.resources"


def sql_contains_insert(sql: str) -> bool:
    return sql.find(INSERT_FEATURES) != -1 or sql.find(INSERT_RESOURCES) != -1
