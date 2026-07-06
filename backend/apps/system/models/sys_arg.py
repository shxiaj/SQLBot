from typing import Optional
from pydantic import BaseModel
from sqlalchemy import BigInteger, Column
from sqlmodel import Field, SQLModel


def id_default():
    return None


class SysArgModel(SQLModel, table=True):
    __tablename__ = "sys_arg"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True))
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
