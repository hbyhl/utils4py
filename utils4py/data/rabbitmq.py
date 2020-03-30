#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc: 
# FileName: rabbitmq.py
# Author:yhl
# Version:
# Last modified: 2019-12-12 18:59
import copy
import json
import multiprocessing
import random
import threading
import traceback

import pika
from pika.exceptions import AMQPError

from utils4py import ConfUtils

_rabbitmq_conf = ConfUtils.load_parser("data_source/rabbitmq.conf")

_client_pool = dict()  # key：配置名称，value:自己封装的rabbitmq client
_reuse_mutex = threading.RLock()


def connect_pool(section, settings_reuse_pool=True):
    """
    :param section:
    :rtype: SqlShell
    """
    if settings_reuse_pool:
        with _reuse_mutex:
            if section not in _client_pool:
                client_obj = _ConnectParams().init_with_section(section).connect()
                if client_obj:
                    _client_pool[section] = client_obj
            return _client_pool[section]
    else:
        return _ConnectParams().init_with_section(section).connect()


connect = connect_pool


class _ConnectParams(object):
    """
        rabbitmq
    """

    _default_params = {
        'host': "localhost",
        "port": 5672,
        "user": "",
        "password": "",
        "queue": "",
        "is_delay": "False",
        "durable": "True",  # 默认队列是永久保存的
        "delivery_mode": 2,  # 默认消息是要持久化的
        "virtual_host": "/"
    }

    def __init__(self):
        self._params = copy.deepcopy(_ConnectParams._default_params)
        self._section = None

    def init_with_section(self, section_name):
        self._section = section_name
        for k, v in _rabbitmq_conf.items(section_name):
            self._params[k] = v
        self._params['port'] = int(self._params['port'])
        self._params['delivery_mode'] = int(self._params['delivery_mode'])
        self._params['durable'] = eval(self._params['durable'])
        self._params['is_delay'] = eval(self._params['is_delay'])

        return self

    def connect(self):
        """
        :return:
        :rtype: _RabbitMQWorkQueueWrapper
        """
        if self._params.get('user'):
            user_pwd = pika.PlainCredentials(self._params.get('user'), self._params.get('password'))
            connection_parameters = pika.ConnectionParameters(host=self._params.get('host'), virtual_host=self._params['virtual_host'],
                                                              port=self._params['port'],
                                                              credentials=user_pwd, heartbeat=0)
        else:
            connection_parameters = pika.ConnectionParameters(host=self._params.get('host'), virtual_host=self._params['virtual_host'],
                                                              port=self._params['port'],
                                                              heartbeat=0)

        return _RabbitMQWorkQueueWrapper(connection_parameters, **self._params)

    def __str__(self):
        return json.dumps(self._params)


def connect_from_conf(conf_file_path):
    """
    :return:
    :rtype: _RabbitMQWorkQueueWrapper
    """
    _rabbitmq_conf = ConfUtils.load_parser(conf_file_path)
    _params = {
        'host': "localhost",
        "port": 5672,
        "user": "",
        "password": "",
        "queue": "",
        "is_delay": "False",
        "durable": "True",  # 默认队列是永久保存的
        "delivery_mode": 2,  # 默认消息是要持久化的
        "virtual_host": "/"
    }
    for k, v in _rabbitmq_conf.items('default'):
        _params[k] = v
    _params['port'] = int(_params['port'])
    _params['delivery_mode'] = int(_params['delivery_mode'])
    _params['durable'] = eval(_params['durable'])
    _params['is_delay'] = eval(_params['is_delay'])
    if _params.get('user'):
        user_pwd = pika.PlainCredentials(_params.get('user'), _params.get('password'))
        connection_parameters = pika.ConnectionParameters(host=_params.get('host'), virtual_host=_params['virtual_host'], port=_params['port'],
                                                          credentials=user_pwd, heartbeat=0)
    else:
        connection_parameters = pika.ConnectionParameters(host=_params.get('host'), virtual_host=_params['virtual_host'], port=_params['port'], heartbeat=0)
    return _RabbitMQWorkQueueWrapper(connection_parameters, **_params)


