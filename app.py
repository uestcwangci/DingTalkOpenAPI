import asyncio
import json
import logging
import os
import socket
import subprocess
import threading
import time
from threading import Thread

import requests
from flask import Flask, request, jsonify, render_template, send_from_directory, abort, url_for
from werkzeug.utils import safe_join

from android.dt_msg_helper import MessageHelper
from android.lang_ch import LanguageHelper
# from android.aqara_home import CameraHelper
from android.appium_action import AppiumAction
import websocket
import sys

app = Flask(__name__, static_folder="static")
WS_URL = "wss://devtool.dingtalk.com/cloud/ding8196cd9a2b2405da24f2f5cc6abecb85/221510?token=lippi-node-devops-token&platform=android"
MJPEG_PORT = 8093  # Appium MJPEG流端口
HLS_PORT = 5000    # HLS流服务端口
PUBLIC_IP = "121.43.49.135"  # 公网IP地址
# 全局变量存储FFmpeg进程
ffmpeg_process = None
# 全局Appium实例（避免每次请求都创建新实例）
appium_handler = None
message_helper = None
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s %(levelname)s %(message)s',
                   handlers=[
                       logging.FileHandler('trace.log', encoding='utf-8'),
                       logging.StreamHandler(sys.stdout)
                   ])


def run_async(func, *args, **kwargs):
    """
    异步运行函数

    Args:
      func: 要异步运行的函数
      *args: 函数的位置参数
      **kwargs: 函数的关键字参数
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if asyncio.iscoroutinefunction(func):
            loop.run_until_complete(func(*args, **kwargs))
        else:
            loop.run_until_complete(loop.run_in_executor(None, func, *args, **kwargs))
    finally:
        loop.close()

def change_language_async():
    # 创建一个新的事件循环，因为在新的线程中无法使用默认循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # 在新的事件循环中运行 change_to_ch()
        loop.run_until_complete(LanguageHelper().change_to_ch())
    finally:
        loop.close()



@app.route('/')
def hello_world():
    return 'hello world'

@app.route("/index")
def index():
    return render_template('index.html', name="Flask")

screenshot_directory = '/home/ecs-user/dev/py/DingTalkOpenAPI/screenshots'

def list_files(directory, base_url):
    file_tree = '<ul>'
    for entry in os.listdir(directory):
        full_path = os.path.join(directory, entry)
        if os.path.isdir(full_path):
            file_tree += f'<li><strong><a href="{base_url}/{entry}">{entry}/</a></strong></li>'
        else:
            file_tree += f'<li><a href="{base_url}/{entry}">{entry}</a></li>'
    file_tree += '</ul>'
    return file_tree

@app.route('/files/<path:filename>')
def serve_file(filename):
    full_path = safe_join(screenshot_directory, filename)
    if not os.path.isfile(full_path):
        abort(404)
    directory = os.path.dirname(filename)
    return send_from_directory(safe_join(screenshot_directory, directory), os.path.basename(filename))

@app.route('/screenshot', defaults={'path': ''})
@app.route('/screenshot/<path:path>')
def screenshot(path):
    full_directory = safe_join(screenshot_directory, path)
    if not os.path.exists(full_directory):
        abort(404)
    if os.path.isfile(full_directory):
        return send_from_directory(screenshot_directory, path)
    base_url = url_for('screenshot', path=path)
    files_list = list_files(full_directory, base_url)
    return f'<h1>Directory listing for {path if path else "root"}</h1>{files_list}'

# @app.route('/files/<path:filename>')
# def serve_file(filename):
#     full_path = safe_join(screenshot_directory, filename)
#     if not os.path.isfile(full_path):
#         abort(404)
#     return send_from_directory(screenshot_directory, filename)

# @app.route('/screenshot')
# def screenshot():
#     files_list = list_files(screenshot_directory)
#     return f'<h1>File List</h1><ul>{files_list}</ul>'

# def list_files(base_path):
#     file_tree = ""
#     for dirpath, dirnames, filenames in os.walk(base_path):
#         relative_dir = os.path.relpath(dirpath, base_path)
        
#         if relative_dir == ".":
#             relative_dir = ""
        
#         file_tree += f'<li><strong>{relative_dir}</strong><ul>'
        
#         for dirname in dirnames:
#             file_tree += f'<li>{dirname}/</li>'
        
#         for filename in filenames:
#             full_path = os.path.join(relative_dir, filename)
#             file_tree += f'<li><a href="/files/{full_path}">{filename}</a></li>'
            
#         file_tree += '</ul></li>'
        
#     return file_tree

@app.route('/v1/actions/openapi/dingtalk/send_message', methods=['GET'])
def send_message():
    name = request.args.get('name')
    message = request.args.get('message')

    app.logger.info(f'Sending message to {name}: {message}')

    # 实现发送钉钉消息的逻辑
    message_helper = MessageHelper()

    thread = Thread(target=run_async, args=(message_helper.send_message, name, message))
    thread.start()

    response = {
        'success': True,
        'message': f'Message sent to {name}: {message}'
    }
    app.logger.info(response)
    return jsonify(response)

@app.route('/v1/actions/openapi/dingtalk/reply_message', methods=['GET'])
def reply_message():
    watcher_name = request.args.get('watcher_name')
    group = request.args.get('group')

    app.logger.info(f'Sending message to {group}: {watcher_name}')

    # 实现发送钉钉消息的逻辑
    message_helper = MessageHelper()

    thread = Thread(target=run_async, args=(message_helper.reply_message, group, watcher_name))
    thread.start()

    response = {
        'success': True,
        'message': f'Message sent to {group}: {watcher_name}'
    }
    app.logger.info(response)
    return jsonify(response)

@app.route('/v1/actions/openapi/dingtalk/summarize', methods=['POST'])
def summarize():
    body = request.json
    # 获取body中的workbookId字段
    group = body.get("group")

    app.logger.info(f'summarize message to {group}')

    # 实现发送钉钉消息的逻辑
    message_helper = MessageHelper()

    thread = Thread(target=run_async, args=(message_helper.summarize_message, group))
    thread.start()

    response = {
        'success': True,
        'message': f'Summarize sent to {group}'
    }
    app.logger.info(response)
    return jsonify(response)

@app.route('/v1/actions/openapi/dingtalk/check_read_status', methods=['GET'])
def check_read_status():
    group = request.args.get('group')
    watcher_text = request.args.get('watcher_text')

    app.logger.info(f'Checking read status in {group}: {watcher_text}')

    # 实现发送钉钉消息的逻辑
    message_helper = MessageHelper()

    thread = Thread(target=run_async, args=(message_helper.check_read_status, group, watcher_text))
    thread.start()

    response = {
        'success': True,
        'message': f'Checking read status in {group}: {watcher_text}'
    }
    app.logger.info(response)
    return jsonify(response)

@app.route('/v1/actions/openapi/dingtalk/update_status', methods=['GET'])
def update_status():
    status = request.args.get('status')
    app.logger.info(f'Update status to {status}')

    # 实现修改工作状态的逻辑 (忽略)

    response = {
        'success': True,
        'message': f'Work status updated to: {status}'
    }
    app.logger.info(response)
    return jsonify(response)

@app.route('/v1/actions/openapi/aqara/detect', methods=['GET'])
def detect_camera():
    # label = request.args.get('label')
    # original_input = request.args.get('input') # 原始输入
    # app.logger.info(f"Check aqara detect with label: {label}, input: {original_input}")
    # print(f"Check aqara detect with label: {label}, input: {original_input}")
    #
    # # 实现发送钉钉消息的逻辑
    # camera_helper = CameraHelper()
    #
    # thread = Thread(target=run_async, args=(camera_helper.keep_watch, label, original_input)) # 中的逗号是必须的，以确保 args 是一个元组，当只传递一个元素时
    # thread.start()

    response = {
        'success': True,
        'message': "Start watching"
    }
    app.logger.info(response)
    return jsonify(response)

@app.route('/v1/actions/openapi/dingtalk/updateSheet', methods=['POST'])
def update_sheet():
    access_token = get_dingtalk_access_token()
    if access_token is None:
        return jsonify({"success": False, "message": "Failed to get access"})
    # 获取请求body
    body = request.json
    # 获取body中的workbookId字段
    workbook_id = body.get("workbookId")
    sheet_name = body.get("sheetName")
    ranges = body.get("ranges")
    operator_id = body.get("operatorId")
    values = body.get("values")

    url = f"https://api.dingtalk.com/v1.0/doc/workbooks/{workbook_id}/sheets/{sheet_name}/ranges/{ranges}?operatorId={operator_id}"

    headers = {
        "x-acs-dingtalk-access-token": access_token,
        "Content-Type": "application/json"
    }

    payload = {
        "values": values
    }

    response = requests.put(url, headers=headers, json=payload)

    # 打印响应内容
    if response.status_code == 200:
        print("成功获取访问令牌:")
        response_data = response.json()  # 解析 JSON 响应
        a1Notation = response_data.get("a1Notation")  # 获取 accessToken
        print("a1Notation:", a1Notation)
        return jsonify({"success": True, "message": "Update sheet success", "a1Notation": a1Notation})
    else:
        print("请求失败，状态码:", response.status_code)
        print("响应内容:", response.text)
        return jsonify({"success": False, "message": "Update sheet failed"})


def get_dingtalk_access_token():
    # 定义请求的 URL
    url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"

    # 定义请求体
    payload = {
        "appKey": "ding3fsubpczmmihoerg",
        "appSecret": "7C9x2xqrMnOr_bzOC3w6kpE1zj1DkgPHiDnc-9CMewPgOw6yXtBvNXo8_UKuK57N"
    }

    # 发送 POST 请求
    response = requests.post(url, json=payload)

    # 打印响应内容
    if response.status_code == 200:
        print("成功获取访问令牌:")
        response_data = response.json()  # 解析 JSON 响应
        access_token = response_data.get("accessToken")  # 获取 accessToken
        expire_in = response_data.get("expireIn")  # 获取 token 过期时间
        print("Access Token:", access_token)
        print("Token 过期时间（秒）:", expire_in)
        return access_token
    else:
        print("请求失败，状态码:", response.status_code)
        print("响应内容:", response.text)
        return None

def start_ffmpeg_transcoding():
    global ffmpeg_process
    hls_output = "static/stream.m3u8"
    if ffmpeg_process is None or ffmpeg_process.poll() is not None:
        mjpeg_url = f"http://localhost:{MJPEG_PORT}"
        # 等待MJPEG流就绪
        import requests
        for _ in range(10):  # 最多等待10秒
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', MJPEG_PORT))
                sock.close()

                if result == 0:
                    app.logger.info(f"MJPEG stream ready at port {MJPEG_PORT}")
                    break
            except Exception as e:
                app.logger.error(f"MJPEG stream not ready: {str(e)}")
                time.sleep(1)
        else:
            app.logger.error("MJPEG stream not available after 10 seconds")

        cmd = [
            "ffmpeg",
            "-i", mjpeg_url,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-f", "hls",
            "-hls_time", "2",
            "-hls_list_size", "10",
            "-hls_wrap", "0",
            hls_output
        ]
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        app.logger.info(f"Started FFmpeg transcoding MJPEG to HLS at {hls_output}")
        time.sleep(2)
        if ffmpeg_process.poll() is not None:
            stdout, stderr = ffmpeg_process.communicate()
            app.logger.error(f"FFmpeg failed: {stderr.decode()}")

def stop_ffmpeg_transcoding():
    global ffmpeg_process
    if ffmpeg_process and ffmpeg_process.poll() is None:
        ffmpeg_process.terminate()
        ffmpeg_process.wait()
        app.logger.info("Stopped FFmpeg transcoding")
        ffmpeg_process = None


# WebSocket函数
def send_heartbeat(ws):
    while True:
        try:
            if ws.sock and ws.sock.connected:
                ws.send(json.dumps({"actionType": "ping"}))
                app.logger.info("Sent heartbeat: ping")
            else:
                break
        except Exception as e:
            app.logger.error(f"Heartbeat error: {str(e)}")
            break
        time.sleep(30)


def on_open(ws):
    app.logger.info("Connected to DingTalk WebSocket server")
    global appium_handler
    if appium_handler is None:
        appium_handler = AppiumAction()
    threading.Thread(target=send_heartbeat, args=(ws,), daemon=True).start()


def on_message(ws, message):
    try:
        action_data = json.loads(message)
        app.logger.info(f"Received action: {action_data}")
        action_type = action_data.get("action")

        global appium_handler
        if appium_handler:
            result = appium_handler.execute(action_data)
            if action_type == "start":
                ws.send(json.dumps({
                    "data": {
                        "videoUrl": "http://121.43.49.135:8093/"
                    },
                    "action": "openVideo"
                }))
            elif action_type == "startScreenStreaming":
                # start_ffmpeg_transcoding()
                # result["message"] = f"Screen streaming started at http://{PUBLIC_IP}:{HLS_PORT}/stream.m3u8"
                result["message"] = f"Screen streaming started at http://121.43.49.135:8093/"
            elif action_type == "stopScreenStreaming":
                stop_ffmpeg_transcoding()
            ws.send(json.dumps({
                "action": "execSuccess",
                "data": {
                    "execAction": action_type,
                    "url": result.get("screenshot", "")  # 默认返回截图
                },
                "message": result.get("message", "Action executed")
            }))

    except Exception as e:
        app.logger.error(f"Error processing message: {str(e)}")
        ws.send(json.dumps({"status": "error", "result": str(e)}))


def on_error(ws, error):
    app.logger.error(f"WebSocket error: {str(error)}")


def on_close(ws, close_status_code, close_msg):
    app.logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
    stop_ffmpeg_transcoding()


def run_websocket():
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()


# HTTP接口
@app.route('/v1/actions/execute', methods=['POST'])
def execute_action():
    global appium_handler
    try:
        body = request.get_json()
        if not body:
            return jsonify({"status": "error", "result": "No JSON data provided"}), 400

        app.logger.info(f"HTTP request: {body}")
        action = body.get("action")  # 改为actionType与WebSocket一致

        # if action == "start" and appium_handler is None:
        if action == "start":
            appium_handler = AppiumAction()
            return jsonify({
                "data": {
                    "videoUrl": "http://121.43.49.135:8093/"
                },
                "action": "openVideo"
            })
        elif action == "quit" and appium_handler:
            appium_handler.quit()
            appium_handler = None
            return jsonify({"status": "success", "result": "Appium driver quit"}), 200

        if appium_handler is None:
            return jsonify({"status": "error", "result": "Appium driver not started"}), 400

        result = appium_handler.execute(body)

        # 处理屏幕流转码
        if action == "startScreenStreaming":
            # start_ffmpeg_transcoding()
            hls_url = f"http://{PUBLIC_IP}:{HLS_PORT}/stream.m3u8"
            return jsonify({
                "data": {
                    "execAction": "startScreenStreaming",
                    "url": "http://121.43.49.135:8093/"
                },
                "action": "execSuccess"
            }), 200
        elif action == "stopScreenStreaming":
            stop_ffmpeg_transcoding()

        return jsonify({
            "data": {
                "execAction": action,
                "url": result.get("screenshot", "")  # 默认返回截图
            },
            "message": result.get("message", "Action executed"),
            "action": "execSuccess"
        }), 200
    except Exception as e:
        app.logger.error(f"HTTP error: {str(e)}")
        return jsonify({"status": "error", "result": str(e)}), 500


@app.route('/stream.m3u8')
def serve_hls():
    return app.send_static_file('stream.m3u8')


@app.route('/<path:filename>')
def serve_hls_segment(filename):
    return app.send_static_file(filename)

if __name__ == '__main__':
    try:
        import os

        if not os.path.exists("static"):
            os.makedirs("static")
        ws_thread = threading.Thread(target=run_websocket, daemon=True)
        ws_thread.start()
        app.run(host="0.0.0.0", port=HLS_PORT, debug=True)
    except KeyboardInterrupt:
        if appium_handler:
            appium_handler.quit()
        app.logger.info("Server stopped")
    except Exception as e:
        app.logger.error(f"Server startup error: {str(e)}")
        if appium_handler:
            appium_handler.quit()
