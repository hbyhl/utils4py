#!/usr/bin/env python
# -*- coding: utf-8 -*-

from six import iteritems

from utils4py.s import TextUtils

_error_map = dict({
    "101"  : "参数错误",
    "104"  : "安全检查错误",
    "-1000": "内部错误",
})


def register_error(k, v, force=None):
    code = TextUtils.to_string(k)
    if not force:
        if code in _error_map:
            raise Exception("error code %s has registered!" % code)
    val = TextUtils.to_string(v).strip()
    if val:
        _error_map[code] = val
    return


def register_errors(err_map):
    for k, v in iteritems(err_map):
        register_error(k, v, force=True)
    return


class SimpleError(Exception):
    """ Simple Error """

    def __init__(self, code, message=None):
        msg = "#".join(filter(
            lambda x: x,
            map(
                TextUtils.to_string,
                [
                    _error_map.get(TextUtils.to_string(code), ''),
                    message,
                ]
            )
        ))
        if not msg:
            msg = '未知错误'

        Exception.__init__(self, *(code, msg))

    @property
    def code(self):
        return self.args[0]

    @property
    def message(self):
        return self.args[1]

    def __str__(self):
        return ",".join(filter(lambda x: x, map(TextUtils.to_string, self.args)))

    pass


class ParamError(SimpleError):  # 参数错误

    def __init__(self, code=101, message=None):
        SimpleError.__init__(self, code, message)

    pass


class SecurityError(SimpleError):  # 安全拦截错误

    def __init__(self, code=104, message=None):
        SimpleError.__init__(self, code, message)

    pass
