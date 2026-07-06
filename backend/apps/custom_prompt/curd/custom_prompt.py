from typing import Optional, List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
from apps.custom_prompt.models.custom_prompt_model import CustomPrompt, CustomPromptTypeEnum


async def find_custom_prompts(
    session: Session,
    custom_prompt_type: CustomPromptTypeEnum,
    oid: int,
    datasource: Optional[int] = None,
    advanced_application_id: Optional[int] = None
) -> Tuple[str, List[dict]]:
    prompts = []
    
    # 全局提示词
    stmt = select(CustomPrompt).where(
        CustomPrompt.type == custom_prompt_type,
        CustomPrompt.oid == oid,
        CustomPrompt.specific_ds == False
    )
    result = session.exec(stmt).all()
    for p in result:
        prompts.append({
            "name": p.name,
            "prompt": p.prompt,
            "type": p.type.value
        })
    
    # 指定数据源的提示词
    if datasource is not None:
        stmt2 = select(CustomPrompt).where(
            CustomPrompt.type == custom_prompt_type,
            CustomPrompt.specific_ds == True,
            CustomPrompt.datasource_ids != None
        )
        result2 = session.exec(stmt2).all()
        for p in result2:
            ds_ids = p.datasource_ids or []
            if isinstance(ds_ids, list) and datasource in ds_ids:
                prompts.append({
                    "name": p.name,
                    "prompt": p.prompt,
                    "type": p.type.value
                })
    
    # 高级应用提示词
    if advanced_application_id is not None:
        stmt3 = select(CustomPrompt).where(
            CustomPrompt.type == custom_prompt_type,
            CustomPrompt.advanced_application == advanced_application_id
        )
        result3 = session.exec(stmt3).all()
        for p in result3:
            prompts.append({
                "name": p.name,
                "prompt": p.prompt,
                "type": p.type.value
            })
    
    prompt_text = '\n'.join([f"{p['name']}:\n{p['prompt']}" for p in prompts])
    return prompt_text, prompts
