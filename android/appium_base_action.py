import json
from typing import Union, Dict, List

from appium.webdriver import WebElement
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from android import logger


class AppiumBaseAction:
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

    def call_native(self, call_type: str, **kwargs):
        """
        Consolidated method to call native functionality via broadcast intents.

        Args:
            call_type: Type of call - "static", "instance", or "jsapi"
            **kwargs: Arguments specific to each call type:
                - static: class_name, method, params (optional)
                - instance: class_name, method, instance_method (optional), params (optional)
                - jsapi: service_name, action_name, params (optional)

        Returns:
            None
        """
        method_call = {"type": call_type}

        if call_type == "static" or call_type == "instance":
            """
            数据结构示例:
            {
                "type": "static",
                "className": "com.alibaba.android.dingtalkbase.tools.AndTools",
                "method": "showToast",
                "params": [
                    {"type": "string", "value": "Hello World"}
                ]
            }
            """
            class_name = kwargs.get("class_name")
            method = kwargs.get("method")

            if not class_name or not method:
                raise ValueError(f"For {call_type} calls, class_name and method are required")

            method_call["className"] = class_name
            method_call["method"] = method
            method_call["params"] = kwargs.get("params")

            if call_type == "instance":
                method_call["instanceMethod"] = kwargs.get("instance_method", "getInstance")

        elif call_type == "jsapi":
            service_name = kwargs.get("service_name")
            action_name = kwargs.get("action_name")

            if not service_name or not action_name:
                raise ValueError("For jsapi calls, service_name and action_name are required")

            method_call["jsapiParams"] = {
                "serviceName": service_name,
                "actionName": action_name,
                "params": kwargs.get("params")
            }
        else:
            raise ValueError(f"Unsupported call type: {call_type}")

        # Convert method_call to a properly escaped JSON string
        json_string = json.dumps(method_call, ensure_ascii=False)

        broadcast_command = {
            'command': 'am broadcast',
            'args': ['-a', 'appium.to.dingtalk.ACTION', '--es', 'methodCall', json_string]
        }

        try:
            result = self.driver.execute_script('mobile: shell', broadcast_command)
            logger.info(f"Shell command result: {result}")
            return result
        except Exception as e:
            import traceback
            logger.error(f"Call native error: {str(e)}\n{traceback.format_exc()}")
            raise
