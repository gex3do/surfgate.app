from typing import Final

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from src.core.webscrapper import log_and_raise_compact_err
from src.utils.logger import logger


class WebDriveScrapper:
    ua = UserAgent()

    # TODO config???
    pageload_timeout: Final[int] = 15
    script_timeout: Final[int] = 15
    proxy_host = "35.157.186.69:3128"

    def init_ff_driver(self, **kwargs) -> webdriver.Firefox:
        user_agent = self.ua.random
        logger.info("UserAgent: %s", user_agent)

        ff_options = Options()
        ff_options.add_argument("--headless")
        ff_options.add_argument("--no-sandbox")
        ff_options.add_argument(f"--user-agent={user_agent}")
        ff_options.add_argument("--disable-web-security")
        ff_options.add_argument("--disable-extensions")

        ff_profile = FirefoxProfile()
        if kwargs.get("proxy", False):
            ff_options.add_argument(f"--proxy-server={WebDriveScrapper.proxy_host}")
            ff_profile.set_preference("network.proxy.type", 1)
            ff_profile.set_preference("network.proxy.http", "35.157.186.69")
            ff_profile.set_preference("network.proxy.http_port", 3128)
            ff_profile.set_preference("network.proxy.ssl", "35.157.186.69")
            ff_profile.set_preference("network.proxy.ssl_port", 3128)
            ff_profile.set_preference("network.proxy.ftp", "35.157.186.69")
            ff_profile.set_preference("network.proxy.ftp_port", 3128)

        # You would also like to block flash
        ff_profile.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", False)
        ff_profile.set_preference("dom.webdriver.enabled", False)
        ff_profile.set_preference("media.peerconnection.enabled", False)
        ff_profile.set_preference("useAutomationExtension", False)
        ff_profile.set_preference("general.useragent.override", user_agent)
        ff_profile.update_preferences()

        ff_options.profile = ff_profile
        ff_service = Service(executable_path="/usr/bin/geckodriver")
        driver = webdriver.Firefox(
            service=ff_service,
            options=ff_options,
        )
        driver.add_cookie(
            {"name": "__ewl", "value": "2eaeb082a2fc429abobc340ae4df6a7b"}
        )
        return driver

    def fetch(self, url: str) -> str:
        driver = None
        try:
            driver = self.init_ff_driver()
            driver.set_script_timeout(self.script_timeout)
            driver.set_page_load_timeout(self.pageload_timeout)
            driver.get(url)
            return driver.page_source
        except Exception as e:
            log_and_raise_compact_err(str(e))
        finally:
            if driver:
                driver.close()
                driver.quit()
