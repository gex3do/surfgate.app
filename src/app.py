import argparse

from src.app.main import start_server
from src.utils.settings import read_settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", action="store", default="development.yaml")
    args = parser.parse_args()

    settings = read_settings(args.settings)
    start_server(settings)
