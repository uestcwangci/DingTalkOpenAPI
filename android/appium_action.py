import sys
import tempfile

from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
import time
import base64
from android import logger
from typing import Literal
import os
from android.molecular import Molecular

from selenium.webdriver.support.wait import WebDriverWait


ACCESS_TOKEN = "lGqMusyvAMqNJEJLmgZanGPAgPNdEtNBwZJAnAxndkE"  # 替换为你的DingTalk token

def upload_file_to_cdn(file_path: str, file_type: Literal['image', 'video']) -> str:
    if not file_path or not os.path.exists(file_path):
        raise ValueError('Invalid file path')
    if file_type not in ['image', 'video']:
        raise ValueError('Invalid file type. Must be "image" or "video"')

    file_name = os.path.basename(file_path)

    try:
        from requests_toolbelt.multipart.encoder import MultipartEncoder
        import requests
        m = MultipartEncoder(
            fields={
                'file': (file_name, open(file_path, 'rb'), 'image/png' if file_type == 'image' else 'video/mp4'),
                'mimeType': file_type  # 修正mimeType为动态值
            }
        )
        headers = {
            'Content-Type': m.content_type,
            'Authorization': f'Bearer {ACCESS_TOKEN}'
        }
        logger.info(f"Uploading {'screenshot' if file_type == 'image' else 'video'} file: {file_path}")
        response = requests.post(
            'https://devtool.dingtalk.com/vscode/uploadFile',
            headers=headers,
            data=m,
            timeout=None
        )
        response.raise_for_status()
        data = response.json()
        if 'cdnUrl' not in data:
            raise ValueError('Upload response missing CDN URL')
        logger.info(f"{'截屏' if file_type == 'image' else '视频'}文件上传成功 {data['cdnUrl']}")
        return data['cdnUrl']
    except requests.RequestException as error:
        error_message = error.response.json() if error.response and error.response.text else str(error)
        logger.error(f'文件上传失败: {error_message}')
        raise

