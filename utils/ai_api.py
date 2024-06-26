import json

import requests


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
        url = 'https://pre-ai-api-runtime.dingtalk.com/api/llmStream/23e9a8/cardEvaluator'
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




