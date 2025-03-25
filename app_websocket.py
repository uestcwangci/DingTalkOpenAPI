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

WS_URL = "wss://devtool.dingtalk.com/cloud/ding8196cd9a2b2405da24f2f5cc6abecb85/221510?token=lippi-node-devops-token&platform=android"

all_clients = ["121.43.49.135:5555", "47.96.90.145:1001"]
active_clients: dict[str, AppiumAction] = {}

def get_available_clients() -> list[str]:
    return list(set(all_clients) - set(active_clients.keys()))

def is_client_available(udid: str) -> bool:
    return udid in get_available_clients()

# WebSocket 客户端的心跳机制
def send_heartbeat(ws):
    while True:
        try:
            if ws.sock and ws.sock.connected:
                ws.send(json.dumps({"action": "ping"}))
                logger.debug("Sent heartbeat: ping")
            else:
                logger.warning("WebSocket disconnected, stopping heartbeat")
                break
        except Exception as e:
            logger.error(f"Heartbeat error: {str(e)}")
            break
        time.sleep(30)


def on_open(ws):
    logger.info("Connected to external WebSocket server")
    threading.Thread(target=send_heartbeat, args=(ws,), daemon=True).start()


def process_message(message):
    """处理消息的核心逻辑，线程安全"""
    logger.info(f"Processing message: {message}")
    try:
        action_data = json.loads(message)
        logger.debug(f"Parsed action data: {action_data}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        return json.dumps({"status": "error", "result": "Invalid JSON format"})

    try:
        action = action_data.get("action")
        if not action:
            logger.error("No action specified in message")
            return json.dumps({"action": "execFail","data": {"execAction": action,},"message": "No action specified in message"})

        udid = action_data.get("data").get("udid")
        if not udid:
            logger.warn("No udid specified in message")
            return json.dumps({"action": "execFail", "data": {"execAction": action}, "message": "No udid specified"})

        if action == "getAvailableClients":
            return json.dumps({"action": "execSuccess", "data": get_available_clients()})
        elif action == "isClientAvailable":
            return json.dumps({"action": "execSuccess", "data": is_client_available(udid)})

        appium_action: AppiumAction
        if action == "start":
            # 如果不存在则创建新实例，否则使用现有实例
            active_clients[udid] = active_clients.get(udid) or AppiumAction(udid)
            appium_action = active_clients[udid]
        elif action == "done":
            # 如果存在则移除并返回，否则返回 None
            appium_action = active_clients.pop(udid, None)
        else:
            appium_action = active_clients.get(udid)

        if appium_action is None:
            logger.error("Appium driver not started")
            return json.dumps(
                {"action": "execFail", "data": {"execAction": action}, "message": "Appium driver not started"})

        result = appium_action.execute(action_data)

        desc = action_data.get("desc")
        if desc:
            appium_action.show_toast(desc)

        logger.info(f"Action result: {result}")
        return json.dumps({
            "action": "execSuccess" if result.get("success") else "execFail",
            "data": {
                "execAction": action,
                "url": result.get("screenshot", "")
            },
            "message": result.get("message", "Action executed")
        })
    except Exception as e:
        logger.error(f"Error processing message: {traceback.format_exc()}")
        return json.dumps({"status": "error", "result": str(e)})


def on_message_client(ws, message):
    logger.info(f"Received from server: {message}")
    response = process_message(message)
    ws.send(response)


def on_error(ws, error):
    logger.error(f"WebSocket client error: {str(error)}")


def on_close(ws, close_status_code, close_msg):
    logger.info(f"WebSocket client closed: {close_status_code} - {close_msg}")


def run_websocket_client():
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message_client,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()


# WebSocket 服务器处理函数
async def on_message_server(websocket, message):
    logger.info(f"Received from client: {message}")
    # 将阻塞操作移到线程中，避免阻塞事件循环
    response = await asyncio.to_thread(process_message, message)
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
        logger.error(f"handle_connection error: {traceback.format_exc()}")


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
    except Exception as e:
        logger.error(f"Server startup error: {traceback.format_exc()}")