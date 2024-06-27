# dt_msg_helper.py
from time import sleep

from appium.webdriver.common.appiumby import AppiumBy
from flask import Flask

from utils.ai_api import create_chat, send_chat_message
from .base_test import AppiumHelper


class MessageHelper:
    def __init__(self, logger: Flask.logger = None):
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
        self.listen_session_id = create_chat('你好，请和我用中文对话')
        self.logger = logger

    def send_message(self, name: str = None, message: str = None):
        if name is None or message is None:
            return
        wait_for_find = self.appium_helper.wait_for_find
        wait_for_finds = self.appium_helper.wait_for_finds
        # 点击消息
        wait_for_finds(by=AppiumBy.ID, timeout=20,
                           value="com.alibaba.android.rimet:id/home_app_item")[0].click()
        sleep(3)
        # 点击搜索框
        wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/search_btn").click()
        # 搜索人名
        wait_for_find(by=AppiumBy.ID, value="android:id/search_src_text", timeout=15).send_keys(name)
        # 点击联系人
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.alibaba.android.rimet:id/tv_name").fromParent(new UiSelector().text("联系人"))', timeout=15).click()
        # 点击第一个元素
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.alibaba.android.rimet:id/list_view").childSelector(new UiSelector().index(1))', timeout=15).click()
        # 填充输入的文字
        wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/et_sendmessage").send_keys(message)
        # 点击发送
        wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/btn_send").click()
        sleep(3)

    last_msg: str = None

    def reply_message(self, group: str, watcher: str):
        if group is None:
            return
        wait_for_find = self.appium_helper.wait_for_find
        wait_for_finds = self.appium_helper.wait_for_finds

        # 点击消息
        wait_for_finds(by=AppiumBy.ID, timeout=20,
                       value="com.alibaba.android.rimet:id/home_app_item")[0].click()
        sleep(3)
        # 点击搜索框
        wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/search_btn").click()
        # 搜索群组
        wait_for_find(by=AppiumBy.ID, value="android:id/search_src_text", timeout=15).send_keys(group)
        # 点击群组
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.alibaba.android.rimet:id/tv_name").fromParent(new UiSelector().text("群组"))', timeout=15).click()
        # 点击第一个元素
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.alibaba.android.rimet:id/list_view").childSelector(new UiSelector().index(1))', timeout=15).click()
        # 找到文本填充框
        input = wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/et_sendmessage")
        loop = True
        while loop:
            # 找到要监听的人的所有消息
            msgs = wait_for_find(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/list_view').find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR, value=f'new UiSelector().descriptionContains("{watcher}说").childSelector(new UiSelector().resourceId("com.alibaba.android.rimet:id/chatting_content_tv"))')
            if len(msgs) > 0:
                text = msgs[-1].text
                if self.last_msg != text:
                    self.logger(f'收到消息：{text}')
                    # 说明消息是新的
                    self.last_msg = text
                    reply = send_chat_message(self.listen_session_id, text)
                    self.logger.info(f'回复消息：{reply}')
                    input.send_keys(reply)
                    # 点击发送
                    wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/btn_send").click()
                else:
                    self.logger('没有新消息')
                    sleep(3)
                    continue
            else:
                self.logger.info(f'没有{watcher}的消息')
                sleep(3)
                continue

