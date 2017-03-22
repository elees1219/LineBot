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


    def db_version(self):
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT version()')
            db_version = cur.fetchone()
            cur.close()
            return str(db_version)
        except psycopg2.Error as ex:
            return str(ex.message)
        except Exception as ex:
            return str(ex.message)


