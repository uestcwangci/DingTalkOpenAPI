# dt_msg_helper.py
import subprocess
from time import sleep

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException
from utils.openCV import yolo_detect

from utils.openai import OpenAI
from .base_test import AppiumHelper
import concurrent.futures
import time
import threading


class CameraHelper:
    def __init__(self):
        # 执行adb指令先kill掉钉钉进程
        # adb_command = ["adb", "shell", "am", "force-stop", "com.lumiunited.aqarahome"]
        # process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # # 获取命令输出和错误信息
        # process.communicate()
        #
        # if process.returncode != 0:
        #     raise RuntimeError("Aqara进程kill失败")

        # capabilities = dict(
        #     platformName='Android',
        #     automationName='uiautomator2',
        #     deviceName='Android',
        #     appPackage='com.lumiunited.aqarahome',
        #     appActivity='com.lumiunited.aqara.main.MainActivity',
        #     unicodeKeyboard=False,
        #     resetKeyboard=False,
        #     noReset=True,
        # )

        capabilities = dict(
            platformName='Android',
            automationName='uiautomator2',
            deviceName='Android',
            appPackage='com.android.documentsui',
            appActivity='.files.FilesActivity',
            unicodeKeyboard=False,
            resetKeyboard=False,
            noReset=False,
        )
        appium_server_url = 'http://8.219.235.114:4723'
        appium_helper = AppiumHelper(appium_server_url, capabilities)
        self.appium_helper = appium_helper
        self.openAI = OpenAI()

    def keep_watch(self):
        wait_for_find = self.appium_helper.wait_for_find
        wait_for_finds = self.appium_helper.wait_for_finds
        sleep(5)
        # 点击设备按钮
        wait_for_find(by=AppiumBy.ID, timeout=20, value="com.lumiunited.aqarahome:id/btn_device_list").click()
        # 找到对应的摄像头
        cameras = wait_for_finds(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/tv_cell_left")
        for camera in cameras:
            if '客厅' in camera.text:
                camera.click()
                break
        # 点击回放按钮
        control_tab = wait_for_finds(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/btn_tab")
        for tab in control_tab:
            if "回放" in tab.text:
                tab.click()
                break
        # 点击相册按钮
        wait_for_find(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/ll_item_album").click()
        sleep(7)
        # 点击推送小视频
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, value='new UiSelector().text("推送小视频")').click()
        # 找到第一个视频
        wait_for_find(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/iv_icon").click()
        # 点击全屏按钮
        wait_for_find(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/iv_fullscreen").click()
        # 找到视频区域
        video = wait_for_find(by=AppiumBy.ID, value="com.lumiunited.aqarahome:id/surface_view")
        # 开始串流
        self.appium_helper.driver.execute_script('mobile: startScreenStreaming', {
            'host': '0.0.0.0',
            'width': 1080,
            'height': 1920,
            'considerRotation': True,
            'quality': 45,
            'bitRate': 500000,
        })
        # 此时http://localhost:8093 可以访问到视频流

        loop = True
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(yolo_detect)
            while loop:
                time.sleep(50)  # 在实际应用中这个睡眠时间可以调整
                print("Checking current activity:", self.appium_helper.driver.current_activity)
                if future.done():
                    result = future.result()  # 获取结果
                    if result == "done":
                        loop = False
                        print("YOLO detection completed, exiting loop.")

    def album(self):
        wait_for_find = self.appium_helper.wait_for_find
        wait_for_finds = self.appium_helper.wait_for_finds
        sleep(3)
        # 点击视频
        wait_for_find(by=AppiumBy.ANDROID_UIAUTOMATOR, timeout=20, value='new UiSelector().text("视频")').click()

        # 开始串流
        self.appium_helper.driver.execute_script('mobile: startScreenStreaming', {
            'host': '0.0.0.0',
            'width': 1080,
            'height': 1920,
            'considerRotation': True,
            'quality': 45,
            'bitRate': 500000,
        })
        # 此时http://localhost:8093 可以访问到视频流
        # 选择视频
        wait_for_find(by=AppiumBy.ID, value="com.android.documentsui:id/thumbnail").click()

        loop = True
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(yolo_detect)
            while loop:
                time.sleep(50)  # 在实际应用中这个睡眠时间可以调整
                print("Checking current activity:", self.appium_helper.driver.current_activity)
                if future.done():
                    result = future.result()  # 获取结果
                    if result == "done":
                        loop = False
                        print("YOLO detection completed, exiting loop.")
        self.appium_helper.driver.execute_script('mobile: stopScreenStreaming')


    def stream(self):
        # 开始串流
        self.appium_helper.driver.execute_script('mobile: startScreenStreaming', {
            'host': '0.0.0.0',
            'width': 1080,
            'height': 1920,
            'considerRotation': True,
            'quality': 45,
            'bitRate': 500000,
        })

        while True:
            self.appium_helper.driver.current_activity
            sleep(50)









