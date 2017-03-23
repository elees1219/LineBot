import os

import urlparse
import psycopg2

class db_manager(object):

    # SQL Command Escape Value
    # Common Operation to use
    # Change Language to bilangual
    # Check Data Exist and iterate to display
    # Re-organize package
    # Make user easy to input like ¤p¤ô¥À  A  Keyword  Reply - using double space to separate
    # Add function to know who add keyword
    # Add keyword analysis
    # No Result No Return

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
                            keyword VARCHAR(255) PRIMARY KEY,\
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
                              VALUES(\'' + keyword + '\', \'' + reply + '\') RETURNING *;')
            Result = self.cur.fetchone()

        except psycopg2.Error as ex:
            self.close_connection()
            return str(ex.message)
        except Exception as ex:
            self.close_connection()
            return str(ex.message)
        
        self.close_connection()
        return str('Keyword ID: ' + str(Result[0]) + 
                   '\nKeyword: ' + str(Result[1]) + 
                   '\nReply: ' + str(Result[2]))

    def get_reply(self, keyword):
        self.set_connection()
        try:
            self.cur.execute('SELECT * FROM keyword_dict \
                              WHERE keyword = \'' + keyword + '\';')
            exec_res = self.cur.fetchone()
            reply = None

            if exec_res:
                reply = exec_res[2]
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
                              WHERE keyword = \'' + keyword + '\' RETURNING *;')

            result = self.cur.fetchone()
            kw = 'None'
            reply = 'None'

            if result:
                kw = result[1]
                reply = result[2]

        except psycopg2.Error as ex:
            self.close_connection()
            return str('psycopg2.Error in delete_keyword\n' + ex.message)
        except Exception as ex:
            self.close_connection()
            return str('Exception in delete_keyword\n' + ex.message)
        
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