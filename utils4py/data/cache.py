#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import json
import threading
import time
import traceback

import redis
import redis.client

from utils4py import ConfUtils, TextUtils
from utils4py.flask_ext.errors import SimpleError
from utils4py.uni_identifier import get_uuid

_redis_conf = ConfUtils.load_parser("data_source/redis.conf")

_conn_pool = dict()
_reuse_mutex = threading.RLock()


def connect(section, settings_reuse_pool=True):
    if settings_reuse_pool:
        with _reuse_mutex:
            conn = _conn_pool.get(section, None)
            if not conn:
                conn = _ConnectParams().init_with_section(section).connect()
                if conn:
                    _conn_pool[section] = conn
            return conn
    else:
        params = _ConnectParams().init_with_section(section)
        return params.connect()


class _RedisWrapper(object):
    """
        Redis
    """

    _method_groups_1 = {'hexists', 'decr', 'exists', 'expire', 'get',
                        'getset', 'hdel', 'hget', 'hgetall', 'hkeys',
                        'hlen', 'hmget', 'hmset', 'hset', 'hsetnx',
                        'incr', 'keys', 'llen', 'lpop', 'lpush', 'lrange', 'lindex',
                        'rpop', 'rpush', 'sadd', 'set', 'setex', 'setnx',
                        'sismember', 'smembers', 'srem', 'ttl', 'type', }

    _method_groups_2 = {"delete", "mget"}

    def __init__(self, client, key_prefix):
        self._client = client  # type:redis.Redis
        self._key_prefix = key_prefix  # type:str

    def __getattr__(self, item):
        try:
            assert item in self._method_groups_1 or item in self._method_groups_2
            method = getattr(self._client, item)
            assert method
        except:
            raise AttributeError(item)

        if item in self._method_groups_1:
            def _inner(*args, **kwargs):
                add_prefix_to_key = kwargs.pop('add_prefix_to_key', True)
                if add_prefix_to_key:
                    make_key = self.make_key_with_prefix
                else:
                    make_key = self.make_key_without_prefix
                arg_lst = list(args)
                a0 = make_key(arg_lst[0])
                arg_lst[0] = a0
                return method(*tuple(arg_lst), **kwargs)
        else:
            def _inner(*args, **kwargs):
                add_prefix_to_key = kwargs.pop('add_prefix_to_key', True)
                if add_prefix_to_key:
                    make_key = self.make_key_with_prefix
                else:
                    make_key = self.make_key_without_prefix
                arg_lst = list(args)
                a0 = arg_lst[0]
                a_els = arg_lst[1:]
                a_new = list(map(
                    make_key,
                    redis.client.list_or_args(a0, a_els)
                ))
                return method(*tuple(a_new), **kwargs)

        return _inner

    def ping(self):
        return self._client.ping()

    def make_key_with_prefix(self, key):
        if self._key_prefix:
            return "{}:{}".format(self._key_prefix, key)
        else:
            return key

    def make_key_without_prefix(self, key):
        return key


class _ConnectParams(object):
    """
        redis
    """

    _default_params = {
        'host': "localhost",
        "port": 6379,
        "db": 0,
    }

    def __init__(self):
        self._params = copy.deepcopy(_ConnectParams._default_params)
        self._section = None
        self._with_key_prefix = True

    def init_with_section(self, section_name):
        self._section = section_name
        for k, v in _redis_conf.items(section_name):
            self._params[k] = v
        self._params['port'] = int(self._params['port'])
        self._params['db'] = int(self._params['db'])
        if 'with_key_prefix' in self._params:
            self._with_key_prefix = eval(self._params.pop('with_key_prefix'))
        return self

    def connect(self):
        """
        :return: 
        :rtype: redis.Redis
        """
        conn = redis.Redis(**self._params)
        if conn.ping():
            if self._with_key_prefix:
                return _RedisWrapper(conn, self._section)
            else:
                return _RedisWrapper(conn, "")
        return None

    def __str__(self):
        return json.dumps(self._params)


class SimpleQueue(object):
    """
        Redis simple queue
    """

    def __init__(self, queue_name, section=None, client=None):
        self._queue_name = queue_name
        assert section or client

        self._client_section = section
        self._client = client

    @property
    def client(self):
        if not self._client:
            self._client = connect(self._client_section)
        return self._client

    def push(self, data):
        s = TextUtils.json_dumps(data) if isinstance(data, (list, dict)) else TextUtils.to_string(data)
        return self.client.lpush(self._queue_name, s)

    def pop(self):
        return self.client.rpop(self._queue_name)

    def size(self):
        return self.client.llen(self._queue_name)


class RedisLock(object):

    def __init__(self, redis_client, timeout=10):
        self._redis_client = redis_client
        self._timeout = timeout

    def _get_lock(self, lock_key):
        """
        :param lock_key: 要锁订单key值
        :return: lock标识，释放锁或重入时需要以此作为身份标识，判断当前线程是持有锁的线程,若lock标识为None，说明未获得锁
        """
        try:
            lock_value = get_uuid()  # 唯一值，锁标识
            result = self._redis_client.set(lock_key, lock_value, ex=self._timeout, nx=True)
            if result:
                return lock_value
            else:
                return None
        except Exception as e:
            traceback.print_exc()
            return None

    def get_lock(self, lock_key, blocked=False):
        """
        :param lock_key:
        :param blocked: blocked=True时，通过一直重试实现阻塞等待
        :return:
        """
        if not lock_key:
            return True
        if blocked:
            while True:
                lock_value = self._get_lock(lock_key)
                if lock_value:
                    return lock_value
                else:
                    time.sleep(0.03)
        else:
            return self._get_lock(lock_key)

    def release_lock(self, lock_key, lock_value):
        if not lock_key:
            return True
        val = self._redis_client.get(lock_key)
        if lock_value is not None and bytes.decode(val) == lock_value:
            self._redis_client.delete(lock_key)
            return True
        else:
            return False


def lock_decorator(lock, lock_key_para):
    def decorator(func):
        def wrapper(*args,**kwargs):
            lock_key = kwargs[lock_key_para]
            try:
                lock_value = lock.get_lock(lock_key)
                if lock_value is None:
                    raise SimpleError(code=199, message="获取%s的锁失败" % lock_key)
                ret = func(*args, **kwargs)
                return ret
            except Exception as e:
                raise e
            finally:
                lock.release_lock(lock_key, lock_value)

        return wrapper

    return decorator
