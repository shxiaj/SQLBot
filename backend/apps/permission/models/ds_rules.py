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
