#!/usr/bin/python

import argparse
import os

from src.core.manager.DomainQueryMgr import DomainQueryMgr
from src.core.manager.FeatureExtractMgr import FeatureExtractMgr
from src.core.manager.ResourceMgr import ResourceMgr
from src.core.manager.SqlMgr import SqlMgr
from src.core.manager.TokenizationMgr import TokenizationMgr
from src.utils.logger import logger
from src.utils.settings import read_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", action="store", default="development")
    args = parser.parse_args()

    settings = read_settings(args.settings)

    SqlMgr.init(settings, initial_table=False)

    token_mgr = TokenizationMgr(settings)
    feature_extract_mgr = FeatureExtractMgr(settings, token_mgr)
    domainquery_mgr = DomainQueryMgr(settings)
    resource_mgr = ResourceMgr(settings, feature_extract_mgr, domainquery_mgr)

    # prepare and add `checked` resources
    sources = settings["model"]["train"]["sources"]
    sources = sources.split(",")

    logger.info("Read data source files for updating true rate")

    sess = SqlMgr.create_session()
    for source in sources:
        curr_dir = os.path.dirname(__file__)
        absolute_file_path = f"{curr_dir}/data/{source}.txt"
        logger.info("Read data source file: %s", absolute_file_path)
        resource_mgr.read_resources_from_file(sess, absolute_file_path, True)

    sess.commit()
    sess.close()

    logger.info("Finished updating true rate")


if __name__ == "__main__":
    main()
