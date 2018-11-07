#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import decimal
import hashlib
import json

import six


class TextUtils(object):
    """
        Text utilities
    """

    class _JSONEncoder(json.JSONEncoder):
        """
            default json encoder handle datetime
        """

        def default(self, o):  # pylint: disable=E0202
            if isinstance(o, decimal.Decimal):
                return float(o)
            if isinstance(o, datetime.datetime):
                return o.strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(o, datetime.date):
                return o.strftime('%Y-%m-%d')
            return json.JSONEncoder.default(self, o)

        pass

    @classmethod
    def to_string(cls, value):
        if isinstance(value, six.text_type):
            return value.encode('utf8')
        if isinstance(value, six.string_types):
            return value
        if isinstance(value, Exception):
            return cls.to_string(value.args)
        if value is None:
            return ""
        return str(value)

    @classmethod
    def json_dumps(cls, val, indent=None, encoder_cls=None, separators=None, ensure_ascii=None, sort_keys=None):
        kwargs = {'cls': encoder_cls if encoder_cls else cls._JSONEncoder}
        if isinstance(indent, six.integer_types) and indent > 0:
            kwargs['indent'] = indent
        if ensure_ascii is not None:
            kwargs['ensure_ascii'] = ensure_ascii

        if sort_keys is not None:
            kwargs['sort_keys'] = sort_keys

        if separators is not None:
            kwargs['separators'] = separators
        else:
            kwargs['separators'] = (',', ':')

        return json.dumps(val, **kwargs)

    @classmethod
    def json_loads(cls, val):
        if isinstance(val, six.string_types):
            return json.loads(val)
        return json.load(val)

    @classmethod
    def md5_string(cls, val):
        if isinstance(val, six.text_type):
            return hashlib.md5(val.encode('utf8')).hexdigest()
        return hashlib.md5(val).hexdigest()

    pass


pass
