#!/usr/bin/env python
# -*- coding: utf-8 -*-

import six

from utils4py.flask_ext.errors import ParamError, SimpleError
from utils4py.s import TextUtils


class ErrUtils(object):
    """
        Error Utilities
    """

    err_code_parameter = 100  # parameter error
    err_code_unknown = 1000  # unknown error

    @classmethod
    def build_error(cls, code, message=None):
        return SimpleError(code, message)

    @classmethod
    def get_code(cls, err):
        """
        
        :param Exception err: 
        :return: 
        """
        code = None
        if isinstance(err, SimpleError):
            code = err.code
        elif err.args and isinstance(err.args, (tuple, list)) and len(err.args) > 0:
            code = err.args[0]

        if isinstance(code, six.integer_types):
            return code
        try:
            return int(code)
        except (Exception,):
            return cls.err_code_unknown

    @classmethod
    def get_message(cls, err):
        """
        :param Exception err: 
        :return: 
        """

        if isinstance(err, SimpleError):
            return TextUtils.to_string(err.message)

        if err.args and isinstance(err.args, (tuple, list)) and len(err.args) > 1:
            return TextUtils.to_string(err.args[1])
        return TextUtils.to_string(err)

    @classmethod
    def build_parameter_error(cls, message=None):
        return ParamError(cls.err_code_parameter, message)

