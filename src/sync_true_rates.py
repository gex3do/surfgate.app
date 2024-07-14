#!/usr/bin/python

import argparse

from src.core.manager.SqlMgr import SqlMgr
from src.utils.init import init_resources
from src.utils.logger import logger
from src.utils.settings import read_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", action="store", default="development.yaml")
    args = parser.parse_args()

    settings = read_settings(args.settings)

    SqlMgr.init(settings, initial_table=False)

    logger.info("Updating resources true-rates")
    init_resources(settings, update=True)
    logger.info("Finished updating resources true-rates")


if __name__ == "__main__":
    main()
