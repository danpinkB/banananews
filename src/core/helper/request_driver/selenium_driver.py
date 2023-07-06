from typing import Dict

from selenium import webdriver
from selenium.webdriver.common.by import By

from src.const import SELENIUM_REMOTE_DRIVER
from src.core.helper.req_inspector import RequestInspector
from src.core.helper.request_driver.base_driver import BaseDriver


class SeleniumDriver(BaseDriver):
    def __init__(self, inspector: RequestInspector) -> None:
        options = webdriver.ChromeOptions()
        self._inspector = inspector
        headers = inspector.get_headers()
        for header in headers:
            options.add_argument(f'--header="{header}:{headers[header]}"')
        self.__driver = webdriver.Remote(
            command_executor=SELENIUM_REMOTE_DRIVER,
            options=options
        )

    def get_resource(self, url: str, req_args: Dict[str, str]) -> str:
        self._inspector.lock_request()
        self.__driver.get(url)
        return self.get_data()

    def move_to_page(self, by: str, value: str, action: str) -> None:
        if action == "click":
            self.__driver.find_element(by=_parse_by(by), value=value).click()
        else:
            self.__driver.execute_script(f"document.querySelector({value}).scrollIntoView()")

    def get_data(self) -> str:
        return self.__driver.find_element(by=By.TAG_NAME, value="html").get_attribute("innerHTML")

    def __del__(self):
        self.__driver.quit()


def _parse_by(text):
    text = text.upper()  # Convert to uppercase for case-insensitive matching
    if text == "ID":
        return By.ID
    elif text == "NAME":
        return By.NAME
    elif text == "XPATH":
        return By.XPATH
    elif text == "CSS_SELECTOR":
        return By.CSS_SELECTOR
    elif text == "LINK_TEXT":
        return By.LINK_TEXT
    elif text == "PARTIAL_LINK_TEXT":
        return By.PARTIAL_LINK_TEXT
    elif text == "TAG_NAME":
        return By.TAG_NAME
    elif text == "CLASS_NAME":
        return By.CLASS_NAME
    else:
        raise ValueError("Invalid 'By' value: " + text)
