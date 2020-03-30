#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: dict_ext.py
# Author:yhl
# Version:
# Last modified: 2020-01-02 13:55

class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.
    copied from web.py

        >>> o = Storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a

    """

    def __getattr__(self, key):
        return self.get(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError

    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'
