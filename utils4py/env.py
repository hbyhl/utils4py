#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

__DEBUG_ENV_KEY__ = "IS_DEBUG"
__IS_DEBUG__ = False

if os.path.exists(os.path.join(os.getcwd(), "conf_test")):
    __IS_DEBUG__ = True
else:
    try:
        __IS_DEBUG__ = True if int(os.environ.get('IS_DEBUG', 0)) == 1 else False
    except (ValueError, KeyError):
        __IS_DEBUG__ = False


def is_debug():
    return __IS_DEBUG__
