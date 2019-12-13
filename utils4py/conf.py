#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from six.moves import configparser

import utils4py.env


class ConfUtils(object):
    """
        Config utilities
    """

    __CONF_DIR__ = "conf"
    __CONF_TEST_DIR__ = "conf_test"

    @classmethod
    def get_base_dir(cls):
        if utils4py.env.is_debug():
            return os.path.abspath(os.path.join(os.getcwd(), cls.__CONF_TEST_DIR__))
        return os.path.abspath(os.path.join(os.getcwd(), cls.__CONF_DIR__))

    @classmethod
    def complete_path(cls, relative_path):
        return os.path.abspath(os.path.join(cls.get_base_dir(), relative_path))

    @classmethod
    def _new_parser(cls):
        """
            new parser
        """
        p = configparser.ConfigParser()
        p.optionxform = lambda x: x
        return p

    @classmethod
    def load_parser(cls, config_file):
        """
        :param str config_file: 
        :rtype: ConfigParser.ConfigParser
        """
        filename = config_file
        if not str.startswith(config_file, "/"):
            filename = cls.complete_path(config_file)

        parser = cls._new_parser()
        parser.read(filename)
        return parser



    pass


pass
