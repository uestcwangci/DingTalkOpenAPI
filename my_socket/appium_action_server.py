from websocket_server import WebsocketServer
from android.appium_action import AppiumAction
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储每个客户端对应的Appium实例
clients_appium = {}


def new_client(client, server):
    """新客户端连接时调用"""
    logger.info(f"Client {client['id']} connected")
    clients_appium[client['id']] = AppiumAction()


def client_left(client, server):
    """客户端断开时调用"""
    if client is not None:
        logger.info(f"Client {client['id']} disconnected")
        if client['id'] in clients_appium:
            clients_appium[client['id']].quit()
            del clients_appium[client['id']]


def message_received(client, server, message):
    """接收到消息时调用"""
    try:
        action_data = json.loads(message)
        logger.info(f"Received action from client {client['id']}: {action_data}")

        # 获取对应的Appium实例并执行指令
        appium_handler = clients_appium.get(client['id'])
        if appium_handler:
            result = appium_handler.execute(action_data)
            # result 现在是一个字典，包含 'message' 和 'screenshot'
            server.send_message(client, json.dumps({
                "status": "success",
                "result": result["message"],
                "screenshot": result["screenshot"]  # base64编码的截图
            }))
        else:
            server.send_message(client, json.dumps({"status": "error", "result": "No Appium session"}))
    except json.JSONDecodeError:
        server.send_message(client, json.dumps({"status": "error", "result": "Invalid JSON"}))
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        server.send_message(client, json.dumps({"status": "error", "result": str(e)}))


def main():
    server = WebsocketServer(host="0.0.0.0", port=8765)
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)

    logger.info("WebSocket server started at ws://0.0.0.0:8765")
    server.run_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Server startup error: {str(e)}")