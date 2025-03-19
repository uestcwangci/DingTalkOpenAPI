# __init__.py
import logging
import sys

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s %(levelname)s %(message)s',
                   handlers=[
                       logging.FileHandler('trace.log', encoding='utf-8'),
                       logging.StreamHandler(sys.stdout)
                   ])
logger = logging.getLogger(__name__)
