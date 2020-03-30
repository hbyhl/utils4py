#!/usr/bin/env python
# -*- coding: utf-8 -*-
from utils4py.flask_ext.err import ErrUtils
from utils4py.flask_ext.service import ResultBuilder


def adapt(**kwargs):
    if 'key_error_code' in kwargs:
        ResultBuilder.KEY_ERROR_CODE = kwargs['key_error_code']
    if 'key_error_message' in kwargs:
        ResultBuilder.KEY_ERROR_MESSAGE = kwargs['key_error_message']
    if 'key_result_data' in kwargs:
        ResultBuilder.KEY_RESULT_DATA = kwargs['key_result_data']
    if 'err_code_ok' in kwargs:
        ResultBuilder.ERROR_CODE_OK = kwargs['err_code_ok']
    if 'err_code_parameter' in kwargs:
        ErrUtils.err_code_parameter = kwargs['err_code_parameter']
    if 'err_code_unknown' in kwargs:
        ErrUtils.err_code_unknown = kwargs['err_code_unknown']
    return
