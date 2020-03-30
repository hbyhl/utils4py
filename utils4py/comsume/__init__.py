#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import logging
import multiprocessing
import os
import signal
import threading
import time
import traceback

import six

import utils4py

# function flag
_FLAG_PREPARE = "_flag_prepare"
_FLAG_ON_POP = "_flag_on_pop"
_FLAG_EXECUTE = "_flag_execute"
_FLAG_ON_SUCC = "_flag_on_success"
_FLAG_ON_FAIL = "_flag_on_fail"

_FLAG_LIST = [
    _FLAG_PREPARE,
    _FLAG_ON_POP,
    _FLAG_EXECUTE,
    _FLAG_ON_SUCC,
    _FLAG_ON_FAIL,
]

# execute sequence flag
_FLAG_INDEX = "_flag_index"


class BaseModel(object):
    """
        Base Model
    """

    def __init__(self):
        self.raw_message = ""
        self.obj_message = None
        self.context = dict()
        self.trace = dict()

    def add_trace(self, k, v):
        self.trace[k] = v

    def add_context(self, k, v):
        self.context[k] = v

    def get_context(self, k):
        return self.context.get(k)

    def set_message(self, raw_message):
        if not self.raw_message and raw_message:
            self.raw_message = raw_message
            try:
                self.obj_message = utils4py.TextUtils.json_loads(raw_message)
            except (Exception,):
                traceback.print_exc()
                pass


class BasicConsumer(object):
    """
        Basic Consumer
    """

    DEFAULT_LOOP_INTERVAL = 50 / 1000.0

    class D(object):  # 装饰器工具集

        @classmethod
        def prepare(cls):
            """
            从队列取数据前，准备现场
            :return: 
            """

            def _(func):
                if callable(func):
                    setattr(func, _FLAG_PREPARE, True)
                    setattr(func, _FLAG_INDEX, 1)
                return func

            return _

        @classmethod
        def after_pop(cls, **kwargs):
            """
            从队列取数据之后，标记状态，数据格式转换，写入临时区等工作
            可以有多个，按照index的顺序执行

            :param kwargs: 
            :return: 
            """
            idx = kwargs.get("index", 1)

            def _(func):
                if callable(func):
                    setattr(func, _FLAG_ON_POP, True)
                    setattr(func, _FLAG_INDEX, idx)
                return func

            return _

        @classmethod
        def execute(cls, **kwargs):
            """
            具体执行工作，可以有多个，按照index顺序执行

            :param kwargs: 
            :return: 
            """
            idx = kwargs.get("index", 1)

            def _(func):
                if callable(func):
                    setattr(func, _FLAG_EXECUTE, True)
                    setattr(func, _FLAG_INDEX, idx)
                return func

            return _

        @classmethod
        def success(cls, **kwargs):
            """
            任务执行成功后操作，可以有多个，按照index顺序执行

            :param kwargs: 
            :return: 
            """
            idx = kwargs.get("index", 1)

            def _(func):
                if callable(func):
                    setattr(func, _FLAG_ON_SUCC, True)
                    setattr(func, _FLAG_INDEX, idx)
                return func

            return _

        @classmethod
        def fail(cls, **kwargs):
            """
            执行失败后操作，可以有多个，按照顺序执行
            :param kwargs: 
            :return: 
            """
            idx = kwargs.get("index", 1)

            def _(func):
                if callable(func):
                    setattr(func, _FLAG_ON_FAIL, True)
                    setattr(func, _FLAG_INDEX, idx)
                return func

            return _

    @classmethod
    def __default_prepare(cls):
        return BaseModel()

    @classmethod
    def __build_func_dict(cls, obj):
        assert isinstance(obj, BasicConsumer)
        tmp_dict = dict()
        for attr_name in dir(obj):
            if str.startswith(attr_name, "__"):
                continue
            func = getattr(obj, attr_name)
            if not func or not callable(func):
                continue

            for flag in _FLAG_LIST:
                if getattr(func, flag, None) is not True:
                    continue

                idx = getattr(func, _FLAG_INDEX, 1)
                if flag not in tmp_dict:
                    tmp_dict[flag] = list()
                tmp_dict[flag].append((idx, func))

        fc_dict = {
            k: [item[1] for item in sorted(v, key=lambda x: x[0])]
            for k, v in tmp_dict.items()
        }

        if _FLAG_PREPARE not in fc_dict:
            fc_dict[_FLAG_PREPARE] = [BasicConsumer.__default_prepare]

        assert len(fc_dict[_FLAG_PREPARE]) == 1, 'More than one prepare method registered'

        return fc_dict

    def __init__(self, **kwargs):
        self._loop_interval = kwargs.get("loop_interval", BasicConsumer.DEFAULT_LOOP_INTERVAL)
        self._trace_logger = kwargs.get("trace_logger", None) or logging
        self._max_loop = kwargs.get("max_loop", 0)

    def _init(self):
        if not getattr(self, '_loaded_', None):
            self._func_dict = BasicConsumer.__build_func_dict(self)
            self._func_prepare = self._func_dict[_FLAG_PREPARE][0]
            setattr(self, "_loaded_", True)
        return

    @abc.abstractmethod
    def init_queue(self):
        pass

    @property
    def trace_logger(self):
        return self._trace_logger

    @property
    def queue(self):
        return getattr(self, '_queue_', None)

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
        self._init()
        setattr(self, '_queue_', self.init_queue())

        loop = 0

        while not self.pause:
            if 0 < self._max_loop <= loop:
                break

            item = self.queue.pop()
            if not item:
                time.sleep(self._loop_interval)
                continue

            loop += 1
            model = self._func_prepare()  # type:BaseModel
            model.set_message(item)

            try:
                # after pop
                for on_ap in self._func_dict.get(_FLAG_ON_POP, []):
                    on_ap(model)

                # execute
                for exe in self._func_dict.get(_FLAG_EXECUTE, []):
                    exe(model)

                # on succ
                for on_succ in self._func_dict.get(_FLAG_ON_SUCC, []):
                    on_succ(model)

                # 执行成功，开始下一轮任务
                self.trace(model)
                continue

            except Exception as err:
                self.trace_logger.error(traceback.format_exc())
                model.add_trace("exception", err)

            # 执行失败，处理失败信息
            for on_fail in self._func_dict.get(_FLAG_ON_FAIL, []):
                on_fail(model)

            self.trace(model)
            continue


