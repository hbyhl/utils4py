#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import threading

from pymysql.cursors import DictCursor

from utils4py import ConfUtils
from utils4py.data.pymysql_pool import Pool, SqlShell

_mysql_conf = ConfUtils.load_parser("data_source/mysql.conf")

_conn_pool = dict()  # 配置池
_conn_mutex = threading.RLock()


def connect_pool(section):
    """
    :param section: 
    :rtype: SqlShell 
    """
    with _conn_mutex:
        if section not in _conn_pool:
            params = _ConnectParams().init_with_section(section).get_connect_params()
            _conn_pool[section] = Pool(**params)

        return SqlShell(_conn_pool[section])


connect = connect_pool


class _ConnectParams(object):
    """
        mysql 连接参数
    """

    def __init__(self):
        self._host = "localhost"
        self._port = 3306
        self._user = ""
        self._password = ""
        self._db = ""
        self._time_zone = "+4:00"
        self._charset = 'utf8'
        self._max_idle_time = 7 * 3600


    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port or 3306

    @property
    def password(self):
        return self._password or ""

    @property
    def user(self):
        return self._user

    @property
    def db(self):
        return self._db

    @property
    def charset(self):
        return self._charset or 'utf8'

    @property
    def time_zone(self):
        return self._time_zone or '+4:00'

    def init_with_section(self, section_name):
        items = dict(_mysql_conf.items(section_name))
        self._host = str.strip(items.get('host', ""))
        self._port = int(items.get('port', 3306))
        self._user = str.strip(items.get('user', ""))
        self._password = str.strip(items.get('password', ""))
        self._db = str.strip(items.get('db', ""))
        self._time_zone = str.strip(items.get('time_zone', '+4:00'))
        self._charset = str.strip(items.get('charset', 'utf8'))
        self._max_idle_time = int(items.get('max_idle_time', 7 * 3600))
        return self

    def get_connect_params(self):
        time_zone = self.time_zone
        init_command = None
        if time_zone:
            init_command = 'SET time_zone = "%s"' % time_zone

        return dict(host=self.host,
                    port=self.port,
                    database=self.db,
                    user=self.user,
                    password=self.password,
                    use_unicode=True,
                    autocommit=True,
                    init_command=init_command,
                    charset=self.charset,
                    cursorclass=DictCursor,
                    max_idle_time=self._max_idle_time,
                    )

    def __str__(self):
        return json.dumps({'host': self.host,
                           'port': self.port,
                           'database': self.db,
                           'user': self.user,
                           'password': self.password,
                           'time_zone': self.time_zone,
                           'charset': self.charset,
                           'max_idle_time': self._max_idle_time,
                           })
