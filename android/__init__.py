# __init__.py
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
import os

def setup_logger(log_dir='logs'):
    """
    配置日志系统，按天分割日志文件。

    Args:
        log_dir (str): 日志存储目录，默认为 'logs'

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志目录（如果不存在）
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件处理器（按天分割）
    log_file = os.path.join(log_dir, 'trace.log')
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',  # 每天午夜分割
        interval=1,  # 间隔1天
        backupCount=30,  # 保留30天的日志
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    # 设置后缀格式，例如 trace.log.2025-03-28
    file_handler.suffix = "%Y-%m-%d"

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 获取根记录器并配置
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers = []  # 清空默认处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # 如果原始 trace.log 存在且不需要，可以在启动时清理
    if os.path.exists(log_file) and os.path.getsize(log_file) == 0:
        try:
            os.remove(log_file)
            logger.info(f"Removed empty initial log file: {log_file}")
        except Exception as e:
            logger.error(f"Failed to remove initial log file: {e}")

    return logging.getLogger(__name__)


# 使用示例
logger = setup_logger()