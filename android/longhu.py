# longhu.py
from time import sleep

from appium.webdriver.common.appiumby import AppiumBy
from android.base_test import AppiumHelper


class LongHuHelper:
    def __init__(self):
        capabilities = dict(
            platformName='Android',
            automationName='uiautomator2',
            deviceName='Android',
            appPackage='com.longfor.supera',
            appActivity='.main.MainActivity',
            unicodeKeyboard=True,
            resetKeyboard=True,
            noReset=True,
            forceAppLaunch=True,
            autoGrantPermissions=True,
            newCommandTimeout=300,  # 5分钟
            udid="47.97.156.72:1001"
        )

        appium_server_url = 'http://localhost:4723'
        appium_helper = AppiumHelper(appium_server_url, capabilities)
        self.appium_helper = appium_helper

    def qian_dao(self):
        wait_for_find = self.appium_helper.wait_for_find
        wait_for_finds = self.appium_helper.wait_for_finds
        # 点击设备按钮
        sleep(5)
        # 点击“会员”按钮
        tabs = wait_for_finds(by=AppiumBy.ID, value="com.longfor.supera:id/tab_text")
        for tab in tabs:
            if '会员' in tab.text:
                tab.click()
                break
        # 向下滑动
        self.appium_helper.driver.swipe(400, 900, 400, 600)
        # 点击“抽奖按钮"
        sleep(2)
        wait_for_finds(by=AppiumBy.ID, value="com.longfor.supera:id/img_item")[1].click()
        # 点击“点击抽奖”按钮
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("点击抽奖")').click()
        # 点击“去签到”按钮
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("去签到")').click()
        # 返回
        self.appium_helper.driver.back()
        # 点击“点击抽奖”按钮
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("点击抽奖")').click()

if __name__ == '__main__':
    longhu_helper = LongHuHelper()
    longhu_helper.qian_dao()
    longhu_helper.appium_helper.driver.quit()
