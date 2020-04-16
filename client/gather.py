import sqlite3
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from time import time
from socket import gethostname
import urllib.request
import urllib.parse

import psutil

class MonitorClientDatabase:
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

    def __del__(self):
        if hasattr(self, 'db_conn'):
            print('Disconnecting from database')
            self.db_conn.close()

class Deliver(MonitorClientDatabase):
    
    def __init__(self, api_base_url = 'https://monitor.aroonie.com/api/'):
        super().__init__()
        self.api_base_url = api_base_url
        self.get_signing_key_pair()
        self.get_api_token()

    def upload_monitoring_data(self): 
        monitoring_data = self.get_monitoring_data()
        monitoring_data_signature = self.sign_message(monitoring_data)


        if self.http_post_request('deliver/', monitoring_data, monitoring_data_signature) == True:
            # get last entry so we can delete data that has been uploaded
            last_entry = max([x['timestamp'] for x in monitoring_data])
            self.delete_monitoring_data(last_entry)


    def get_api_token(self):
        api_token = self.db_get_configuration_item('api_token')

        if api_token == None:
            api_token = self.get_new_api_token()
            self.db_set_configuration_item('api_token', api_token)
        
        self.api_token = api_token
    
    def sign_message(self, message):
        return self.private_signing_key.sign(
            message,
            padding.PSS(
                mgf = padding.MGF1(hashes.SHA256()),
                salt_length = padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

    def get_new_api_token(self):
        url = self.api_base_url + 'register/host/'        
        params = urllib.parse.urlencode({
            'public_signing_key': self.public_signing_key,
            'hostname': gethostname(),
            'signed_hostname': self.sign_message(gethostname())
        }).encode('UTF8')
        
        response = urllib.request.urlopen(url, params)
        if response.getcode() == 200:
            return response.read()
        raise Exception(str(response.getcode())) 

    def http_post_request(self, destination, payload, payload_signature):
        url = self.api_base_url + destination
        params = urllib.parse.urlencode({'payload': payload, 
                'payload_signature': payload_signature, 
                'api_token': self.api_token
        }).encode('UTF8')

        response = urllib.request.urlopen(url, params)
        if response.getcode() == 200:       # OK
            return True
        else:
            raise Exception(str(response.getcode())) 

    def generate_key_pair(self):
        keys = rsa.generate_private_key(
            public_exponent = 65537, 
            key_size = 4096,
            backend = default_backend(),
        )

        private_key = keys.private_bytes(
            encoding = serialization.Encoding.PEM,
            format = serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm = serialization.NoEncryption()
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
            private_signing_key_pem, self.public_signing_key = self.db_get_keys('signing')
            private_signing_key_pem = private_signing_key_pem.splitlines()
            self.private_signing_key = serialization.load_pem_private_key(private_signing_key_pem, password=None, backend=default_backend())
        except TypeError:
            # Got this because no key existed in the database, try to recreate a new key.
            self.new_signing_key_pair()
            private_signing_key_pem, self.public_signing_key = self.db_get_keys('signing')
            self.private_signing_key = serialization.load_pem_private_key(private_signing_key_pem, password=None ,backend=default_backend())


class Gather(MonitorClientDatabase):
    def __init__(self):
        pass

    def record_stats(self, stats = 'ALL'):
        super().__init__()
        pass

    def get_stats(self, stats = 'ALL'):
        result = {}
        if stats == 'ALL':
            result['cpu'] = self.get_cpu_measurement()
            result['memory'] = self.get_memory_measurement()
            result['disk'] = self.get_disk_measurement()
            result['network'] = self.get_network_measurement()
            result['process'] = self.get_process_measurements()
        return result

    def get_cpu_measurement(self):
        return {
            'percent_usage': psutil.cpu_percent(interval=0.5, percpu=True),
            'logical_cores': psutil.cpu_count(logical=True),
            'physical_cores': psutil.cpu_count(logical=False),
            'measured_at': int(time()),
            } 

    def get_memory_measurement(self):
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'used': mem.used,
            'free': mem.free,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'measured_at': int(time()),
            } 

    def get_disk_measurement(self):
        disks = []
        for partition in psutil.disk_partitions(all=False):
            if partition.opts != 'removable':
                size = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'size': size.total,
                    'used': size.used,
                    'measured_at': int(time())
                })
        return disks
    
    def get_network_measurement(self):
        adapters = []
        all_adapters = psutil.net_io_counters(pernic=True)
        ips = psutil.net_if_addrs()
        for adapter in all_adapters:
            if 'loopback' not in adapter and adapter != 'lo':
                adapters.append({
                    'name': adapter,
                    'addresses': ips[adapter],
                    'bytes_sent': all_adapters[adapter].bytes_sent,
                    'bytes_recv': all_adapters[adapter].bytes_recv,
                    'measured_at': int(time())
                })
        return adapters

    def get_process_measurements(self):
        listening_processes = []
        for con in psutil.net_connections():
            if con.status == 'LISTEN':
                listening_processes.append({
                    'process': con.pid,
                    'ip': con.laddr.ip,
                    'port': con.laddr.port
                })

        processes = []
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                
                with p.oneshot():
                    name = 'restricted'
                    executable = 'restricted'

                    try:
                        executable = p.exe()
                    except psutil.AccessDenied:
                        pass

                    try:
                        name = p.name()
                    except psutil.AccessDenied:
                        pass

                    processes.append({
                        'process': pid,
                        'executable': executable,
                        'name': name,
                        
                    })
            except psutil.NoSuchProcess:
                pass
            except psutil.AccessDenied:
                pass
        return {
            'listening_processes': listening_processes,
            'processes': processes,
            'measured_at': int(time())
        }

if __name__ == '__main__':
    stats = Gather()
    print(stats.get_stats()['process'])
    pass