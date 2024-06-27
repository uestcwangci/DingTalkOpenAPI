import unittest
from time import sleep

from appium.webdriver.common.appiumby import AppiumBy

from test.base import BaseTest


class TestAppium(BaseTest):
    def __init__(self, methodName="runTest"):
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
        super().__init__(methodName, appium_server_url=appium_server_url, capabilities=capabilities)

    def test_send_msg(self) -> None:
        # # 同意协议
        # self.wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/btn_agree").click()
        # # 输入电话
        # self.wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/et_phone_input", timeout=30).send_keys("18981571994")
        # # 同意协议
        # self.wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/cb_privacy").click()
        # # 点击下一步
        # self.wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/ll_next").click()
        # #  点击密码登录
        # self.wait_for_find(by=AppiumBy.XPATH, value='//*[@text="密码登录"]').click()
        # #  输入密码
        # self.wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/et_pwd_input").send_keys("wc452871960")
        # #  点击登录
        # self.wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/btn_confirm").click()
        # 点击消息
        self.wait_for_finds(by=AppiumBy.ID, timeout=20,
                           value="com.alibaba.android.rimet:id/home_app_item")[0].click()
        sleep(3)
        # 点击搜索框
        self.wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/search_btn").click()
        # 搜索聪明的Copilot
        self.wait_for_find(by=AppiumBy.ID, value="android:id/search_src_text", timeout=15).send_keys("零封")
        # 点击联系人
        self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.alibaba.android.rimet:id/tv_name").fromParent(new UiSelector().text("联系人"))', timeout=15).click()
        # 点击第一个元素
        self.wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.alibaba.android.rimet:id/list_view").childSelector(new UiSelector().index(1))', timeout=15).click()
        # 填充输入的文字
        self.wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/et_sendmessage").send_keys("测试一下，收到请回复")
        # 点击发送
        self.wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/btn_send").click()
        sleep(3)


if __name__ == '__main__':
    unittest.main()
