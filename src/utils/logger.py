import logging
import os
import posixpath
import sys

utils_dir = os.path.dirname(__file__)
log_filename = "../logs/app.log"
log_filepath_relative = os.path.join(utils_dir, log_filename)
log_filepath_absolute = posixpath.normpath(log_filepath_relative)

file_handler = logging.FileHandler(filename=log_filepath_absolute)
stdout_handler = logging.StreamHandler(stream=sys.stdout)

LOG_FORMAT = "%(asctime)s,%(msecs)03d %(levelname)-5.5s [PID-%(process)d] %(message)s"
formatter = logging.Formatter(LOG_FORMAT)
file_handler.setFormatter(formatter)
stdout_handler.setFormatter(formatter)
handlers = [file_handler, stdout_handler]

logging.basicConfig(
    level=logging.ERROR,
    datefmt="%a, %d %b %Y %H:%M:%S",
    handlers=handlers,
)

logger = logging.getLogger("app")
