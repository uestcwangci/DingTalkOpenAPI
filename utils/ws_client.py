import websocket
import json
from android.web_search import SearchHelper

# 定义 WebSocket 连接的 URL
ws_url = "wss://pre-adaptive-cloud-driver.dingtalk.com?deviceId=virtual-android"

# 定义消息处理函数
def on_message(ws, message):
    print("Received message:", message)
    # 处理接收到的消息
    handle_message(message)

def on_error(ws, error):
    print("Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("Connection closed with code:", close_status_code, "and message:", close_msg)

def on_open(ws):
    print("Connection opened")

# 处理接收到的消息的函数
def handle_message(message):
    # 根据需要解析和处理消息
    data = json.loads(message)
    print("Parsed data:", data)
    text = SearchHelper().search_for(data.get("url"))
    print("Reviews:", text)
    # 这里可以添加对下发任务的处理逻辑

# 创建 WebSocket 应用程序
ws = websocket.WebSocketApp(ws_url,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

# 在打开连接时调用的函数
ws.on_open = on_open

# 启动 WebSocket 连接
'''
ping_interval=30：每 30 秒发送一次心跳包，以保持连接活跃。
ping_timeout=10：如果在 10 秒内没有收到 pong 响应，则关闭连接。
'''
ws.run_forever(ping_interval=30, ping_timeout=10)