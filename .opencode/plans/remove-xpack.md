# 移除 sqlbot-xpack 限制计划

## 执行前确认

请确认以下操作：
1. 删除 `pyproject.toml` 中 `sqlbot-xpack` 依赖
2. 新建 8 个本地模型/工具文件
3. 修改 13 个后端文件
4. 修改 9 个前端文件 + 删除 14 个 xpack 组件

## 一、新建文件内容

### 1. apps/permission/models/ds_rules.py
```python
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Text, DateTime
from sqlmodel import Field, SQLModel

class DsRules(SQLModel, table=True):
    __tablename__ = "ds_rules"
    id: int = Field(primary_key=True)
    oid: int = Field(sa_column=BigInteger)
    enable: bool = Field(default=True)
    name: str = Field(max_length=128)
    description: Optional[str] = Field(default=None, max_length=512, nullable=True)
    permission_list: str = Field(sa_column=Text)
    user_list: str = Field(sa_column=Text)
    white_list_user: str = Field(sa_column=Text)
    create_time: datetime = Field(sa_column=DateTime)
```

### 2. apps/permission/models/ds_permission.py
```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy import BigInteger, Text, DateTime
from sqlmodel import Field, SQLModel

class PermissionTree(BaseModel):
    tree_id: str = ''
    tree_node_name: str = ''
    children: Optional[List['PermissionTree']] = None

class ColumnPermissionItem(BaseModel):
    field_id: int = 0
    field_name: str = ''
    enable: bool = True

class DsPermission(SQLModel, table=True):
    __tablename__ = "ds_permission"
    id: int = Field(primary_key=True, sa_column=BigInteger)
    name: Optional[str] = Field(default=None, max_length=128, nullable=True)
    enable: bool = Field(default=True)
    auth_target_type: str = Field(max_length=128)
    auth_target_id: int = Field(sa_column=BigInteger)
    type: str = Field(max_length=64)
    ds_id: int = Field(sa_column=BigInteger)
    table_id: int = Field(sa_column=BigInteger)
    expression_tree: str = Field(sa_column=Text)
    permissions: str = Field(sa_column=Text)
    white_list_user: str = Field(sa_column=Text)
    create_time: datetime = Field(sa_column=DateTime)

class PermissionDTO(SQLModel):
    id: Optional[int] = None
    name: Optional[str] = None
    enable: bool = True
    auth_target_type: str = 'user'
    auth_target_id: Optional[int] = None
    type: str = 'row'
    ds_id: Optional[int] = None
    table_id: Optional[int] = None
    expression_tree: str = '{}'
    permissions: str = '[]'
    white_list_user: str = '[]'
    create_time: Optional[datetime] = None
    tree: Optional[PermissionTree] = None
    permission_list: List[ColumnPermissionItem] = Field(default_factory=list)
    ds_name: Optional[str] = None
    table_name: Optional[str] = None
```

### 3. apps/custom_prompt/models/custom_prompt_model.py
```python
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import BigInteger, Text, DateTime, Boolean, JSON
from sqlmodel import Field, SQLModel

class CustomPromptTypeEnum(str, Enum):
    GENERATE_SQL = 'GENERATE_SQL'
    ANALYSIS = 'ANALYSIS'
    PREDICT_DATA = 'PREDICT_DATA'

class CustomPrompt(SQLModel, table=True):
    __tablename__ = "custom_prompt"
    id: Optional[int] = Field(default=None, primary_key=True, sa_column=BigInteger)
    oid: Optional[int] = Field(default=None, sa_column=BigInteger)
    type: CustomPromptTypeEnum = Field()
    create_time: Optional[datetime] = Field(default=None, sa_column=DateTime)
    name: str = Field(max_length=255)
    prompt: str = Field(sa_column=Text)
    specific_ds: bool = Field(default=False, sa_column=Boolean)
    datasource_ids: Optional[List[int]] = Field(default=None, sa_column=JSON)
    advanced_application: int = Field(default=0, sa_column=BigInteger)
```

