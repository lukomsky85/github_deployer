# utils/crypto.py
import os
import base64
import hashlib
import uuid

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

class TokenManager:
    TOKEN_FILE = "secure_token.dat"
    
    @staticmethod
    def _get_key():
        try: 
            machine_id = str(uuid.getnode())
        except: 
            machine_id = "default"
        key_hash = hashlib.sha256((machine_id + "Salt_v3.2").encode()).digest()
        return base64.urlsafe_b64encode(key_hash)

    @staticmethod
    def save_token(token):
        if not CRYPTO_AVAILABLE or not token: 
            return False
        try:
            with open(TokenManager.TOKEN_FILE, 'wb') as f:
                f.write(Fernet(TokenManager._get_key()).encrypt(token.encode()))
            return True
        except: 
            return False

    @staticmethod
    def load_token():
        if not CRYPTO_AVAILABLE or not os.path.exists(TokenManager.TOKEN_FILE): 
            return None
        try:
            with open(TokenManager.TOKEN_FILE, 'rb') as f:
                return Fernet(TokenManager._get_key()).decrypt(f.read()).decode()
        except:
            if os.path.exists(TokenManager.TOKEN_FILE): 
                os.remove(TokenManager.TOKEN_FILE)
            return None

    @staticmethod
    def delete_token():
        if os.path.exists(TokenManager.TOKEN_FILE): 
            os.remove(TokenManager.TOKEN_FILE)