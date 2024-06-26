import time
from typing import Union, Dict

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait


class AppiumHelper:
    def __init__(self, appium_server_url: str = None, capabilities: Dict = None):
        self.driver = webdriver.Remote(appium_server_url,
                                       options=UiAutomator2Options().load_capabilities(capabilities))
        # 设置等待元素出现10s
        self.driver.implicitly_wait(10)
        # 获取宽高
        self.start_x = self.driver.get_window_size()['width'] / 2
        self.start_y = self.driver.get_window_size()['height'] / 3 * 2
        self.distance = self.driver.get_window_size()['height'] / 2

    def stop_driver(self):
        if self.driver:
            self.driver.quit()

    def wait_for_find(self, by: str = AppiumBy.ID, value: Union[str, Dict, None] = None, timeout: int = 5):
        # timeout 单位s
        element = WebDriverWait(self.driver, timeout).until(lambda x: self.driver.find_element(by=by, value=value))
        return element

    def wait_for_finds(self, by: str = AppiumBy.ID, value: Union[str, Dict, None] = None, timeout: int = 5):
        # timeout 单位s
        elements = WebDriverWait(self.driver, timeout).until(lambda x: self.driver.find_elements(by=by, value=value))
        return elements

    def swipe(self):
        self.driver.swipe(self.start_x, self.start_y, self.start_x, self.start_y - self.distance)
        time.sleep(2)