@six.add_metaclass(abc.ABCMeta)
class MultiConsumer(multiprocessing.Process, BasicConsumer):
    """
        multi processor
    """

    SIG_STOP = "stop"

    def __init__(self, **kwargs):
        multiprocessing.Process.__init__(self)
        BasicConsumer.__init__(self, **kwargs)
        self._pipe = kwargs.get("pipe", None)

    def run(self):

        logging.info("start sub process = %s", os.getpid())

        def _listen():
            while not self.pause and self._pipe:
                sig = self._pipe.recv()
                if sig == self.SIG_STOP:
                    self.pause = True
                else:
                    time.sleep(self.DEFAULT_LOOP_INTERVAL)

        t = threading.Thread(target=_listen)
        t.start()
        BasicConsumer.run(self)
        t.join()

        logging.info("sub process = %s, Consumer quit ok ", os.getpid())



class Controller(object):
    """
        Controller
    """

    def __init__(self, consume_cls, trace_logger, num=0):
        self.message_pipe_list = list()
        self.consumer_list = list()
        self.pause = False
        self.consume_cls = consume_cls
        self.trace_logger = trace_logger
        self.num = num or multiprocessing.cpu_count()

        signal.signal(signal.SIGINT, self.safe_shutdown)
        signal.signal(signal.SIGHUP, self.safe_shutdown)
        signal.signal(signal.SIGTERM, self.safe_shutdown)

    def safe_shutdown(self, *args):
        logging.warning("capture sig = %s ......", args[0])
        if self.message_pipe_list:
            for pipe in self.message_pipe_list:
                pipe.send(MultiConsumer.SIG_STOP)
        self.pause = True
        return

    def start(self):

        logging.info("pid  = %s", os.getpid())
        consumers = list()
        pipes = list()
        for i in range(multiprocessing.cpu_count()):
            p = multiprocessing.Pipe()
            mc = self.consume_cls(max_loop=0, trace_logger=self.trace_logger, pipe=p[0])
            mc.daemon = True
            consumers.append(mc)
            pipes.append(p[1])

        self.consumer_list = consumers
        self.message_pipe_list = pipes

        for mc in consumers:
            mc.start()
            logging.info("start a consumer")

        # logging.info("pid %s get here ", os.getpid())
        for mc in consumers:
            mc.join()

        # logging.info("pid %s right here ", os.getpid())
        while not self.pause:
            continue
        logging.info("process = %d ,quite main ok", os.getpid())
