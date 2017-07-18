# -*- coding: utf-8 -*-

import os, sys
from collections import defaultdict
from error import error

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
        """
        Type of Event:
        1 = receive text message
        2 = receive text message and auto reply system has been triggered
        3 = receive sticker message
        4 = receive sticker message and auto reply system has been triggered
        5 = count of reply with text message
        6 = count of reply with sticker message

        None listed code of Type of Event and Illegal channel id length will raise ValueError.
        """
        if len(cid) != self.channel_id_length:
            raise ValueError();
        else:
            if type_of_event == 1:
                update_last_message_recv = True
            elif type_of_event == 2:
                update_last_message_recv = True
            elif type_of_event == 3:
                update_last_message_recv = True
            elif type_of_event == 4:
                update_last_message_recv = True
            elif type_of_event == 5:
                update_last_message_recv = False
            elif type_of_event == 6:
                update_last_message_recv = False
            else:
                raise ValueError();
            
            column_to_add = _col_list[type_of_event]

            cmd = u'UPDATE msg_track SET {col} = {col} + 1{recv_time} WHERE cid = %(cid)s'.format(
                recv_time=u', last_msg_recv = NOW()' if update_last_message_recv else u'',
                col=column_to_add)
            cmd_dict = {'cid': cid}
            self.sql_cmd(cmd, cmd_dict)
            return True
        
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
            return result[0]

    def count_sum(self):
        """
        Returns a dictionary contains data.

        Keys(Data Description): 
        text_msg = receive text message
        text_msg_trig = receive text message and auto reply system has been triggered
        stk_msg = receive sticker message
        stk_msg_trig = receive sticker message and auto reply system has been triggered
        text_rep = count of reply with text message
        stk_rep = count of reply with sticker message
        """
        results = defaultdict(int)

        cmd = u'SELECT MIN(last_msg_recv), SUM(text_msg), SUM(text_msg_trig), SUM(stk_msg), SUM(stk_msg_trig), SUM(text_rep), SUM(stk_rep) FROM msg_track'
        sql_result = self.sql_cmd_only(cmd)
        sql_result = sql_result[0]
        results['text_msg'] = sql_result[msg_track_col.text_msg]
        results['text_msg_trig'] = sql_result[msg_track_col.text_msg_trig]
        results['stk_msg'] = sql_result[msg_track_col.stk_msg]
        results['stk_msg_trig'] = sql_result[msg_track_col.stk_msg_trig]
        results['text_rep'] = sql_result[msg_track_col.text_rep]
        results['stk_rep'] = sql_result[msg_track_col.stk_rep]
        return results

    def order_by_recorded_msg_count(self, limit=1000):
        cmd = u'SELECT *, RANK() OVER (ORDER BY SUM(text_msg) + SUM(text_msg_trig) + SUM(stk_msg) + SUM(stk_msg_trig) DESC) AS total_msg FROM msg_track GROUP BY cid ORDER BY total_msg ASC LIMIT %(limit)s;'
        cmd_dict = {'limit': limit}
        
        result = self.sql_cmd(cmd, cmd_dict)
        return result




    @staticmethod
    def entry_detail(data, group_ban=None):
        gid = data[msg_track_col.cid]

        text = u'群組/房間ID: {} {}'.format(
            gid, u'' if group_ban is None else u'({})'.format(
                u'停用自動回覆' if group_ban.get_group_by_id(gid)[gb_col.silence] else u'啟用自動回覆'))
        text += u'\n收到(無對應回覆組): {}則文字訊息 | {}則貼圖訊息'.format(data[msg_track_col.text_msg], data[msg_track_col.stk_msg])
        text += u'\n收到(有對應回覆組): {}則文字訊息 | {}則貼圖訊息'.format(data[msg_track_col.text_msg_trig], data[msg_track_col.stk_msg_trig])
        text += u'\n回覆: {}則文字訊息 | {}則貼圖訊息'.format(data[msg_track_col.text_rep], data[msg_track_col.stk_rep])

    @staticmethod
    def entry_detail_list(data_list, limit=10, group_ban=None):
        """return two object to access by [\'limited\'] and [\'full\']."""
        ret = {'limited': u'', 'full': u''}
        limited = False
        count = len(data_list)

        if count <= 0:
            ret['limited'] = error.main.no_result()
        else:
            ret['limited'] = u'\n\n'.join([message_tracker.entry_detail(data, group_ban) for data in data_list[0 : limit - 1]])
            if count - limit > 0:
                ret['limited'] += u'\n\n...還有{}筆資料'.format(count - limit)

            ret['full'] = u', '.join(data_list)
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




_col_list = ['cid', 
             'text_msg',  'text_msg_trig', 
             'stk_msg', 'stk_msg_trig', 
             'text_rep', 'stk_rep',
             'last_msg_recv']
_col_tuple = collections.namedtuple('msg_track_col', _col_list)
msg_track_col = _col_tuple(0, 1, 2, 3, 4, 5, 6, 7)