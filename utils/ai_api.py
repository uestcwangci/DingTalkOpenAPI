import json

import requests

BASE_URL = "https://ai-api-runtime.dingtalk.com"


def send_AI_API(img_list: list):
    payload = {
        'corpId': 'ding8196cd9a2b2405da24f2f5cc6abecb85',
        'staffId': '221510',
        'data': {
            'image': json.dumps(img_list)
        }
    }
    send_request(payload)


def send_request(payload):
    try:
        # 发起POST请求并以流的方式获取响应
        url = f'{BASE_URL}/api/llmStream/23e9a8/cardEvaluator'
        headers = {
            'Content-Type': 'application/json',
        }
        response = requests.post(url=url, headers=headers, json=payload, stream=True)

        if response.status_code == 200:
            # 处理流数据
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    print(chunk)
            print('End')
        else:
            print(f'Request failed with status code {response.status_code}')
    except Exception as e:
        print(f'An error occurred: {e}')


def create_chat(input_text: str) -> str:
    """
    创建聊天会话，返回 sessionId。

    Args:
        input_text (str):  初始聊天内容

    Returns:
        str:  会话 ID (sessionId)，如果创建失败则返回空字符串
    """
    url = f"{BASE_URL}/api/createChat/750294/chat"
    payload = {
        'corpId': 'ding8196cd9a2b2405da24f2f5cc6abecb85',
        'staffId': '221510',
        "data": {"input": input_text},
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # 如果请求失败，抛出异常
        session_id = response.json().get("sessionId", "")
        return session_id
    except requests.exceptions.RequestException as e:
        print(f"创建聊天会话失败: {e}")
        return ""


def send_chat_message(session_id: str, input_text: str) -> str:
    """
    发送聊天消息，返回聊天机器人的回复。

    Args:
        session_id (str): 会话 ID
        input_text (str):  聊天内容

    Returns:
        str: 聊天机器人的回复内容，如果发送失败则返回空字符串
    """
    url = f"{BASE_URL}/api/chat/750294/chat"
    payload = {
        'corpId': 'ding8196cd9a2b2405da24f2f5cc6abecb85',
        'staffId': '221510',
        "sessionId": session_id,
        "input": input_text,
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # 如果请求失败，抛出异常
        reply = response.json().get("data", "").get("content", "")
        return reply
    except requests.exceptions.RequestException as e:
        print(f"发送聊天消息失败: {e}")
        return ""


