from datetime import datetime
from enum import Enum
from typing import Optional, Any

from sqlalchemy import BigInteger, Text, DateTime, Boolean, JSON, Column
from sqlmodel import Field, SQLModel


class CustomPromptTypeEnum(str, Enum):
    GENERATE_SQL = 'GENERATE_SQL'
    ANALYSIS = 'ANALYSIS'
    PREDICT_DATA = 'PREDICT_DATA'


class CustomPrompt(SQLModel, table=True):
    __tablename__ = "custom_prompt"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True))
    oid: Optional[int] = Field(default=None, sa_column=Column(BigInteger, nullable=True))
    type: str = Field(max_length=20)
    create_time: Optional[datetime] = Field(default=None, sa_column=DateTime)
    name: str = Field(max_length=255)
    prompt: str = Field(sa_column=Text)
    specific_ds: bool = Field(default=False, sa_column=Column(Boolean, nullable=True))
    datasource_ids: Any = Field(default=None, sa_column=Column(JSON, nullable=True))
