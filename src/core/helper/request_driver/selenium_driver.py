from typing import Dict

from jinja2 import Template
from selenium import webdriver
from selenium.webdriver.common.by import By

from src.const import SELENIUM_REMOTE_DRIVER
from src.core.entity import PageGetterSettings, PageGetterAction
from src.core.helper.request_driver.base_driver import BaseDriver


class SeleniumDriver(BaseDriver):
    def __init__(self, headers: Dict[str, str], settings: PageGetterSettings) -> None:
        options = webdriver.ChromeOptions()
        self._url = None
        self._settings = settings
        for header in headers:
            options.add_argument(f'--header="{header}:{headers[header]}"')
        self.__driver = webdriver.Remote(
            command_executor=SELENIUM_REMOTE_DRIVER,
            options=options
        )

    def get_resource(self, url: str, req_args: Dict[str, str]) -> str:
        if url != self._url:
            self.__driver.get(url)
            self._url = url
        res = self.__driver.find_element(by=By.TAG_NAME, value="html").get_attribute("innerHTML")
        return res

    def get_page(self, url: Template, req_args: Dict[str, str], page: str) -> str:
        rendered = url.render()
        if rendered != self._url:
            self.__driver.get(rendered)
            self._url = rendered
        if self._settings.action == PageGetterAction.CLICK:
            self.__driver.find_element(by=self._settings.get_by, value=page).click()
        else:
            self.__driver.execute_script(f"document.querySelector({page}).scrollIntoView()")
        return self.__driver.find_element(by=By.TAG_NAME, value="html").get_attribute("innerHTML")

    def __del__(self):
        self.__driver.quit()

