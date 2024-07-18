import requests
from openai import OpenAI
import os

client = OpenAI(
    api_key = os.environ.get("GPT_API_US_KEY"),
    base_url = os.environ.get("GPT_API_US_URL")
)

def is_accessible_url(img_url_list):
    for img_url in img_url_list:
        if not img_url.startswith(("http://", "https://")):
            return False
        # try:
        #     response = requests.head(img_url, allow_redirects=True, timeout=5)
        #     if response.status_code != 200:
        #         return False
        # except requests.RequestException:
        #     return False
    return True

class OpenAIClass:
    def __init__(self, role = None):
        # 定义一个列表，用于存储对话的历史记录
        if role:
            self.conversation_history = [
                {'role': 'system', 'content': role}
            ]
        else:
            self.conversation_history = []

    # 定义一个函数，用于与 OpenAI 的 ChatGPT 进行对话
    def chat_with_gpt(self, user_input, img_url_list = None):
        print("prompt:" + user_input)
        # 检查img_url_list是否为字符串
        if isinstance(img_url_list, str):
            img_url_list = [img_url_list]
        # 将用户输入添加到对话历史记录中
        if img_url_list and is_accessible_url(img_url_list):
            for img_url in img_url_list:
                user_input += f" ![image]({img_url})"
            self.conversation_history.append({'role': 'user', 'content': user_input})
            # content = [{"type": "text", "text": user_input}]
            # for img_url in img_url_list:
            #     content.append({"type": "image_url","image_url": {"url": img_url}})
            # self.conversation_history.append({'role': 'user', 'content': content})
        else: 
            self.conversation_history.append({'role': 'user', 'content': user_input})

        print(self.conversation_history)
        # 调用 OpenAI 的 API 进行对话
        try:
            response = client.chat.completions.create(model="gpt-4o", messages=self.conversation_history)
            # 获取模型的回复
            model_reply = response.choices[0].message.content
            print(model_reply)
            # 将模型的回复添加到对话历史记录中
            self.conversation_history.append({'role': 'assistant', 'content': model_reply})
            return model_reply
        except Exception as e:
            print(e)
            return "系统错误，无法识别"
    

# 测试示例
if __name__ == '__main__':
    api = OpenAIClass(
            role="我会给你一组图片和一个问题，你需要描述一下你看到的画面，并且根据图片回答问题。如果没有图片，请回复没有信息，无法识别。")
    reply = api.chat_with_gpt("我的电脑在哪里", ["http://8.219.235.114:5000/files/1721282158/detected_10_laptop.png",
                                   "http://8.219.235.114:5000/files/1721282158/detected_20_laptop.png",
                                   "http://8.219.235.114:5000/files/1721282158/detected_30_laptop.png"])