import asyncio
import threading
from typing import Any

from aliyun.client import AliyunClient
from android import logger
from android.appium_action import AppiumAction

"""
Singleton decorator to ensure only one instance of InstanceManager exists.
"""
def singleton(cls):
    instances = {}
    lock = threading.Lock()

    def get_instance(*args, **kwargs):
        with lock:
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

@singleton
class InstanceManager:
    def __init__(self):
        self.aliyun_client = AliyunClient()
        self.all_clients: dict[str, str] = {}
        self.active_clients: dict[str, AppiumAction] = {}
        self.active_clients_lock = threading.Lock()
        asyncio.run(self.load_modules())

    async def load_modules(self):
        instances = await self.aliyun_client.describe_android_instances()
        for instance in instances:
            self.all_clients[instance.android_instance_id] = instance.network_interface_ip
        logger.info(f"all clients: {self.all_clients}")

    def get_all_instances(self) -> dict[Any, Any]:
        return self.all_clients

    def get_available_instances(self) -> set[str]:
        with self.active_clients_lock:
            return self.all_clients.keys() - self.active_clients.keys()

    def clear(self):
        with self.active_clients_lock:
            for appium_client in self.active_clients.values():
                appium_client.quit()
            self.active_clients.clear()