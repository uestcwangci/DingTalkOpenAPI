from flask import Flask, request, jsonify, render_template
import logging
app = Flask(__name__)

logging.basicConfig(filename='trace.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

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

    # 实现发送钉钉消息的逻辑 (忽略)

    response = {
        'success': True,
        'message': f'Message sent to {name}: {message}'
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
    app.run(host="0.0.0.0", port=5000)
