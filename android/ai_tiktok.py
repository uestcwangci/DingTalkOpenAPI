import glob
import os
import time

import test
from utils.ai_api import send_AI_API
from utils.img_compress import take_screenshot_and_compress
from utils.upload_file import upload
from .base_test import AppiumHelper


def clear_screenshots(directory='screenshots'):
    # 使用glob模块获取指定目录下的所有文件
    files = glob.glob(os.path.join(directory, '*'))

    for file in files:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except Exception as e:
            print(f"Failed to delete {file}. Reason: {e}")


class WatchTikTok():
    def __init__(self):
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

        appium_server_url = 'http://localhost:4723'
        appium_helper = AppiumHelper(appium_server_url, capabilities)
        self.appium_helper = appium_helper
        clear_screenshots()

    def test_ai_see(self) -> None:
        img_list = []
        time.sleep(5)
        # 查看5个视频，每个视频播放1s截个图
        for i in range(5):
            for j in range(5):
                # 截图
                index = f"{time.time_ns()}-{i + 1}-{j + 1}"
                file_path = f"screenshots/{index}.png"
                print(f"第{index}次截图")
                if self.appium_helper.driver.get_screenshot_as_file(file_path):
                    take_screenshot_and_compress(file_path, index)
                    print(f"第{index}次上传")
                    img_url = upload(f"{index}.png", file_path)
                    img_list.append(img_url)
            self.appium_helper.swipe()
        send_AI_API(img_list)


if __name__ == '__main__':
    test.main()
