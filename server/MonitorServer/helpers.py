from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
from base64 import b64decode

def pem_to_key(pem):
    return serialization.load_pem_public_key(data=pem.encode(), backend=default_backend())

def validate_signature(message, signature, public_signing_key_pem):
    public_key = pem_to_key(public_signing_key_pem)
    print(public_key)
    print(signature)
    try: 
        result = public_key.verify(
            b64decode(signature),
            message.encode(),
            padding.PSS(
                mgf = padding.MGF1(hashes.SHA256()),
                salt_length = padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    except InvalidSignature:
        result = False

    return result