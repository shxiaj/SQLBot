from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlalchemy import BigInteger, Text, DateTime, Column
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

    id: int = Field(sa_column=Column(BigInteger, primary_key=True))
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
