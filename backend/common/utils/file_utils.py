import os
import uuid
import re
from typing import List, Optional, Tuple
from fastapi import UploadFile, HTTPException


class SQLBotFileUtils:
    """文件工具类"""
    
    @staticmethod
    def get_file_path(file_id: str) -> str:
        from common.core.config import settings
        return os.path.join(settings.UPLOAD_FOLDER, file_id)
    
    @staticmethod
    def split_filename_and_flag(filename: str) -> Tuple[str, str]:
        match = re.match(r'^(.+)_([a-f0-9]{8})$', filename)
        if match:
            return match.group(1), match.group(2)
        return filename, ''
    
    @staticmethod
    def check_file(file: UploadFile, file_types: List[str], limit_file_size: int):
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in file_types:
            raise ValueError(f"不支持的文件类型: {ext}")
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        if size > limit_file_size:
            raise ValueError(f"文件大小超过限制（最大 {limit_file_size // 1024 // 1024} M）")
    
    @staticmethod
    async def upload(file: UploadFile) -> str:
        file_id = str(uuid.uuid4())
        file.filename = f"{file_id}_{file.filename}"
        file_path = SQLBotFileUtils.get_file_path(file.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        return file_id
    
    @staticmethod
    def delete_file(file_id: str):
        file_path = SQLBotFileUtils.get_file_path(file_id)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    @staticmethod
    def generate_filename(original_name: str) -> str:
        return f"{uuid.uuid4().hex[:8]}_{original_name}"
    
    @staticmethod
    def is_real_image(file: UploadFile) -> bool:
        file.file.seek(0)
        header = file.file.read(8)
        file.file.seek(0)
        signatures = {b'\xff\xd8\xff': '.jpg', b'\x89PNG': '.png', b'GIF': '.gif'}
        for sig, ext in signatures.items():
            if header.startswith(sig):
                return True
        return False
    
    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        return bool(re.match(r'^[a-zA-Z0-9._-]+$', filename))
    
    @staticmethod
    def validate_file_header(file: UploadFile) -> bool:
        file.file.seek(0)
        header = file.file.read(4)
        file.file.seek(0)
        return len(header) > 0
