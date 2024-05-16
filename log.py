# -*- coding: utf-8 -*-
"""
@Software: PyCharm
@Project: WebsiteMonitor
@Author: ZQ
@File: log.py
@Time: 2024/3/4 15:10
"""
import logging.config
import os
import sys
import yaml


def read_yaml(log_config_path):
    """读取yaml文件"""
    if os.path.exists(log_config_path):
        with open(log_config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data
    else:
        logging.error(f'Yaml文件不存在：{log_config_path}\n')
        sys.exit()


class MyLog:
    def __init__(self, logger_name='root'):
        if not os.path.exists('Logs'):
            os.mkdir('Logs')
        logging.config.dictConfig(read_yaml('logging.config.yaml'))
        self.logger = logging.getLogger(logger_name)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
