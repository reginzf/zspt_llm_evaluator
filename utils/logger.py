import logging
import os
from datetime import datetime
from pathlib import Path
from env_config_init import settings

class Logger:
    _instances = {}

    def __new__(cls, log_dir=None, log_level=logging.INFO, name="default"):
        # 实现单例模式，确保相同名称的logger只有一个实例
        if name in cls._instances:
            return cls._instances[name]
        instance = super(Logger, cls).__new__(cls)
        cls._instances[name] = instance
        return instance

    def __init__(self, log_dir=None, log_level=logging.INFO, name="default"):
        # 防止重复初始化
        if hasattr(self, 'logger'):
            return

        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        # 清除现有的处理器以避免重复添加
        self.logger.handlers.clear()

        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 如果指定了日志目录，则添加文件处理器
        if log_dir:
            # 确保日志目录存在
            Path(log_dir).mkdir(parents=True, exist_ok=True)

            # 创建带时间戳的日志文件名
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")

            # 添加文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    def get_logger(self):
        return self.logger

logger = Logger(log_dir=settings.LOG_DIR if hasattr(settings, 'LOG_DIR') else './logs',
                      log_level=logging.INFO,
                      name="zlpt_ls_operate")