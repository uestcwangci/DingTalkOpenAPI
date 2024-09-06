# dt_msg_helper.py
import subprocess
from time import sleep

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException
from utils.dingtalk_api import DingTalkAPI

from .base_test import AppiumHelper


class SearchHelper:
    def __init__(self):
        capabilities = dict(
            platformName='Android',
            automationName='Uiautomator2',
            deviceName='Android',
            appPackage='org.chromium.webview_shell',
            appActivity='.WebViewBrowserActivity',
            unicodeKeyboard=True,
            resetKeyboard=True
            # browserName='Chromium',
            # chromedriverExecutableDir='/home/ecs-user/dev/chromedriver',
            # nativeWebScreenshot=True, # 在Web上下文中，使用nat ive（adb）方法获取屏幕截图，而不是代理ChromeDriver
            # recreateChromeDriverSessions=True, # 移至非ChromeDriver网页浏览时，请停用ChromeDriver会话
            # noReset=True
        )

        appium_server_url = 'http://127.0.7.1:4723'
        appium_helper = AppiumHelper(appium_server_url, capabilities)
        self.appium_helper = appium_helper
        self.dingtalk_api = DingTalkAPI("dingmyqgaxb9rwvqiuh5",
                                        "DshTZwI5kcRKlJNMXwoaxe1_MSkFnsKTpPnK5raWUtfu5Ut3t-ObzYy0LqudIDS2")

    def search_for(self, url:str):
        wait_for_find = self.appium_helper.wait_for_find
        wait_for_finds = self.appium_helper.wait_for_finds
        # 搜索网页
        search_block = wait_for_find(AppiumBy.ID, 'url_field')
        search_block.clear()
        search_block.send_keys(url)
        wait_for_find(AppiumBy.ACCESSIBILITY_ID, 'Load URL').click()
        # 等待跳转
        sleep(10)

        # 定位元素
        all_text_view = wait_for_finds(AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().className("android.widget.TextView")')
        text_list = []
        # 打印页面中class_name为android.widget.TextView元素的文本内容
        for i in all_text_view:
            stripped_text = i.text.strip()
            if stripped_text:  # 仅当不为空时添加到 text_list
                text_list.append(stripped_text)
        print(text_list)
        result = {}
        if text_list and text_list[0].startswith("WebView"):
            text_list = text_list[1:]
        if len(text_list) < 3:
            result = {}
        if len(text_list) > 3:
            result["title"] = text_list[0]
            result["time"] = text_list[1]
            result["content"] = text_list[2]
            result["extension"] = text_list[3:]
        else:
            result["title"] = text_list[0]
            result["time"] = text_list[1]
            result["content"] = text_list[2]
            result["extension"] = []
        self.appium_helper.driver.quit()
        print("Appium driver quit.")
        return result