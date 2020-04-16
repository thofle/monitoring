from helpers import validate_signature
from MonitorServerDatabase import MonitorServerDatabase
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
        


