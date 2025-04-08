from alibabacloud_eds_aic20230930.models import BatchGetAcpConnectionTicketResponseBodyInstanceConnectionModels
from quart import Quart, jsonify, request
from android import logger
from aliyun.client import AliyunClient
from aiocache import Cache
from typing import Dict, Any, List

app = Quart(__name__)
aliyun_client = AliyunClient()
cache = Cache(Cache.MEMORY)

user_device_mapping = {
    "221510": "acp-cyk63ik9jk32ju330"
}


class APIResponse:
    @staticmethod
    def success(data: Any = None, message: str = "success") -> Dict:
        return {
            "code": 200,
            "message": message,
            "data": data
        }

    @staticmethod
    def error(message: str, code: int = 500, data: Any = None) -> Dict:
        return {
            "code": code,
            "message": message,
            "data": data
        }

def map_ticket_from_model(staff_id:str, tickets_model: List[BatchGetAcpConnectionTicketResponseBodyInstanceConnectionModels]):
    instance_id = user_device_mapping[staff_id]
    for model in tickets_model:
        if model.instance_id == instance_id:
            return model.ticket
    return None


@app.route('/api/getTicket', methods=['GET'])
async def get_ticket():
    try:
        # 从request的query中取staff_id
        staff_id = request.args.get('staffId')
        if not staff_id:
            response = APIResponse.error(
                message="staffId is required",
                code=400
            )
            return jsonify(response), 400

        # 尝试从缓存获取
        # cached_data = await cache.get("tickets")
        # if cached_data is not None:
        #     return jsonify(cached_data)

        # 获取新数据
        tickets_model = await aliyun_client.batch_get_acp_connection_ticket()
        if not tickets_model:
            response = APIResponse.error(
                message="No tickets found",
                code=404
            )
            return jsonify(response), 404

        ticket = map_ticket_from_model(staff_id, tickets_model)
        if ticket is None:
            response = APIResponse.error(
                message="Ticket not found",
                code=404
            )
            return jsonify(response), 404
        response = APIResponse.success(data={'ticket': ticket})
        # await cache.set("tickets", response, ttl=60)

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error in get_ticket: {e}", exc_info=True)
        return jsonify(APIResponse.error(message=str(e))), 500


@app.route('/api/clearCache', methods=['POST'])
async def clear_cache():
    """清除缓存的接口"""
    try:
        await cache.delete("tickets")
        return jsonify(APIResponse.success(message="Cache cleared"))
    except Exception as e:
        return jsonify(APIResponse.error(message=str(e)))


@app.errorhandler(404)
async def not_found(error):
    return jsonify(APIResponse.error(
        message="Resource not found",
        code=404
    )), 404


@app.errorhandler(500)
async def internal_error(error):
    return jsonify(APIResponse.error(
        message="Internal server error",
        code=500
    )), 500


# 添加健康检查接口
@app.route('/health', methods=['GET'])
async def health_check():
    return jsonify(APIResponse.success(data={"status": "healthy"}))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)