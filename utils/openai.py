from openai import OpenAI

client = OpenAI()

# 设置代理地址
proxy_url = 'https://www.gptapi.us'

# 使用你的 OpenAI API 密钥

# 设置代理


class OpenAI:
    def __init__(self):
        # 定义一个列表，用于存储对话的历史记录
        self.conversation_history = [
            {'role': 'system', 'content': '''
            你是一个幽默风趣的智能对话助手，你的任务是与我进行自然、流畅的对话。无论话题严肃或轻松，你都要积极回应，并根据情境提供相关信息。当遇到可能让人感到尴尬或棘手的话题时，你应巧妙地运用机智和幽默来化解，使得对话始终保持愉快的氛围。

        示例1：
        用户：最近我感觉压力好大，不知道怎么办。
        优化后的回复：哎呀，听起来你像是背负了一座喜马拉雅山啊！试试深呼吸，或者找点你喜欢的事情做，比如看个喜剧片，让心情放松一下。如果压力山大到需要搬运工，我随时准备化身“笑声小能手”帮你卸货哦！

        示例2：
        用户：我对量子物理一窍不通，你能解释一下吗？
        优化后的回复：当然可以！想象一下，你在派对上跳舞，你的每一个动作（状态）都同时存在，直到有人（观察者）看你跳舞，你才确定了舞步。这就是量子物理中的“叠加原理”。不过别担心，你不需要在现实生活中同时跳恰恰和探戈，除非你想成为派对焦点！'''}
        ]
    # 定义一个函数，用于与 OpenAI 的 ChatGPT 进行对话
    def chat_with_gpt(self, user_input):
        # 将用户输入添加到对话历史记录中
        self.conversation_history.append({'role': 'user', 'content': user_input})

        # 调用 OpenAI 的 API 进行对话
        response = client.chat.completions.create(model="gpt-3.5-turbo-1106",
        messages=self.conversation_history)

        # 获取模型的回复
        model_reply = response.choices[0].message.content

        # 将模型的回复添加到对话历史记录中
        self.conversation_history.append({'role': 'assistant', 'content': model_reply})

        return model_reply

