from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import BigInteger, Text, DateTime, Boolean, JSON, Column, Enum as SQLAlchemyEnum
from sqlmodel import Field, SQLModel


def enum_values(enum):
    return [e.value for e in enum]


class CustomPromptTypeEnum(str, Enum):
    GENERATE_SQL = 'GENERATE_SQL'
    ANALYSIS = 'ANALYSIS'
    PREDICT_DATA = 'PREDICT_DATA'


class CustomPrompt(SQLModel, table=True):
    __tablename__ = "custom_prompt"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True))
    oid: Optional[int] = Field(default=None, sa_column=BigInteger)
    type: CustomPromptTypeEnum = Field(
        sa_column=Column(SQLAlchemyEnum(CustomPromptTypeEnum, native_enum=False, values_callable=enum_values, length=32))
    )
    create_time: Optional[datetime] = Field(default=None, sa_column=DateTime)
    name: str = Field(max_length=255)
    prompt: str = Field(sa_column=Text)
    specific_ds: bool = Field(default=False, sa_column=Boolean)
    datasource_ids: Optional[List[int]] = Field(default=None, sa_column=Column(JSON))
    advanced_application: int = Field(default=0, sa_column=BigInteger)
