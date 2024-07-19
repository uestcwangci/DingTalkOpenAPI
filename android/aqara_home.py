# dt_msg_helper.py
import subprocess
from time import sleep

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException
from utils.openCV import yolo10_detect
from utils.dingtalk_api import DingTalkAPI

from utils.openai_api import Open_AI_API
from .base_test import AppiumHelper
import concurrent.futures
import time
import threading


class CameraHelper:
    def __init__(self):
        # 执行adb指令先kill掉钉钉进程
        adb_command = ["adb", "shell", "am", "force-stop", "com.lumiunited.aqarahome"]
        process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 获取命令输出和错误信息
        process.communicate()

        if process.returncode != 0:
            raise RuntimeError("Aqara进程kill失败")
        
        sleep(3)

        capabilities = dict(
            platformName='Android',
            automationName='uiautomator2',
            deviceName='Android',
            appPackage='com.lumiunited.aqarahome',
            appActivity='com.lumiunited.aqara.main.MainActivity',
            unicodeKeyboard=False,
            resetKeyboard=False,
            noReset=True,
            forceAppLaunch=True
        )

        # capabilities = dict(
        #     platformName='Android',
        #     automationName='uiautomator2',
        #     deviceName='Android',
        #     appPackage='com.android.documentsui',
        #     appActivity='.files.FilesActivity',
        #     unicodeKeyboard=False,
        #     resetKeyboard=False,
        #     noReset=False,
        # )
        appium_server_url = 'http://8.219.235.114:4723'
        appium_helper = AppiumHelper(appium_server_url, capabilities)
        self.appium_helper = appium_helper
        self.openAI = Open_AI_API(
            role="我会给你一组已经标记好的图片图片和一个问题，其中标记的内容就是我需要查看的内容，你可以忽略这个标记并且描述一下你看到的画面，并且根据图片回答问题。如果没有图片，请回复没有信息，无法识别。")
        self.dingtalk_api = DingTalkAPI("dingmyqgaxb9rwvqiuh5",
                                        "DshTZwI5kcRKlJNMXwoaxe1_MSkFnsKTpPnK5raWUtfu5Ut3t-ObzYy0LqudIDS2")

    def keep_watch(self, label:str, input:str):
        wait_for_find = self.appium_helper.wait_for_find
        wait_for_finds = self.appium_helper.wait_for_finds
        sleep(5)
        # 点击设备按钮
        wait_for_find(by=AppiumBy.ID, timeout=20, value="com.lumiunited.aqarahome:id/btn_device_list").click()
        sleep(5)
        # 找到对应的摄像头
        cameras = wait_for_finds(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/tv_cell_left")
        for camera in cameras:
            if '主卧' in camera.text:
                camera.click()
                break
        # # 点击回放按钮
        # control_tab = wait_for_finds(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/btn_tab")
        # for tab in control_tab:
        #     if "回放" in tab.text:
        #         tab.click()
        #         break
        # # 点击相册按钮
        # wait_for_find(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/ll_item_album").click()
        # sleep(7)
        # # 点击推送小视频
        # wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("推送小视频")').click()
        # # 找到第一个视频
        # wait_for_find(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/iv_icon").click()
        # 点击全屏按钮
        wait_for_find(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/iv_fullscreen").click()
        sleep(1)
        window_size = self.appium_helper.driver.get_window_size()

        # 开始串流
        self.appium_helper.driver.execute_script('mobile: startScreenStreaming', {
            'host': '0.0.0.0',
            'width': window_size.get("width"),
            'height': window_size.get("height"),
            'considerRotation': True,
            'quality': 45,
            'bitRate': 500000,
        })
        # 此时http://localhost:8093 可以访问到视频流

        loop = True
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(yolo10_detect, label, 60, 20, 1)
            while loop:
                time.sleep(20)  # 在实际应用中这个睡眠时间可以调整
                print("录屏心跳:", self.appium_helper.driver.current_activity)
                if future.done():
                    result = future.result()  # 获取结果
                    loop = False
                    print("Exiting loop.")
                    # 结束后停止串流
                    self.appium_helper.driver.execute_script('mobile: stopScreenStreaming')
                    if result:
                        self.dingtalk_api.send_prepare_request(
                            open_conversation_id="cid41Nets4tls9Y3Zqa5SKhZFPyRniSmRS3/Qk15wyZkIo=",
                            content=self.dingtalk_api.build_request_content(
                                template_id="02815812-c30b-4164-9ca6-8b7af45c93df.schema",
                                card_data={})
                        )
                        # 基础URL
                        base_url = "http://8.219.235.114:5000/files/"

                        # 使用列表推导式进行转换
                        full_urls = [base_url + filename for filename in result]
                        reply = self.openAI.chat_with_gpt(input, img_url_list=full_urls)

                        self.dingtalk_api.send_update_request(content=self.dingtalk_api.build_request_content(
                                template_id="02815812-c30b-4164-9ca6-8b7af45c93df.schema",
                                card_data={"prompt": input, "reply": reply, "imgList": full_urls}))
                        self.dingtalk_api.send_finish_request()
            self.appium_helper.driver.quit()
            print("Appium driver quit.")
             # 执行adb指令先kill掉进程
            adb_command = ["adb", "shell", "am", "force-stop", "com.lumiunited.aqarahome"]
            process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 获取命令输出和错误信息
            process.communicate()


    # def album(self):
    #     wait_for_find = self.appium_helper.wait_for_find
    #     wait_for_finds = self.appium_helper.wait_for_finds
    #     sleep(3)
    #     # 点击视频
    #     wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, timeout=20, value='new UiSelector().text("视频")').click()
    #     sleep(1)
    #     window_size = self.appium_helper.driver.get_window_size()

    #     # 开始串流
    #     self.appium_helper.driver.execute_script('mobile: startScreenStreaming', {
    #         'host': '0.0.0.0',
    #         'width': window_size.get("width"),
    #         'height': window_size.get("height"),
    #         'considerRotation': True,
    #         'quality': 45,
    #         'bitRate': 500000,
    #     })
    #     # 此时http://localhost:8093 可以访问到视频流
    #     # 选择视频
    #     wait_for_find(by=AppiumBy.ID, value="com.android.documentsui:id/thumbnail").click()

    #     loop = True
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         future = executor.submit(yolo10_detect, 10, 3)
    #         while loop:
    #             time.sleep(50)  # 在实际应用中这个睡眠时间可以调整
    #             print("Checking current activity:", self.appium_helper.driver.current_activity)
    #             if future.done():
    #                 result = future.result()  # 获取结果
    #                 if result == "done":
    #                     loop = False
    #                     print("YOLO detection completed, exiting loop.")
    #     self.appium_helper.driver.execute_script('mobile: stopScreenStreaming')

    def stream(self):
        # 开始串流
        wait_for_find = self.appium_helper.wait_for_find
        wait_for_finds = self.appium_helper.wait_for_finds
        sleep(5)
        # 点击设备按钮
        wait_for_find(by=AppiumBy.ID, timeout=20, value="com.lumiunited.aqarahome:id/btn_device_list").click()
        sleep(5)
        # 找到对应的摄像头
        cameras = wait_for_finds(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/tv_cell_left")
        for camera in cameras:
            if '主卧' in camera.text:
                camera.click()
                break
        wait_for_find(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/iv_fullscreen").click()
        sleep(1)
        window_size = self.appium_helper.driver.get_window_size()
        # width, height = self.appium_helper.driver.get_window_size().values()
        # print(window_size)
        # print(width)
        # print(height)
        # # self.appium_helper.driver.swipe(start_x=int(window_size.get("width")), start_y=int(window_size.get("height")), end_x=int(window_size.get("width")) + 100, end_y=int(window_size.get("height")), duration=500)
        # for i in range(5):
        #     self.appium_helper.driver.swipe(int(width/3), int(height/2), int(width*2/3), int(height/2))
        #     print("滑动from", int(width/3), int(height/2), "to", int(width*2/3), int(height/2))
        #     sleep(2)
        # 开始串流
        self.appium_helper.driver.execute_script('mobile: startScreenStreaming', {
            'host': '0.0.0.0',
            'width': window_size.get("width"),
            'height': window_size.get("height"),
            'considerRotation': True,
            'quality': 45,
            'bitRate': 500000,
        })
        while True:
            sleep(30)
            print("录屏心跳:", self.appium_helper.driver.current_activity)
        