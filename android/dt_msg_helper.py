# dt_msg_helper.py
import subprocess
from time import sleep

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException

from utils.openai_api import OpenAiApi
from .base_test import AppiumHelper

default_role = '''
你是一个幽默风趣的智能对话助手，你的任务是与我进行自然、流畅的对话。无论话题严肃或轻松，你都要积极回应，并根据情境提供相关信息。当遇到可能让人感到尴尬或棘手的话题时，你应巧妙地运用机智和幽默来化解，使得对话始终保持愉快的氛围。

示例1：
用户：最近我感觉压力好大，不知道怎么办。
优化后的回复：哎呀，听起来你像是背负了一座喜马拉雅山啊！试试深呼吸，或者找点你喜欢的事情做，比如看个喜剧片，让心情放松一下。如果压力山大到需要搬运工，我随时准备化身“笑声小能手”帮你卸货哦！

示例2：
用户：我对量子物理一窍不通，你能解释一下吗？
优化后的回复：当然可以！想象一下，你在派对上跳舞，你的每一个动作（状态）都同时存在，直到有人（观察者）看你跳舞，你才确定了舞步。这就是量子物理中的“叠加原理”。不过别担心，你不需要在现实生活中同时跳恰恰和探戈，除非你想成为派对焦点！
'''

