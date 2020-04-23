
from MonitorServer.ServerDatabase import ServerDatabase
from os import urandom
from base64 import b64encode
import json
from datetime import datetime
from inspect import stack

class MServer():
    def __init__(self, client_ip=''):
        self._db = ServerDatabase()
        self.connection_info = {}
        self.connection_info["client_ip"] = client_ip

    def log_message(self, message):
        source_method = stack()[1][3]
        self._db.log_message(message, self.connection_info["client_ip"], source_method)

    def get_new_api_key(self, hostname, hostname_signature, public_signing_key):   
        api_key = b64encode(urandom(128)).decode('utf-8')
        parent_id = self._db.store_api_key(hostname, api_key, public_signing_key)
        self.log_message(f'Requested new api_key, parent_id: {parent_id}')
        return api_key

    def get_parent_id_and_psk(self, api_key):
        return self._db.get_parent_id_and_psk(api_key)

    def deliver_measurement(self, input, parent_id):
        measurements = json.loads(input)
        if type(measurements) != list:
            measurements = [measurements,]
        
        for i in range(0, len(measurements)):
            measurements[i]['parent_id'] = parent_id

        self._db.store_measurement(measurements)
        return True