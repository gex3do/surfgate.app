from typing import Final

import requests
from fake_useragent import UserAgent
from starlette import status

from src.core.webscrapper import log_and_raise_compact_err


class RequestsScrapper:
    ua = UserAgent()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/65.0.3325.181 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.9",
        "Accept-encoding": "gzip, deflate",
        "Accept-language": "en-US,en;q=0.9,de;q=0.7,ru-RU;q=0.5,ru;q=0.5,*;q=0.1",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    # TODO config???
    timeout: Final[int] = 15
    errors_handling: str = "ignore"

    def fetch(self, url: str) -> str:
        try:
            self.headers["User-Agent"] = self.ua.random
            response = requests.get(
                url, timeout=self.timeout, headers=self.headers, allow_redirects=True
            )
            if response.status_code >= status.HTTP_400_BAD_REQUEST:
                raise RuntimeError(f"url: {url} -> {response.reason}")
            return response.content.decode("utf-8", errors=self.errors_handling)
        except Exception as e:
            log_and_raise_compact_err(str(e))
