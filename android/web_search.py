# dt_msg_helper.py
import subprocess
from time import sleep

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException

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
            chromedriverExecutableDir='/home/ecs-user/dev/chromedriver125',
            ensureWebviewsHavePages=True, # Appium是否应该增强它的页面webview检测，以保证任何webview上下文显示在上下文列表有活动的页面。 这可以防止在Chromedriver无法找到任何页面的情况下选择上下文时发生的错误。
            nativeWebScreenshot=True
            # nativeWebScreenshot=True, # 在Web上下文中，使用nat ive（adb）方法获取屏幕截图，而不是代理ChromeDriver
            # recreateChromeDriverSessions=True, # 移至非ChromeDriver网页浏览时，请停用ChromeDriver会话
            # noReset=False
        )

        appium_server_url = 'http://127.0.7.1:4723'
        appium_helper = AppiumHelper(appium_server_url, capabilities)
        self.appium_helper = appium_helper
        self.dingtalk_api = DingTalkAPI("dingmyqgaxb9rwvqiuh5",
                                        "DshTZwI5kcRKlJNMXwoaxe1_MSkFnsKTpPnK5raWUtfu5Ut3t-ObzYy0LqudIDS2")

    def search_for(self, url: str):

        try:
            wait_for_find = self.appium_helper.wait_for_find
            # 搜索网页
            # self.appium_helper.driver.get(url)
            search_block = wait_for_find(AppiumBy.ID, 'url_field')
            search_block.clear()
            search_block.send_keys(url)
            wait_for_find(AppiumBy.ACCESSIBILITY_ID, 'Load URL').click()
            # 切换到webView context
            self.appium_helper.driver.switch_to.context("WEBVIEW_org.chromium.webview_shell")
            # 等待页面加载完成
            WebDriverWait(self.appium_helper.driver, 20).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            # 等待加载
            # sleep(10)

            # 获取当前url
            print(self.appium_helper.driver.current_url)

            # 定位元素
            html = self.appium_helper.driver.execute_script("return document.documentElement.outerHTML")
            self.appium_helper.driver.quit()
            print("Appium driver quit.")
            return {"html": html}
        except TimeoutException:
            print("页面加载超时，未能完成加载。")
            return {"error": "TimeoutException"}
