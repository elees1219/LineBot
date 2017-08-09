# -*- coding: utf-8 -*-

import os, sys
from collections import defaultdict
from error import error
from enum import Enum

import urlparse
import psycopg2
from sqlalchemy.exc import IntegrityError
from db import group_ban, gb_col
import hashlib

import collections

class message_tracker(object):

    def __init__(self, scheme, db_url):
        urlparse.uses_netloc.append(scheme)
        self.url = urlparse.urlparse(db_url)
        self._set_connection()
        self.channel_id_length = 33



    def sql_cmd_only(self, cmd):
        return self.sql_cmd(cmd, None)

    def sql_cmd(self, cmd, dict):
        self._set_connection()
        self.cur.execute(cmd, dict)
        try:
            result = self.cur.fetchall()
        except psycopg2.ProgrammingError as ex:
            if ex.message == 'no results to fetch':
                result = None
            else:
                raise ex
        
        self._close_connection()
        return result




    @property
    def table_structure(self):
        cmd = u'CREATE TABLE msg_track( \
                    {} VARCHAR(33) PRIMARY KEY, \
                    {} INTEGER NOT NULL DEFAULT 0, \
                    {} INTEGER NOT NULL DEFAULT 0, \
                    {} INTEGER NOT NULL DEFAULT 0, \
                    {} INTEGER NOT NULL DEFAULT 0, \
                    {} INTEGER NOT NULL DEFAULT 0, \
                    {} INTEGER NOT NULL DEFAULT 0);'.format(*_col_list)
        return cmd

    def log_message_activity(self, cid, type_of_event):
        if len(cid) != self.channel_id_length:
            raise ValueError(error.main.incorrect_thing_with_correct_format(u'頻道ID', u'33字元長度', cid));
        else:
            update_last_message_recv = True
            if type_of_event == msg_event_type.send_stk or type_of_event == msg_event_type.send_txt:
                update_last_message_recv = False
            
            column_to_add = int(type_of_event)
            
            cmd = u'SELECT * FROM msg_track WHERE cid = %(cid)s'
            cmd_dict = {'cid': cid}
            result = self.sql_cmd(cmd, cmd_dict)
            
            if len(result) < 1:
                self.new_data(cid)

            cmd = u'UPDATE msg_track SET {col} = {col} + 1{recv_time} WHERE cid = %(cid)s'.format(
                recv_time=u', last_msg_recv = NOW()' if update_last_message_recv else u'',
                col=column_to_add)
            self.sql_cmd(cmd, cmd_dict)
        
    def new_data(self, cid):
        if len(cid) != self.channel_id_length:
            raise ValueError();
        else:
            cmd = u'INSERT INTO msg_track (cid) VALUES (%(cid)s)'
            cmd_dict = {'cid': cid}
            self.sql_cmd(cmd, cmd_dict)
            return True

    def get_data(self, cid):
        """return group entry"""
        if len(cid) != self.channel_id_length:
            raise ValueError();
        else:
            cmd = u'SELECT * FROM msg_track WHERE cid = %(cid)s'
            cmd_dict = {'cid': cid}
            result = self.sql_cmd(cmd, cmd_dict)
            if len(result) > 0:
                return result[0]
            else:
                return None

    def count_sum(self):
        results = defaultdict(int)

        cmd = u'SELECT MIN(last_msg_recv), SUM(text_msg), SUM(text_msg_trig), SUM(stk_msg), SUM(stk_msg_trig), SUM(text_rep), SUM(stk_rep) FROM msg_track'
        sql_result = self.sql_cmd_only(cmd)
        sql_result = sql_result[0]
        results[msg_event_type.recv_txt] = sql_result[msg_track_col.text_msg]
        results[msg_event_type.recv_txt_repl] = sql_result[msg_track_col.text_msg_trig]
        results[msg_event_type.recv_stk] = sql_result[msg_track_col.stk_msg]
        results[msg_event_type.recv_stk_repl] = sql_result[msg_track_col.stk_msg_trig]
        results[msg_event_type.send_txt] = sql_result[msg_track_col.text_rep]
        results[msg_event_type.send_stk] = sql_result[msg_track_col.stk_rep]
        return results

    def order_by_recorded_msg_count(self, limit=1000):
        cmd = u'SELECT *, RANK() OVER (ORDER BY SUM(text_msg) + SUM(text_msg_trig) + SUM(stk_msg) + SUM(stk_msg_trig) DESC) AS total_msg FROM msg_track GROUP BY cid ORDER BY total_msg ASC LIMIT %(limit)s;'
        cmd_dict = {'limit': limit}
        
        result = self.sql_cmd(cmd, cmd_dict)
        return result




    @staticmethod
    def entry_detail(data, group_ban=None):
        gid = data[msg_track_col.cid]

        if group_ban is not None:
            if gid.startswith('U'):
                activation_status = u'私訊頻道'
            else:
                group_data = group_ban.get_group_by_id(gid)
                if group_data is not None:
                    activation_status = u'停用回覆' if group_data[gb_col.silence] else u'啟用回覆'
                else:
                    activation_status = u'啟用回覆'
        else:
            activation_status = u'啟用回覆'

        text = u'群組/房間ID: {} 【{}】'.format(gid, activation_status)
        text += u'\n收到(無對應回覆組): {}則文字訊息 | {}則貼圖訊息'.format(data[msg_track_col.text_msg], data[msg_track_col.stk_msg])
        text += u'\n收到(有對應回覆組): {}則文字訊息 | {}則貼圖訊息'.format(data[msg_track_col.text_msg_trig], data[msg_track_col.stk_msg_trig])
        text += u'\n回覆: {}則文字訊息 | {}則貼圖訊息'.format(data[msg_track_col.text_rep], data[msg_track_col.stk_rep])

        return text

    @staticmethod
    def entry_detail_list(data_list, limit=10, group_ban=None):
        """return two object to access by [\'limited\'] and [\'full\']."""
        ret = {'limited': u'', 'full': u''}
        count = len(data_list)

        if count <= 0:
            ret['limited'] = error.main.no_result()
        else:
            ret['limited'] = u'\n\n'.join([message_tracker.entry_detail(data, group_ban) for data in data_list[0:limit]])
            if count - limit > 0:
                ret['limited'] += u'\n\n...還有{}筆資料'.format(count - limit)

            ret['full'] = u'\n\n'.join([message_tracker.entry_detail(data, group_ban) for data in data_list])
        return ret




    def _close_connection(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()

    def _set_connection(self):
        self.conn = psycopg2.connect(
            database=self.url.path[1:],
            user=self.url.username,
            password=self.url.password,
            host=self.url.hostname,
            port=self.url.port
        )
        self.cur = self.conn.cursor()


class msg_track_col(Enum):
    cid = 0
    text_msg = 1
    text_msg_trig = 2
    stk_msg = 3
    stk_msg_trig = 4
    text_rep = 5
    stk_rep = 6
    last_msg_recv = 7

class msg_event_type(Enum):
    recv_txt = 1
    recv_txt_repl = 2
    recv_stk = 3
    recv_stk_repl = 4
    send_txt = 5
    send_stk = 6

    def __int__(self):
        return self.value