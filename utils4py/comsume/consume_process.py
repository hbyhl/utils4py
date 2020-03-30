#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc: 
# FileName: consume_process.py
# Author:yhl
# Version:
# Last modified: 2019-12-13 12:07
import abc
import logging
import multiprocessing
import os
import threading
import time

import six

from utils4py.comsume.simple_consume import SimpleBasicConsumer


@six.add_metaclass(abc.ABCMeta)
class ComponetConsumerProcess(multiprocessing.Process):
    """
        multi processor
    """

    SIG_STOP = "stop"

    def __init__(self, consumer, **kwargs):
        multiprocessing.Process.__init__(self)
        self._pipe = kwargs.get("pipe", None)
        if isinstance(consumer, SimpleBasicConsumer):
            self._consumer = consumer
        else:
            raise ("[%s] is not an instance of Consumer" % consumer)

    def run(self):

        logging.info("start sub process = %s", os.getpid())

        def _listen():
            while not self._consumer.pause and self._pipe:
                sig = self._pipe.recv()
                if sig == self.SIG_STOP:
                    self._consumer = True
                else:
                    time.sleep(self._consumer.DEFAULT_LOOP_INTERVAL)

        t = threading.Thread(target=_listen)
        t.start()
        self._consumer.run()
        t.join()

        logging.info("sub process = %s, Consumer quit ok ", os.getpid())
