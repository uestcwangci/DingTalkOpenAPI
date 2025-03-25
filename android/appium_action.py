import base64
import os
import tempfile
import time
from typing import Literal

from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.support.wait import WebDriverWait

from android import logger
from android.appium_base_action import AppiumBaseAction
from android.molecular import Molecular

ACCESS_TOKEN = "lGqMusyvAMqNJEJLmgZanGPAgPNdEtNBwZJAnAxndkE"  # 替换为你的DingTalk token

def upload_file_to_cdn(file_path: str, file_type: Literal['image', 'video']) -> str:
    if not file_path or not os.path.exists(file_path):
        raise ValueError('Invalid file path')
    if file_type not in ['image', 'video']:
        raise ValueError('Invalid file type. Must be "image" or "video"')

    file_name = os.path.basename(file_path)
    import requests
    try:
        from requests_toolbelt.multipart.encoder import MultipartEncoder
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

class AppiumAction(AppiumBaseAction):
    def execute(self, action_data):
        """根据actionType执行不同操作"""
        action = action_data.get("action")
        data = action_data.get("data", {})
        logger.info(f"Executing action: {action} with data: {data}")

        try:
            if action != "start" and self.driver is None:
                return {"message": "Error: Appium driver not started", "success": False}
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
                    self.molecular = Molecular(self)
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