### 4. apps/system/models/sys_arg.py
```python
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import BigInteger
from sqlmodel import Field, SQLModel

def id_default():
    return None

class SysArgModel(SQLModel, table=True):
    __tablename__ = "sys_arg"
    id: Optional[int] = Field(default=None, primary_key=True, sa_column=BigInteger)
    pkey: str = Field(max_length=255, unique=True)
    pval: str = Field(max_length=255)
    ptype: str = Field(default='str', max_length=255)
    sort_no: int = Field(default=0)

class SysArgSchema(BaseModel):
    id: int = Field(default=0)
    pkey: str
    pval: str
    ptype: str = 'str'
    sort_no: int = 0
```

### 5. apps/permission/api/permission.py
```python
from sqlalchemy.orm import Session
from apps.datasource.models.datasource import CoreDatasource, CoreTable
from apps.permission.models.ds_permission import DsPermission, PermissionDTO, PermissionTree, ColumnPermissionItem
from apps.datasource.crud.row_permission import transFilterTreeToPermissionTree, parse_permissions

def transRecord2DTO(session: Session, record: DsPermission) -> PermissionDTO:
    dto = PermissionDTO.model_validate(record)
    dto.tree = transFilterTreeToPermissionTree(record.expression_tree)
    dto.permission_list = parse_permissions(record.permissions)
    ds = session.get(CoreDatasource, record.ds_id)
    if ds:
        dto.ds_name = ds.name
    table = session.get(CoreTable, record.table_id)
    if table:
        dto.table_name = table.table_name
    return dto
```

### 6. apps/system/crud/sys_arg_manage.py
```python
from typing import Optional
from sqlalchemy import select, delete
from sqlmodel import Session
from common.core.db import engine
from apps.system.models.sys_arg import SysArgModel, SysArgSchema
from sqlbot_xpack.file_utils import SQLBotFileUtils

async def get_group_args(session: Session, flag: Optional[str] = None) -> list[SysArgSchema]:
    stmt = select(SysArgModel).order_by(SysArgModel.sort_no)
    if flag:
        stmt = stmt.where(SysArgModel.pkey.startswith(flag))
    result = session.exec(stmt)
    return [SysArgSchema(id=x.id, pkey=x.pkey, pval=x.pval, ptype=x.ptype, sort_no=x.sort_no) for x in result]

async def save_group_args(session: Session, sys_args: list[SysArgModel], file_mapping: Optional[dict[str, str]] = None):
    for arg in sys_args:
        existing = session.get(SysArgModel, arg.id) if arg.id else session.exec(
            select(SysArgModel).where(SysArgModel.pkey == arg.pkey)
        ).first()
        if existing:
            existing.pval = arg.pval
            existing.ptype = arg.ptype
            existing.sort_no = arg.sort_no
        else:
            session.add(SysArgModel(**arg.model_dump()))
    if file_mapping:
        for flag_name, file_id in file_mapping.items():
            existing = session.exec(
                select(SysArgModel).where(SysArgModel.pkey == f"{flag_name}")
            ).first()
            if existing:
                SQLBotFileUtils.delete_file(existing.pval)
    session.commit()
```

### 7. apps/custom_prompt/curd/custom_prompt.py
```python
from typing import Optional, List, Tuple
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from apps.custom_prompt.models.custom_prompt_model import CustomPrompt, CustomPromptTypeEnum
from apps.datasource.models.datasource import CoreDatasource

async def find_custom_prompts(session: Session, custom_prompt_type: CustomPromptTypeEnum, 
                              oid: int, datasource: Optional[int] = None, 
                              advanced_application_id: Optional[int] = None) -> Tuple[str, List[dict]]:
    prompts = []
    stmt = select(CustomPrompt).where(
        CustomPrompt.type == custom_prompt_type,
        CustomPrompt.oid == oid,
        CustomPrompt.specific_ds == False
    )
    result = session.exec(stmt).all()
    prompts.extend([{"name": p.name, "prompt": p.prompt, "type": p.type.value} for p in result])
    
    if datasource is not None:
        stmt2 = select(CustomPrompt).where(
            CustomPrompt.type == custom_prompt_type,
            CustomPrompt.specific_ds == True,
            CustomPrompt.datasource_ids.cast(List[int]).contains([datasource])
        )
        result2 = session.exec(stmt2).all()
        prompts.extend([{"name": p.name, "prompt": p.prompt, "type": p.type.value} for p in result2])
    
    if advanced_application_id is not None:
        stmt3 = select(CustomPrompt).where(
            CustomPrompt.type == custom_prompt_type,
            CustomPrompt.advanced_application == advanced_application_id
        )
        result3 = session.exec(stmt3).all()
        prompts.extend([{"name": p.name, "prompt": p.prompt, "type": p.type.value} for p in result3])
    
    prompt_text = '\n'.join([f"{p['name']}:\n{p['prompt']}" for p in prompts])
    return prompt_text, prompts
```

