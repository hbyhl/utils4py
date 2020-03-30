#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: base_enum.py
# Author:yhl
# Version:
# Last modified: 2019-12-30 13:43
import enum


class BaseEnum(enum.Enum):
    def __init__(self, code, msg):
        self._code = code
        self._msg = msg

    @property
    def code(self):
        return self._code

    @property
    def msg(self):
        return self._msg

    @classmethod
    def trans_dict(cls):
        code_map = {}
        for name, member in cls.__members__.items():
            code_map[member.code] = member.msg
        return code_map
