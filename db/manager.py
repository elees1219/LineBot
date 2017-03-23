import os

import urlparse
import psycopg2

class db_manager(object):

    def __init__(self, scheme, db_url):
        urlparse.uses_netloc.append(scheme)
        self.url = urlparse.urlparse(db_url)
        self.set_connection()


    def db_version(self):
        self.set_connection()
        try:
            self.cur.execute('SELECT version();')
            db_version = self.cur.fetchone()
        except psycopg2.Error as ex:
            self.close_connection()
            return str(ex.message)
        except Exception as ex:
            self.close_connection()
            return str(ex.message)

        self.close_connection()
        return str(db_version)


    def table_create(self):
        self.set_connection()
        try:
            self.cur.execute('CREATE TABLE keyword_dict(\
                            id SERIAL,\
                            keyword VARCHAR(255),\
                            reply VARCHAR(255));')
        except psycopg2.Error as ex:
            self.close_connection()
            return str(ex.message)
        except Exception as ex:
            self.close_connection()
            return str(ex.message)

        self.close_connection()


    def table_exist(self):
        self.set_connection()
        try:
            self.cur.execute('SELECT * FROM keyword_dict;')

            recv_content = self.cur.fetchone()
        except psycopg2.Error as ex:
            self.close_connection()
            return str(ex.message)
        except Exception as ex:
            self.close_connection()
            return str(ex.message)

        self.close_connection()
        return str(recv_content)


    def insert_keyword(self, keyword, reply):
        self.set_connection()
        try:
            self.cur.execute('INSERT INTO keyword_dict(keyword, reply)\
                              VALUES(\'' + keyword + '\', \'' + reply + '\') RETURNING id;')
            register_id = self.cur.fetchone()[0]
        except psycopg2.Error as ex:
            self.close_connection()
            return str(ex.message)
        except Exception as ex:
            self.close_connection()
            return str(ex.message)
        
        self.close_connection()
        return str('Keyword ID: ' + str(register_id))

    def get_reply(self, keyword):
        self.set_connection()
        try:
            self.cur.execute('SELECT * FROM keyword_dict \
                              WHERE keyword = \'' + keyword + '\';')
            reply = self.cur.fetchone()[2]
        except psycopg2.Error as ex:
            self.close_connection()
            return str(ex.message)
        except Exception as ex:
            self.close_connection()
            return str(ex.message)
        
        self.close_connection()
        return str(reply)

    def delete_keyword(self, keyword):
        self.set_connection()
        try:
            self.cur.execute('DELETE FROM keyword_dict \
                              WHERE keyword = \'' + keyword + '\';')
            kw = self.cur.fetchone()[1]
            reply = self.cur.fetchone()[2]
        except psycopg2.Error as ex:
            self.close_connection()
            return str(ex.message)
        except Exception as ex:
            self.close_connection()
            return str(ex.message)
        
        self.close_connection()
        return str('Auto reply pair below has been DELETED.\nkeyword: ' + kw + '\nreply: ' + reply)


    def sql_cmd(self, cmd):
        self.set_connection()
        try:
            self.cur.execute(cmd)
            cmd_return = self.cur.fetchone()
        except psycopg2.Error as ex:
            self.close_connection()
            return str(ex.message)
        except Exception as ex:
            self.close_connection()
            return str(ex.message)
        
        self.close_connection()
        return str(cmd_return)


    def close_connection(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()
        

    def set_connection(self):
        self.conn = psycopg2.connect(
            database=self.url.path[1:],
            user=self.url.username,
            password=self.url.password,
            host=self.url.hostname,
            port=self.url.port
        )
        self.cur = self.conn.cursor()