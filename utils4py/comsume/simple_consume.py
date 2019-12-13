#!usr/bin/env python
# -*- coding:utf-8 _*-

# Desc:
# FileName: simple_consume.py
# Author:yhl
# Version:
# Last modified: 2019-12-12 16:12
import abc
import logging
import time
import traceback

import numpy as np

import utils4py
from utils4py.comsume import BaseModel
from utils4py.data import connect_rabbitmq

class Consumer(object):
    def run(self):
        pass

class SimpleBasicConsumer(Consumer):
    """
        Simple Basic Consumer
    """

    DEFAULT_LOOP_INTERVAL = 50 / 1000.0


    def __init__(self, **kwargs):
        """
            _loop_interval:当未获取到数据时sleep段时间，重新循环执行，此参数指sleep 时间
            _trace_logger:用于打印日志的logger client
            _max_loop:指定循环消费次数，默认为无限
        """
        self._loop_interval = kwargs.get("loop_interval", SimpleBasicConsumer.DEFAULT_LOOP_INTERVAL)
        self._trace_logger = kwargs.get("trace_logger", None) or logging
        self._max_loop = kwargs.get("max_loop", 0)


    @abc.abstractmethod
    def recv_msg(self):
        pass

    @abc.abstractmethod
    def exec(self,model):
        pass

    def pre_exec(self,model):
        return True
    def after_exec(self,model):
        return True

    def success(self,model):
        pass
    def fail(self,model):
        pass

    @property
    def trace_logger(self):
        return self._trace_logger


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
        self.trace_logger.info("\t".join(map(
            lambda x: "{}={}".format(*tuple(map(utils4py.TextUtils.to_string, x))),
            model.trace.items()
        )))
        return

    def run(self):
        """
        Run process

        :return:
        """
        loop = 0

        while not self.pause:
            if 0 < self._max_loop <= loop:
                break
            item = self.recv_msg()
            if not item:
                time.sleep(self._loop_interval)
                continue
            loop += 1
            model = BaseModel()
            model.set_message(item)
            try:
                exec_result = self.exec(model)
                if exec_result:
                    self.success(model)
                else:
                    self.fail(model)
            except Exception as err:
                self.trace_logger.error(traceback.format_exc())
                model.add_trace("exception", err)

            # 执行完毕，开始下一轮任务
            self.trace(model)

        pass

    pass

class RabbitMQWorkQueueConsumer(SimpleBasicConsumer):
    #持有
    def __init__(self,conf_section,**kwargs):
        SimpleBasicConsumer.__init__(self,**kwargs)
        self._rabbit_client = connect_rabbitmq(conf_section)

    def recv_msg(self):
        return self._rabbit_client.recv_msg()
    def exec(self,model):
        print(model.raw_message)
        result = np.random.randint(0,2)
        return result
    def success(self,model):
        self._rabbit_client.del_msg()
    def fail(self,model):
        self._rabbit_client.re_in_queue_msg()
