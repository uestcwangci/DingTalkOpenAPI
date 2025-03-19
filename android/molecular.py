import time

from appium.webdriver import WebElement
from appium.webdriver.common.appiumby import AppiumBy
from typing import Union, Dict, List
from android import logger
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Molecular:
    def __init__(self, driver):
        self.driver = driver
        self.webview_context = "WEBVIEW_com.alibaba.android.rimet"  # 可配置的 WebView 上下文

    def _switch_context_for_by(self, by: str) -> None:
        """
        根据定位策略自动切换上下文。
        """
        # WebView 支持的定位方式
        webview_strategies = [AppiumBy.CSS_SELECTOR]

        current_context = self.driver.current_context
        available_contexts = self.driver.contexts

        if by in webview_strategies:
            if self.webview_context in available_contexts:
                if current_context != self.webview_context:
                    logger.info(f"Switching context from '{current_context} to '{self.webview_context}")
                    self.driver.switch_to.context(self.webview_context)
            else:
                raise Exception(f"WebView context '{self.webview_context}' not available. Available contexts: {available_contexts}")
        else:
            if current_context != "NATIVE_APP":
                logger.info(f"Switching context from '{current_context} to 'NATIVE_APP'")
                self.driver.switch_to.context("NATIVE_APP")

    def wait_for_find(self, by: str = AppiumBy.ID, value: Union[str, Dict, None] = None, timeout: int = 5) -> WebElement:
        """
        等待并查找单个元素，自动切换上下文。
        :param by: 定位策略 (e.g., AppiumBy.ID, AppiumBy.CSS_SELECTOR)
        :param value: 定位值
        :param timeout: 等待超时时间（单位：秒）
        :return: 找到的元素
        """
        self._switch_context_for_by(by)
        element = WebDriverWait(self.driver, timeout).until(
            lambda x: self.driver.find_element(by=by, value=value)
        )
        return element

    def wait_for_finds(self, by: str = AppiumBy.ID, value: Union[str, Dict, None] = None, timeout: int = 5) -> List[WebElement]:
        """
        等待并查找多个元素，自动切换上下文。
        :param by: 定位策略 (e.g., AppiumBy.ID, AppiumBy.CSS_SELECTOR)
        :param value: 定位值
        :param timeout: 等待超时时间（单位：秒）
        :return: 找到的元素列表
        """
        self._switch_context_for_by(by)
        elements = WebDriverWait(self.driver, timeout).until(
            lambda x: self.driver.find_elements(by=by, value=value)
        )
        return elements

    def scroll_into_text(self, parent_value, text, direction="vertical", timeout=10):
        """
        在指定容器内滚动，直到找到包含指定文本的元素并返回。

        Args:
            parent_value: 滚动容器的 resourceId (如 "com.example:id/scroll_view")。
            text: 目标元素的文本内容。
            direction: 滚动方向，"vertical"（垂直，默认）或 "horizontal"（水平）。
            timeout: 查找超时时间（秒），默认 5。

        Returns:
            WebElement: 找到的目标元素。

        Raises:
            NoSuchElementException: 如果滚动容器未找到。
            TimeoutException: 如果目标元素未找到。
            ValueError: 如果方向参数无效。
        """
        # 验证方向参数并构造 UIAutomator 滚动表达式
        scroll_expression = (
            f'new UiScrollable(new UiSelector().resourceId("{parent_value}").scrollable(true))'
        )
        if direction == "horizontal":
            scroll_expression += f'.setAsHorizontalList().scrollTextIntoView("{text}")'
        elif direction == "vertical":
            scroll_expression += f'.scrollTextIntoView("{text}")'
        else:
            logger.error(f"Invalid scroll direction: {direction}")
            raise ValueError(f"Direction must be 'vertical' or 'horizontal', got: {direction}")

        # 查找并返回目标元素
        try:
            target_element = self.wait_for_find(AppiumBy.ANDROID_UIAUTOMATOR, scroll_expression, timeout=timeout)
            logger.info(f"Found target element with text: '{text}' in {direction} scroll")
            return target_element
        except TimeoutException:
            logger.error(f"Could not find element with text '{text}' in {timeout} seconds")
            raise TimeoutException(f"Failed to scroll to element with text '{text}'")

    def _enter_chat(self, chat_type: str, value: str):
        """
        进入聊天（单聊或群聊）
        chat_type: "contact（联系人）" || "group（群组） || "workapp（工作台）"
        value: 搜索的名称
        """
        if value is None:
            raise ValueError(f"Value for enter_{chat_type} is required")

        # 点击搜索按钮
        self.wait_for_find(AppiumBy.ID, "com.alibaba.android.rimet:id/search_btn").click()

        # 根据类型选择不同的标签
        tab_text = "工作台" if chat_type == "workapp" else "联系人" if chat_type == "contact" else "群组"
        tab = self.scroll_into_text("com.alibaba.android.rimet:id/lv_tabs",
                                    tab_text,direction="horizontal",timeout=10)
        tab.click()

        # 输入搜索内容
        self.wait_for_find(by=AppiumBy.ID, value="android:id/search_src_text", timeout=15).send_keys(value)

        if tab_text == "工作台":
            # Web页面
            # 打印当前状态
            print("Available Contexts:", self.driver.contexts)

            # 等待页面加载
            time.sleep(2)
            # 等待 WebView 可用
            WebDriverWait(self.driver, 30).until(lambda d: len(d.contexts) > 1)
            # 点击第一个搜索结果
            self.wait_for_find(
                by=AppiumBy.CSS_SELECTOR,
                value='.dtm-list-item:first-of-type .dtm-button-button',
                timeout=5
            ).click()
            return {"message": f"Entered {chat_type} chat with {value}", "success": True}
        else:
            # Native页面
            # 点击第一个搜索结果
            self.wait_for_find(
                by=AppiumBy.ANDROID_UIAUTOMATOR,
                value='new UiSelector().resourceId("com.alibaba.android.rimet:id/list_view").childSelector(new UiSelector().index(1))',
                timeout=15
            ).click()
            return {"message": f"Entered {chat_type} chat with {value}", "success": True}

    def execute(self, action, data):
        value = data.get("value")

        if action == "enter_single_chat":
            return self._enter_chat("contact", value)
        elif action == "enter_group_chat":
            return self._enter_chat("group", value)
        elif action == "enter_app":
            return self._enter_chat("workapp", value)
        else:
            logger.error(f"Unknown molecular: {action}")
            return {"message": f"Error: Unsupported actionType '{action}'", "success": True}

