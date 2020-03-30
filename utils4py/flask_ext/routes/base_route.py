#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: base_route.py
# Author:yhl
# Version:
# Last modified: 2019-12-30 12:33
import abc

from flask import g
from six import add_metaclass

from utils4py.flask_ext.service import BaseService


@add_metaclass(abc.ABCMeta)
class BaseRoute(BaseService):
    """
        对route的参数做统一的校验
    """
    # 为参数指定checker方法,子类中请根据需要实例化
    PARA_CHECK_DICT = {

    }
    # 必须的字段名称
    REQUIRED_PARAMS = []

    def check_args(self, *args, **kwargs):
        # 过滤非空参数
        for key in g.params.keys():
            self.params[key] = g.params[key]
        # 参数正确性校验
        for key in self.params.keys():
            if key in self.PARA_CHECK_DICT and not self.PARA_CHECK_DICT[key](self.params[key]):
                raise self.build_error(101, '参数%s错误' % key)
        for key in self.REQUIRED_PARAMS:
            if key not in self.params:
                raise self.build_error(101, '%s is required' % key)

