#!/usr/bin/env python
# -*- coding: utf-8 -*-


from utils4py.data.cache import SimpleQueue as RedisQueue
from utils4py.data.cache import connect as connect_redis
from utils4py.data.mysql import connect as connect_mysql
from utils4py.data.mongo import connect as connect_mongo
from utils4py.data.rabbitmq import connect as connect_rabbitmq
from utils4py.data.rabbitmq import connect_from_conf as connect_rabbitmq_from_conf
from utils4py.data.neo4j import connect as connect_neo4j
