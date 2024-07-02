import asyncio
import logging
from threading import Thread

from flask import Flask, request, jsonify, render_template

from android.dt_msg_helper import MessageHelper
from android.lang_ch import LanguageHelper

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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
