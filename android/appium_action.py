import tempfile

from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
import time
import base64
import logging
from typing import Literal
import os

from selenium.webdriver.support.wait import WebDriverWait

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            "appium:unicodeKeyboard": False,
            "appium:resetKeyboard": False,
            "appium:noReset": True,
            "appium:forceAppLaunch": True,
            "appium:newCommandTimeout": 0,
        }

    def execute(self, action_data):
        """根据actionType执行不同操作"""
        action_type = action_data.get("action")
        params = action_data.get("data", {})
        delay = params.get("delay", 5)  # 默认延迟5秒

        try:
            if action_type == "start":
                if self.driver is None:
                    self.driver = webdriver.Remote('http://localhost:4723',
                                                   options=UiAutomator2Options().load_capabilities(self.desired_caps))
                    logger.info("Appium driver initialized")
                    # 等待应用的主Activity加载完成
                    WebDriverWait(self.driver, timeout=30).until(
                        lambda driver: driver.current_activity == self.desired_caps["appium:appActivity"]
                    )
                    logger.info(f"Application {self.desired_caps['appium:appActivity']} is ready")
                    return {"message": "Appium driver started"}
                return {"message": "Appium driver already started"}
            elif action_type == "quit":
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                    return {"message": "Appium driver quit"}
                return {"message": "No Appium driver to quit"}

            elif action_type == "screenshot":
                if self.driver:
                    # 获取base64截图并保存为临时文件
                    screenshot_base64 = self.driver.get_screenshot_as_base64()
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                        temp_file.write(base64.b64decode(screenshot_base64))
                        temp_file_path = temp_file.name
                    try:
                        # 上传到CDN
                        cdn_url = upload_file_to_cdn(temp_file_path, "image")
                        return {"message": "Screenshot captured", "screenshot": cdn_url}
                    finally:
                        os.remove(temp_file_path)  # 清理临时文件
                return {"message": "Appium driver not started"}

            elif action_type == "click":
                x = params.get("x")
                y = params.get("y")
                if x is not None and y is not None:
                    actions = ActionChains(self.driver)
                    pointer = PointerInput(interaction.POINTER_TOUCH, "touch")
                    actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)
                    actions.w3c_actions.pointer_action.move_to_location(x, y)
                    actions.w3c_actions.pointer_action.pointer_down()
                    actions.w3c_actions.pointer_action.pause(0.1)
                    actions.w3c_actions.pointer_action.release()
                    actions.perform()
                    return {"message": f"Clicked at ({x}, {y})"}
                return {"message": "Error: Missing x or y coordinates"}

            elif action_type == "type":
                x = params.get("x")
                y = params.get("y")
                text = params.get("text")
                if x is not None and y is not None and text:
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
                    return {"message": f"Typed '{text}' at ({x}, {y})"}
                return {"message": "Error: Missing x, y, or text"}

            elif action_type == "scroll":
                from_coords = params.get("beginPoint", [])
                to_coords = params.get("endPoint", [])
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
                    return {"message": f"Scrolled from ({from_x}, {from_y}) to ({to_x}, {to_y})"}
                return {"message": "Error: Missing from or to coordinates"}
            elif action_type == "startScreenStreaming":
                if self.driver:
                    stream_args = {
                        "host": "0.0.0.0",
                        "quality": 45,
                        "bitRate": 500000,
                        "considersRotation": True
                    }
                    self.driver.execute_script("mobile: startScreenStreaming", stream_args)
                    # return {"message": f"Screen streaming started at http://121.43.49.135:5000/stream.m3u8"}
                    return {"message": f"Screen streaming started at http://121.43.49.135:8093/"}
                return {"message": "Error: Appium driver not started"}

            elif action_type == "stopScreenStreaming":
                if self.driver:
                    self.driver.execute_script("mobile: stopScreenStreaming")
                    return {"message": "Screen streaming stopped"}

            else:
                return {"message": f"Error: Unsupported actionType '{action_type}'"}
        except Exception as e:
            logger.error(f"Execution error: {str(e)}")
            return {"message": f"Error: {str(e)}"}

    def quit(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Appium driver quit")