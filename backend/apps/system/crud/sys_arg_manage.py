from typing import Optional
import json
from sqlalchemy import select, or_
from sqlmodel import Session
from apps.system.models.sys_arg import SysArgModel, SysArgSchema
from common.core.config import settings
import os


async def get_group_args(session: Session, flag: Optional[str] = None) -> list[SysArgSchema]:
    stmt = select(SysArgModel).order_by(SysArgModel.sort_no, SysArgModel.id)
    if flag:
        stmt = stmt.where(SysArgModel.pkey.startswith(flag))
    result = session.exec(stmt).all()
    return [
        SysArgSchema(
            id=x.id if x.id else 0,
            pkey=x.pkey,
            pval=x.pval,
            ptype=x.ptype,
            sort_no=x.sort_no
        ) for x in result
    ]


async def save_group_args(session: Session, sys_args: list[SysArgModel], file_mapping: Optional[dict[str, str]] = None):
    for arg in sys_args:
        if arg.id:
            existing = session.get(SysArgModel, arg.id)
            if existing:
                existing.pval = arg.pval
                existing.ptype = arg.ptype
                existing.sort_no = arg.sort_no
        else:
            existing = session.exec(
                select(SysArgModel).where(SysArgModel.pkey == arg.pkey)
            ).first()
            if existing:
                existing.pval = arg.pval
                existing.ptype = arg.ptype
                existing.sort_no = arg.sort_no
            else:
                new_arg = SysArgModel(
                    pkey=arg.pkey,
                    pval=arg.pval,
                    ptype=arg.ptype,
                    sort_no=arg.sort_no
                )
                session.add(new_arg)
    
    if file_mapping:
        for flag_name, file_id in file_mapping.items():
            existing = session.exec(
                select(SysArgModel).where(SysArgModel.pkey == flag_name)
            ).first()
            if existing and existing.pval:
                _delete_file(existing.pval)
    
    session.commit()


def _delete_file(file_id: str):
    """简单文件删除"""
    upload_dir = getattr(settings, 'UPLOAD_FOLDER', 'uploads')
    file_path = os.path.join(upload_dir, file_id)
    if os.path.exists(file_path):
        os.remove(file_path)