### 8. common/utils/file_utils.py
```python
import os
import uuid
import re
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import UploadFile, HTTPException
from common.core.config import settings
from apps.system.models.assistant import AssistantModel

class SQLBotFileUtils:
    UPLOAD_DIR = 'uploads'
    
    @staticmethod
    def get_file_path(file_id: str) -> str:
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
```

### 1. DsRules (数据权限规则)
```python
class DsRules(SQLModel, table=True):
    id: int = Field(primary_key=True)
    oid: int = Field(sa_column=Column(BigInteger))
    enable: bool = Field(default=True)
    name: str = Field(max_length=128)
    description: str | None = Field(max_length=512, nullable=True)
    permission_list: str = Field(sa_column=Column(Text))
    user_list: str = Field(sa_column=Column(Text))
    white_list_user: str = Field(sa_column=Column(Text))
    create_time: datetime = Field(sa_column=Column(DateTime))
```

### 2. DsPermission (数据权限)
```python
class DsPermission(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_column=Column(BigInteger))
    name: str | None = Field(max_length=128, nullable=True)
    enable: bool = Field(default=True)
    auth_target_type: str = Field(max_length=128)
    auth_target_id: int = Field(sa_column=Column(BigInteger))
    type: str = Field(max_length=64)
    ds_id: int = Field(sa_column=Column(BigInteger))
    table_id: int = Field(sa_column=Column(BigInteger))
    expression_tree: str = Field(sa_column=Column(Text))
    permissions: str = Field(sa_column=Column(Text))
    white_list_user: str = Field(sa_column=Column(Text))
    create_time: datetime = Field(sa_column=Column(DateTime))

class PermissionTree(BaseModel):
    tree_id: str
    tree_node_name: str
    children: Optional[List['PermissionTree']] = None

class ColumnPermissionItem(BaseModel):
    field_id: int
    field_name: str
    enable: bool

class PermissionDTO(SQLModel):
    id: int | None = None
    name: str | None = None
    enable: bool = True
    auth_target_type: str = 'user'
    auth_target_id: int | None = None
    type: str = 'row'
    ds_id: int | None = None
    table_id: int | None = None
    expression_tree: str = '{}'
    permissions: str = '[]'
    white_list_user: str = '[]'
    create_time: datetime = Field(default_factory=datetime.now)
    tree: PermissionTree | None = None
    permission_list: List[ColumnPermissionItem] = Field(default_factory=list)
    ds_name: str | None = None
    table_name: str | None = None
```

### 3. CustomPrompt (自定义提示词)
```python
class CustomPromptTypeEnum(str, Enum):
    GENERATE_SQL = 'GENERATE_SQL'
    ANALYSIS = 'ANALYSIS'
    PREDICT_DATA = 'PREDICT_DATA'

class CustomPrompt(SQLModel, table=True):
    id: int | None = Field(primary_key=True, sa_column=Column(BigInteger))
    oid: int | None = Field(sa_column=Column(BigInteger, default=1))
    type: CustomPromptTypeEnum = Field(sa_column=Column(Enum('GENERATE_SQL', 'ANALYSIS', 'PREDICT_DATA', name='customprompttypeenum')))
    create_time: datetime = Field(sa_column=Column(DateTime))
    name: str = Field(max_length=255)
    prompt: str = Field(sa_column=Column(Text))
    specific_ds: bool = Field(default=False, sa_column=Column(Boolean))
    datasource_ids: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    advanced_application: int = Field(sa_column=Column(BigInteger))
```

