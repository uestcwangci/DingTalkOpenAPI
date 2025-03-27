import base64
import json
import mimetypes
import os
import tempfile
import time
from http.client import HTTPConnection
from typing import Literal
from urllib.parse import urlparse

from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.wait import WebDriverWait

from android import logger
from android.appium_base_action import AppiumBaseAction, AppiumDriverWrapper, session_timeout_seconds
from android.molecular import Molecular

ACCESS_TOKEN = "lGqMusyvAMqNJEJLmgZanGPAgPNdEtNBwZJAnAxndkE"  # 替换为你的DingTalk token

def upload_file_to_cdn(source: str | bytes, file_type: Literal['image', 'video'], filename: str = None) -> str:
    if isinstance(source, str):
        if not source or not os.path.exists(source):
            raise ValueError('Invalid file path')
        file_name = os.path.basename(source)
        mime_type = mimetypes.guess_type(source)[0] or ('image/png' if file_type == 'image' else 'video/mp4')
        with open(source, 'rb') as f:
            file_content = f.read()
    else:  # 处理二进制数据
        if not isinstance(source, bytes):
            raise ValueError('Source must be a file path or bytes')
        file_name = filename or f"upload_{int(time.time())}.{'png' if file_type == 'image' else 'mp4'}"
        mime_type = 'image/png' if file_type == 'image' else 'video/mp4'
        file_content = source

    if file_type not in ['image', 'video']:
        raise ValueError('Invalid file type. Must be "image" or "video"')
    if file_type == 'video':
        os.makedirs(os.path.join('logs', 'recordVideos'), exist_ok=True)

    try:
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Authorization': f'Bearer {ACCESS_TOKEN}'
        }
        body = []
        body.append(f'--{boundary}')
        body.append(f'Content-Disposition: form-data; name="file"; filename="{file_name}"')
        body.append(f'Content-Type: {mime_type}')
        body.append('')
        body_bytes = '\r\n'.join(body).encode() + b'\r\n' + file_content + f'\r\n--{boundary}--\r\n'.encode()

        url = urlparse('https://devtool.dingtalk.com/vscode/uploadFile')
        conn = HTTPConnection(url.netloc)
        conn.request('POST', url.path, body=body_bytes, headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(f'Upload failed with status code: {response.status}')
        response_data = json.loads(response.read().decode())
        if 'cdnUrl' not in response_data:
            raise ValueError('Upload response missing CDN URL')
        print(f"{'image' if file_type == 'image' else 'video'} upload success {response_data['cdnUrl']}")
        return response_data['cdnUrl']
    except Exception as error:
        print('upload fail:', str(error))
        raise


def on_timeout(device_id):
    logger.warn(f"{device_id} Timeout or session disconnect detected！")


class AppiumAction(AppiumBaseAction):
    def execute(self, action_data):
        action = action_data.get("action")
        data = action_data.get("data", {})
        logger.info(f"Executing action: #{action}# with data: {data}")

        # 检查超时事件
        if self.driver and self.driver.timeout_event.is_set():
            return {"message": "Timeout occurred previously, please start again", "success": False, "timeout": True}
        try:
            if action != "start" and self.driver is None:
                return {"message": "Error: Appium driver not started", "success": False}
            if action == "start":
                if self.driver is None:
                    self.driver = AppiumDriverWrapper('http://localhost:4723',
                                                      options=UiAutomator2Options().load_capabilities(self.desired_caps),
                                                      timeout_seconds=session_timeout_seconds,
                                                      callback=lambda:on_timeout(self.desired_caps["appium:udid"]))
                    logger.info("Appium driver initialized")
                    WebDriverWait(self.driver, timeout=30).until(
                        lambda driver: driver.current_activity == self.desired_caps["appium:appActivity"]
                    )
                    logger.info(f"Application {self.desired_caps['appium:appActivity']} is ready")
                    time.sleep(3)
                    # 传递 driver 给 Molecular
                    self.molecular = Molecular(self.udid, driver=self.driver)
                    return {"message": f"Appium driver {self.driver.capabilities['udid']} started", "success": True}
                return {"message": "Appium driver already started", "success": True}
            elif action == "done":
                self.driver.quit()
                self.driver = None
                self.molecular = None
                return {"message": "Appium driver quit", "success": True}
            elif action == "home":
                # 重新启动应用
                self.home()
                return {"message": "Successfully returned to home page", "success": True}
            elif action == "screenshot":
                # 获取 PNG 二进制数据
                screenshot_png = self.driver.get_screenshot_as_png()
                logger.info("Screenshot captured")

                try:
                    # 直接上传二进制数据
                    cdn_url = upload_file_to_cdn(screenshot_png, "image", filename="screenshot.png")
                    return {"message": "Screenshot captured", "screenshot": cdn_url, "success": True}
                except Exception as e:
                    logger.error(f"Error uploading screenshot: {str(e)}")
                    return {"message": f"Error uploading screenshot: {str(e)}", "success": False}
            elif action == "wait":
                seconds = data.get("value", 2)
                if seconds > 0:
                    time.sleep(seconds)
                    return {"message": f"Waited for {seconds} seconds", "success": True}
                return {"message": "Error: Invalid wait time", "success": False}
            elif action == "click":
                x = data.get("x")
                y = data.get("y")
                if x is None or y is None:
                    return {"message": "Error: Missing x or y coordinates", "success": False}
                self.click(x, y)
                return {"message": f"Clicked at ({x}, {y})", "success": True}
            elif action == "long_press":
                x = data.get("x")
                y = data.get("y")
                if x is None or y is None:
                    return {"message": "Error: Missing x or y coordinates", "success": False}
                self.long_press(x, y)
                return {"message": f"Long pressed at ({x}, {y})", "success": True}
            elif action == "type":
                x = data.get("x")
                y = data.get("y")
                text = data.get("value")
                if x is None or y is None or text is None:
                    return {"message": "Error: Missing x, y, or value", "success": False}
                self.type(x, y, text)
                return {"message": "Text input successful", "success": True}
            elif action == "scroll":
                from_coords = data.get("start", [])
                to_coords = data.get("end", [])
                if not from_coords or not to_coords:
                    return {"message": "Error: Missing from or to coordinates", "success": False}
                self.scroll(from_coords, to_coords)
                return {"message": "Scroll successful", "success": True}
            elif action == "startScreenStreaming":
                stream_args = {
                    "host": "0.0.0.0",
                    "quality": 45,
                    "bitRate": 500000,
                    "considersRotation": True
                }
                self.driver.execute_script("mobile: startScreenStreaming", stream_args)
                return {"message": f"Screen streaming started at http://121.43.49.135:8093/", "success": True}
            elif action == "stopScreenStreaming":
                self.driver.execute_script("mobile: stopScreenStreaming")
                return {"message": "Screen streaming stopped", "success": True}
            elif self.molecular.execute(action, data):
                return {"message": f"Molecular action '{action}' executed successfully", "success": True}
            else:
                # PS: 未识别的action要求返回成功，以便后端处理
                return {"message": f"Error: Unsupported actionType '{action}'", "success": True}
        except Exception as e:
            if self.driver.timeout_event.is_set():
                return {"message": f"Timeout occurred: {str(e)}", "success": False, "timeout": True}
            import traceback
            # Replace the selected line with this
            logger.error(f"Execution error: {str(e)}\n{traceback.format_exc()}")
            return {"message": f"Error: {str(e)}", "success": False}

    def show_toast(self, message):
        if self.molecular:
            self.molecular.show_toast(message)

    def quit(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.molecular = None
            logger.info("Appium driver quit")
        else:
            logger.info("No Appium driver to quit")