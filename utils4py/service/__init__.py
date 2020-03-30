#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import logging
import traceback

from six import add_metaclass, iteritems

import utils4py
from utils4py.errors import SimpleError
from utils4py.mixin import ArgMixin, ErrMixin


class ResultBuilder(object):
    """
        Result builder
    """

    ERROR_CODE_OK = 0

    KEY_ERROR_CODE = "errno"
    KEY_ERROR_MESSAGE = "msg"
    KEY_RESULT_DATA = "data"

    @classmethod
    def build(cls, code, message=None, data=None, appends=None):
        ret = {cls.KEY_ERROR_CODE: code, cls.KEY_ERROR_MESSAGE: message or ""}
        if data:
            ret[cls.KEY_RESULT_DATA] = data

        if appends and isinstance(appends, dict):
            for k, v in iteritems(appends):
                if k == cls.KEY_RESULT_DATA or k == cls.KEY_ERROR_CODE or k == cls.KEY_ERROR_MESSAGE:
                    continue
                ret[k] = v

        return ret


@add_metaclass(abc.ABCMeta)
class BaseService(ErrMixin, ArgMixin):
    """
        base service 
    """

    def __init__(self, **kwargs):
        self._logger = kwargs.get('logger') or logging
        pass

    @property
    def logger(self):
        return self._logger or logging

    @abc.abstractmethod
    def run(self, *args, **kwargs):
        pass

    def check_args(self, *args, **kwargs):
        pass

    def mock_run(self, *args, **kwargs):
        id(self), id(args), id(kwargs)
        return 0

    @classmethod
    def format_result(cls, result):
        return result

    def init(self, *args, **kwargs):
        if 'logger' in kwargs:
            self._logger = kwargs.get('logger') or logging

        try:
            self.check_args(*args, **kwargs)
        except Exception as err:
            if isinstance(err, SimpleError):
                raise err
            raise self.build_parameter_error(str(err))

    def execute(self, *args, **kwargs):

        try:
            self.init(*args, **kwargs)
            result, appends = None, None

            r = None
            for _ in range(0, 1):
                if utils4py.env.is_debug():
                    r = self.mock_run(*args, **kwargs)  # pylint: disable=E1111
                    if r:
                        break
                r = self.run(*args, **kwargs)
                break

            if r and isinstance(r, tuple):
                result = r[0] if len(r) > 0 else None
                appends = r[1] if len(r) > 1 else None
            else:
                result = r

            if result:
                result = self.format_result(result)

            return ResultBuilder.build(ResultBuilder.ERROR_CODE_OK, data=result, appends=appends)

        except Exception as err:
            self.logger.error(traceback.format_exc())
            code = self.get_code(err)
            msg = self.get_message(err)
            return ResultBuilder.build(code, message=msg)

        pass

    pass


pass