### 4. SysArgModel (系统参数)
```python
class SysArgModel(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default_factory=id_default, sa_index=True, sa_column=Column(BigInteger))
    pkey: str = Field(max_length=255, unique=True)
    pval: str = Field(max_length=255)
    ptype: str = Field(max_length=255, default='str')
    sort_no: int = Field(default=0)

class SysArgSchema(BaseModel):
    id: int = Field(default=0)
    pkey: str
    pval: str
    ptype: str = 'str'
    sort_no: int = 0
```

## 二、xpack 函数定义（需迁移到项目内）

### 1. transRecord2DTO
```python
def transRecord2DTO(session: Session, record: DsPermission) -> PermissionDTO:
    dto = PermissionDTO.model_validate(record)
    dto.tree = transFilterTreeToPermissionTree(...)  # 使用已有的 transFilterTree 转换
    dto.permission_list = parse_permissions(record.permissions)
    dto.ds_name = get_datasource_name(session, record.ds_id)
    dto.table_name = get_table_name(session, record.table_id)
    return dto
```

### 2. file_utils (SQLBotFileUtils)
```python
class SQLBotFileUtils:
    @staticmethod
    def get_file_path(file_id: str) -> str
    @staticmethod
    def split_filename_and_flag(filename: str) -> tuple[str, str]
    @staticmethod
    def check_file(file, file_types, limit_file_size)
    @staticmethod
    async def upload(file) -> str
    @staticmethod
    def delete_file(file_id: str)
    @staticmethod
    def generate_filename(original_name: str) -> str
    @staticmethod
    def is_real_image(file) -> bool
    @staticmethod
    def is_safe_filename(filename: str) -> bool
    @staticmethod
    def validate_file_header(file) -> bool
```

### 3. arg_manage (get_group_args, save_group_args)
```python
async def get_group_args(session: Session, flag: str | None = None) -> list[SysArgSchema]
async def save_group_args(session: Session, sys_args: list[SysArgModel], file_mapping: dict | None = None)
```

### 4. find_custom_prompts
```python
async def find_custom_prompts(session: Session, custom_prompt_type: CustomPromptTypeEnum, oid: int, datasource: int | None = None, advanced_application_id: int | None = None) -> tuple[str, list[dict]]
```

### 5. SQLBotLicenseUtil
```python
class SQLBotLicenseUtil:
    @staticmethod
    def valid() -> bool:
        return True  # 始终返回 true
```

### 6. 加密函数
```python
async def sqlbot_encrypt(text: str) -> str: return base64.b64encode(text.encode()).decode()
async def sqlbot_decrypt(text: str) -> str: return base64.b64decode(text.encode()).decode()
```

## 三、后端文件改动清单

| 文件 | 改动 |
|------|------|
| `pyproject.toml` | 删除 sqlbot-xpack 依赖 |
| `main.py` | 删除 import sqlbot_xpack 及 3 处调用 |
| `common/utils/crypto.py` | 重写为 base64 加密 |
| `common/utils/aes_crypto.py` | 重写为本地 AES 实现 |
| `apps/permission/models/ds_rules.py` | 新建 - DsRules 模型 |
| `apps/permission/models/ds_permission.py` | 新建 - DsPermission, PermissionDTO 模型 |
| `apps/permission/api/permission.py` | 新建 - transRecord2DTO 函数 |
| `apps/custom_prompt/models/custom_prompt_model.py` | 新建 - CustomPrompt, CustomPromptTypeEnum |
| `apps/system/models/sys_arg.py` | 新建 - SysArgModel, SysArgSchema |
| `apps/system/crud/sys_arg_manage.py` | 新建 - get_group_args, save_group_args |
| `apps/custom_prompt/curd/custom_prompt.py` | 新建 - find_custom_prompts |
| `common/utils/file_utils.py` | 新建 - SQLBotFileUtils |
| `common/audit/schemas/log_utils.py` | 使用本地模型替换 xpack 模型 |
| `common/audit/schemas/logger_decorator.py` | 使用本地函数替换 xpack 函数 |
| `apps/datasource/crud/permission.py` | 使用本地模型替换 |
| `apps/datasource/crud/datasource.py` | 使用本地模型替换 |
| `apps/system/crud/parameter_manage.py` | 使用本地模型和函数 |
| `apps/system/api/parameter.py` | 使用本地模型 |
| `apps/system/api/assistant.py` | 使用本地 file_utils |
| `apps/system/api/login.py` | 删除 xpack logout |
| `apps/chat/task/llm.py` | 使用本地模型，移除许可证检查 |

