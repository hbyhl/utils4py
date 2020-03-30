#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: redis_client.py
# Author:yhl
# Version:
# Last modified: 2020-02-01 17:33

import zlib
from redis import StrictRedis

try:
    import cPickle as pickle
except:
    import pickle


class RedisClient(object):
    def __init__(self, app, params):
        self._redis_client = StrictRedis(
            host=params['host'],
            port=params['port'],
            db=params['db'],
            password=params.get('password',None),
            max_connections=params.get('max_connections', 100),
            socket_timeout=params.get('socket_timeout', 1)
        )
        self._appname = app

    def _gen_cachekey(self, key):
        return '%s:%s' % (self._appname, key)

    def _compress(self, value):
        compressed_value = zlib.compress(pickle.dumps(value), zlib.Z_BEST_COMPRESSION)
        return compressed_value

    def _decompress(self, value):
        decompress_value = pickle.loads(zlib.decompress(value))
        return decompress_value

    def set(self, key, value, ex=None, px=None, nx=False, xx=False):
        nkey = self._gen_cachekey(key)
        nvalue = self._compress(value)
        return self._redis_client.set(nkey, nvalue, ex=ex, px=px, nx=nx, xx=xx)

    def get(self, key, default=None):
        nkey = self._gen_cachekey(key)
        value = self._redis_client.get(nkey)
        if value == None:
            return default
        return self._decompress(value)

    def expire(self, key, time):
        nkey = self._gen_cachekey(key)
        return self._redis_client.expire(nkey, time)

    def delete(self, key):
        nkey = self._gen_cachekey(key)
        return self._redis_client.delete(nkey)

    def hset(self, key, field, value):
        nkey = self._gen_cachekey(key)
        return self._redis_client.hset(nkey, field, value)

    def hmget(self, key, field):
        nkey = self._gen_cachekey(key)
        return self._redis_client.hmget(nkey, field)

    def incrby(self, key, value):
        nkey = self._gen_cachekey(key)
        return self._redis_client.incrby(nkey, value)
