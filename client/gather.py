import sqlite3
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from time import time
import operator

class MonitorDatabase:
    def __init__(self, local_db_path = 'monitor.sqlite'):
        print('Connecting to database')
        self.db_conn = sqlite3.connect(local_db_path)
        self.initialize_database()

    def initialize_database(self):
        cursor = self.db_conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS monitoring(timestamp INTEGER, data TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS configuration(key TEXT, value TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS keys(name TEXT PRIMARY KEY, private BLOB, public BLOB)')
        self.db_conn.commit()

    def add_monitoring_data(self, json):
        cursor = self.db_conn.cursor()
        cursor.execute('INSERT INTO monitoring (timestamp, data) VALUES(?,?)', (int(time()), json))
        self.db_conn.commit()

    def get_monitoring_data(self):
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT timestamp, data FROM monitoring')
        result = cursor.fetchall()
        return result
    
    def delete_monitoring_data(self, timestamp):
        cursor = self.db_conn.cursor()
        cursor.execute('DELETE FROM monitoring WHERE timestamp <= ?',(timestamp, ))
        self.db_conn.commit()

    def db_save_keys(self, name, private, public):
        cursor = self.db_conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO keys(name, private, public) VALUES(?,?,?)', (name, private, public))
        self.db_conn.commit()

    def db_get_keys(self, name):
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT private, public FROM keys WHERE name = ?', (name,))
        data = cursor.fetchone()
        if data is not None:
            return data[0], data[1]
        return None

    def db_get_api_token(self):
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT value FROM configuration WHERE key = ?', ('api_token',))
        return cursor.fetchone()[0]

    def __del__(self):
        print('Disconnecting from database')
        self.db_conn.close()

class Deliver(MonitorDatabase):
    def upload_monitoring_data(self): 
        api_token = self.db_get_api_token()
        # if api_token is None, initiate process to get new token from server

        monitoring_data = self.get_monitoring_data()
        last_entry = max([x['timestamp'] for x in monitoring_data])
        ## sign data

        ## post data

        if self.http_post_request() == True:
            self.delete_monitoring_data(last_entry))
    
    def http_post_request(self, destination, payload, signature):
        result_code = 200

        if result_code = 200:       # OK
            return True
        elif result_code = 498:     # Invalid token
            return False

    def generate_key_pair(self):
        keys = rsa.generate_private_key(
            public_exponent = 65537, 
            key_size = 4096,
            backend = default_backend(),
        )

        private_key = keys.private_bytes(
            encoding = serialization.Encoding.PEM,
            format = serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm = serialization.NoEncryption(),
        )

        public_key = keys.public_key().public_bytes(
            encoding = serialization.Encoding.PEM,
            format = serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return private_key, public_key
    
    def new_signing_key_pair(self):
        private_key, public_key = self.generate_key_pair()
        self.db_save_keys('signing', private_key, public_key)

    def get_signing_key_pair(self):
        try:
            self.private_signing_key, self.public_signing_key = self.db_get_keys('signing')
        except TypeError:
            # Got this because no key existed in the database, try to recreate a new key.
            self.new_signing_key_pair()
            self.private_signing_key, self.public_signing_key = self.db_get_keys('signing')

        print(self.private_signing_key, self.public_signing_key)


class Gather(MonitorDatabase):
    def RegisterValue(self, value):
        pass

        

if __name__ == '__main__':
    stats = Deliver()
    stats.get_signing_key_pair()
