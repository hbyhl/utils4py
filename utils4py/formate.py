#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: formate.py
# Author:yhl
# Version:
# Last modified: 2019-12-20 10:48
import datetime
import json
import traceback

from utils4py import TextUtils

DT_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
DM_FORMAT = "%Y-%m"
LDT_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'


def format_kv(kv_log):
    """
    :param kv_log:
    :return:
    """
    return "\t".join(map(
        lambda x: "{}={}".format(*x),
        [(k, TextUtils.to_string(kv_log[k]).replace('\t', ' ')) for k in sorted(kv_log.keys())]
    ))

def format_to_json(obj):
    """
    :param obj:
    :return:
    """
    if isinstance(obj,dict):
        tmp_dict = {}
        for k, v in obj.items():
            tmp_dict[k] = str(v)
        return json.dumps(tmp_dict)
    else:
        return str(obj)



def trans_fen_to_yuan(amount):
    if not amount:
        return 0
    amount = int(amount)
    yuan = amount / 100.00
    return yuan


def trans_wan_to_bai_rate(rate):
    if not rate:
        return ""
    else:
        rate = int(rate)
        pecent_rate = rate / 10000.00
        return format(pecent_rate, '.0%')


def format_datetime(date_time, fomat=DT_FORMAT):
    if date_time and isinstance(date_time, datetime.datetime):
        return date_time.strftime(fomat)
    return ''


if __name__ == '__main__':
    print(trans_fen_to_yuan(10))
