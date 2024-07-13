#!/usr/bin/python

import os

from src.utils import Settings


def main():
    # Read settings
    app_versions = Settings.read_settings("versions")

    # Get product version
    version = app_versions["current"]

    # Prepare command for building the docker with a current version
    buildProductionCmd = "sudo ./build_production_job.sh prod_{}".format(version)
    os.system(buildProductionCmd)


if __name__ == "__main__":
    main()