class AppiumAction:
    def __init__(self):
        self.driver = None
        self.desired_caps = {
            "platformName": "Android",
            "appium:deviceName": "Android",  # 建议替换为具体设备名，如 "emulator-5554"
            "appium:appPackage": "com.alibaba.android.rimet",
            "appium:appActivity": ".biz.LaunchHomeActivity",
            "appium:automationName": "Uiautomator2",
            "appium:chromeOptions": {
                "androidProcess": "com.alibaba.android:rimet"
            },
            # "appium:ensureWebviewsHavePages": True,
            # "appium:chromedriverExecutable": "/home/ecs-user/.appium/drivers/chromedriver/chrome-linux64",  # 替换为你的chromedriver路径
            "appium:unicodeKeyboard": False,
            "appium:resetKeyboard": False,
            "appium:noReset": True,
            "appium:forceAppLaunch": True,
            "appium:newCommandTimeout": 0,
        }
        self.molecular = None

    def execute(self, action_data):
        """根据actionType执行不同操作"""
        action = action_data.get("action")
        data = action_data.get("data", {})
        logger.info(f"Executing action: {action} with data: {data}")

        try:
            if action == "start":
                if self.driver is None:
                    self.driver = webdriver.Remote('http://localhost:4723',
                                                   options=UiAutomator2Options().load_capabilities(self.desired_caps))
                    logger.info("Appium driver initialized")
                    # 等待应用的主Activity加载完成
                    WebDriverWait(self.driver, timeout=30).until(
                        lambda driver: driver.current_activity == self.desired_caps["appium:appActivity"]
                    )
                    logger.info(f"Application {self.desired_caps['appium:appActivity']} is ready")
                    time.sleep(3)
                    self.molecular = Molecular(self.driver)
                    return {"message": "Appium driver started", "success": True}
                return {"message": "Appium driver already started", "success": True}
            elif action == "done":
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                    return {"message": "Appium driver quit", "success": True}
                return {"message": "No Appium driver to quit", "success": False}
            elif action == "home":
                # 重新启动应用
                self.driver.terminate_app(self.desired_caps["appium:appPackage"])  # 先关闭应用
                self.driver.activate_app(self.desired_caps["appium:appPackage"])  # 重新启动应用

                # 等待主页面加载
                WebDriverWait(self.driver, timeout=30).until(
                    lambda driver: driver.current_activity == self.desired_caps["appium:appActivity"]
                )
                time.sleep(3)  # 等待页面完全加载

                return {"message": "Successfully returned to home page", "success": True}
            elif action == "screenshot":
                if self.driver:
                    # 获取base64截图并保存为临时文件
                    screenshot_base64 = self.driver.get_screenshot_as_base64()
                    logger.info("Screenshot captured")
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                        temp_file.write(base64.b64decode(screenshot_base64))
                        temp_file_path = temp_file.name
                    try:
                        # 上传到CDN
                        cdn_url = upload_file_to_cdn(temp_file_path, "image")
                        return {"message": "Screenshot captured", "screenshot": cdn_url, "success": True}
                    except Exception as e:
                        logger.error(f"Error uploading screenshot: {str(e)}")
                        return {"message": f"Error uploading screenshot: {str(e)}", "success": False}
                    finally:
                        os.remove(temp_file_path)  # 清理临时文件
                return {"message": "Appium driver not started", "success": False}
            elif action == "wait":
                seconds = data.get("value", 2)
                if seconds > 0:
                    time.sleep(seconds)
                    return {"message": f"Waited for {seconds} seconds", "success": True}
                return {"message": "Error: Invalid wait time", "success": False}
            elif action == "click":
                x = data.get("x")
                y = data.get("y")
                if x is not None and y is not None:
                    actions = ActionChains(self.driver)
                    pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
                    actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)
                    actions.w3c_actions.pointer_action.move_to_location(x, y)
                    actions.w3c_actions.pointer_action.pointer_down()
                    actions.w3c_actions.pointer_action.pause(0.1)
                    actions.w3c_actions.pointer_action.release()
                    actions.perform()
                    return {"message": f"Clicked at ({x}, {y})", "success": True}
                return {"message": "Error: Missing x or y coordinates", "success": False}
            elif action == "long_press":
                x = data.get("x")
                y = data.get("y")
                if x is not None and y is not None:
                    actions = ActionChains(self.driver)
                    pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
                    actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)
                    actions.w3c_actions.pointer_action.move_to_location(x, y)
                    actions.w3c_actions.pointer_action.pointer_down()
                    actions.w3c_actions.pointer_action.pause(1)
                    actions.w3c_actions.pointer_action.release()
                    actions.perform()
                    return {"message": f"Long pressed at ({x}, {y})", "success": True}
                return {"message": "Error: Missing x or y coordinates", "success": False}
            elif action == "type":
                x = data.get("x")
                y = data.get("y")
                text = data.get("value")
                if x is None or y is None or text is None:
                    return {"message": "Error: Missing x, y, or value", "success": False}

                # 点击输入框位置
                actions = ActionChains(self.driver)
                pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
                actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)
                actions.w3c_actions.pointer_action.move_to_location(x, y)
                actions.w3c_actions.pointer_action.pointer_down()
                actions.w3c_actions.pointer_action.pause(0.1)
                actions.w3c_actions.pointer_action.release()
                actions.perform()

                # 动态等待输入框就绪
                try:
                    WebDriverWait(self.driver, 5).until(
                        lambda driver: driver.switch_to.active_element.tag_name in ["input", "textarea"]
                    )
                    logger.info("Input field is ready")
                except Exception as wait_error:
                    logger.warning(f"Failed to wait for input field: {wait_error}")
                    time.sleep(1)  # 备用等待

                # 获取当前活跃元素
                element = self.driver.switch_to.active_element

                # 方法 1：尝试 send_keys
                try:
                    element.send_keys(text)
                    logger.info("Text input via send_keys succeeded")
                except Exception as e:
                    logger.info(f"Send_keys failed: {e}")
                    # 方法 2：使用 ADB 输入（适合英文和简单字符）
                    try:
                        adb_text = text.replace(" ", "%s")  # 处理空格
                        self.driver.execute_script("mobile: shell", {
                            "command": "input",
                            "args": ["text", adb_text]
                        })
                        logger.info("Text input via ADB succeeded")
                    except Exception as adb_error:
                        logger.error(f"ADB input failed: {adb_error}")
                        # 方法 3：使用剪贴板输入（支持中文）
                        try:
                            self.driver.set_clipboard_text(text)
                            element.click()  # 确保焦点
                            self.driver.execute_script("mobile: shell", {
                                "command": "input",
                                "args": ["keyevent", "279"]  # KEYCODE_PASTE
                            })
                            logger.info("Text input via clipboard succeeded")
                        except Exception as clipboard_error:
                            logger.error(f"Clipboard input failed: {clipboard_error}")
                            # 方法 4：备用方案，使用 JavaScript（H5 页面）
                            try:
                                self.driver.execute_script("arguments[0].value = arguments[1];", element, text)
                                logger.info("Text input via JavaScript succeeded")
                            except Exception as js_error:
                                logger.error(f"JavaScript input failed: {js_error}")
                                return {"message": f"Error: {js_error}", "success": False}
                return {"message": "Text input successful", "success": True}
            elif action == "scroll":
                from_coords = data.get("start", [])
                to_coords = data.get("end", [])
                from_x = from_coords[0]
                from_y = from_coords[1]
                to_x = to_coords[0]
                to_y = to_coords[1]
                if all([from_x, from_y, to_x, to_y]):
                    actions = ActionChains(self.driver)
                    pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
                    actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)
                    actions.w3c_actions.pointer_action.move_to_location(from_x, from_y)
                    actions.w3c_actions.pointer_action.pointer_down()
                    actions.w3c_actions.pointer_action.move_to_location(to_x, to_y)
                    actions.w3c_actions.pointer_action.release()
                    actions.perform()
                    return {"message": f"Scrolled from ({from_x}, {from_y}) to ({to_x}, {to_y})", "success": True}
                return {"message": "Error: Missing from or to coordinates"}
            elif action == "startScreenStreaming":
                if self.driver:
                    stream_args = {
                        "host": "0.0.0.0",
                        "quality": 45,
                        "bitRate": 500000,
                        "considersRotation": True
                    }
                    self.driver.execute_script("mobile: startScreenStreaming", stream_args)
                    # return {"message": f"Screen streaming started at http://121.43.49.135:5000/stream.m3u8"}
                    return {"message": f"Screen streaming started at http://121.43.49.135:8093/", "success": True}
                return {"message": "Error: Appium driver not started", "success": False}

            elif action == "stopScreenStreaming":
                if self.driver:
                    self.driver.execute_script("mobile: stopScreenStreaming")
                    return {"message": "Screen streaming stopped", "success": True}
            elif self.molecular.execute(action, data):
                return {"message": f"Molecular action '{action}' executed successfully", "success": True}
            else:
                # PS: 未识别的action要求返回成功，以便后端处理
                return {"message": f"Error: Unsupported actionType '{action}'", "success": True}
        except Exception as e:
            logger.error(f"Execution error: {str(e)}")
            return {"message": f"Error: {str(e)}", "success": False}

    def quit(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Appium driver quit")