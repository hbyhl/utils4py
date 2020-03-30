#!usr/bin/env python
# -*- coding: utf-8 -*-

# Desc:
# FileName: sql_util.py
# Author:yhl
# Version:
# Last modified: 2019-12-20 18:16

def create_insert_sql(table_name, field_names, **kwargs):
    """

    :param table_name: 表名
    :param fields: 表的字段名list
    :param kwargs: 插入方法传入的key:value参数
    :return: 带占位符的sql，参数值
    """
    insert_sql_base = 'INSERT INTO {table_name} ({fields_str}) value ({field_values_phd})'
    fields_str = ''
    field_values_phd = ''
    target_params = []
    for key in field_names:
        if key in kwargs:
            fields_str += key + ','
            field_values_phd += '%s,'
            target_params.append(kwargs.get(key))
    if fields_str:
        fields_str = fields_str[0:-1]
        field_values_phd = field_values_phd[0:-1]
        sql = insert_sql_base.format(table_name=table_name, fields_str=fields_str, field_values_phd=field_values_phd)
        return sql, target_params
    return '', []


def create_update_sql(table_name, all_filed_names, can_update_field_names, filter_params, set_params):
    set_sql_str = ''
    filter_sql_str = ''
    update_sql_base = 'update {table_name} set {set_sql_str} {filter_sql_str}'
    target_params = []
    for key in set_params:
        if key in can_update_field_names:
            set_sql_str += key + '=%s,'
            target_params.append(set_params.get(key))

    for key in filter_params:
        if key in all_filed_names:
            if filter_sql_str == "":
                filter_sql_str += 'where ' + key + '=%s and '
            else:
                filter_sql_str += key + '=%s and '
            target_params.append(filter_params.get(key))

    if filter_sql_str:
        filter_sql_str = filter_sql_str[0:-4]
    if set_sql_str:
        set_sql_str = set_sql_str[0:-1]
        sql = update_sql_base.format(table_name=table_name, set_sql_str=set_sql_str, filter_sql_str=filter_sql_str)
        return sql, target_params
    return '', []
