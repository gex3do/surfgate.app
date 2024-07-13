#!/usr/bin/env python
import os
import posixpath

import yaml

from src.utils.logger import logger

curr_dir = os.path.dirname(__file__)


def read_settings(filename: str) -> dict:
    """
    Read yaml file from settings folder and return dict object.

    Args:
        filename: filename of the `settings` file

    Returns: configuration as dict-object
    """
    assert filename is not None

    settings_filename = posixpath.normpath(
        os.path.join(curr_dir, f"../settings/{filename}")
    )

    if not os.path.isfile(settings_filename):
        raise IOError(settings_filename)

    with open(settings_filename, "r") as fp:
        try:
            settings = yaml.safe_load(fp)
        except yaml.YAMLError:
            raise ValueError("settings file cannot be read as yaml file")
        except Exception as e:
            logger.error(e)
            raise ValueError(
                "something wierd happened while reading settings file, please check the logs"
            )
    return settings


def read_version():
    with open(os.path.join(curr_dir, "../VERSION"), "r") as fp:
        version = fp.read().strip()
    return version
