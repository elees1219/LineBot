# -*- coding: utf-8 -*-

import os

import urlparse
import psycopg2

import collections

class kw_dict_mgr(object):

    def __init__(self, scheme, db_url):
        urlparse.uses_netloc.append(scheme)
        self.url = urlparse.urlparse(db_url)
        self._set_connection()




    def sql_cmd(self, cmd):
        return sql_cmd(cmd, None)

    def sql_cmd(self, cmd, *args):
        self._set_connection()
        try:
            self.cur.execute(cmd, args)
            result = self.cur.fetchall()
        except psycopg2.Error as ex:
            self._close_connection()
            return [[args for args in ex.args], []]
        except Exception as ex:
            self._close_connection()
            return [[args for args in ex.args], []]
        
        self._close_connection()
        return result




    def create_kwdict(self):
        cmd = u'CREATE TABLE keyword_dict( \
                    id SERIAL, \
                    keyword VARCHAR(500), \
                    reply VARCHAR(500), \
                    deleted BOOLEAN NOT NULL DEFAULT FALSE, \
                    override BOOLEAN NOT NULL DEFAULT FALSE, \
                    admin BOOLEAN NOT NULL DEFAULT FALSE, \
                    used_time INTEGER NOT NULL, \
                    creator VARCHAR(33) NOT NULL);'
        result = self.sql_cmd(cmd)
        return True if len(result) <= 1 else False

    def insert_keyword(self, keyword, reply, creator_id):
        cmd = u'INSERT INTO keyword_dict(keyword, reply, creator, used_time, admin) \
               VALUES(\'{kw}\', \'{rep}\', \'{cid}\', 0, FALSE) RETURNING *;'.format(kw=keyword, rep=reply, cid=creator_id)
        cmd_override = u'UPDATE keyword_dict SET override = TRUE WHERE keyword = \'{kw}\''.format(kw=keyword)
        self.sql_cmd(cmd_override)
        result = self.sql_cmd(cmd)
        return result

    def insert_keyword_sticker(self, keyword, sticker_id, creator_id):
        cmd = u'INSERT INTO keyword_dict(keyword, reply, creator, used_time, admin, is_sticker) \
               VALUES(\'{kw}\', \'{rep}\', \'{cid}\', 0, FALSE, TRUE) RETURNING *;'.format(kw=keyword, rep=sticker_id, cid=creator_id)
        cmd_override = u'UPDATE keyword_dict SET override = TRUE WHERE keyword = \'{kw}\''.format(kw=keyword)
        self.sql_cmd(cmd_override)
        result = self.sql_cmd(cmd)
        return result

    def insert_keyword_sys(self, keyword, reply, creator_id):
        cmd = u'INSERT INTO keyword_dict(keyword, reply, creator, used_time, admin) \
               VALUES(\'{kw}\', \'{rep}\', \'{cid}\', 0, TRUE) RETURNING *;'.format(kw=keyword, rep=reply, cid=creator_id)
        cmd_override = u'UPDATE keyword_dict SET override = TRUE WHERE keyword = \'{kw}\''.format(kw=keyword)
        self.sql_cmd(cmd_override)
        result = self.sql_cmd(cmd)
        return result

    def get_reply(self, keyword):
        cmd = u'SELECT * FROM keyword_dict WHERE keyword = \'{kw}\' AND deleted = FALSE ORDER BY admin DESC, id DESC;'.format(kw=keyword)
        cmd_update = u'UPDATE keyword_dict SET used_time = used_time + 1 WHERE keyword = \'{kw}\' AND override = FALSE'.format(kw=keyword)
        self.sql_cmd(cmd_update)
        result = self.sql_cmd(cmd)
        if len(result) > 0:
            return result
        else:
            return None

    def search_keyword(self, keyword):
        cmd = u'SELECT * FROM keyword_dict WHERE keyword LIKE \'%%{kw}%%\' OR reply LIKE \'%%{kw}%%\' ORDER BY id DESC;'.format(kw=keyword)
        result = self.sql_cmd(cmd)
        if len(result) > 0:
            return result
        else:
            return None

    def search_keyword_index(self, startIndex, endIndex):
        cmd = u'SELECT * FROM keyword_dict WHERE id >= {si} AND id <= {ei} ORDER BY id DESC;'.format(si=startIndex, ei=endIndex)
        result = self.sql_cmd(cmd)
        if len(result) > 0:
            return result
        else:
            return None

    def get_info(self, keyword):
        cmd = u'SELECT * FROM keyword_dict WHERE keyword = \'{kw}\' OR reply = \'{kw}\' ORDER BY id DESC;'.format(kw=keyword)
        result = self.sql_cmd(cmd)
        if len(result) > 0:
            return result
        else:
            return None

    def get_info_id(self, id):
        cmd = u'SELECT * FROM keyword_dict WHERE id = \'{id}\' ORDER BY id DESC;'.format(id=id)
        result = self.sql_cmd(cmd)
        if len(result) > 0:
            return result
        else:
            return None

    def order_by_usedtime(self, count):
        cmd = u'SELECT * FROM keyword_dict ORDER BY used_time DESC LIMIT {ct};'.format(ct=count)
        result = self.sql_cmd(cmd)
        if len(result) > 0:
            return result
        else:
            return None

    def order_by_usedtime_all(self):
        cmd = u'SELECT * FROM keyword_dict ORDER BY used_time DESC;'
        result = self.sql_cmd(cmd)
        if len(result) > 0:
            return result
        else:
            return None

    def delete_keyword(self, keyword):
        cmd = u'UPDATE keyword_dict SET deleted = TRUE WHERE keyword = \'{kw}\' AND admin = FALSE AND deleted = FALSE RETURNING *;'.format(kw=keyword)
        result = self.sql_cmd(cmd)
        if len(result) > 0:
            return result
        else:
            return None

    def delete_keyword_id(self, id):
        cmd = u'UPDATE keyword_dict SET deleted = TRUE WHERE id = \'{id}\' AND admin = FALSE AND deleted = FALSE RETURNING *;'.format(id=id)
        result = self.sql_cmd(cmd)
        if len(result) > 0:
            return result
        else:
            return None

    def delete_keyword_sys(self, keyword):
        cmd = u'UPDATE keyword_dict SET deleted = TRUE WHERE keyword = \'{kw}\' AND admin = TRUE AND deleted = FALSE RETURNING *;'.format(kw=keyword)
        result = self.sql_cmd(cmd)
        if len(result) > 0:
            return result
        else:
            return None

    def user_sort_by_created_pair(self):
        cmd = u'SELECT creator, COUNT(creator) FROM keyword_dict GROUP BY creator ORDER BY COUNT(creator) DESC;'
        result = self.sql_cmd(cmd)
        if len(result) > 0:
            return result
        else:
            return None




    def row_count(self):
        cmd = u'SELECT COUNT(id) FROM keyword_dict;'
        result = self.sql_cmd(cmd)
        return int(result[0][0])

    def used_time_sum(self):
        cmd = u'SELECT SUM(used_time) FROM keyword_dict;'
        result = self.sql_cmd(cmd)
        return int(result[0][0])




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


_col_list = ['id', 'keyword', 'reply', 'deleted', 'override', 'admin', 'used_time', 'creator', 'is_sticker']
_col_tuple = collections.namedtuple('kwdict_col', _col_list)
kwdict_col = _col_tuple(0, 1, 2, 3, 4, 5, 6, 7, 8)