class MessageHelper:
    def __init__(self):
        # 执行adb指令先kill掉钉钉进程
        adb_command = ["adb", "shell", "am", "force-stop", "com.alibaba.android.rimet"]
        process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 获取命令输出和错误信息
        process.communicate()

        if process.returncode != 0:
            raise RuntimeError("钉钉进程kill失败")

        capabilities = dict(
            platformName='Android',
            automationName='uiautomator2',
            deviceName='Android',
            appPackage='com.alibaba.android.rimet',
            appActivity='.biz.LaunchHomeActivity',
            unicodeKeyboard=True,
            resetKeyboard=True,
            noReset=True

            # language='en',
            # locale='US'
        )
        appium_server_url = 'http://8.219.235.114:4723'
        appium_helper = AppiumHelper(appium_server_url, capabilities)
        self.appium_helper = appium_helper
        self.openAI = OpenAiApi(role=default_role)

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
        input_slot = wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/et_sendmessage")
        loop = True
        while loop:
            try:
                if watcher is None or watcher == '' or '所有' in watcher:
                    # 找到所有消息
                    msgs = (wait_for_find(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/list_view').find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR,value='new UiSelector().resourceId("com.alibaba.android.rimet:id/ll_container").childSelector(new UiSelector().resourceId("com.alibaba.android.rimet:id/chatting_content_tv"))')
                     + wait_for_find(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/list_view').find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR,value='new UiSelector().resourceId("com.alibaba.android.rimet:id/ll_reply_content_container").childSelector(new UiSelector().resourceId("com.alibaba.android.rimet:id/tv_reply_text"))'))
                else:
                    # 找到要监听的人的所有消息
                    msgs = (wait_for_find(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/list_view').find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR,value=f'new UiSelector().descriptionStartsWith("{watcher}说").childSelector(new UiSelector().resourceId("com.alibaba.android.rimet:id/chatting_content_tv"))'),
                           + wait_for_find(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/list_view').find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR,value=f'new UiSelector().descriptionStartsWith("{watcher}说").childSelector(new UiSelector().resourceId("com.alibaba.android.rimet:id/tv_reply_text"))'))
            except WebDriverException:
                sleep(3)
                continue
            if len(msgs) > 0:
                msgs.sort(key=lambda x: x.location['y'])
                text = msgs[-1].text
                if True or self.last_msg != text:
                    print(f'收到消息：{text}')
                    # 说明消息是新的
                    self.last_msg = text
                    reply = self.openAI.chat_with_gpt(text)
                    print(f'回复消息：{reply}')
                    input_slot.send_keys(reply)
                    # 滑动回复
                    self.appium_helper.driver.swipe(msgs[-1].rect['x'] + msgs[-1].rect['width']/2, msgs[-1].rect['y'] + msgs[-1].rect['height']/2,
                                                    self.appium_helper.driver.get_window_size()['width'], msgs[-1].rect['y'] + msgs[-1].rect['height']/2, duration=500)
                    # 点击发送
                    wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/btn_send").click()
                else:
                    print('没有新消息')
                    sleep(3)
                    continue
            else:
                print(f'没有{watcher}的消息')
                sleep(3)
                continue

    def check_read_status(self, group: str, watcher_text: str):
        # 查看消息已读、未读情况
        wait_for_find = self.appium_helper.wait_for_find
        wait_for_finds = self.appium_helper.wait_for_finds
        # 点击消息
        wait_for_finds(by=AppiumBy.ID, timeout=20, value="com.alibaba.android.rimet:id/home_app_item")[0].click()
        sleep(3)
        # 点击搜索框
        wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/search_btn").click()
        # 搜索群组
        wait_for_find(by=AppiumBy.ID, value="android:id/search_src_text", timeout=15).send_keys(group)
        # 点击群组
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.alibaba.android.rimet:id/tv_name").fromParent(new UiSelector().text("群组"))', timeout=15).click()
        # 点击第一个元素
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.alibaba.android.rimet:id/list_view").childSelector(new UiSelector().index(1))', timeout=15).click()
        # 清空文本框
        wait_for_find(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/et_sendmessage').clear()
        try:
            if watcher_text is None or watcher_text == '':
                # 尝试寻找自己的消息已读、未读标签
                unread_status_list = wait_for_finds(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/chatting_unreadcount_tv1', timeout=5)
                unread_texts_list = wait_for_finds(by=AppiumBy.ANDROID_UIAUTOMATOR, value='resourceId("com.alibaba.android.rimet:id/ll_msg_status").fromParent(new UiSelector().resourceId("com.alibaba.android.rimet:id/chatting_content_view_stub")).childSelector(new UiSelector().resourceId("com.alibaba.android.rimet:id/chatting_content_tv"))', timeout=5)
            else:
                text_in_screen = wait_for_find(timeout=10, by=AppiumBy.ANDROID_UIAUTOMATOR, value=f'new UiScrollable(new UiSelector().scrollable(true)).setMaxSearchSwipes(10).scrollTextIntoView("{watcher_text}")')
                unread_status_list = text_in_screen.find_elements(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/chatting_unreadcount_tv1')
                unread_texts_list = text_in_screen.find_elements(by=AppiumBy.ANDROID_UIAUTOMATOR,
                                                   value='resourceId("com.alibaba.android.rimet:id/ll_msg_status").fromParent(new UiSelector().resourceId("com.alibaba.android.rimet:id/chatting_content_view_stub")).childSelector(new UiSelector().resourceId("com.alibaba.android.rimet:id/chatting_content_tv"))')
            if unread_status_list is None or len(unread_status_list) < 1:
                print('没有未读消息')
                return
            ready_to_send_text = ''
            for i in range(min(len(unread_texts_list),len(unread_status_list))):
                if unread_texts_list[i].text != watcher_text:
                    continue
                ready_to_send_text += unread_texts_list[i].text + "\n"
                sleep(1)
                unread_status = unread_status_list[i]
                unread_status.click()
                # 进入消息接收人列表页，查看已读、未读数
                no_read, yes_read = wait_for_finds(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/tv_text', timeout=5)
                # 找到未读人列表
                # no_read.click()
                unread_list = wait_for_finds(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/tv_contact_name', timeout=5)
                ready_to_send_text += no_read.text + ":\n"
                for unread in unread_list:
                    ready_to_send_text += unread.text + " "
                # 找到已读人列表
                yes_read.click()
                read_list = wait_for_finds(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/tv_contact_name', timeout=5)
                ready_to_send_text += "\n" + yes_read.text + ":\n"
                for read in read_list:
                    ready_to_send_text += read.text + " "
                ready_to_send_text += "\n\n"
                # 点击返回
                self.appium_helper.driver.back()
                print(ready_to_send_text)
            # 点击返回
            self.appium_helper.driver.back()
            # 点击联系人
            wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().resourceId("com.alibaba.android.rimet:id/tv_name").fromParent(new UiSelector().text("联系人"))', timeout=15).click()
            # 搜索人名
            search_slot = wait_for_find(by=AppiumBy.ID, value="android:id/search_src_text", timeout=15)
            search_slot.clear()
            search_slot.send_keys("我")
            # 点击第一个元素
            wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR,value='new UiSelector().resourceId("com.alibaba.android.rimet:id/list_view").childSelector(new UiSelector().index(1))', timeout=15).click()
            # 找到文本框
            wait_for_find(by=AppiumBy.ID, value='com.alibaba.android.rimet:id/et_sendmessage').send_keys(f'{ready_to_send_text}')
            # 点击发送
            wait_for_find(by=AppiumBy.ID, value="com.alibaba.android.rimet:id/btn_send").click()
        except WebDriverException as e:
            raise e





