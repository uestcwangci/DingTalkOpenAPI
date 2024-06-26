import time
import unittest

from android.base_test import BaseTest
from appium.webdriver.common.appiumby import AppiumBy


class TestAppium(BaseTest):
    def __init__(self, methodName="runTest"):
        capabilities = dict(
            platformName='Android',
            automationName='uiautomator2',
            deviceName='Android',
            appPackage='com.android.settings',
            appActivity='.Settings'
            # language='en',
            # locale='US'
        )

        appium_server_url = 'http://localhost:4723'
        # appium_server_url = 'http://147.139.208.135:4723'
        super().__init__(methodName, appium_server_url=appium_server_url, capabilities=capabilities)

    def test_ai_see(self):
        self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiScrollable(new UiSelector().scrollable(true)).scrollTextIntoView("System")')
        time.sleep(2)
        self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("System")').click()
        # 点击 Languages & input
        self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("Languages & input")').click()
        # 点击 Languages
        self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("Languages")').click()
        elements = self.driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().textContains("简体中文（中国）")')
        if not elements:
            # 点击 Add a language
            self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("Add a language")').click()
            # 滑动到底部
            self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR,
                               value='new UiScrollable(new UiSelector().scrollable(true)).scrollTextIntoView("简体中文")', timeout=10)
            time.sleep(2)
            # 找到简体中文
            self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("简体中文")').click()
            # 点击中国
            self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("中国")').click()
        chinese = self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("简体中文（中国）").fromParent(new UiSelector().className("android.widget.ImageView"))')
        first = self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("1").fromParent(new UiSelector().className("android.widget.ImageView"))')
        self.driver.drag_and_drop(chinese, first)
        time.sleep(3)


if __name__ == '__main__':
    unittest.main()