class _RabbitMQWorkQueueWrapper(object):
    """消费是非线程安全的，同一个对象不能用于多个进程或线程中"""
    send_lock = multiprocessing.Lock()
    consume_lock = multiprocessing.Lock()

    class _Message(object):
        def __init__(self, msg_delivery_tag, msg_body):
            self.msg_delivery_tag = msg_delivery_tag
            self.msg_body = msg_body

    def __init__(self, connection_parameters, **kwargs):
        self._connection_parameters = connection_parameters
        self._durable = kwargs.get('durable')
        self._queue_name = kwargs.get('queue')
        self._exchange_name = kwargs.get('queue')  # exchang 名称与队列名称保持一致
        self._routing_key = kwargs.get('queue')  # routing_key 名称与队列名称保持一致
        self._delivery_mode = kwargs.get('delivery_mode')
        self._is_delay = kwargs.get('is_delay')
        self._consume_queue_name = kwargs.get('queue')

        self._send_channel = None
        self._consume_channel = None

        self._has_init_send_channel = False
        self._has_init_consume_channel = False

        self._consumed_msg = None
        self._consumed_msg_status = 0  # 0：当前消息未本取走消费，1：表示消费中，

    def _init_send_channel(self):
        if not self._has_init_send_channel:
            self.send_lock.acquire()
            try:
                if not self._has_init_send_channel:
                    if not self._send_channel or not self._send_channel.connection or not self._send_channel.connection.is_open:
                        connection = pika.BlockingConnection(self._connection_parameters)
                    else:
                        connection = self._send_channel.connection
                    self._send_channel = connection.channel()
                    if self._is_delay:
                        self._delay_exchange_name = 'delay_' + self._exchange_name
                        self._delay_queue_name = 'delay_' + self._queue_name
                        # 设置延迟队列参数
                        arguments = {
                            'x-dead-letter-exchange': self._delay_exchange_name,  # 延迟结束后指向交换机（死信收容交换机）
                            'x-dead-letter-routing-key': self._delay_queue_name,  # 延迟结束后指向队列（死信收容队列）
                        }
                        # 配置发送channel
                        # 声明交换机
                        self._send_channel.exchange_declare(exchange=self._exchange_name, exchange_type='direct', durable=self._durable)
                        # 声明收容交换机
                        self._send_channel.exchange_declare(exchange=self._delay_exchange_name, exchange_type='fanout',
                                                            durable=self._durable)
                        # 声明队列
                        self._send_channel.queue_declare(queue=self._queue_name, durable=self._durable, arguments=arguments)
                        # 声明收容队列
                        self._send_channel.queue_declare(queue=self._delay_queue_name, durable=self._durable)

                        # 队列和交换机绑定
                        self._send_channel.queue_bind(exchange=self._exchange_name, queue=self._queue_name)
                        # 收容队列和收容交换机绑定
                        self._send_channel.queue_bind(exchange=self._delay_exchange_name, queue=self._delay_queue_name)
                    else:
                        # 配置发送channel
                        # 声明交换机
                        self._send_channel.exchange_declare(exchange=self._exchange_name, exchange_type='direct', durable=self._durable)
                        # 声明队列
                        self._send_channel.queue_declare(queue=self._queue_name, durable=self._durable)
                        # 队列和交换机绑定
                        self._send_channel.queue_bind(exchange=self._exchange_name, queue=self._queue_name)
                    self._has_init_send_channel = True
            finally:
                self.send_lock.release()

    def _init_consume_channel(self):
        if not self._has_init_consume_channel:
            self.consume_lock.acquire()
            try:
                if not self._has_init_consume_channel:
                    if not self._consume_channel or not self._consume_channel.connection or not self._consume_channel.connection.is_open:
                        connection = pika.BlockingConnection(self._connection_parameters)
                    else:
                        connection = self._consume_channel.connection
                    self._consume_channel = connection.channel()
                    if self._is_delay:
                        # 配置消费channel
                        self._consume_queue_name = 'delay_' + self._consume_queue_name
                        self._consume_channel.queue_declare(queue=self._consume_queue_name, durable=self._durable)
                    else:
                        # 配置消费channel
                        self._consume_channel.queue_declare(queue=self._consume_queue_name, durable=self._durable)
                    self._has_init_consume_channel = True
            finally:
                self.consume_lock.release()

    def send(self, msg, delay_time=1):
        """延迟队列的情况下，默认延迟1ms"""
        self._init_send_channel()
        try:
            if self._is_delay:
                properties = pika.BasicProperties(delivery_mode=self._delivery_mode, expiration=str(delay_time))
            else:
                properties = pika.BasicProperties(delivery_mode=self._delivery_mode)

            self._send_channel.basic_publish(exchange=self._exchange_name,  # 交换机
                                             routing_key=self._routing_key,
                                             properties=properties,
                                             body=msg)  # 生产者要发送的消息
            return True
        except AMQPError as e:
            traceback.print_exc()
            self._has_init_send_channel = False
            raise e

    def tx_send(self, msg, delay_time=1):
        """延迟队列的情况下，默认延迟1ms"""
        self._init_send_channel()
        if self._is_delay:
            properties = pika.BasicProperties(delivery_mode=self._delivery_mode, expiration=str(delay_time))
        else:
            properties = pika.BasicProperties(delivery_mode=self._delivery_mode)
        # 开启事务
        self._send_channel.tx_select()
        try:
            self._send_channel.basic_publish(exchange=self._exchange_name,  # 交换机
                                             routing_key=self._routing_key,
                                             properties=properties,
                                             body=msg)  # 生产者要发送的消息
            self._send_channel.tx_commit()
            return True
        except AMQPError as e:
            traceback.print_exc()
            self._has_init_send_channel = False
            self._send_channel.tx_rollback()
            raise e
        except Exception as e2:
            self._send_channel.tx_rollback()
            raise e2

    def serial_confirm_send(self, msg, delay_time=1):
        """延迟队列的情况下，默认延迟1ms"""
        self._init_send_channel()
        if self._is_delay:
            properties = pika.BasicProperties(delivery_mode=self._delivery_mode, expiration=str(delay_time))
        else:
            properties = pika.BasicProperties(delivery_mode=self._delivery_mode)
        try:
            # 开启确认机制
            if not self._send_channel._delivery_confirmation:
                self._send_channel.confirm_delivery()

            self._send_channel.basic_publish(exchange=self._exchange_name,  # 交换机
                                             routing_key=self._routing_key,  # 路由键，写明将消息发往哪个队列
                                             properties=properties,
                                             body=msg)  # 生产者要发送的消息
            return True
        except AMQPError as e:
            traceback.print_exc()
            self._has_init_send_channel = False
            raise e

    def recv_msg(self):
        self._init_consume_channel()
        if self._consumed_msg_status == 0:
            # 获取消息
            try:
                response = self._consume_channel.basic_get(queue=self._consume_queue_name)
                if response[0] is not None:
                    msg_delivery_tag = response[0].delivery_tag
                    msg_body = bytes.decode(response[2])
                    self._consumed_msg = _RabbitMQWorkQueueWrapper._Message(msg_delivery_tag, msg_body)
                    self._consumed_msg_status = 1
                    return msg_body
            except:
                traceback.print_exc()
                self._consumed_msg = None
                self._consumed_msg_status = 0

        return None

    def del_msg(self):
        """消费成功后删除消息"""
        if self._consumed_msg_status == 0:
            return
        try:
            self._consume_channel.basic_ack(delivery_tag=self._consumed_msg.msg_delivery_tag)
        finally:
            self._consumed_msg = None
            self._consumed_msg_status = 0

    def re_in_queue_msg(self, msg):
        """消费失败后，消息重新入队，以待下次消费"""
        try:
            res_status = False
            for i in range(3):
                try:
                    res_status = self.serial_confirm_send(msg)
                    if res_status:
                        break
                except Exception as e:
                    traceback.print_exc()
                    if i == 2:
                        break
            if res_status:
                self._consume_channel.basic_ack(delivery_tag=self._consumed_msg.msg_delivery_tag)
            else:
                self._consume_channel.basic_nack(delivery_tag=self._consumed_msg.msg_delivery_tag)
        finally:
            self._consumed_msg = None
            self._consumed_msg_status = 0
