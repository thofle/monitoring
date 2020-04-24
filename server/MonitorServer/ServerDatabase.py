from pymongo import MongoClient
from datetime import datetime
from socket import gethostname
from config import config

class ServerDatabase:
    def __init__(self):
        self.dbconn = MongoClient(
            host=config.MONGO_HOSTNAME, 
            port=config.MONGO_PORT, 
            username=config.MONGO_USERNAME, 
            password=config.MONGO_PASSWORD, 
            authSource=config.MONGO_AUTH_DB
        )

    def log_message(self, message, client_ip=None, source_method=None):
        self.dbconn.monitor.log_messages.insert_one({
            'message': message,
            'client_ip': client_ip,
            'executing_server': gethostname(),
            'source_method': source_method,
            'timestamp': datetime.utcnow()
        })

    def store_api_key(self, hostname, api_key, public_signing_key):
        id = self.dbconn.monitor.api_key.insert_one({
            'hostname': hostname,
            'api_key': api_key,
            'public_signing_key': public_signing_key,
            'approved': False
        })
        return str(id)
    
    def store_measurement(self, input):
        self.dbconn.monitor.measurement.insert_many(input)
    
    def get_parent_id_and_psk(self, api_key):
        result = self.dbconn.monitor.api_key.find_one({
            'api_key': api_key,
            'approved': True
        })
        if result != None:
            return result['_id'], result['public_signing_key']
        return None, None