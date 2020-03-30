#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import inspect
import logging

import flask
import six
from six.moves import map, reduce

import utils4py.scan


@six.add_metaclass(abc.ABCMeta)
class BaseFilter(object):
    """
        define flask filter
    """

    def __init__(self, app, **kwargs):
        """
        :param flask.Flask app: 
        """
        self.app = app
        self.logger = kwargs.get('logger') or logging
        self.init()

    def init(self):
        pass

    def before_request(self, *args, **kwargs):
        """在请求收到之前绑定一个函数做一些事情"""
        pass

    def after_request(self, response, *args, **kwargs):
        """每一个请求之后绑定一个函数，如果请求没有异常"""
        # 必须返回response，否则会导致response为None，导致异常
        return response

    def teardown_request(self, *args, **kwargs):
        """每一个请求之后绑定一个函数，即使遇到了异常。"""
        pass

    def __call__(self, *args, **kwargs):
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
        self.app.teardown_request(self.teardown_request)

        return


def _scan_filters(path):
    filters = []
    for mod in utils4py.scan.walk_modules(path):
        for attr_name in vars(mod):  # type: str
            if attr_name.startswith('_') or not attr_name[0].isupper():
                continue

            filter_cls = getattr(mod, attr_name, None)  # type: BaseFilter
            try:
                assert filter_cls, 'must not by empty'
                assert inspect.isclass(filter_cls), 'must be class'
                assert issubclass(filter_cls, BaseFilter), 'must be sub class of BaseFilter'
                assert filter_cls is not BaseFilter, 'must not be BaseFilter'
                assert filter_cls.__module__ == mod.__name__, 'must be defined in this module'
                filters.append(filter_cls)
            except AssertionError:
                continue
    return filters


def init_filters(app, filters=None, paths=None, **kwargs):
    """
    init filters 

    :param flask.Flask app: 
    :param list filters: 
    :param list paths:
    :param kwargs: 
    :return: 
    """

    registered_map = dict()

    def _register(filter_classes):
        if not filter_classes:
            return
        for cls_filter in filter_classes:
            if not inspect.isclass(cls_filter) or not issubclass(cls_filter, BaseFilter) \
                    or cls_filter is BaseFilter:
                continue
            cls_id = id(cls_filter)
            if cls_id in registered_map:
                continue
            cls_filter(app, **kwargs)()
            str_name = "{}".format(cls_filter.__module__)
            logging.debug("\tRegistered Filter ok, name = %-50s", str_name)
            registered_map[id(cls_filter)] = cls_filter
        return

    _register(filters)

    if paths and isinstance(paths, list):
        other_filters = reduce(lambda x, y: x + y, map(_scan_filters, paths))
        _register(other_filters)

    logging.info("\tRegistered %d filters", len(registered_map))
    return
