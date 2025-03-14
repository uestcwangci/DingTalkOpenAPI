import time
from typing import Union, Dict

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput


class AppiumHelper:
    def __init__(self, appium_server_url: str = None, capabilities: Dict = None):
        self.driver = webdriver.Remote(appium_server_url,
                                       options=UiAutomator2Options().load_capabilities(capabilities))
        # 设置等待元素出现10s
        self.driver.implicitly_wait(10)
        # 获取宽高
        self.start_x = self.driver.get_window_size()['width'] / 2
        self.start_y = self.driver.get_window_size()['height'] / 3 * 2
        self.distance = self.driver.get_window_size()['height'] / 2

    def stop_driver(self):
        if self.driver:
            self.driver.quit()

    def wait_for_find(self, by: str = AppiumBy.ID, value: Union[str, Dict, None] = None, timeout: int = 5):
        # timeout 单位s
        element = WebDriverWait(self.driver, timeout).until(lambda x: self.driver.find_element(by=by, value=value))
        return element

    def wait_for_finds(self, by: str = AppiumBy.ID, value: Union[str, Dict, None] = None, timeout: int = 5):
        # timeout 单位s
        elements = WebDriverWait(self.driver, timeout).until(lambda x: self.driver.find_elements(by=by, value=value))
        return elements

    def swipe(self):
        self.driver.swipe(self.start_x, self.start_y, self.start_x, self.start_y - self.distance)
        time.sleep(2)

    def click(self, x, y):
        actions = ActionChains(self.driver)
        pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
        actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)
        actions.w3c_actions.pointer_action.move_to_location(x, y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(0.1)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

    def doubleClick(self, x, y):
        # 创建双击动作序列
        actions = ActionChains(self.driver)
        pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
        actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)

        # 移动到指定位置
        actions.w3c_actions.pointer_action.move_to_location(x, y)

        # 执行两次点击
        for _ in range(2):
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pointer_action.pause(0.1)
            actions.w3c_actions.pointer_action.release()
            actions.w3c_actions.pointer_action.pause(0.1)

        actions.perform()

    def scroll(self, start, end):
        from_x = start[0]
        from_y = start[1]
        to_x = end[0]
        to_y = end[1]
        if all([from_x, from_y, to_x, to_y]):
            actions = ActionChains(self.driver)
            pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
            actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)
            actions.w3c_actions.pointer_action.move_to_location(from_x, from_y)
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pointer_action.move_to_location(to_x, to_y)
            actions.w3c_actions.pointer_action.release()
            actions.perform()

    def type(self, x, y, text):
        # 点击输入框位置
        actions = ActionChains(self.driver)
        pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
        actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)
        actions.w3c_actions.pointer_action.move_to_location(x, y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(0.1)
        actions.w3c_actions.pointer_action.release()
        actions.perform()
        # 输入文本
        self.driver.execute_script("mobile: shell", {
            "command": "input",
            "args": ["text", text]
        })

    def longClick(self, x, y, duration=1.0):
        """
        在指定位置执行长按操作

        参数:
        x, y: 点击位置的坐标
        duration: 长按持续时间(秒)，默认1秒
        """
        actions = ActionChains(self.driver)
        pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
        actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)

        # 移动到指定位置
        actions.w3c_actions.pointer_action.move_to_location(x, y)

        # 按下并保持指定时间
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(duration)  # 持续按压
        actions.w3c_actions.pointer_action.release()

        actions.perform()

    def copy_text(self, text):
        """
        直接将文本复制到剪贴板

        参数:
        text: 要复制的文本
        """
        escaped_text = text.replace('"', '\\"')  # 转义引号
        self.driver.execute_script('mobile: shell', {
            'command': f'am broadcast -a clipper.set -e text "{escaped_text}"'
        })

    def paste_text(self, x, y):
        """
        在指定位置粘贴文本
        x, y: 目标位置坐标
        """
        # 1. 点击目标位置
        actions = ActionChains(self.driver)
        pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
        actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)
        actions.w3c_actions.pointer_action.move_to_location(x, y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(0.1)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

        # 2. 等待输入框获得焦点
        time.sleep(0.5)

        # 3. 执行粘贴操作
        try:
            # 方法1：使用系统按键模拟粘贴操作
            self.driver.execute_script('mobile: shell', {
                'command': 'input keyevent 279'  # KEYCODE_PASTE
            })
        except:
            try:
                # 方法2：尝试点击粘贴按钮
                paste_button = self.driver.find_element(AppiumBy.XPATH,
                                                        "//android.widget.TextView[@text='粘贴']")
                paste_button.click()
            except:
                # 方法3：使用快捷键组合
                self.driver.press_keycode(47, 50)  # Ctrl + V

        return True

    def show_toast(self, message, duration=2):
        """
        使用 UiAutomator2 显示 Toast
        """
        try:
            # 使用 UiAutomator2 的脚本执行 Toast
            script = f"""
            UiDevice.getInstance().executeShellCommand(
                "am broadcast -a android.intent.action.SHOW_TOAST " +
                "-e message \\"{message}\\" " +
                "-e duration \\"{duration * 1000}\\""
            );
            """
            self.driver.execute_script(script)
        except Exception as e:
            print(f"Toast显示失败: {str(e)}")
            # 备用方案：使用 adb shell
            try:
                adb_command = f'am broadcast -a android.intent.action.SHOW_TOAST -e message "{message}" -e duration "{duration * 1000}"'
                self.driver.execute_script('mobile: shell', {'command': adb_command})
            except Exception as e2:
                print(f"备用方案失败: {str(e2)}")
                raise



