import re
from typing import Callable

from bs4 import BeautifulSoup
from fastapi import HTTPException

from src.core.app_error import AppError
from src.utils.logger import logger


def parse(url: str, fetch: Callable) -> BeautifulSoup:
    content = fetch(url)
    return BeautifulSoup(content, "html.parser")


def get_content_by_val_and_collect_links(
    fetch: Callable, url: str, collect_links: bool = False
):
    try:
        logger.info("start parsing resource: %s", url)
        content = parse(url, fetch)
        logger.info("end parsing resource: %s", url)
    except HTTPException as e:
        logger.info("end parsing resource: %s with an error %s", url, str(e))
        return None

    links = []
    if collect_links:
        for link in content.findAll(
            "a", attrs={"href": re.compile("^(http|https)://.*$")}
        ):
            href = link.get("href")
            if href not in links:
                links.append(href)

    return links


def log_and_raise_compact_err(err: str) -> None:
    err_msg = err[0:255]
    logger.error(err_msg)
    raise AppError.resource_not_fetchable(err_msg)
