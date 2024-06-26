import json

import requests


def upload(file_name: str, file_path: str):
    # 配置上传的URL
    url = 'https://pre-open-center.alibaba-inc.com/api/jsapi/oss/uploadFile'

    # 构建文件部分
    files = {
        'file': (file_name, open(file_path, 'rb'), 'image/png')
    }

    # 配置headers
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundaryC3qRpGHnTQAV1MVS',
        'Dnt': '1',
        'Origin': 'https://open-center.alibaba-inc.com',
        'Referer': 'https://open-center.alibaba-inc.com/',
        'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }

    # 发送POST请求上传文件
    response = requests.post(url, files=files, headers=headers)

    if response.status_code == 200 and parse_response(response.text) is not None:
        # 输出响应状态码和内容
        print('Status code:', response.status_code)
        print('Response:', response.text)
        return json.loads(response.text).get('data').get('url')
    else:
        print('Upload failed')
        return None


def parse_response(response_str):
    try:
        # 尝试将字符串解析为JSON对象
        response_json = json.loads(response_str)

        # 判断 JSON 中的 'success' 字段是否为 True
        if 'success' in response_json and response_json['success'] == True:
            print("Success is True")
            # 返回数据，也可以在这里继续处理其它字段
            return response_json
        else:
            print("Success is not True or key 'success' not found")
            return None

    except json.JSONDecodeError:
        print("The response is not a valid JSON string")
        return None
