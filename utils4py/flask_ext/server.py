#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging

import flask
from gevent.pywsgi import WSGIServer

import utils4py
from utils4py.flask_ext.filter import init_filters
from utils4py.flask_ext.routes import init_routes


class AppServer(object):
    """
        App Server
    """
    filters = []  # 单个添加filter
    filter_paths = ["utils4py.flask_ext.filter"]  # 添加指定包下的filter
    route_paths = []  # 添加指定包下的route

    def __init__(self, app_name, logger):
        self._app_name = app_name
        self._logger = logger
        self._app = None
        self.registered_map = {}
        self._debug = utils4py.env.is_debug()

    def _init_app(self):
        app = flask.Flask(self._app_name)
        init_filters(app, filters=self.filters, paths=self.filter_paths, logger=self._logger)
        self.registered_map = init_routes(app, paths=self.route_paths)
        setattr(app, "_logger", self._logger)

        if self._debug:
            app.config["DEBUG"] = True
        self._app = app
        return app

    @property
    def app(self):
        """
        :rtype: flask.Flask
        """
        if not self._app:
            self._init_app()
        return self._app

    def run(self, port):
        logging.info("Start server, port=%s, debug=%s", port, self._debug)
        self.app.run(host='0.0.0.0', port=port)

    def run_wsgi(self, port):
        logging.info("Start wsgi server, port=%s, debug=%s", port, self._debug)
        server = WSGIServer(('', port), self.app)
        server.serve_forever()
