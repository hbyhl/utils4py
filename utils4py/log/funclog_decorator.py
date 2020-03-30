#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: log_decorator.py
# Author:yhl
# Version:
# Last modified: 2019-07-31 10:32
import logging
import time
import traceback

from utils4py.formate import format_kv

_logger = logging.getLogger(__name__)


def log_decorator(logger=_logger):
    def decorator(func):
        def wrapper(*args, **kw):
            func_class_name = 'function'  # 默认为function
            if len(args) > 0 and hasattr(args[0], '__class__'):
                func_class_name = args[0].__class__.__name__

            start_log = {'log_type': 'func_call_start',
                         'func_name': func_class_name + ':' + func.__name__,
                         'args': args,
                         'kwargs': kw
                         }
            logger.debug(format_kv(start_log))
            start_time = time.time()
            try:
                result = func(*args, **kw)
            except Exception as e:
                logger.error(traceback.format_exc())
                raise e
            end_time = time.time()
            end_log = {'log_type': 'func_call_result',
                       'func_name': func.__name__,
                       'args': args,
                       'kwargs': kw,
                       'result': result,
                       'cost': int(end_time * 1000 - start_time * 1000)
                       }
            logger.debug(format_kv(end_log))
            return result

        return wrapper

    return decorator
