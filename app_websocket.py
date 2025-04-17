import asyncio
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

import websockets

from aliyun.instance_manager import InstanceManager
from android import logger
from connection_tools.socket_manager import SocketManager, process_message

executor = ThreadPoolExecutor(max_workers=5)
WS_URL = "wss://devtool.dingtalk.com/cloud/ding8196cd9a2b2405da24f2f5cc6abecb85/221510-prod?token=lippi-node-devops-token&platform=android&envTag=20250409-pre-6q23yo"
instance_manager = InstanceManager()
socket_manager = SocketManager()



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
        logger.error(f"Client {websocket.remote_address} handle_connection error: {e}")
    finally:
        logger.info(f"Client {websocket.remote_address} disconnected")


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
        ws_client_thread = threading.Thread(target=socket_manager.connect, args=(WS_URL,), daemon=True)
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
        socket_manager.disconnect_all()
    except Exception as e:
        logger.error(f"Server startup error: {traceback.format_exc()}")