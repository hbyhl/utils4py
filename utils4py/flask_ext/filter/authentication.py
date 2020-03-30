#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: authentication.py
# Author:yhl
# Version:
# Last modified: 2019-12-24 14:34
import os
import threading
import time

import schedule
from flask import request

from utils4py.conf import Constant
from utils4py.data import connect_redis
from utils4py import ConfUtils
from utils4py.flask_ext import ResultBuilder
from utils4py.flask_ext.filter import BaseFilter
from utils4py.scan import find_class


class BaseAuthenticationStrategy(object):
    """自定义鉴权验证策略需继承此类，并在配置文件conf/server.yaml中添加AUTHENTICATION_CLS_NAME  ： 自定义类的名称"""

    def has_auth(self, request_app_key, path=None):
        return True



class LocalAuthenticationStrategy(BaseAuthenticationStrategy):
    """定时获取权限控制文件到本地，本地判断权限实现"""

    def __init__(self):
        self._schedule_thread = None
        self._authored_app_keys = None  # get_strategy 获取到的策略保存于此，用于authentication验证

    @property
    def authored_app_keys(self):
        return self._authored_app_keys

    def get_authored_app_keys(self):
        """
            重新此方法是，获取到app_keys需要赋值给self.authored_app_keys
        """
        self._authored_app_keys = None

    def start_schedule_thread(self):
        def _():
            schedule.every(30).minutes.do(self.get_authored_app_keys)
            while True:
                schedule.run_pending()
                time.sleep(1)

        self._schedule_thread = threading.Thread(target=_, name="get_strategy_thread")

    def has_auth(self, request_app_key, path=None):
        if self._schedule_thread is None or not self._schedule_thread.is_alive():
            self.start_schedule_thread()
        if self._authored_app_keys is None:
            return True
        else:
            return request_app_key in self._authored_app_keys



class RedisAuthenticationStrategy(BaseAuthenticationStrategy):
    """
        控制策略数据存储在redis中，key：value中key = "authenticate:{APP_KEY}"（校验粒度在服务级别）或"authenticate:{APP_KEY}:{PATH}"(校验力度在方法级别)，value的值为授权了的app_key 的set
        此默认约定：
            1、要有配置文件cong/data_source/redis.conf,并且文件中配置了section="authen_redis"的配置，指明使用的redis集群
                或在conf/server.yaml 配置AUTHENTICATION_REDIS_SECTION 指明使用的redis配置
            3、conf/server.yaml 中可通过"AUTHENTICATION_GRANULARITY" 指定控制粒度，1为服务级别，2为接口级别
            4、conf/server.yaml中通过APPKEY指明本服务的APPKEY
    """

    def __init__(self, *args, **kwargs):
        # 设定默认值
        server_conf = ConfUtils.load_yaml(Constant.SERVER_CONF_FILE_NAME)
        self._app_key = server_conf[Constant.APPKEY]
        # 如果配置中有配置项，使用配置值
        self.__redis_section = "authen_redis" if not server_conf.get("AUTHENTICATION_REDIS_SECTION", None) else \
            server_conf['AUTHENTICATION_REDIS_SECTION']
        self._authentication_granularity = 1 if not server_conf.get('AUTHENTICATION_GRANULARITY', None) else int(
            server_conf['AUTHENTICATION_GRANULARITY'])
        self._redis_cli = connect_redis("authen_redis")

    def has_auth(self, request_app_key, path=None):
        if not request_app_key:
            return False
        if self._authentication_granularity == 1:
            return self._redis_cli.sismember("authenticate:%s" % self._app_key, request_app_key)
        else:
            return self._redis_cli.sismember("authenticate:%s:%s" % (self._app_key, path), request_app_key)


class AuthenticationFilter(BaseFilter):
    """
        对请求来源做访问控制
        使用此filter需要添加配置如下
            1、conf/server.yaml 中通过AUTHENTICATION_CLS_NAME使用哪个AuthenticationStrategy
    """

    def __init__(self, app, **kwargs):
        BaseFilter.__init__(self, app, **kwargs)
        authentication_stratege_cls = find_class(self._get_authentication_cls_name())
        assert issubclass(authentication_stratege_cls, BaseAuthenticationStrategy)
        self._AuthenticationStrategy = authentication_stratege_cls()

    @classmethod
    def _get_authentication_cls_name(cls):
        full_conf_path = ConfUtils.complete_path(Constant.SERVER_CONF_FILE_NAME)
        if os.path.exists(full_conf_path):
            server_conf = ConfUtils.load_yaml(Constant.SERVER_CONF_FILE_NAME)
            if server_conf is not None:
                return server_conf.get("AUTHENTICATION_CLS_NAME",
                                       'utils4py.flask_ext.filter.authentication.BaseAuthenticationStrategy')
        return 'utils4py.flask_ext.filter.authentication.BaseAuthenticationStrategy'

    def before_request(self, *args, **kwargs):
        request_app_key = request.headers.get(Constant.APPKEY, None)
        if not request_app_key:
            request_app_key = request.args.get(Constant.APPKEY, None)
        if not request_app_key:
            request_app_key = request.form.get(Constant.APPKEY, None)
        has_auth = self._AuthenticationStrategy.has_auth(request_app_key)
        if not has_auth:
            return ResultBuilder.build(104, message="Authentication failed")
