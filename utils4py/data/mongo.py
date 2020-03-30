#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
from urllib.parse import quote_plus

from pymongo import MongoClient
from pymongo.database import Database

from utils4py import ConfUtils

_mongo_conf = ConfUtils.load_parser("data_source/mongo.conf")

_conn_pool = dict()
_reuse_mutex = threading.RLock()


def connect(section, settings_reuse_pool=True):
    """
    :param section: 
    :rtype: Database
    """
    if settings_reuse_pool:
        with _reuse_mutex:
            if section not in _conn_pool:
                db_obj = _ConnectParams().init_with_section(section).connect()
                if db_obj:
                    _conn_pool[section] = db_obj
            return _conn_pool[section]
    else:
        return _ConnectParams().init_with_section(section).connect()


class _ConnectParams(object):
    """
        mongo connect params
    """

    def __init__(self):
        self._user = ""
        self._password = ""
        self._host = ""
        self._db = ""
        self._params = ""
        self._client = ""
        pass

    @property
    def db_name(self):
        return self._db

    def init_with_section(self, section):
        conf = dict(_mongo_conf.items(section=section))
        self._user = conf.get("user", "")
        self._password = conf.get("password", "")
        self._host = conf.get("host", "")
        self._db = conf.get("db", "")
        self._params = conf.get("params", "")
        return self

    def connect(self):
        if self._user and self._password:
            uri = "mongodb://%s:%s@%s" % (quote_plus(self._user), quote_plus(self._password), self._host)
        else:
            uri = "mongodb://%s" % self._host
        uri = "%s/%s" % (uri, self._db)
        if self._params:
            uri = uri + "?" + self._params

        client = MongoClient(uri, unicode_decode_error_handler='ignore')
        if self.db_name:
            return client.get_database(self.db_name)
        else:
            return client

