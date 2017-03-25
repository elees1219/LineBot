# -*- coding: utf-8 -*-

import os, sys

import urlparse
import psycopg2
import hashlib

import collections

class group_ban(object):

    def __init__(self, scheme, db_url):
        urlparse.uses_netloc.append(scheme)
        self.url = urlparse.urlparse(db_url)
        self._set_connection()
        self.administrator = os.getenv('ADMIN', None)
        self.group_admin = os.getenv('G_ADMIN', None)
        self.group_mod = os.getenv('G_MOD', None)
        if administrator is None:
            print('The SHA224 of ADMIN not defined. Program will be terminated.')
            sys.exit(1)
        if group_admin is None:
            print('The SHA224 of G_ADMIN not defined. Program will be terminated.')
            sys.exit(1)
        if group_mod is None:
            print('The SHA224 of G_MOD not defined. Program will be terminated.')
            sys.exit(1)




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




    def create_ban(self):
        cmd = u'CREATE TABLE group_ban( \
                    groupId VARCHAR(33) PRIMARY KEY, \
                    silence BOOLEAN NOT NULL DEFAULT FALSE, \
                    admin VARCHAR(33) NOT NULL, \
                    admin_sha VARCHAR(56) NOT NULL, \
                    moderator1 VARCHAR(33), \
                    moderator1_sha VARCHAR(56), \
                    moderator2 VARCHAR(33), \
                    moderator2_sha VARCHAR(56), \
                    moderator3 VARCHAR(33), \
                    moderator3_sha VARCHAR(56));'
        result = self.sql_cmd(cmd)
        return True if len(result) <= 1 else False

    def new_data(self, groupId, adminUID, global_admin_key, key_for_admin):
        if global_admin_key == self.administrator:
            cmd = u'INSERT INTO group_ban(groupId, silence, admin, admin_sha) VALUES(\'groupId\', FALSE, \'{adm}\', \'{key}\')'.format(
                id=groupId, 
                adm=admin,
                key=hashlib.sha224(key_for_admin).hexdigest())
            self.sql_cmd(cmd)
            return True
        else:
            return False

    def is_silence(self, groupId):
        cmd = u'SELECT silence FROM group_ban WHERE groupId = \'{id}\''.format(id=groupId)
        result = self.sql_cmd(cmd)
        if len(result) < 1:
            return result[0]
        else:
            return None

    def set_silence(self, groupId, set, key):
        cmd_check = u'SELECT * FROM group_ban WHERE admin_sha = \'{key}\' OR \
                                                    moderator1_sha = \'{key}\' OR \
                                                    moderator2_sha = \'{key}\' OR \
                                                    moderator3_sha = \'{key}\''.format(key=key)
        results = self.sql_cmd(cmd)
        if len(results) > 1:
            cmd = u'UPDATE group_ban SET silence = {set} WHERE groupId = \'{id}\''.format(id=groupId, set=set)
            self.sql_cmd(cmd)
            return True
        else:
            return False

    def change_admin(self, groupId, newAdminUID, key, newkey):
        cmd_check = u'SELECT * FROM group_ban WHERE admin_sha = \'{key}\''.format(key=key)
        results = self.sql_cmd(cmd)

        if len(results) > 1:
            cmd = u'UPDATE group_ban SET admin = \'{adm}\', admin_sha = \'{sha}\' WHERE groupId = \'{id}\''.format(
                id=groupId, 
                adm=newAdminUID,
                sha=hashlib.sha224(newkey).hexdigest())
            self.sql_cmd(cmd)
            return True
        else:
            return False

    def set_mod1(self, groupId, newModUID, key, newkey):
        cmd_check = u'SELECT * FROM group_ban WHERE admin_sha = \'{key}\' OR moderator1_sha = \'{key}\''.format(key=key)
        results = self.sql_cmd(cmd)
        
        if len(results) > 1:
            cmd = u'UPDATE group_ban SET moderator1 = \'{mod}\', moderator1_sha = \'{nk}\' WHERE groupId = \'{id}\''.format(
                id=groupId, 
                mod=newModUID,
                newkey=hashlib.sha224(newkey).hexdigest())
            self.sql_cmd(cmd)
            return True
        else:
            return False

    def set_mod2(self, groupId, newModUID, key, newkey):
        cmd_check = u'SELECT * FROM group_ban WHERE admin_sha = \'{key}\' OR moderator2_sha = \'{key}\''.format(key=key)
        results = self.sql_cmd(cmd)
        
        if len(results) > 1:
            cmd = u'UPDATE group_ban SET moderator2 = \'{mod}\', moderator2_sha = \'{nk}\' WHERE groupId = \'{id}\''.format(
                id=groupId, 
                mod=newModUID,
                newkey=hashlib.sha224(newkey).hexdigest())
            self.sql_cmd(cmd)
            return True
        else:
            return False

    def set_mod3(self, groupId, newModUID, key, newkey):
        cmd_check = u'SELECT * FROM group_ban WHERE admin_sha = \'{key}\' OR moderator3_sha = \'{key}\''.format(key=key)
        results = self.sql_cmd(cmd)
        
        if len(results) > 1:
            cmd = u'UPDATE group_ban SET moderator3 = \'{mod}\', moderator3_sha = \'{nk}\' WHERE groupId = \'{id}\''.format(
                id=groupId, 
                mod=newModUID,
                newkey=hashlib.sha224(newkey).hexdigest())
            self.sql_cmd(cmd)
            return True
        else:
            return False




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


_col_list = ['groupId', 'silence', 
             'admin', 'admin_sha', 
             'moderator1', 'moderator1_sha', 
             'moderator2', 'moderator2_sha', 
             'moderator3', 'moderator3_sha']
_col_tuple = collections.namedtuple('gb_col', _col_list)
gb_col = _col_tuple(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)