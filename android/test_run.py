import sys
import os

# 将项目根目录添加到sys.path中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from android.dt_msg_helper import MessageHelper
from android.aqara_home import CameraHelper
from utils.openai_api import Open_AI_API

# message_sender.reply_message("Virtual-Runtime", "")
# message_sender.check_read_status("Virtual-Runtime", "八嘎呀路")
#
# lang_helper = LanguageHelper()
# lang_helper.change_to_ch()

camera_helper = CameraHelper()
# camera_helper.keep_watch("电脑", "帮我看看电脑在哪里")
camera_helper.stream()


# message_sender = MessageHelper()
# message_sender.send_message("零封🌚", "检测到宠物")

# openai = OpenAIClass()
# openai.chat_with_gpt("我的猫是否在床上", "http://8.219.235.114:5000/files/pet_detected_57_1720782748.png")
