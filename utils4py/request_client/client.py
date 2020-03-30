#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: client.py
# Author:yhl
# Version:
# Last modified: 2019-12-27 13:55
import abc
import json
import logging
import traceback

import requests
from requests.adapters import HTTPAdapter

_logger = logging.getLogger(__name__)


class BaseClient(object):
    """
        对requests的二次封装，格式化response解析，重试机制
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, logger_handler=_logger, retry_times=3, request_timeout=10, base_headers=None):
        """
        :param logger_handler:  若需要将请求接口的错误日志与其他日志一起收集，请传递公用的logger
        :param retry_times:
        :param request_timeout:
        :param base_headers:
        """
        self.__logger_handler = logger_handler
        self.__retry_times = retry_times
        self.__request_timeout = request_timeout
        self.__base_headers = base_headers
        ##构建session属性，并设置重试次数，使用此属性发送请求
        self.__request_session = requests.Session()
        self.__request_session.mount('http://', HTTPAdapter(max_retries=self.__retry_times))
        self.__request_session.mount('https://', HTTPAdapter(max_retries=self.__retry_times))

    def send_request(self, url, data=None, json_param=None, method='POST', headers=None):
        """
        :param url:
        :param data:
        :param json_param:
        :param method:
        :param headers:
        :return:
        """
        result = {'code': 1, 'data': {}, 'msg': ''}
        try:
            _headers = {}
            if headers:
                _headers.update(headers)
            if self.__base_headers:
                _headers.update(self.__base_headers)
            if 'POST' == method.upper():
                response = self.__request_session.post(url, data=data, json=json_param, timeout=self.__request_timeout, headers=_headers)
            else:
                response = self.__request_session.get(url, data=data, json=json_param, timeout=self.__request_timeout, headers=_headers)

            if response.status_code != 200:
                result['msg'] = 'error_code:%s' % response.status_code
                return result

            response_json = json.loads(response.content)
            ret_code = response_json.get('code')
            if ret_code != 0:
                result['msg'] = response_json.get('msg')
                result['code'] = ret_code
                return result
            else:
                result['data'] = response_json.get('data')
                result['code'] = 0
        except Exception as e:
            except_detail = traceback.format_exc()
            self.__logger_handler.error(except_detail)
            result['msg'] = 'request exception'
            result['except_detail'] = except_detail
        return result

    def get_data(self, url, params=None, method='POST', headers=None):
        """单纯的只是send_request方法的一个别名方法，无其他意义"""
        if isinstance(params, str):
            return self.send_request(url, json_param=params, method=method, headers=headers)
        return self.send_request(url, data=params, method=method, headers=headers)
