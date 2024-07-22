from time import sleep

from appium.webdriver.common.appiumby import AppiumBy

from .base_test import AppiumHelper


class LanguageHelper:
    def __init__(self):
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
        appium_helper = AppiumHelper(appium_server_url, capabilities)
        self.appium_helper = appium_helper

    def change_to_ch(self):
        wait_for_find = self.appium_helper.wait_for_find
        # wait_for_finds = self.appium_helper.wait_for_finds
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiScrollable(new UiSelector().scrollable(true)).scrollTextIntoView("System")')
        sleep(2)
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("System")').click()
        # 点击 Languages & input
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("Languages & input")').click()
        # 点击 Languages
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("Languages")').click()
        elements = self.appium_helper.driver.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().textContains("简体中文（中国）")')
        if not elements:
            # 点击 Add a language
            wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("Add a language")').click()
            # 滑动到底部
            wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR,
                               value='new UiScrollable(new UiSelector().scrollable(true)).scrollTextIntoView("简体中文")', timeout=10)
            sleep(2)
            # 找到简体中文
            wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("简体中文")').click()
            # 点击中国
            wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("中国")').click()
        chinese = wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("简体中文（中国）").fromParent(new UiSelector().className("android.widget.ImageView"))')
        first = wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("1").fromParent(new UiSelector().className("android.widget.ImageView"))')
        self.appium_helper.driver.drag_and_drop(chinese, first)
        sleep(3)
