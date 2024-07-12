from android.dt_msg_helper import MessageHelper
from android.aqara_home import CameraHelper

# message_sender.reply_message("Virtual-Runtime", "")
# message_sender.check_read_status("Virtual-Runtime", "八嘎呀路")
#
# lang_helper = LanguageHelper()
# lang_helper.change_to_ch()

camera_helper = CameraHelper()
camera_helper.screen_streaming()

# message_sender = MessageHelper()
# message_sender.send_message("零封", "检测到cat")