## 四、前端文件改动清单

| 文件 | 改动 |
|------|------|
| `router/watch.ts` | 移除 loadXpackStatic 和 LicenseGenerator.generateRouters |
| `api/login.ts` | 移除 sqlbotEncrypt，改用 btoa |
| `api/system.ts` | 同上 |
| `stores/appearance.ts` | 移除 LicenseGenerator.getLicense 检查 |
| `utils/request.ts` | 移除 /xpack_static/ 特殊处理 |
| `views/login/index.vue` | 移除 Handler 组件 |
| `views/login/xpack/*.vue` | 删除整个目录 |
| `views/login/xpack/*.ts` | 删除整个目录 |
| `views/system/parameter/index.vue` | 移除 PlatformParam 组件 |
| `views/system/parameter/xpack/PlatformParam.vue` | 删除 |
| `views/system/user/User.vue` | 移除许可证检查 |
| `views/system/embedded/iframe.vue` | 移除 xpack_static 脚本引用 |

## 二、后端文件修改详情

### 1. pyproject.toml
删除第40行: `"sqlbot-xpack>=0.0.5.22,<0.0.6.0",`

### 2. main.py
- 删除第4行: `import sqlbot_xpack`
- 删除第59行: `await sqlbot_xpack.core.clean_xpack_cache()`
- 删除第61行: `await sqlbot_xpack.core.monitor_app(app)`
- 删除第214行: `sqlbot_xpack.init_fastapi_app(app)`

### 3. common/utils/crypto.py (重写)
```python
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
```

### 4. common/utils/aes_crypto.py (重写)
```python
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
```

### 5. common/audit/schemas/log_utils.py
将:
- `from sqlbot_xpack.permissions.models.ds_rules import DsRules` → `from apps.permission.models.ds_rules import DsRules`
- `from sqlbot_xpack.custom_prompt.models.custom_prompt_model import CustomPrompt` → `from apps.custom_prompt.models.custom_prompt_model import CustomPrompt`
- `from sqlbot_xpack.permissions.models.ds_permission import DsPermission` → `from apps.permission.models.ds_permission import DsPermission`

### 6. common/audit/schemas/logger_decorator.py
将:
- `from sqlbot_xpack.audit.curd.audit import build_resource_union_query` → 保留现有实现（已在 log_utils.py 中定义）

### 7. apps/datasource/crud/permission.py
将:
- `from sqlbot_xpack.permissions.api.permission import transRecord2DTO` → `from apps.permission.api.permission import transRecord2DTO`
- `from sqlbot_xpack.permissions.models.ds_permission import DsPermission, PermissionDTO` → `from apps.permission.models.ds_permission import DsPermission, PermissionDTO`
- `from sqlbot_xpack.permissions.models.ds_rules import DsRules` → `from apps.permission.models.ds_rules import DsRules`

### 8. apps/datasource/crud/datasource.py
将:
- `from sqlbot_xpack.permissions.models.ds_rules import DsRules` → `from apps.permission.models.ds_rules import DsRules`

### 9. apps/system/crud/parameter_manage.py
将:
- `from sqlbot_xpack.config.arg_manage import get_group_args, save_group_args` → `from apps.system.crud.sys_arg_manage import get_group_args, save_group_args`
- `from sqlbot_xpack.config.model import SysArgModel` → `from apps.system.models.sys_arg import SysArgModel`
- `from sqlbot_xpack.file_utils import SQLBotFileUtils` → `from common.utils.file_utils import SQLBotFileUtils`

### 10. apps/system/api/parameter.py
将:
- `from sqlbot_xpack.config.model import SysArgModel` → `from apps.system.models.sys_arg import SysArgModel`

### 11. apps/system/api/assistant.py
将:
- `from sqlbot_xpack.file_utils import SQLBotFileUtils` → `from common.utils.file_utils import SQLBotFileUtils`

### 12. apps/system/api/login.py
将:
- `from sqlbot_xpack.authentication.manage import logout as xpack_logout` → 删除
- 删除第51行: `return await xpack_logout(session, request, dto)`
- 将第48-52行改为: `@router.post("/logout")\nasync def logout(session: SessionDep, request: Request, dto: LogoutSchema):\n    return None`

