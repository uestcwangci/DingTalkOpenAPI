# __init__.py
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
import os

def setup_logger(log_dir='logs'):
    # 创建日志目录（如果不存在）
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件处理器（按天分割）
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'trace.log'),
        when='midnight',
        interval=1,
        backupCount=30,  # 保留30天的日志
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 配置根记录器
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )

    # 获取记录器
    logger = logging.getLogger(__name__)

    return logger


# 使用示例
logger = setup_logger()

