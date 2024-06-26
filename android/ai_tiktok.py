import time
import unittest
import os
import glob

from android.base_test import BaseTest
from utils.upload_file import upload
from utils.ai_api import send_AI_API
from utils.img_compress import take_screenshot_and_compress


def clear_screenshots(directory='screen_shot'):
    # 使用glob模块获取指定目录下的所有文件
    files = glob.glob(os.path.join(directory, '*'))

    for file in files:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except Exception as e:
            print(f"Failed to delete {file}. Reason: {e}")


class TestAppium(BaseTest):
    def __init__(self, methodName="runTest"):
        capabilities = dict(
            platformName='Android',
            automationName='uiautomator2',
            deviceName='Android',
            appPackage='com.ss.android.ugc.aweme',
            appActivity='.splash.SplashActivity',
            noReset=True,
            # language='en',
            # locale='US'
        )

        # appium_server_url = 'http://localhost:4723'
        appium_server_url = 'http://147.139.208.135:4723'
        super().__init__(methodName, appium_server_url=appium_server_url, capabilities=capabilities)

    def setUp(self) -> None:
        clear_screenshots()
        super().setUp()

    def test_ai_see(self) -> None:
        img_list = []
        time.sleep(5)
        # 查看5个视频，每个视频播放1s截个图
        for i in range(5):
            for j in range(5):
                # 截图
                index = f"{time.time_ns()}-{i + 1}-{j + 1}"
                file_path = f"screen_shot/{index}.png"
                print(f"第{index}次截图")
                if self.driver.get_screenshot_as_file(file_path):
                    take_screenshot_and_compress(file_path, index)
                    print(f"第{index}次上传")
                    img_url = upload(f"{index}.png", file_path)
                    img_list.append(img_url)
            self.swipe()
        send_AI_API(img_list)


if __name__ == '__main__':
    unittest.main()
