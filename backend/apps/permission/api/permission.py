from sqlalchemy.orm import Session
from sqlalchemy import or_
from apps.datasource.models.datasource import CoreDatasource, CoreTable
from apps.permission.models.ds_permission import DsPermission, PermissionDTO, PermissionTree, ColumnPermissionItem


def transRecord2DTO(session: Session, record: DsPermission) -> PermissionDTO:
    dto = PermissionDTO.model_validate(record)
    
    # Parse expression_tree to PermissionTree
    import json
    try:
        tree_data = json.loads(record.expression_tree) if record.expression_tree else {}
        dto.tree = _parse_tree(tree_data)
    except (json.JSONDecodeError, TypeError):
        dto.tree = None
    
    # Parse permissions to permission_list
    try:
        perm_data = json.loads(record.permissions) if record.permissions else []
        dto.permission_list = [
            ColumnPermissionItem(
                field_id=item.get('field_id', 0),
                field_name=item.get('field_name', ''),
                enable=item.get('enable', True)
            ) for item in perm_data
        ]
    except (json.JSONDecodeError, TypeError):
        dto.permission_list = []
    
    # Get datasource name
    ds = session.get(CoreDatasource, record.ds_id)
    if ds:
        dto.ds_name = ds.name
    
    # Get table name
    table = session.get(CoreTable, record.table_id)
    if table:
        dto.table_name = table.table_name
    
    return dto


def _parse_tree(data: dict) -> PermissionTree:
    """递归解析树结构"""
    if not data:
        return PermissionTree()
    
    tree = PermissionTree(
        tree_id=data.get('id', ''),
        tree_node_name=data.get('name', '')
    )
    
    children = data.get('children', [])
    if children:
        tree.children = [_parse_tree(child) for child in children]
    
    return tree
