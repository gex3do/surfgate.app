#!/usr/bin/python

import argparse

from src.core.manager.sql_mgr import SqlMgr
from src.utils.init import init_domainqueries, init_resources, init_users
from src.utils.logger import logger
from src.utils.settings import read_settings, read_version


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", action="store", default="development.yaml")
    args = parser.parse_args()

    settings = read_settings(args.settings)
    version = read_version()

    logger.info("Start initialization process, version: %s", version)
    SqlMgr.init(settings)

    if settings["main"]["database"]["initial_database"]:
        logger.info("Initialize users")
        # initiate admin user and also add some for demo purpose
        init_users(settings)

    if settings["main"]["database"]["restore_records"]:
        logger.info("Restore records")
        SqlMgr.restore_records()

    logger.info("Initialize domain queries")
    init_domainqueries(settings)

    logger.info("Initialize resources and re-analyse them")
    init_resources(settings, update=False)
    logger.info("Finished initialization process")


if __name__ == "__main__":
    main()
