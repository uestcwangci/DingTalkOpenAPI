import asyncio
import json
import threading
import time
import traceback

import websocket
import websockets

from android import logger
from android.appium_action import AppiumAction
from aliyun.instance_manager import InstanceManager
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=5)

WS_URL = "wss://devtool.dingtalk.com/cloud/ding8196cd9a2b2405da24f2f5cc6abecb85/221510-prod?token=lippi-node-devops-token&platform=android&envTag=20250409-pre-6q23yo"
instance_manager = InstanceManager()

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

    # 处理Appium相关动作
    appium_action = _handle_appium_instance(action, device_id, instance_manager.active_clients)

    if appium_action is None:
        logger.error("Appium driver not started")
        return build_response("execFail", action_uuid, ext, action, "Appium driver not started")

    result = appium_action.execute(action_data)
    return _process_action_result(result, action_data, appium_action)


def _handle_appium_instance(action, device_id, active_clients):
    """处理Appium实例的创建和销毁"""
    with instance_manager.active_clients_lock:
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
        instance_manager.active_clients.pop(action_data.get("deviceId"))

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
    def __init__(self, url, max_retries=None, initial_retry_delay=5):
        self.url = url
        self.ws = None
        self.is_running = True
        self.heartbeat_thread = None
        self.max_retries = max_retries  # None表示无限重试
        self.retry_delay = initial_retry_delay  # 初始重试延迟（秒）
        self.retry_count = 0
        self.reconnect_event = threading.Event()

    def send_heartbeat(self):
        """发送心跳包"""
        while self.ws and self.is_running and not self.reconnect_event.is_set():
            try:
                self.ws.send('{"type": "heartbeat"}')
                time.sleep(30)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                self.reconnect_event.set()  # 通知主线程需要重连
                break

    def on_open(self, ws):
        """连接建立时的回调"""
        logger.info("Connected to external WebSocket server")
        self.retry_count = 0  # 连接成功，重置重试计数
        self.retry_delay = 5  # 重置重试延迟
        self.reconnect_event.clear()

        # 启动心跳线程
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            # 如果之前的线程还在运行，先确保它结束
            self.heartbeat_thread.join(timeout=1)

        self.heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
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
        logger.error(f"WebSocket client error: {str(error)}")
        self.reconnect_event.set()  # 标记需要重连

    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭时的回调"""
        logger.info(f"WebSocket client closed: {close_status_code} - {close_msg}")
        self.reconnect_event.set()  # 标记需要重连

    def cleanup(self):
        """清理资源"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None

    def run(self):
        """运行WebSocket客户端"""
        while self.is_running:
            try:
                if self.max_retries and self.retry_count >= self.max_retries:
                    logger.info(f"Reached the maximum number of retries {self.max_retries}, stopped reconnecting")
                    break

                logger.info(f"Try connecting to {self.url}")
                self.reconnect_event.clear()  # 连接前清除重连事件标志
                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )

                # 运行WebSocket客户端
                self.ws.run_forever(
                    ping_interval=0) # 禁用ping/pong机制，使用自定义心跳

                # 如果连接断开，检查是否应该重新连接
                if not self.is_running:
                    break

                self.retry_count += 1
                retry_time = min(self.retry_delay * (2 ** min(self.retry_count, 5)), 300)  # 指数退避，最大5分钟
                logger.info(f"Disconnected, trying to reconnect {self.retry_count} times after {retry_time} seconds...")

                # 清理旧连接资源
                self.cleanup()

                # 关键修改：直接使用 sleep 等待重连时间，不使用 event
                time.sleep(retry_time)

            except Exception as e:
                logger.error(f"WebSocket client error: {e}")
                self.retry_count += 1
                self.cleanup()
                time.sleep(min(self.retry_delay * (2 ** min(self.retry_count, 5)), 300))

    def stop(self):
        """停止客户端"""
        self.is_running = False
        self.reconnect_event.set()  # 唤醒任何等待的线程
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
        with instance_manager.active_clients_lock:
            for appium in instance_manager.active_clients.values():
                appium.quit()
            instance_manager.active_clients.clear()
    except Exception as e:
        logger.error(f"Server startup error: {traceback.format_exc()}")
