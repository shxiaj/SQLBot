import base64


def sqlbot_decrypt(text: str) -> str:
    if not text:
        return ''
    try:
        return base64.b64decode(text).decode('utf-8')
    except Exception:
        return text


def sqlbot_encrypt(text: str) -> str:
    if not text:
        return ''
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')
