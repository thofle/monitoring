




from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
def pem_to_key(pem):
    return serialization.load_pem_public_key(data=pem, backend=default_backend())

def validate_signature(message, signature, public_signing_key_pem):
    public_key = pem_to_key(public_signing_key_pem)
    try: 
        result = public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf = padding.MGF1(hashes.SHA256()),
                salt_length = padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    except InvalidSignature:
        result = False

    return result

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

from os import urandom
from base64 import b64encode
import json
from datetime import datetime
class MonitorServer(MonitorServerDatabase):
    def __init__(self, connection_info):
        super().__init__()
        self.connection_info = {}
        self.connection_info["client_ip"] = connection_info["client_ip"]

    def validate_signature(self, input, signature, public_signing_key):
        pass

    def get_new_api_key(self, hostname, hostname_signature, public_signing_key):
        if validate_signature(hostname, hostname_signature, public_signing_key) == False:
            self.log_message('Invalid signature', self.connection_info['client_ip'])
            return False
        
        api_key = b64encode(urandom(128))
        self.store_api_key(hostname, api_key, public_signing_key)
        return api_key

    def deliver_measurement(self, measurement, measurement_signature, api_key):
        parent_id, public_signing_key = self.get_doc_id_and_key(api_key)
        if parent_id == None or public_signing_key == None:
            self.log_message('Invalid parent_id or public key for api_key ' + api_key, connection_info['client_ip'])
            return False

        if validate_signature(measurement, measurement_signature, public_signing_key) == False:
            self.log_message('Invalid signature from api_key ' + api_key, connection_info['client_ip'])
            return False

        input = json.loads(measurement)
        input['parent_id'] = parent_id
        input['time_stored'] = datetime.utcnow()
        self.store_measurement(input, parent_id)
        return True
        


if __name__ == '__main__':
    connection_info = {
        'client_ip': '123.0.0.1',
        'version': '0.04.a'
    }
    
    server = MonitorServer(connection_info)

    server.log_message('tests')