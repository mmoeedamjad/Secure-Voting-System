import random

# ---------------- HASH ----------------
def simple_hash(data: bytes):
    return sum(data) % 256


# ---------------- SYMMETRIC (XOR) ----------------
def symmetric_encrypt(key, data: bytes):
    key = key % 256
    return bytes([b ^ key for b in data])

def symmetric_decrypt(key, encrypted_data: bytes):
    return symmetric_encrypt(key, encrypted_data)


# ---------------- ASYMMETRIC (TOY RSA) ----------------
def generate_asymmetric_keys():
    p = 61
    q = 53
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 17
    d = pow(e, -1, phi)
    return (e, n), (d, n)

def asymmetric_encrypt(public_key, data: bytes):
    e, n = public_key
    return [pow(b, e, n) for b in data]

def asymmetric_decrypt(private_key, encrypted_data):
    d, n = private_key
    return bytes([pow(c, d, n) for c in encrypted_data])


# ---------------- DIGITAL SIGNATURE ----------------
def sign_data(private_key, data_hash):
    return asymmetric_encrypt(private_key, bytes([data_hash]))[0]

def verify_signature(public_key, signature, data_hash):
    decrypted = asymmetric_decrypt(public_key, [signature])[0]
    return decrypted == data_hash
