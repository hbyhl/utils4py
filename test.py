#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: test.py
# Author:yhl
# Version:
# Last modified: 2019-12-18 17:43
import os
from urllib.parse import urlsplit

from pika.exceptions import ChannelWrongStateError, AMQPError
from py2neo import Graph
from py2neo.internal.connectors import coalesce

if __name__ == '__main__':
    # d = {'key1': 1, 'key2': 2}
    # b = map(lambda x,y: (x,y * 10), d.keys(),d.values())
    # for k,v in b:
    #     print(k)
    #     print(v)

    # graph = Graph('http://10.31.1.102:7474', username='neo4j', password='neo4j4topay')
    # print('')
    # parsed= urlsplit("http://user:password@host:port/db/db/")
    # u_v = coalesce(parsed.username, "use0r")
    # print(parsed)
    # print(u_v)
    print(os.path.abspath('.abc'))

    if not os.path.exists(os.path.abspath('abc')):
        os.makedirs(os.path.abspath('abc'))

    try:
        raise AMQPError('cuowu ')
    except AMQPError as e:
        print('catch excption')
        raise e
    except Exception:
        print('other exception')
    finally:
        print('finally')
        ChannelWrongStateError



