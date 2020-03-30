#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: neo4j.py
# Author:yhl
# Version:
# Last modified: 2020-02-28 11:12


import threading

from py2neo import Graph

from utils4py import ConfUtils

_neo4j_conf = ConfUtils.load_parser("data_source/neo4j.conf")

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

class _GraphWrapper(object):

    def __init__(self,graph):
        self._graph = graph

    def execute(self, cypher, **kwargs):
        cur = self._graph.run(cypher, **kwargs)
        data = cur.data()
        cur.close()
        return data

class _ConnectParams(object):
    """
        neo4j connect params
    """

    def __init__(self):
        self._user = "neo4j"
        self._password = "password"
        self._host = "localhost"
        self._port = 7474
        self._scheme = 'http'
        pass


    def init_with_section(self, section):
        conf = dict(_neo4j_conf.items(section=section))
        self._user = conf.get("user", "neo4j")
        self._password = conf.get("password", "password")
        self._host = conf.get("host", "localhost")
        self._port = int(conf.get("port", 7474))
        self._scheme = conf.get('scheme','http')
        return self

    def connect(self):
        graph = Graph(username=self._user, password=self._password,host=self._host,port=self._port,scheme=self._scheme)
        return _GraphWrapper(graph)
