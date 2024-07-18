import requests
import json
from time import sleep


class DingTalkAPI:
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = None
        self.conversation_token = None

    @staticmethod
    def build_request_content(template_id: str, card_data: dict):
        return json.dumps({
            "templateId": template_id,
            "cardData": card_data
        })

    def send_post_request(self, url, headers, payload):
        response = requests.post(url, headers=headers, json=payload)

        # 检查请求是否成功
        if response.status_code == 200:
            return response.json()  # 返回响应的JSON内容
        else:
            response.raise_for_status()  # 抛出请求异常

    def get_access_token(self):
        if self.access_token:
            return self.access_token
        url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "appKey": self.app_key,
            "appSecret": self.app_secret
        }

        response = self.send_post_request(url, headers, payload)
        self.access_token = response["accessToken"]
        return self.access_token

    def send_prepare_request(self, content, open_conversation_id=None, union_id=None, content_type="ai_card"):
        url = "https://api.dingtalk.com/v1.0/aiInteraction/prepare"
        headers = {
            "x-acs-dingtalk-access-token": self.get_access_token(),
            "Content-Type": "application/json"
        }
        payload = {
            "openConversationId": open_conversation_id,
            "unionId": union_id,
            "contentType": content_type,
            "content": content
        }

        try:
            response = self.send_post_request(url, headers, payload)
            self.conversation_token = response["result"]["conversationToken"]
            return response
        except requests.exceptions.RequestException as e:
            print("Prepare request failed:", e)

    def send_update_request(self, content, content_type="ai_card"):
        url = "https://api.dingtalk.com/v1.0/aiInteraction/update"
        headers = {
            "x-acs-dingtalk-access-token": self.get_access_token(),
            "Content-Type": "application/json"
        }
        payload = {
            "conversationToken": self.conversation_token,
            "contentType": content_type,
            "content": content
        }
        return self.send_post_request(url, headers, payload)

    def send_finish_request(self):
        url = "https://api.dingtalk.com/v1.0/aiInteraction/finish"
        headers = {
            "x-acs-dingtalk-access-token": self.get_access_token(),
            "Content-Type": "application/json"
        }
        payload = {
            "conversationToken": self.conversation_token
        }
        return self.send_post_request(url, headers, payload)


# 测试示例
if __name__ == '__main__':
    # 替换你的 appKey 和 appSecret
    app_key = "dingmyqgaxb9rwvqiuh5"
    app_secret = "DshTZwI5kcRKlJNMXwoaxe1_MSkFnsKTpPnK5raWUtfu5Ut3t-ObzYy0LqudIDS2"

    # 实例化 DingTalkAPI 类
    ding_api = DingTalkAPI(app_key, app_secret)

    # 调用 prepare 函数
    try:
        prepare_response = ding_api.send_prepare_request(
            open_conversation_id="cid41Nets4tls9Y3Zqa5SKhZFPyRniSmRS3/Qk15wyZkIo=",
            content=ding_api.build_request_content(
                template_id="02815812-c30b-4164-9ca6-8b7af45c93df.schema",
                card_data={})
        )
        print("Prepare response:", prepare_response)
        print("Conversation Token:", ding_api.conversation_token)
    except requests.exceptions.RequestException as e:
        print("Prepare request failed:", e)

    sleep(3)

    # 调用 update 函数
    try:
        update_response = ding_api.send_update_request(
            content=ding_api.build_request_content(template_id="02815812-c30b-4164-9ca6-8b7af45c93df.schema",
                                                   card_data={"promot": "## 更新中...[元气满满]", "reply": "元气满满", "imgList": ["http://8.219.235.114:5000/files/1721287161/detected_60_laptop.png"]})
        )
        print("Update response:", update_response)
    except requests.exceptions.RequestException as e:
        print("Update request failed:", e)

    # sleep(5)

    # # 调用 finish 函数
    # try:
    #     finish_response = ding_api.send_finish_request()
    #     print("Finish response:", finish_response)
    # except requests.exceptions.RequestException as e:
    #     print("Finish request failed:", e)
