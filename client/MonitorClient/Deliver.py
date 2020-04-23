from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from socket import gethostname
from MonitorClient.ClientDatabase import ClientDatabase
from base64 import b64encode

import urllib.request
import urllib.parse
import json

class Deliver(ClientDatabase):
    
    def __init__(self, api_base_url = 'https://monitor.aroonie.com/api/'):
        super().__init__()
        self.api_base_url = api_base_url
        self.private_signing_key, self.public_signing_key = self.get_signing_key_pair()
        self.api_key = self.get_api_key()

    def upload(self): 
        monitoring_data = self.get_monitoring_data()
        while (monitoring_data is not None and len(monitoring_data) > 0):
            if len(monitoring_data) == 0:
                return True

            monitoring_data_prepared = json.dumps([json.loads(x[1]) for x in monitoring_data])
            monitoring_data_signature = self.sign_message(monitoring_data_prepared)

            if self.http_post_request('v1/deliver/measurement', monitoring_data_prepared, monitoring_data_signature) == True:
                # get last entry so we can delete data that has been uploaded
                last_entry = max([x[0] for x in monitoring_data])
                self.delete_monitoring_data(last_entry)
            monitoring_data = self.get_monitoring_data()


    def get_api_key(self):
        api_key = self.db_get_configuration_item('api_key')

        if api_key == None:
            api_key = self.get_new_api_key()
            self.db_set_configuration_item('api_key', api_key)
        
        return api_key
    
    def sign_message(self, message):
        return b64encode(self.private_signing_key.sign(
            message.encode(),
            padding.PSS(
                mgf = padding.MGF1(hashes.SHA256()),
                salt_length = padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        ))

    def get_new_api_key(self):
        url = self.api_base_url + 'v1/register/client'        
        params = urllib.parse.urlencode({
            'public_signing_key': self.public_signing_key,
            'hostname': gethostname(),
            'hostname_signature': self.sign_message(gethostname())
        }).encode('UTF8')
        
        response = urllib.request.urlopen(url, params)
        if response.getcode() == 200:
            return response.read()

    def http_post_request(self, destination, payload, payload_signature):
        url = self.api_base_url + destination
        params = urllib.parse.urlencode({
                'measurement': payload, 
                'measurement_signature': payload_signature, 
                'api_key': self.api_key
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
            private_signing_key_pem, public_signing_key = self.db_get_keys('signing')
            return serialization.load_pem_private_key(private_signing_key_pem, password=None, backend=default_backend()), public_signing_key
        except TypeError:
            # Got this because no key existed in the database, try to recreate a new key.
            self.new_signing_key_pair()
            private_signing_key_pem, public_signing_key = self.db_get_keys('signing')
            return serialization.load_pem_private_key(private_signing_key_pem, password=None, backend=default_backend()), public_signing_key