### 13. apps/chat/task/llm.py
将:
- `from sqlbot_xpack.config.model import SysArgModel` → `from apps.system.models.sys_arg import SysArgModel`
- `from sqlbot_xpack.custom_prompt.curd.custom_prompt import find_custom_prompts` → `from apps.custom_prompt.curd.custom_prompt import find_custom_prompts`
- `from sqlbot_xpack.custom_prompt.models.custom_prompt_model import CustomPromptTypeEnum` → `from apps.custom_prompt.models.custom_prompt_model import CustomPromptTypeEnum`
- `from sqlbot_xpack.license.license_manage import SQLBotLicenseUtil` → `from apps.custom_prompt.models.custom_prompt_model import SQLBotLicenseUtil`
- 在 CustomPromptTypeEnum 后添加: `class SQLBotLicenseUtil:\n    @staticmethod\n    def valid() -> bool:\n        return True`
- 或单独创建一个 `common/utils/license_util.py` 文件

## 三、前端文件修改详情

### 1. router/watch.ts
```typescript
// 删除第19行: await loadXpackStatic()
// 删除第21行: LicenseGenerator.generateRouters(router)
// 删除第80-98行: loadXpackStatic 函数定义
```

### 2. api/login.ts
```typescript
// 第5-6行改为:
username: credentials.username,
password: credentials.password,
// 或删除 btoa 包装
```

### 3. api/system.ts
```typescript
// 第9,12,19,22行:
// param.api_key = LicenseGenerator.sqlbotEncrypt(data.api_key) → param.api_key = data.api_key
// param.api_domain = LicenseGenerator.sqlbotEncrypt(data.api_domain) → param.api_domain = data.api_domain
```

### 4. stores/appearance.ts
```typescript
// 第256-262行:
// 删除 LicenseGenerator.getLicense() 检查
// 直接执行: const resData = await request.get('/system/appearance/ui')
```

### 5. utils/request.ts
```typescript
// 第138-141行: 删除 /xpack_static/ 特殊处理
```

### 6. views/login/index.vue
```vue
<!-- 第86行: 删除 <Handler> 组件引用 -->
<!-- 第6行: 删除 class="xpack-login-handler-mask" -->
```

### 7. views/system/parameter/index.vue
```typescript
// 第5行: 删除 import PlatformParam from './xpack/PlatformParam.vue'
// 第197行: 删除 <platform-param />
```

### 8. views/system/user/User.vue
```typescript
// 第1184-1193行: 改为始终加载数据
const showSyncBtn = ref(false)
onMounted(() => {
  loadData()
  // ... 其余代码不变
})
```

### 9. views/system/embedded/iframe.vue
```javascript
// 第526行: 删除 sqlbot-embedded-dynamic.umd.js 加载
// 第529-534行: 删除轮询 mounted 代码
```

## 四、前端文件删除清单

需要删除以下文件:
- `frontend/src/views/login/xpack/Handler.vue`
- `frontend/src/views/login/xpack/QrcodeLdap.vue`
- `frontend/src/views/login/xpack/Oidc.vue`
- `frontend/src/views/login/xpack/Cas.vue`
- `frontend/src/views/login/xpack/Oauth2.vue`
- `frontend/src/views/login/xpack/QrTab.vue`
- `frontend/src/views/login/xpack/PlatformClient.ts`
- `frontend/src/views/login/xpack/platformUtils.ts`
- `frontend/src/views/login/xpack/LdapLoginForm.vue`
- `frontend/src/views/login/xpack/LarkQr.vue`
- `frontend/src/views/login/xpack/LarksuiteQr.vue`
- `frontend/src/views/login/xpack/DingtalkQr.vue`
- `frontend/src/views/login/xpack/WecomQr.vue`
- `frontend/src/views/system/parameter/xpack/PlatformParam.vue`

1. 后端模型定义 (4个新文件)
2. 后端工具函数 (file_utils, arg_manage, custom_prompt, permission)
3. 后端核心文件 (crypto, aes_crypto)
4. 后端主文件 (main.py)
5. 后端 CRUD/API 文件
6. 前端路由和 API
7. 前端组件移除
