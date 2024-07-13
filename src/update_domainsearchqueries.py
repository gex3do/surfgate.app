#!/usr/bin/python

import argparse
import os

from src.core.manager.DomainQueryMgr import DomainQueryMgr
from src.core.manager.SqlMgr import SqlMgr
from src.utils.settings import read_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", action="store", default="development")
    args = parser.parse_args()

    # read settings
    settings = read_settings(args.settings)

    SqlMgr.init(settings, initial_table=False)

    # import domain queries
    domainqueries_filename = settings["main"]["domainqueries_filename"]

    if domainqueries_filename:
        curr_dir = os.path.dirname(__file__)
        absolute_file_path = f"{curr_dir}/../data/{domainqueries_filename}.txt"

        sess = SqlMgr.create_session()
        domainquery_mgr = DomainQueryMgr(settings)
        domainquery_mgr.read_domainquery_from_file(sess, absolute_file_path)
        sess.commit()
        sess.close()


if __name__ == "__main__":
    main()
