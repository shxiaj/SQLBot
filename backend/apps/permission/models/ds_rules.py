from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, BigInteger, Text, DateTime, Column, Boolean
from sqlmodel import Field, SQLModel


class DsRules(SQLModel, table=True):
    __tablename__ = "ds_rules"

    id: int = Field(default=None, sa_column=Column(Integer, primary_key=True))
    enable: bool = Field(default=True, sa_column=Column(Boolean, nullable=False))
    name: str = Field(max_length=128, nullable=False)
    description: Optional[str] = Field(default=None, max_length=512, sa_column=Column(Text, nullable=True))
    permission_list: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    user_list: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    white_list_user: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    create_time: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    oid: Optional[int] = Field(default=None, sa_column=Column(BigInteger, nullable=True))
