from time import time
import sqlite3


class ClientDatabase:
    def __init__(self, local_db_path = 'monitor.sqlite'):
        self.db_conn = sqlite3.connect(local_db_path)
        self.initialize_database()

    def initialize_database(self):
        cursor = self.db_conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS monitoring(timestamp INTEGER, data TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS configuration(key TEXT PRIMARY KEY, value TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS keys(name TEXT PRIMARY KEY, private BLOB, public BLOB)')
        self.db_conn.commit()

    def add_monitoring_data(self, json):
        cursor = self.db_conn.cursor()
        cursor.execute('INSERT INTO monitoring (timestamp, data) VALUES(?,?)', (int(time()), json))
        self.db_conn.commit()

    def get_monitoring_data(self):
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT timestamp, data FROM monitoring ORDER BY timestamp ASC LIMIT 500')
        result = cursor.fetchall()
        return result
    
    def get_measurements_to_capture(self):
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT value FROM configuration WHERE key = ?', ('tick',))
        result = cursor.fetchone()
        if result is None:
            tick = 0
        else:
            tick = int(result[0])
        
        cursor.execute('INSERT OR REPLACE INTO configuration (key, value) VALUES(?,?)', ('tick',str(tick+1)))
        self.db_conn.commit()
        if (tick % 5) == 0:
            return ['ALL']
        else:
            return ['CPU','NETWORK','MEMORY']


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
            return data[0], data[1].decode('utf-8')
        return None

    def db_get_configuration_item(self, key):
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT value FROM configuration WHERE key = ?', (key,))
        data = cursor.fetchone()
        if data is not None:
            return data[0]
        return None

    def db_set_configuration_item(self, key, value):
        cursor = self.db_conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO configuration(key, value) VALUES(?,?)', (key, value))
        self.db_conn.commit()

#    def __del__(self):
#        if hasattr(self, 'db_conn'):
#            print('Disconnecting from database')
#            self.db_conn.close()
