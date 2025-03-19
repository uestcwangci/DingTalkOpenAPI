import asyncio
import json
from android import logger
import os
import socket
import subprocess
import threading
import time
from threading import Thread

import requests
import websockets
from datetime import datetime
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
task_time = 600 # 60s不操作，退出appium
timer = None
# 用于客户端的事件循环
client_loop = asyncio.new_event_loop()
# 全局变量存储FFmpeg进程
ffmpeg_process = None
# 全局Appium实例（避免每次请求都创建新实例）
appium_handler = None
message_helper = None


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

    logger.info(f'Sending message to {name}: {message}')

    # 实现发送钉钉消息的逻辑
    message_helper = MessageHelper()

    thread = Thread(target=run_async, args=(message_helper.send_message, name, message))
    thread.start()

    response = {
        'success': True,
        'message': f'Message sent to {name}: {message}'
    }
    logger.info(response)
    return jsonify(response)

@app.route('/v1/actions/openapi/dingtalk/reply_message', methods=['GET'])
def reply_message():
    watcher_name = request.args.get('watcher_name')
    group = request.args.get('group')

    logger.info(f'Sending message to {group}: {watcher_name}')

    # 实现发送钉钉消息的逻辑
    message_helper = MessageHelper()

    thread = Thread(target=run_async, args=(message_helper.reply_message, group, watcher_name))
    thread.start()

    response = {
        'success': True,
        'message': f'Message sent to {group}: {watcher_name}'
    }
    logger.info(response)
    return jsonify(response)

@app.route('/v1/actions/openapi/dingtalk/summarize', methods=['POST'])
def summarize():
    body = request.json
    # 获取body中的workbookId字段
    group = body.get("group")

    logger.info(f'summarize message to {group}')

    # 实现发送钉钉消息的逻辑
    message_helper = MessageHelper()

    thread = Thread(target=run_async, args=(message_helper.summarize_message, group))
    thread.start()

    response = {
        'success': True,
        'message': f'Summarize sent to {group}'
    }
    logger.info(response)
    return jsonify(response)

@app.route('/v1/actions/openapi/dingtalk/check_read_status', methods=['GET'])
def check_read_status():
    group = request.args.get('group')
    watcher_text = request.args.get('watcher_text')

    logger.info(f'Checking read status in {group}: {watcher_text}')

    # 实现发送钉钉消息的逻辑
    message_helper = MessageHelper()

    thread = Thread(target=run_async, args=(message_helper.check_read_status, group, watcher_text))
    thread.start()

    response = {
        'success': True,
        'message': f'Checking read status in {group}: {watcher_text}'
    }
    logger.info(response)
    return jsonify(response)

@app.route('/v1/actions/openapi/dingtalk/update_status', methods=['GET'])
def update_status():
    status = request.args.get('status')
    logger.info(f'Update status to {status}')

    # 实现修改工作状态的逻辑 (忽略)

    response = {
        'success': True,
        'message': f'Work status updated to: {status}'
    }
    logger.info(response)
    return jsonify(response)

@app.route('/v1/actions/openapi/aqara/detect', methods=['GET'])
def detect_camera():
    # label = request.args.get('label')
    # original_input = request.args.get('input') # 原始输入
    # logger.info(f"Check aqara detect with label: {label}, input: {original_input}")
    # logger.info(f"Check aqara detect with label: {label}, input: {original_input}")
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
    logger.info(response)
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
        logger.info("成功获取访问令牌:")
        response_data = response.json()  # 解析 JSON 响应
        a1Notation = response_data.get("a1Notation")  # 获取 accessToken
        logger.info("a1Notation:", a1Notation)
        return jsonify({"success": True, "message": "Update sheet success", "a1Notation": a1Notation})
    else:
        logger.error("请求失败，状态码:", response.status_code)
        logger.error("响应内容:", response.text)
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
        logger.info("成功获取访问令牌:")
        response_data = response.json()  # 解析 JSON 响应
        access_token = response_data.get("accessToken")  # 获取 accessToken
        expire_in = response_data.get("expireIn")  # 获取 token 过期时间
        logger.info("Access Token:", access_token)
        logger.info("Token 过期时间（秒）:", expire_in)
        return access_token
    else:
        logger.error("请求失败，状态码:", response.status_code)
        logger.error("响应内容:", response.text)
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
                    logger.info(f"MJPEG stream ready at port {MJPEG_PORT}")
                    break
            except Exception as e:
                logger.error(f"MJPEG stream not ready: {str(e)}")
                time.sleep(1)
        else:
            logger.error("MJPEG stream not available after 10 seconds")

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
        logger.info(f"Started FFmpeg transcoding MJPEG to HLS at {hls_output}")
        time.sleep(2)
        if ffmpeg_process.poll() is not None:
            stdout, stderr = ffmpeg_process.communicate()
            logger.error(f"FFmpeg failed: {stderr.decode()}")

def stop_ffmpeg_transcoding():
    global ffmpeg_process
    if ffmpeg_process and ffmpeg_process.poll() is None:
        ffmpeg_process.terminate()
        ffmpeg_process.wait()
        logger.info("Stopped FFmpeg transcoding")
        ffmpeg_process = None

@app.route('/stream.m3u8')
def serve_hls():
    return app.send_static_file('stream.m3u8')


