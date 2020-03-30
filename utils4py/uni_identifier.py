#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:一些返回唯一标识的方法
# FileName: uni_identifier.py
# Author:yhl
# Version:
# Last modified: 2019-12-20 10:55

import time
import uuid


def get_s_timestamp_id():
    """返回秒数"""
    return time.time().__str__().split('.')[0]


def get_ms_timestamp_id():
    """返回毫秒数"""
    ms = time.time() * 1000
    return ms.__str__().split('.')[0]


def get_uuid():
    return str(uuid.uuid1())


if __name__ == '__main__':
    # print(time.time() * 1000)
    # import sys
    #
    # i = sys.maxsize
    #
    # print(i)
    print(get_s_timestamp_id())
