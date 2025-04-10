from aliyun.client import AliyunClient

aliyun_client = AliyunClient()

async def test_aliyun_client():
    instances = await aliyun_client.describe_android_instances()
    for instance in instances:
        instance.android_instance_id
        instance.network_interface_ip
    a = 1


async def get_ticket():
    # 获取新数据
    tickets_model = await aliyun_client.batch_get_acp_connection_ticket()
    b = 1

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_aliyun_client())
    # asyncio.run(get_ticket())