@app.route('/<path:filename>')
def serve_hls_segment(filename):
    return app.send_static_file(filename)

# 定时器相关函数
def quit_appium():
    global appium_handler
    if appium_handler:
        logger.info("Timeout: No action received in 60s, quitting Appium")
        appium_handler.quit()
        appium_handler = None

def reset_timer():
    global timer
    if timer:
        timer.cancel()
    timer = threading.Timer(task_time, quit_appium)
    timer.start()

# WebSocket 客户端函数（连接外部服务器）
def send_heartbeat(ws):
    while True:
        try:
            if ws.sock and ws.sock.connected:
                ws.send(json.dumps({"action": "ping"}))
                logger.debug("Sent heartbeat: ping")
            else:
                break
        except Exception as e:
            logger.error(f"Heartbeat error: {str(e)}")
            break
        time.sleep(30)

def on_open(ws):
    logger.info("Connected to external WebSocket server")
    threading.Thread(target=send_heartbeat, args=(ws,), daemon=True).start()

# 统一的异步消息处理函数
async def on_message(ws, message):
    try:
        action_data = json.loads(message)
    except json.JSONDecodeError:
        response = json.dumps({"status": "error", "result": "Invalid JSON format"})
        await ws.send(response)
        return

    try:
        logger.info(f"Received action: {action_data}")
        action = action_data.get("action")
        if not action:
            response = json.dumps({"status": "error", "result": "No action specified"})
            await ws.send(response)
            return

        global appium_handler, timer
        if action == "start" and appium_handler is None:
            appium_handler = AppiumAction()  # 假设 AppiumAction 已定义
            reset_timer()
            response = json.dumps({
                "data": {"videoUrl": "http://121.43.49.135:8093/"},
                "action": "openVideo"
            })
            await ws.send(response)
        elif action == "done":
            if timer:
                timer.cancel()
            if appium_handler:
                appium_handler.quit()
                appium_handler = None
                logger.info("Appium driver quit")
            response = json.dumps({"status": "success", "result": "Appium driver quit"})
            await ws.send(response)
            return

        if appium_handler is None:
            logger.error("Appium driver not started")
            response = json.dumps({"status": "error", "result": "Appium driver not started"})
            await ws.send(response)
            return

        reset_timer()
        result = appium_handler.execute(action_data)
        logger.info(f"Action result: {result}")
        response = json.dumps({
            "action": "execSuccess" if result.get("success") else "execFail",
            "data": {
                "execAction": action,
                "url": result.get("screenshot", "")
            },
            "message": result.get("message", "Action executed")
        })
        await ws.send(response)

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        response = json.dumps({"status": "error", "result": str(e)})
        await ws.send(response)

def on_message_client(ws, message):
    logger.info(f"Received from external server: {message}")
    # 在客户端的同步线程中安全调用异步函数
    asyncio.run_coroutine_threadsafe(on_message(ws, message), client_loop)

def on_error(ws, error):
    logger.error(f"WebSocket client error: {str(error)}")

def on_close(ws, close_status_code, close_msg):
    logger.info(f"WebSocket client closed: {close_status_code} - {close_msg}")
    global timer
    if timer:
        timer.cancel()
    if appium_handler:
        appium_handler.quit()
        logger.info("on_close Appium driver quit")

def run_websocket_client():
    # 在单独的线程中运行客户端事件循环
    def run_client_loop():
        asyncio.set_event_loop(client_loop)
        client_loop.run_forever()

    threading.Thread(target=run_client_loop, daemon=True).start()

    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message_client,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

# WebSocket 服务器处理函数
async def handle_connection(websocket):
    try:
        await websocket.send("欢迎连接到WebSocket服务器!")
        logger.info(f"新的客户端已连接: {websocket.remote_address}")
        async for message in websocket:
            await on_message(websocket, message)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[{current_time}] 收到消息: {message}")
            # 可选：添加额外的服务器响应
            # await websocket.send(f"服务器收到: {message}")
    except websockets.ConnectionClosed:
        logger.info(f"客户端断开连接: {websocket.remote_address}")
    except Exception as e:
        logger.error(f"发生错误: {e}")

# 运行 WebSocket 服务器
async def run_websocket_server():
    WS_HOST = "0.0.0.0"
    WS_PORT = 8765
    server = await websockets.serve(handle_connection, WS_HOST, WS_PORT)
    logger.info(f"WebSocket服务器启动在 ws://{WS_HOST}:{WS_PORT}")
    await server.wait_closed()

def start_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_websocket_server())

if __name__ == '__main__':
    try:
        import os

        if not os.path.exists("static"):
            os.makedirs("static")
        # 启动 WebSocket 客户端（连接外部服务器）
        ws_client_thread = threading.Thread(target=run_websocket_client, daemon=True)
        ws_client_thread.start()

        # 启动 WebSocket 服务器
        server_thread = threading.Thread(target=start_websocket_server, daemon=True)
        server_thread.start()

        # 启动 Flask HTTP 服务器
        logger.info("启动HTTP服务器...")
        app.run(host="0.0.0.0", port=HLS_PORT)
    except KeyboardInterrupt:
        logger.info("Server stopped")
        if appium_handler:
            appium_handler.quit()
    except Exception as e:
        logger.error(f"Server startup error: {str(e)}")
        if appium_handler:
            appium_handler.quit()
