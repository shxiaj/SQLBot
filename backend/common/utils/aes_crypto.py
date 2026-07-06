from typing import Optional
from common.core.config import settings
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

simple_aes_iv_text = 'sqlbot_em_aes_iv'


def _get_cipher(key: str) -> AES:
    key_bytes = key.encode('utf-8')[:32]
    iv = simple_aes_iv_text.encode('utf-8')[:16]
    return AES.new(key_bytes, AES.MODE_CBC, iv)


def sqlbot_aes_encrypt(text: str, key: Optional[str] = None) -> str:
    cipher = _get_cipher(key or settings.SECRET_KEY)
    encrypted = cipher.encrypt(pad(text.encode('utf-8'), AES.block_size))
    return base64.b64encode(encrypted).decode('utf-8')


def sqlbot_aes_decrypt(text: str, key: Optional[str] = None) -> str:
    cipher = _get_cipher(key or settings.SECRET_KEY)
    decrypted = cipher.decrypt(base64.b64decode(text))
    return unpad(decrypted, AES.block_size).decode('utf-8')


def simple_aes_encrypt(text: str, key: Optional[str] = None, ivtext: Optional[str] = None) -> str:
    iv = (ivtext or simple_aes_iv_text).encode('utf-8')[:16]
    key_bytes = (key or settings.SECRET_KEY).encode('utf-8')[:32]
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(text.encode('utf-8'), AES.block_size))
    return base64.b64encode(encrypted).decode('utf-8')


def simple_aes_decrypt(text: str, key: Optional[str] = None, ivtext: Optional[str] = None) -> str:
    iv = (ivtext or simple_aes_iv_text).encode('utf-8')[:16]
    key_bytes = (key or settings.SECRET_KEY).encode('utf-8')[:32]
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(base64.b64decode(text))
    return unpad(decrypted, AES.block_size).decode('utf-8')
