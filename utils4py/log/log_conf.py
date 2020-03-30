#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc: 
# FileName: log_conf.py
# Author:yhl
# Version:
# Last modified: 2019-12-11 18:26
import copy

from utils4py.log.filters import DebugFilter, InfoFilter, ErrorFilter, WarnFilter

LOG_DIR = './'
LOG_FILE = 'log'

_LOG_SETTING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s\t%(module)s\t%(process)d\t%(levelname)s\t%(message)s'
        },
        'flume': {
            # 'format': 'log_time=%(asctime)s\tmodule=%(module)s\tprocess=%(process)d\tlevelname=%(levelname)s\thost=%(host)s\t%(message)s'
            'format': '{"log_time":"%(asctime)s","module":"%(module)s","process":"%(process)d","levelname":"%(levelname)s","host":"%(host)s","content":%(message)s}'
        },
    },
    'filters': {
        'DebugFilter': {
            '()': DebugFilter
        },
        'InfoFilter': {
            '()': InfoFilter
        },
        'ErrorFilter': {
            '()': ErrorFilter
        },
        'WarnFilter': {
            '()': WarnFilter
        }
    },
    'handlers': {
        'info_handler': {
            'level': 'INFO',
            'class': 'utils4py.log.handlers.MultiProcessSafeTimedRotatingFileHandler',
            'filename': LOG_DIR + '/' + LOG_FILE + '.info',
            'backupCount': 14,
            'when': 'midnight',
            'formatter': 'flume',
            'filters': ['InfoFilter'],
        },
        'debug_handler': {
            'level': 'DEBUG',
            'class': 'utils4py.log.handlers.MultiProcessSafeTimedRotatingFileHandler',
            'filename': LOG_DIR + '/' + LOG_FILE + '.debug',
            'backupCount': 14,
            'when': 'midnight',
            'formatter': 'flume',
            'filters': ['DebugFilter'],
        },
        'error_handler': {
            'level': 'ERROR',
            'class': 'utils4py.log.handlers.MultiProcessSafeTimedRotatingFileHandler',
            'filename': LOG_DIR + '/' + LOG_FILE + '.error',
            'backupCount': 14,
            'when': 'midnight',
            'formatter': 'flume',
            'filters': ['ErrorFilter'],
        },
        'warn_handler': {
            'level': 'WARN',
            'class': 'utils4py.log.handlers.MultiProcessSafeTimedRotatingFileHandler',
            'filename': LOG_DIR + '/' + LOG_FILE + '.warn',
            'backupCount': 14,
            'when': 'midnight',
            'formatter': 'flume',
            'filters': ['WarnFilter'],
        }
    },
    'loggers': {
        'demo': {
            'handlers': ['warn_handler', 'error_handler', 'debug_handler', 'info_handler'],
            'propagate': False,
        }
    }
}

_NO_ROTATE_LOG_SETTING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s\t%(module)s\t%(process)d\t%(message)s'
        },
        'flume': {
            'format': 'log_time=%(asctime)s\tmodule=%(module)s\tprocess=%(process)d\thost=%(host)s\t%(message)s'
        },
    },
    'filters': {
        'DebugFilter': {
            '()': DebugFilter
        },
        'InfoFilter': {
            '()': InfoFilter
        },
        'ErrorFilter': {
            '()': ErrorFilter
        },
        'WarnFilter': {
            '()': WarnFilter
        }
    },
    'handlers': {
        'info_handler': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR + '/' + LOG_FILE + '.info',
            'formatter': 'flume',
            'filters': ['InfoFilter'],
        },
        'debug_handler': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR + '/' + LOG_FILE + '.debug',
            'formatter': 'flume',
            'filters': ['DebugFilter'],
        },
        'error_handler': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR + '/' + LOG_FILE + '.error',
            'formatter': 'flume',
            'filters': ['ErrorFilter'],
        },
        'warn_handler': {
            'level': 'WARN',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR + '/' + LOG_FILE + '.warn',
            'formatter': 'flume',
            'filters': ['WarnFilter'],
        }
    },
    'loggers': {
        'demo': {
            'handlers': ['warn_handler', 'error_handler', 'debug_handler', 'info_handler'],
            'propagate': False,
        }

    }
}


def get_basic_log_settings(delay=False):
    if delay:
        settings = copy.deepcopy(_LOG_SETTING)
        for k, v in settings['handlers'].items():
            v['delay'] = True
        return settings
    else:
        return copy.deepcopy(_LOG_SETTING)


def get_no_rotate_log_settings(delay=False):
    if delay:
        settings = copy.deepcopy(_NO_ROTATE_LOG_SETTING)
        for k, v in settings['handlers'].items():
            v['delay'] = True
        return settings
    else:
        return copy.deepcopy(_NO_ROTATE_LOG_SETTING)
