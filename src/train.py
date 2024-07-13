#!/usr/bin/python

import argparse

from src.core.manager.SqlMgr import SqlMgr
from src.utils.logger import logger
from src.utils.settings import read_settings, read_version
from src.utils.train import init_train


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", action="store", default="development.yaml")
    args = parser.parse_args()

    settings = read_settings(args.settings)
    version = read_version()

    if not settings["model"]["train"]["status"]:
        logger.info("Skip model training")
        logger.info("Finished training process")
        return

    logger.info("Start training process, version: %s", version)
    SqlMgr.init(settings, initial_table=False)

    init_train(settings)

    logger.info("Finished training process")


if __name__ == "__main__":
    main()
