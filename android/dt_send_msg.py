# dt_send_msg.py
from time import sleep

from appium.webdriver.common.appiumby import AppiumBy

from base_test import AppiumHelper


class MessageSender:
    def __init__(self):
        capabilities = dict(
            platformName='Android',
            automationName='uiautomator2',
            deviceName='Android',
            appPackage='com.alibaba.android.rimet',
            appActivity='.biz.LaunchHomeActivity',
            noReset=True,
            # language='en',
            # locale='US'
        )
        appium_server_url = 'http://localhost:4723'
        appium_helper = AppiumHelper(appium_server_url, capabilities)
        self.appium_helper = appium_helper

    def send_message(self):
        wait_for_find = self.appium_helper.wait_for_find
        wait_for_finds = self.appium_helper.wait_for_finds
        # 点击消息
        wait_for_finds(by=AppiumBy.ID, timeout=20,
                           value="com.alibaba.android.rimet:id/home_app_item")[0].click()
        sleep(3)
        # 点击搜索框
        wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/search_btn").click()
        # 搜索聪明的Copilot
        wait_for_find(by=AppiumBy.ID, value="android:id/search_src_text", timeout=15).send_keys("无最")
        # 点击联系人
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.alibaba.android.rimet:id/tv_name").fromParent(new UiSelector().text("联系人"))', timeout=15).click()
        # 点击第一个元素
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.alibaba.android.rimet:id/list_view").childSelector(new UiSelector().index(1))', timeout=15).click()
        # 填充输入的文字
        wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/et_sendmessage").send_keys("测试一下，收到请回复")
        # 点击发送
        wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/btn_send").click()
        sleep(3)