#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: simple_consume.py
# Author:yhl
# Version:
# Last modified: 2019-12-12 16:12
import abc
import json
import logging
import random
import time
import traceback
from contextlib import contextmanager

import numpy as np

from utils4py.comsume import BaseModel
from utils4py.data import connect_rabbitmq
from utils4py.formate import format_to_json


class SimpleBasicConsumer(object):
    """
        Simple Basic Consumer
    """

    DEFAULT_LOOP_INTERVAL = 50 / 1000.0

    def __init__(self, **kwargs):
        """
            _loop_interval:当未获取到数据时sleep段时间，重新循环执行，此参数指sleep 时间
            _logger:用于打印日志的logger client
            _max_loop:指定循环消费次数，默认为无限
        """
        self._loop_interval = kwargs.get("loop_interval", SimpleBasicConsumer.DEFAULT_LOOP_INTERVAL)
        self._logger = kwargs.get("logger", None) or logging
        self._max_loop = kwargs.get("max_loop", 0)
        self._need_sample_log = kwargs.get("need_sample_log", False)


    @abc.abstractmethod
    @contextmanager
    def recv_msg(self):
        pass

    @abc.abstractmethod
    def exec(self, model):
        """
            处理消息，model的model.obj_message保存的是消息内容
            可调用model的add_trace方法将要打印的日志信息（k：v）暂存起来
            :return True 处理成功，后续流程会删除消息，False ：处理失败，后续会将消息重新入队
        """
        pass

    def pre_exec(self, model):
        """处理消息前准备，及对消息的预处理"""
        return True

    def after_exec(self, model):
        return True

    def success(self, model):
        pass

    def fail(self, model):
        pass

    @property
    def logger(self):
        return self._logger

    @property
    def pause(self):
        return getattr(self, "_pause_", False)

    @pause.setter
    def pause(self, value):
        setattr(self, '_pause_', bool(value))

    def trace(self, model):
        """
        write trace info into log

        :param model:
        :return:
        """
        # if len(model.trace.items()) > 0:
        #     self._logger.info("\t".join(map(
        #         lambda x: "{}={}".format(*tuple(map(utils4py.TextUtils.to_string, x))),
        #         model.trace.items()
        #     )))
        try:
            if model and len(model.trace.items()) > 0:
                log_str = format_to_json(model.trace)
                self._logger.info(log_str)
                if self._need_sample_log and random.randint(0, 99) < 10:
                    self._logger.warning(log_str)

        except:
            traceback.print_exc()

    def init(self):
        """一些run方法内需要使用的对象，在此方法内实例化"""
        pass

    def run(self):
        """
        Run process

        :return:
        """
        loop = 0
        self.init()

        while not self.pause:
            if 0 < self._max_loop <= loop:
                break
            model = None
            try:
                with self.recv_msg() as item:
                    if not item:
                        time.sleep(self._loop_interval)
                        continue
                    # 打印消息内容
                    # loop += 1
                    start_time = time.time()
                    model = BaseModel()
                    model.set_message(item)
                    self.pre_exec(model)
                    exec_result = self.exec(model)
                    if exec_result:
                        model.add_trace('result', 'sucess')
                        self.success(model)
                    else:
                        model.add_trace('result', 'failed')
                        self.fail(model)
                    # 执行完毕，输出处理结果日志。开始下一轮任务
                    endtime = time.time()
                    cost = int((endtime - start_time) * 1000)
                    model.add_trace('cost', cost)
            except Exception as err:
                self._logger.error(traceback.format_exc())
                try:
                    model.add_trace('result', 'exception')
                    model.add_trace("error_msg", str(err))
                    self.fail(model)
                except:
                    self._logger.error(traceback.format_exc())
            self.trace(model)
        pass

    pass


class RabbitMQWorkQueueConsumer(SimpleBasicConsumer):
    def __init__(self, conf_section=None, **kwargs):
        SimpleBasicConsumer.__init__(self, **kwargs)
        self._conf_section = conf_section

    def init(self):
        if self._conf_section:
            self._rabbit_client = connect_rabbitmq(self._conf_section, settings_reuse_pool=False)

    @contextmanager
    def recv_msg(self):
        yield self._rabbit_client.recv_msg()
        return

    def exec(self, model):
        print(model.raw_message)
        result = np.random.randint(0, 2)
        return result

    def success(self, model):
        self._rabbit_client.del_msg()

    def fail(self, model):
        self._rabbit_client.re_in_queue_msg(model.raw_message)


class ManualCommitKafkaConsumer(SimpleBasicConsumer):

    def __init__(self, *topics, **kwargs):
        """
        :param topics: 要消费的topics
        :param kwargs: group_id:消费者组id，bootstrap_servers kafka集群能够提供metadata的broker 李彪
        """
        SimpleBasicConsumer.__init__(self, **kwargs)
        self._topics = topics
        self._group_id = kwargs.get('group_id', None)
        self._bootstrap_servers = kwargs.get('bootstrap_servers', ['127.0.0.1:9092'])
        self._consumer_timeout_ms = kwargs.get('consumer_timeout_ms', -1)

    def init(self):
        from kafka import KafkaConsumer
        self._consumer = KafkaConsumer(*self._topics, group_id=self._group_id, bootstrap_servers=self._bootstrap_servers, enable_auto_commit=False,
                                       consumer_timeout_ms=self._consumer_timeout_ms)

    def pre_exec(self, model):
        """处理消息前准备，及对消息的预处理"""
        # 将msg中的topic，分区信息放到trace中，供后续打印
        kafka_msg = model.raw_message
        model.add_trace('topic', kafka_msg.topic)
        model.add_trace('partition', kafka_msg.partition)
        model.add_trace('offset', kafka_msg.offset)
        model.add_trace('key', kafka_msg.key)
        model.add_trace('value', str(kafka_msg.value))
        return True

    @contextmanager
    def recv_msg(self):
        for message in self._consumer:
            yield message
            break

    def exec(self, model):
        print(model.raw_message)
        result = np.random.randint(0, 2)
        return result

    def success(self, model):
        from kafka import TopicPartition, OffsetAndMetadata

        kafka_msg = model.raw_message
        self._consumer.commit({TopicPartition(kafka_msg.topic, kafka_msg.partition): OffsetAndMetadata(kafka_msg.offset + 1, "")})
