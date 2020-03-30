#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import re

import six
from flask import request

from utils4py.s import TextUtils


class ArgsChecker(object):
    """
         basic arg format checker
    """

    _dt_format = "%Y-%m-%d %H:%M:%S"
    _date_format = "%Y-%m-%d"

    @classmethod
    def is_valid_phone(cls, phone):
        str_phone = TextUtils.to_string(phone)
        assert str_phone and re.match(r'^1\d{10}$', str_phone)
        return True

    @classmethod
    def is_valid_identity(cls, identity):
        str_identity = TextUtils.to_string(identity)
        assert str_identity and re.match(r'^\d{17}[0-9xX]$', str_identity)
        return True

    @classmethod
    def is_valid_url(cls, url):
        assert url and isinstance(url, six.string_types)
        str_url = TextUtils.to_string(url)
        assert str_url.startswith("http://") or str_url.startswith("https://")
        assert len(str_url) > 12
        return True

    @classmethod
    def is_valid_datetime(cls, dt, fmt=None):
        if isinstance(dt, (datetime.datetime, datetime.date)):
            return dt
        _fmt = fmt if fmt and isinstance(fmt, six.string_types) else cls._dt_format
        return datetime.datetime.strptime(dt, _fmt)

    @classmethod
    def is_valid_date(cls, dt, fmt=None):
        _fmt = fmt if fmt and isinstance(fmt, six.string_types) else cls._date_format
        try:
            result = True if datetime.datetime.strptime(dt, _fmt) else False
        except ValueError:
            result = False
        return result

    @classmethod
    def is_number(cls, val):
        if type(val) == int:
            return True
        val_str = TextUtils.to_string(val)
        return val_str.isdigit()


class UserAgentChecker(object):

    @classmethod
    def check_ua_is_ios(cls):
        """
        根据UserAgent判断是否为iphone
        :return:
        """
        ua = request.headers.get('User-Agent', '')
        if ua.lower().find('iphone') >= 0:
            return True
        return False
