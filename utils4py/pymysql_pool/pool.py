#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import threading
import time
import traceback
from itertools import chain

from pymysql.connections import Connection as _Connection

from utils4py.pymysql_pool.log import get_logger

logger = get_logger()


class Connection(_Connection):
    """Connection"""

    def __init__(self, **kwargs):
        self.last_use_time = 0
        self.max_idle_time = kwargs.get('max_idle_time', 5400)  # default server wait_timeout
        super(Connection, self).__init__(**{
            k: v for k, v in kwargs.items() if k != 'max_idle_time'
        })
        self.pid = 0
        pass

    def connect(self, sock=None):
        r = super(Connection, self).connect(sock=sock)
        self.last_use_time = time.time()
        return r

    pass


class Pool(object):
    """ pool """

    _TAG = '\t[Pool]'

    def __init__(self, **connect_args):
        self.connection_args = connect_args

        self.pid = 0
        self._check_lock = None
        self._created_connections = None  # type:int
        self._available_connections = None  # type:list
        self._created_count_lock = None
        self.reset()

    def reset(self):
        self.pid = os.getpid()
        self._check_lock = threading.Lock()
        self._created_count_lock = threading.Lock()
        self._created_connections = 0
        self._available_connections = list()
        return

    def _atom_increment_created_count(self, cnt):
        with self._created_count_lock:
            self._created_connections += cnt

    def check_pid(self):
        if self.pid != os.getpid():
            with self._check_lock:
                if self.pid == os.getpid():
                    # another thread already did the work while we waited
                    # on the lock.
                    return
                self.disconnect()
                self.reset()
            pass
        return

    def get_connection(self):
        """ 
        :rtype: Connection
        """
        self.check_pid()

        try:
            conn = self._available_connections.pop()  # type:Connection
            if time.time() - conn.last_use_time > conn.max_idle_time:
                conn.ping(reconnect=True)
        except IndexError:
            conn = self.make_connection()

        logger.debug("%s %s get connection, count=%s, conn=%s", self._TAG, id(self),
                     self._created_connections, id(conn))

        return conn

    def make_connection(self):
        conn = Connection(**self.connection_args)
        conn.pid = self.pid
        self._atom_increment_created_count(1)

        logger.debug("%s %s make new connection %s", self._TAG, id(self), id(conn))
        return conn

    def release(self, connection, can_reuse=None):
        self.check_pid()
        if connection.pid != self.pid:
            return
        if can_reuse is False:
            self._atom_increment_created_count(-1)
        else:
            self._available_connections.append(connection)

        logger.debug("%s %s release connection, can_reuse = %s, connection_count = %s, conn = %s",
                     self._TAG, id(self), can_reuse, self._created_connections, id(connection))
        pass

    def disconnect(self):
        all_conns = chain(self._available_connections, )
        for connection in all_conns:
            try:
                connection.close()
            except (Exception,):
                logger.error("%s %s disconnect fail, detail= %s",
                             self._TAG,
                             id(self),
                             traceback.format_exc()
                             )
                pass
        return

    pass
