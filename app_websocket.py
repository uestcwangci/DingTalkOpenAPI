import asyncio
import json
import threading
import time
import traceback

import websocket
import websockets

# 假设这些是自定义模块，确保正确导入
from android import logger
from android.appium_action import AppiumAction
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=5)

WS_URL = "wss://devtool.dingtalk.com/cloud/ding8196cd9a2b2405da24f2f5cc6abecb85/221510?token=lippi-node-devops-token&platform=android"

all_clients = ["121.43.49.135:5555", "121.43.49.135:5557", "47.97.156.72:1000", "47.97.156.72:1001", "47.97.156.72:1002"]
active_clients: dict[str, AppiumAction] = {}
active_clients_lock = threading.Lock()

def get_available_devices() -> list[str]:
    with active_clients_lock:
        return list(set(all_clients) - set(active_clients.keys()))

def is_device_available(device_id: str) -> bool:
    return device_id in get_available_devices()

def process_message(message):
    """处理消息的核心逻辑，线程安全"""

    def build_response(action_type, action_uuid, ext, action=None, message="Action executed", data=None):
        """构建标准响应格式"""
        response = {
            "action": action_type,
            "actionUuid": action_uuid,
            "ext": ext,
            "data": data or {"execAction": action} if action else {},
            "message": message
        }
        return json.dumps(response)

    # 解析JSON
    try:
        action_data = json.loads(message)
        logger.debug(f"Parsed action data: {action_data}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        return build_response("error", None, None, message="Invalid JSON format")

    # 提取基本字段
    action = action_data.get("action")
    action_uuid = action_data.get("actionUuid")
    ext = action_data.get("ext")
    device_id = action_data.get("deviceId")

    # 验证必要字段
    if not action:
        logger.error("No action specified in message")
        return build_response("execFail", action_uuid, ext, action, "No action specified in message")

    if not device_id and action not in ["getAvailableDevices"]:
        logger.warning("No device_id specified in message")
        return build_response("execFail", action_uuid, ext, action, "No deviceId specified")

    # 处理不需要Appium实例的动作
    if action == "getAvailableDevices":
        return build_response("execSuccess", action_uuid, ext, action, data=get_available_devices())
    elif action == "isDeviceAvailable":
        return build_response("execSuccess", action_uuid, ext, action, data=is_device_available(device_id))

    # 处理Appium相关动作
    appium_action = _handle_appium_instance(action, device_id, active_clients)

    if appium_action is None:
        logger.error("Appium driver not started")
        return build_response("execFail", action_uuid, ext, action, "Appium driver not started")

    result = appium_action.execute(action_data)
    return _process_action_result(result, action_data, appium_action)


def _handle_appium_instance(action, device_id, active_clients):
    """处理Appium实例的创建和销毁"""
    with active_clients_lock:
        if action == "start":
            active_clients[device_id] = active_clients.get(device_id) or AppiumAction(udid=device_id)
            return active_clients[device_id]
        elif action == "done":
            return active_clients.pop(device_id, None)
        return active_clients.get(device_id)


def _process_action_result(result, action_data, appium_action):
    """处理动作执行结果"""
    action_uuid = action_data.get("actionUuid")
    ext = action_data.get("ext")
    action = action_data.get("action")

    def build_response(action_type, message="Action executed", data=None):
        response = {
            "action": action_type,
            "actionUuid": action_uuid,
            "ext": ext,
            "data": data or {"execAction": action, "url": result.get("screenshot", "")},
            "message": message
        }
        return json.dumps(response)

    if result.get('timeout', False):
        active_clients.pop(action_data.get("deviceId"))

    # desc = (action_data.get("desc") or
    #         (action_data.get("descData", {}).get("text") if action_data.get("descData") else None))
    # if desc:
    #     threading.Timer(2, lambda: appium_action.show_toast(desc)).start()

    logger.info(f"Action result: {result}")
    return build_response(
        "execSuccess" if result.get("success") else "execFail",
        result.get("message", "Action executed"),
        {"execAction": action, "url": result.get("screenshot", "")}
    )


class WebSocketClient:
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.is_running = True
        self.heartbeat_thread = None

    def send_heartbeat(self):
        """发送心跳包"""
        while self.ws and self.is_running:
            try:
                self.ws.send('{"type": "heartbeat"}')
                time.sleep(30)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break

    def on_open(self, ws):
        """连接建立时的回调"""
        logger.info("Connected to external WebSocket server")
        # 启动心跳线程
        self.heartbeat_thread = threading.Thread(target=self.send_heartbeat,daemon=True)
        self.heartbeat_thread.start()

    def on_message(self, ws, message):
        """收到消息时的回调"""
        try:
            logger.info(f"Received from server: {message}")
            response = process_message(message)
            if response:
                ws.send(response)
        except Exception as e:
            logger.error(f"Message processing error: {e}")

    def on_error(self, ws, error):
        """发生错误时的回调"""
        logger.error(f"WebSocket {ws.url} client error: {str(error)}")

    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭时的回调"""
        logger.info(f"WebSocket {ws.url} client closed: {close_status_code} - {close_msg}")
        # 停止心跳线程
        self.is_running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1)

    def cleanup(self):
        """清理资源"""
        self.is_running = False
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1)

    def run(self):
        """运行WebSocket客户端"""
        while self.is_running:
            try:
                logger.info(f"Attempting to connect to {self.url}")
                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )

                # 运行WebSocket客户端
                self.ws.run_forever(
                    ping_interval=30,  # 每30秒发送ping保持连接
                    ping_timeout=10,  # ping超时时间
                )
            except Exception as e:
                logger.error(f"WebSocket client error: {traceback.format_exc()}")
            finally:
                self.cleanup()

            if self.is_running:
                logger.info("Connection lost. Reconnecting in 30 seconds...")
                time.sleep(30)

    def stop(self):
        self.is_running = False
        self.cleanup()
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=2)


def run_websocket_client():
    """主运行函数"""
    client = WebSocketClient(WS_URL)
    try:
        client.run()
    except KeyboardInterrupt:
        logger.info("Stopping client...")
        client.stop()


# WebSocket 服务器处理函数
async def on_message_server(websocket, message):
    logger.info(f"Received from client: {message}")
    response = await asyncio.get_event_loop().run_in_executor(executor, process_message, message)
    await websocket.send(response)

async def handle_connection(websocket):
    try:
        await websocket.send("Welcome to websocket server!")
        logger.info(f"New client connection: {websocket.remote_address}")
        async for message in websocket:
            await on_message_server(websocket, message)
    except websockets.ConnectionClosed:
        logger.info(f"Client connection closed: {websocket.remote_address}")
    except Exception as e:
        logger.error(f"handle_connection error: {e}")


async def run_websocket_server():
    WS_HOST = "0.0.0.0"
    WS_PORT = 8765
    server = await websockets.serve(handle_connection, WS_HOST, WS_PORT)
    logger.info(f"WebSocket server running at ws://{WS_HOST}:{WS_PORT}")
    await server.wait_closed()


# 主程序
async def main():
    try:
        # 启动 WebSocket 客户端（在新线程中运行）
        ws_client_thread = threading.Thread(target=run_websocket_client, daemon=True)
        ws_client_thread.start()

        # 启动 WebSocket 服务器（在主事件循环中运行）
        await run_websocket_server()
    except Exception as e:
        logger.error(f"Main loop error: {traceback.format_exc()}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        with active_clients_lock:
            for appium in active_clients.values():
                appium.quit()
            active_clients.clear()
    except Exception as e:
        logger.error(f"Server startup error: {traceback.format_exc()}")