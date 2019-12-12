#!usr/bin/env python
# -*- coding:utf-8 _*-

# Desc: 
# FileName: filters.py
# Author:yhl
# Version:
# Last modified: 2019-12-11 18:30

from logging import Filter, INFO, DEBUG, WARN, CRITICAL, ERROR


class InfoFilter(Filter):
    def filter(self, record):
        return record.levelno == INFO


class DebugFilter(Filter):
    def filter(self, record):
        return record.levelno == DEBUG


class WarnFilter(Filter):
    def filter(self, record):
        return record.levelno == WARN


class CriticalFilter(Filter):
    def filter(self, record):
        return record.levelno == CRITICAL


class ErrorFilter(Filter):
    def filter(self, record):
        return record.levelno == ERROR
