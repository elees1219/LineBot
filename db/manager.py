import os

import urlparse
import psycopg2

class db_manager(object):

    def __init__(self, scheme, db_url):
        urlparse.uses_netloc.append(scheme)
        url = urlparse.urlparse(db_url)
        self.conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        self.cur = self.conn.cursor()


    def db_version(self):
        try:
            self.cur.execute('SELECT version()')
            db_version = self.cur.fetchone()
            return str(db_version)
        except psycopg2.Error as ex:
            return str(ex.message)
        except Exception as ex:
            return str(ex.message)

    def table_create(self):
        try:
            self.cur.execute('CREATE TABLE keyword_dict(\
                            id SERIAL,\
                            keyword VARCHAR(255),\
                            reply VARCHAR(255)\
                        )')
        except psycopg2.Error as ex:
            return str(ex.message)
        except Exception as ex:
            return str(ex.message)

    def close_connection(self):
        self.cur.close()