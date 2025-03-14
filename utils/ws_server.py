import sys
import os
# 将项目根目录添加到sys.path中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from websocket_server import WebsocketServer
import json
from android.web_search import SearchHelper

# 定义处理新连接的函数
def new_client(client, server):
    print(f"New client connected: {client['id']}")
    server.send_message(client, "Welcome to the WebSocket server!")  # 直接发送字符串

# 定义处理接收到消息的函数
def message_received(client, server, message):
    print(f"Received message from client {client['id']}: {message}")
    server.send_message(client, f"I have receive: {message} wait...")  # 发送字符串
    # 这里可以添加对接收到消息的处理逻辑
    try:
        # 尝试将消息解析为 JSON
        data = json.loads(message)
        print("Received JSON data:", data)
        url = data.get('targetUrl')
        if url:
            result = SearchHelper().search_for(url)
            response = result
        else:
            response = {"error": " I don't understand what you are saying."}
        # 在这里可以处理 JSON 数据
        response_data = {"response": "Received JSON", "data": data}
    except json.JSONDecodeError:
        # 如果解析失败，则将其视为普通字符串
        print("Received plain string:", message)

        # 在这里可以处理普通字符串
        response = {"response": "Received string", "data": message}

    print(response)
    server.send_message(client, json.dumps(response))  # 发送字符串

# 定义处理客户端断开的函数
def client_left(client, server):
    print(f"Client disconnected: {client['id']}")

# 创建 WebSocket 服务器
port = 9001  # 选择一个端口
server = WebsocketServer(port=port, host='0.0.0.0')  # 绑定到 0.0.0.0

# 注册事件处理函数
server.set_fn_new_client(new_client)
server.set_fn_message_received(message_received)
server.set_fn_client_left(client_left)

# 启动服务器
print(f"WebSocket server is running on 0.0.0.0:{port}...")
server.run_forever()
