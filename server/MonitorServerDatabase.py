from inspect import stack
from pymongo import MongoClient
from datetime import datetime
from socket import gethostname
class MonitorServerDatabase:
    def __init__(self, host='127.0.0.1', port=27017, username='', password='', authentication_database=''):
        self.dbconn = MongoClient(host=host, port=port, username=username, password=password, authSource=authentication_database)

    def log_message(self, message, client_ip=None):
        source_method = stack()[0][3]
        self.dbconn.log.messages.insert_one({
            'message': message,
            'client_ip': client_ip,
            'executing_server': gethostname(),
            'source_method': source_method,
            'timestamp': datetime.utcnow()
        })

    def store_api_key(self, hostname, api_key, public_signing_key):
        self.dbconn.monitor.api_key.insert_one({
            'hostname': hostname,
            'api_key': api_key,
            'public_signing_key': public_signing_key,
            'approved': False
        })
    
    def store_measurement(self, input, parent_id):
        self.dbconn.monitor.measurement.insert_one(input)
    
    def get_doc_id_and_key(self, api_key):
        result = self.dbconn.configuration.api_key.find_one({
            'api_key': api_key,
            'approved': True
        })
        if result != None:
            return result['_id'], result['public_signing_key']
        return None, None