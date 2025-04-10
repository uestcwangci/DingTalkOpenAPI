from android import logger
from connection_tools.manus_http_server import http_server
from aliyun.instance_manager import InstanceManager

instance_manager = InstanceManager()
if __name__ == "__main__":
    try:
        http_server.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        http_server.shutdown()
        instance_manager.clear()
    except Exception as e:
        logger.error(f"Server startup error: {e}")