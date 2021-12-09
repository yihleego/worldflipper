import logging
import os
import sys
import threading

import yaml


class Adder:
    def __init__(self, value=0):
        self.value = value
        self.lock = threading.Lock()

    def add(self, delta=1):
        self.lock.acquire()
        v = self.value + delta
        self.value = v
        self.lock.release()
        return v

    def get(self):
        self.lock.acquire()
        v = self.value
        self.lock.release()
        return v


def init():
    global config
    file = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "application.yml"), 'r', encoding='utf-8')
    config = yaml.load(file, Loader=yaml.SafeLoader)
    _logging_config(config.get("logging"))
    _airtest_config()
    _wda_config()


def _logging_config(config):
    level = config.get("level", "INFO")
    filename = config.get("filename")
    format = config.get("format")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    file_handler = logging.FileHandler(filename)
    stream_handler = logging.StreamHandler(sys.stdout)
    if format:
        formatter = logging.Formatter(format)
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)
    logger = logging.getLogger('worldflipper')
    logger.setLevel(logging.getLevelName(level.upper()))
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def _airtest_config():
    from airtest.core.settings import Settings

    Settings.FIND_TIMEOUT = 1
    Settings.FIND_TIMEOUT_TMP = 1
    Settings.SAVE_IMAGE = False


def _wda_config():
    global adder
    adder = Adder(config.get('wda').get('port'))


def get_web_port():
    return config.get('web').get('port')


def get_wda_port():
    return config.get('wda').get('port')


def get_wda_bundle_id():
    return config.get('wda').get('bundle_id')


def next_wda_port():
    return adder.add()
