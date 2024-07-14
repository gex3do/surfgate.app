#!/usr/bin/python
import argparse

from src.core.manager.sql_mgr import SqlMgr
from src.utils.init import init_tasks
from src.utils.settings import read_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", action="store", default="development.yaml")
    args = parser.parse_args()

    settings = read_settings(args.settings)
    task_api = init_tasks(settings)

    sess = SqlMgr.create_session()
    task_api.run_delete_tasks(sess)
    sess.close()


if __name__ == "__main__":
    main()
