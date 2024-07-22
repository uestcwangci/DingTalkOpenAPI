import asyncio
import logging
import os
from threading import Thread

from flask import Flask, request, jsonify, render_template, send_from_directory, abort, url_for
from werkzeug.utils import safe_join

from android.dt_msg_helper import MessageHelper
from android.lang_ch import LanguageHelper
from android.aqara_home import CameraHelper

app = Flask(__name__)

logging.basicConfig(filename='trace.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')


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
    label = request.args.get('label')
    original_input = request.args.get('input') # 原始输入
    app.logger.info(f"Check aqara detect with label: {label}, input: {original_input}")
    print(f"Check aqara detect with label: {label}, input: {original_input}")

    # 实现发送钉钉消息的逻辑
    camera_helper = CameraHelper()

    thread = Thread(target=run_async, args=(camera_helper.keep_watch, label, original_input)) # 中的逗号是必须的，以确保 args 是一个元组，当只传递一个元素时
    thread.start()

    response = {
        'success': True,
        'message': "Start watching"
    }
    app.logger.info(response)
    return jsonify(response)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
