#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time

from flask import request, g
from utils4py import env
from utils4py.flask_ext.filter import BaseFilter
from utils4py.formate import format_kv


class LogFilter(BaseFilter):
    """
        记录请求日志
    """

    IGNORE_LOG_REQUEST_PATH = {"/", "/ping", "/favicon.ico"}

    def before_request(self, *args, **kwargs):
        g.req_timer = {'start': time.time(), 'end': 0, 'cost': 0, }

        g.method = request.method
        g.path = request.path
        g.url = request.url
        g.referer = request.referrer
        # 请求的直接来源地址
        # 若服务使用了nginx做反向代理且未做必要的X-Real-IP的配置时，取到的是nginx的机器ip，若做了相关配置取到的是nginx服务器上一跳的机器ip
        # 若服务未使用nginx做反向代理，取到的就是访问此服务的直接机器ip
        g.remote_ip = request.headers.environ.get("X-Real-IP", request.remote_addr)
        g.x_forwarded_for = request.headers.get("X_FORWARDED_FOR")  # 取请求原始来源，需要nginx中添加响应的配置
        g.user_agent = request.headers.get('User-Agent', '')
        params = dict()
        params.update({k: request.args[k] for k in request.args.keys()} if request.args else {})
        params.update({k: request.form[k] for k in request.form.keys()} if request.form else {})
        json_params = json.loads(request.json) if request.json else {}
        params.update({k: json_params[k] for k in json_params.keys()} if json_params else {})
        if request.data:
            try:
                json_params = json.loads(request.get_data())
                if json_params and isinstance(json_params, dict):
                    params.update(json_params)
            except (Exception,):
                pass

        g.params = params
        g.code = 0
        g.kv_log = dict()
        return

    def teardown_request(self, *args, **kwargs):
        print('+++++++++++++++++++++++++++++++++insert teardown_request')
        path = g.path
        if path and self.IGNORE_LOG_REQUEST_PATH and path in self.IGNORE_LOG_REQUEST_PATH:
            return

        g.req_timer['end'] = time.time()
        g.req_timer['cost'] = round(1000 * (g.req_timer['end'] - g.req_timer['start']), 2)

        if not env.is_debug and 'pass_word' in g.params:
            g.params['pass_word'] = '******'

        log_data = {
            'method': g.get('method',''),
            'remote_ip': g.get('remote_ip',''),
            'x_forwarded_for': g.get('x_forwarded_for',''),
            'referer': g.get('referer',''),
            'user_agent': g.get('user_agent',''),
            'url': g.get('url',''),
            'path': g.get('path',''),
            'params': g.get('params',''),
            'code': g.get('code',''),
            'cost': g.req_timer['cost'],
        }

        if g.kv_log and isinstance(g.kv_log, dict):
            for k, v in g.kv_log.items():
                if k not in log_data:
                    log_data[k] = v
        print('+++++++++++++++++++++++++++++++++to write log to file')
        self.logger.info(format_kv(log_data))
