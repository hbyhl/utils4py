#!usr/bin/env python
# -*- coding:utf-8 _*-

# Desc: 
# FileName: log.py
# Author:yhl
# Version:
# Last modified: 2019-12-11 23:48

import os
import copy
import logging
import logging.config
from logging import LoggerAdapter
import socket
import getpass

from utils4py import ConfUtils
from utils4py.log.log_conf import get_basic_log_settings, get_no_rotate_log_settings

MACHINE_NAME = socket.getfqdn(socket.gethostname())
USER_NAME = getpass.getuser()
BASE = "Base"
LOG_DIR = "log_dir"
LOG_FILE = "log_file"
LOG_LEVEL = "log_level"
required_ops = [(BASE, LOG_DIR), (BASE, LOG_FILE), (BASE, LOG_LEVEL)]

BOOLEAN_TRUE_STRINGS = ('true', 'on', 'ok', 'y', 'yes', '1')

def get_env_bool(key, default):

    if key in os.environ:
        value = os.environ[key]
        if value.lower() in BOOLEAN_TRUE_STRINGS:
            return True
        else:
            return False
    else:
        return default

def init_log_from_config(cfg_file, formatter='standard',delay=False):
    parser = ConfUtils.load_parser(cfg_file)
    for sec,op in required_ops:
        if not parser.has_option(sec, op):
            raise Exception("Log load config file failed")
    log_dir = parser.get(BASE, LOG_DIR)
    log_file = parser.get(BASE, LOG_FILE)
    #add default hostname suffix for log_file
    log_file += '.'+MACHINE_NAME
    log_level = parser.get(BASE, LOG_LEVEL)
    delay = delay or get_env_bool('DELAY_LOG', default=False)

    rotate = get_env_bool("ROTATE_LOG", default=True)
    if not rotate:
        settings = get_no_rotate_log_settings(delay)
    else:
        settings = get_basic_log_settings(delay)
    settings['handlers']['info_handler']['filename'] = log_dir + '/' + log_file +'.info'
    settings['handlers']['debug_handler']['filename'] = log_dir + '/' + log_file +'.debug'
    settings['handlers']['warn_handler']['filename'] = log_dir + '/' + log_file +'.warn'
    settings['handlers']['error_handler']['filename'] = log_dir + '/' + log_file +'.error'
    if formatter == 'flume':
        settings['handlers']['info_handler']['formatter'] = formatter
        settings['handlers']['debug_handler']['formatter'] = formatter
        settings['handlers']['warn_handler']['formatter'] = formatter
        settings['handlers']['error_handler']['formatter'] = formatter
    settings['loggers'][log_file] = copy.deepcopy(settings['loggers']['demo'])
    logging.config.dictConfig(settings)
    extra_dict = {"host":MACHINE_NAME}
    logger = logging.getLogger(log_file)
    logger.propagate = False
    if log_level == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    elif log_level == 'INFO':
        logger.setLevel(logging.INFO)
    elif log_level == 'WARN':
        logger.setLevel(logging.WARN)
    elif log_level == 'ERROR':
        logger.setLevel(logging.ERROR)
    else:
        raise ("unknown log level:[%s]" %log_level)

    return LoggerAdapter(logger,extra_dict)


CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

logger = init_log_from_config(CURRENT_DIR + '/conf/log.conf')

if __name__ == '__main__':
    logger.info("info message")
    logger.info("info message cccccc")

    logger.debug("debug message")
    logger.error("error message")
    logger.warning("warning message")