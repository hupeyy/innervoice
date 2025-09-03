from cryptography.fernet import Fernet
import base64
import hashlib
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

SECRET_KEY = 'innervoice-encryption-key-2025'  # Same as frontend

def decrypt_data(encrypted_data: str) -> dict:
    """Decrypt data using AES decryption compatible with CryptoJS"""
    try:
        # Create key from secret
        key = hashlib.sha256(SECRET_KEY.encode()).digest()[:32]
        
        # Decode the base64 encrypted data
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # Extract IV (first 16 bytes) and ciphertext
        iv = encrypted_bytes[:16]
        ciphertext = encrypted_bytes[16:]
        
        # Decrypt using AES CBC mode
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(ciphertext)
        
        # Remove padding and parse JSON
        decrypted_text = unpad(decrypted_padded, 16).decode('utf-8')
        return json.loads(decrypted_text)
        
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")

def encrypt_data(data: dict) -> str:
    """Encrypt data for sending back to frontend"""
    try:
        # Create key from secret
        key = hashlib.sha256(SECRET_KEY.encode()).digest()[:32]
        
        # Generate random IV
        iv = os.urandom(16)
        
        # Encrypt data
        cipher = AES.new(key, AES.MODE_CBC, iv)
        json_data = json.dumps(data).encode('utf-8')
        
        # Pad data and encrypt
        from Crypto.Util.Padding import pad
        padded_data = pad(json_data, 16)
        encrypted_data = cipher.encrypt(padded_data)
        
        # Combine IV and encrypted data, then base64 encode
        result = base64.b64encode(iv + encrypted_data).decode('utf-8')
        return result
        
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")
