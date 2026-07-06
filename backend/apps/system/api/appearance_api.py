from fastapi import APIRouter, Request

from apps.system.models.sys_arg import SysArgModel
from apps.system.crud.sys_arg_manage import get_group_args

from common.core.deps import SessionDep

router = APIRouter(tags=["system/appearance"], prefix="/system/appearance", include_in_schema=False)


@router.get("/ui")
async def get_appearance_ui(session: SessionDep) -> list:
    args = await get_group_args(session=session, flag='appearance.')
    return [{"pkey": x.pkey.replace('appearance.', ''), "pval": x.pval} for x in args]
