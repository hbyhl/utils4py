#!usr/bin/env python
# -*- coding:utf-8 _*-

# Desc: 
# FileName: rabbitmq.py
# Author:yhl
# Version:
# Last modified: 2019-12-12 18:59
import copy
import json
import threading
from queue import Queue

import pika

from utils4py import ConfUtils

settings_reuse_pool = True

_rabbitmq_conf = ConfUtils.load_parser("data_source/rabbitmq.conf")

_client_pool = dict() #key：配置名称，value:自己封装的rabbitmq client
_reuse_mutex = threading.RLock()


def connect_pool(section):
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
        'host'    : "localhost",
        "port"    : 5672,
        "user"    : "",
        "password": "",
        "queue"   : "",
        "durable" : True, # 默认队列是永久保存的
        #下面3个是发送消息需要的配置
        "exchange" : "",
        "delivery_mode" : 2, #默认消息是要持久化的
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
        self._params['durable'] = int(self._params['durable'])
        return self

    def connect(self):
        """
        :return:
        :rtype: redis.Redis
        """
        if self._params.get('user'):
            user_pwd = pika.PlainCredentials(self._params.get('user'), self._params.get('password'))
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self._params.get('host'),credentials=user_pwd))
        else:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self._params.get('host')))
        queue_params = {
            "queue":self._params.get('queue'),
            "durable":self._params.get('durable')
        }
        send_params = {
            "exchange" : self._params.get('exchange'),
            "delivery_mode" : self._params.get('delivery_mode'),
        }
        consume_params={
            "prefetch_count" : self._params.get('prefetch_count'),
            "auto_ack" : self._params.get('auto_ack'),
        }
        return _RabbitMQWorkQueueWrapper(connection,queue_params,send_params,consume_params)

    def __str__(self):
        return json.dumps(self._params)

class _RabbitMQWorkQueueWrapper(object):
    """非线程安全的"""
    class _Message(object):
        def __init__(self,msg_delivery_tag,msg_body):
            self.msg_delivery_tag = msg_delivery_tag
            self.msg_body = msg_body

    def __init__(self,connection,queue_params,send_params,consume_params):
        self._connection = connection
        self._queue_params = queue_params
        self._send_params = send_params
        self._consume_params = consume_params
        self._send_channel = self._connection.channel()
        self._consume_channel = self._connection.channel()
        self._send_channel.queue_declare(queue=self._queue_params.get('queue'),durable=self._queue_params.get('durable'))
        self._consume_channel.queue_declare(queue=self._queue_params.get('queue'),durable=self._queue_params.get('durable'))

        self._consume_thread = None
        self._msg_queue = Queue(1)
        self._consumed_msg = None
        self._consumed_msg_status = 0 # 0：当前消息未本取走消费，1：表示消费中，
        self._consumed_msg_lock = threading.RLock


    def send(self,msg):
        self._send_channel.basic_publish(exchange=self._send_params.get('exchange'),  #交换机
                                    routing_key=self._queue_params.get('queue'),#路由键，写明将消息发往哪个队列
                                    properties=pika.BasicProperties(delivery_mode = self._send_params.get('delivery_mode')),
                                    body=msg)#生产者要发送的消息

    def tx_send(self,msg):
        # 开启事务
        self._send_channel.tx_select()
        try:
            self._send_channel.basic_publish(exchange=self._send_params.get('exchange'),  #交换机
                                             routing_key=self._send_params.get('routing_key'),#路由键，写明将消息发往哪个队列
                                             properties=pika.BasicProperties(delivery_mode = self._send_params.get('delivery_mode')),
                                             body=msg)#生产者要发送的消息
            self._send_channel.tx_commit()
            return True
        except:
            self._send_channel.tx_rollback()
            return False
        pass

    def recv_msg(self):

        if self._consumed_msg_status == 0:
            self._consumed_msg_status =1
            #获取消息
            response = self._consume_channel.basic_get(queue = self._queue_params.get('queue'))
            if response[0] is not None:
                msg_delivery_tag = response[0].delivery_tag
                msg_body = bytes.decode(response[2])
                self._consumed_msg = _RabbitMQWorkQueueWrapper._Message(msg_delivery_tag,msg_body)
                return msg_body
            return None
        else:
            return None

    def del_msg(self):
        """消费成功后删除消息"""
        if self._consumed_msg_status == 0:
            return
        self._consume_channel.basic_ack(delivery_tag=self._consumed_msg.msg_delivery_tag)
        self._consumed_msg = None
        self._consumed_msg_status = 0

    def re_in_queue_msg(self):
        """消费失败后，消息重新入队，以待下次消费"""
        self._consume_channel.basic_nack(delivery_tag=self._consumed_msg.msg_delivery_tag)
        self._consumed_msg = None
        self._consumed_msg_status = 0







