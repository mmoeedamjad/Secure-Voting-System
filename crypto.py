import random

# --- HASHING (Integrity/Authentication) ---
# Custom FNV-1a like hash for password storage and data integrity
def simple_hash(data: str):
    h = 2166136261
    for char in data:
        h = (h ^ ord(char)) * 16777619
        h &= 0xFFFFFFFF  # Keep it to 32-bit
    return h

# --- SYMMETRIC ENCRYPTION (Confidentiality) ---
# Implementing a stream cipher based on XOR logic (foundational to AES/OTP)
def symmetric_encrypt(key: str, data: str):
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

def symmetric_decrypt(key: str, data: str):
    return symmetric_encrypt(key, data)

# --- ASYMMETRIC ENCRYPTION (RSA) ---
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True

def generate_asymmetric_keys():
    # Small primes for demonstration; in production, these would be huge.
    primes = [p for p in range(100, 250) if is_prime(p)]
    p, q = random.sample(primes, 2)
    n = p * q
    phi = (p - 1) * (q - 1)
    
    e = 65537
    while gcd(e, phi) != 1:
        e = random.randrange(2, phi)
    
    d = pow(e, -1, phi)
    return (e, n), (d, n)

def asymmetric_encrypt(public_key, data: str):
    e, n = public_key
    return [pow(ord(char), e, n) for char in data]

def asymmetric_decrypt(private_key, encrypted_data):
    d, n = private_key
    if isinstance(encrypted_data, str):
        encrypted_data = eval(encrypted_data) # Convert string representation back to list
    return "".join([chr(pow(char, d, n)) for char in encrypted_data])

# --- DIGITAL SIGNATURE (Non-repudiation) ---
def sign_data(private_key, data):
    data_hash = simple_hash(data)
    d, n = private_key
    return pow(data_hash, d, n)

def verify_signature(public_key, signature, data):
    data_hash = simple_hash(data)
    e, n = public_key
    decrypted_hash = pow(signature, e, n)
    return decrypted_hash == data_hash