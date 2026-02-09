"""
MDA 三层架构数据模型 (PIM层)

基于PRP文档的MDA架构定义：
1. CIM (计算无关模型): Domain Concepts
2. PIM (平台无关模型): Ontology Layer (JSON/XML)
3. PSM (平台特定模型): Kernel Runtime (Python/Neo4j/Cypher)

本文件定义PIM层的数据模型，使用Pydantic进行强类型验证。
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


# ========== 基础类型定义 ==========

class DataType(str, Enum):
    """数据类型枚举"""
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    STRING = "string"
    ENUM = "enum"
    DATE = "date"
    DATETIME = "datetime"
    OBJECT = "object"
    ARRAY = "array"


class PropertySchema(BaseModel):
    """属性Schema定义"""
    name: str = Field(..., description="属性名称")
    type: DataType = Field(..., description="数据类型")
    required: bool = Field(default=True, description="是否必需")
    default: Optional[Any] = Field(default=None, description="默认值")
    description: Optional[str] = Field(default=None, description="属性描述")
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict, description="约束条件")
    
    # 枚举类型特有字段
    enum_values: Optional[List[str]] = Field(default=None, description="枚举值列表")
    
    @validator('enum_values', always=True)
    def validate_enum_values(cls, v, values):
        data = values.data if hasattr(values, 'data') else values
        if data.get('type') == DataType.ENUM and not v:
            raise ValueError('枚举类型必须提供enum_values')
        return v


# ========== CIM层：领域概念模型 ==========

class DomainConcept(BaseModel):
    """领域概念模型 (CIM层)"""
    concept_id: str = Field(..., description="概念唯一标识")
    name: str = Field(..., description="概念名称")
    description: str = Field(..., description="概念描述")
    category: str = Field(..., description="概念分类")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    examples: List[str] = Field(default_factory=list, description="示例说明")


# ========== PIM层：本体模型 ==========

class ObjectTypeDefinition(BaseModel):
    """实体类型定义 (PIM层)"""
    type_key: str = Field(..., description="类型唯一标识 (e.g., 'NPC_Guard')")
    name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(default=None, description="类型描述")
    properties: Dict[str, PropertySchema] = Field(default_factory=dict, description="属性Schema")
    visual_assets: List[str] = Field(default_factory=list, description="关联的前端资源")
    tags: List[str] = Field(default_factory=list, description="行为标签 (e.g., 'biological', 'mortal')")
    parent_type: Optional[str] = Field(default=None, description="父类型")
    abstract: bool = Field(default=False, description="是否为抽象类型")
    
    @validator('type_key')
    def validate_type_key(cls, v):
        # 强制使用大写下划线格式
        if not v.isupper() or '_' not in v:
            raise ValueError('type_key必须使用大写下划线格式 (如: NPC_GUARD)')
        return v


class RelationshipDefinition(BaseModel):
    """关系定义 (PIM层)"""
    relation_type: str = Field(..., description="关系类型 (e.g., 'LOCATED_AT')")
    name: str = Field(..., description="关系显示名称")
    description: Optional[str] = Field(default=None, description="关系描述")
    source_constraint: List[str] = Field(default_factory=list, description="源类型约束 (e.g., ['Player', 'NPC'])")
    target_constraint: List[str] = Field(default_factory=list, description="目标类型约束 (e.g., ['Location'])")
    attributes: Dict[str, PropertySchema] = Field(default_factory=dict, description="关系属性")
    bidirectional: bool = Field(default=False, description="是否为双向关系")
    cardinality: Optional[str] = Field(default=None, description="基数约束 (e.g., '1:1', '1:N', 'N:M')")


class ActionTypeDefinition(BaseModel):
    """动作类型定义 (PIM层)"""
    action_id: str = Field(..., description="动作唯一ID (e.g., 'ACT_ATTACK')")
    name: str = Field(..., description="动作显示名称")
    description: Optional[str] = Field(default=None, description="动作描述")
    parameters: Dict[str, PropertySchema] = Field(default_factory=dict, description="入参定义")
    validation_logic: Optional[Dict[str, Any]] = Field(default=None, description="验证逻辑 (Cypher/Python)")
    execution_chain: List[Dict[str, Any]] = Field(default_factory=list, description="执行链")
    allowed_actors: List[str] = Field(default_factory=list, description="允许执行此动作的实体类型")
    allowed_targets: List[str] = Field(default_factory=list, description="允许作为目标的实体类型")
    cooldown: Optional[int] = Field(default=None, description="冷却时间（毫秒）")
    cost: Optional[Dict[str, Any]] = Field(default=None, description="执行成本（如MP消耗）")


class WorldSnapshot(BaseModel):
    """世界快照 (PIM层)"""
    snapshot_id: str = Field(..., description="快照唯一标识")
    name: str = Field(..., description="快照名称")
    description: Optional[str] = Field(default=None, description="快照描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="节点列表")
    links: List[Dict[str, Any]] = Field(default_factory=list, description="关系列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class OntologyModel(BaseModel):
    """完整本体模型 (PIM层)"""
    domain: str = Field(..., description="领域名称")
    version: str = Field(default="1.0.0", description="本体版本")
    object_types: Dict[str, ObjectTypeDefinition] = Field(default_factory=dict, description="实体类型定义")
    relationships: Dict[str, RelationshipDefinition] = Field(default_factory=dict, description="关系定义")
    action_types: Dict[str, ActionTypeDefinition] = Field(default_factory=dict, description="动作类型定义")
    world_snapshots: Dict[str, WorldSnapshot] = Field(default_factory=dict, description="世界快照")
    domain_concepts: List[DomainConcept] = Field(default_factory=list, description="领域概念")


# ========== PSM层：平台特定模型 ==========

class Neo4jNode(BaseModel):
    """Neo4j节点模型 (PSM层)"""
    node_id: str = Field(..., description="节点唯一标识")
    labels: List[str] = Field(..., description="节点标签")
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点属性")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")


class Neo4jRelationship(BaseModel):
    """Neo4j关系模型 (PSM层)"""
    relationship_id: str = Field(..., description="关系唯一标识")
    type: str = Field(..., description="关系类型")
    source_id: str = Field(..., description="源节点ID")
    target_id: str = Field(..., description="目标节点ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="关系属性")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class CypherQuery(BaseModel):
    """Cypher查询模型 (PSM层)"""
    query: str = Field(..., description="Cypher查询语句")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="查询参数")
    description: Optional[str] = Field(default=None, description="查询描述")


class PythonRuntimeObject(BaseModel):
    """Python运行时对象 (PSM层)"""
    object_id: str = Field(..., description="对象唯一标识")
    class_name: str = Field(..., description="Python类名")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="对象属性")
    methods: List[str] = Field(default_factory=list, description="可用方法")
    serialized_data: Optional[str] = Field(default=None, description="序列化数据")


# ========== 转换函数 ==========

def pim_to_psm(ontology: OntologyModel) -> Dict[str, Any]:
    """将PIM模型转换为PSM模型"""
    psm_models = {
        "neo4j_nodes": [],
        "neo4j_relationships": [],
        "cypher_queries": [],
        "python_objects": [],
        "schema_validation": []
    }
    
    # 1. 转换对象类型为Neo4j节点标签和约束
    for type_key, obj_type in ontology.object_types.items():
        # 创建节点标签约束
        constraint_query = CypherQuery(
            query=f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{type_key}) REQUIRE n.id IS UNIQUE",
            description=f"为{type_key}类型创建唯一ID约束"
        )
        psm_models["cypher_queries"].append(constraint_query)
        
        # 创建属性索引
        for prop_name, prop_schema in obj_type.properties.items():
            constraints = prop_schema.constraints or {}
            if prop_schema.required or constraints.get("indexed", False):
                index_query = CypherQuery(
                    query=f"CREATE INDEX IF NOT EXISTS FOR (n:{type_key}) ON (n.{prop_name})",
                    description=f"为{type_key}.{prop_name}创建索引"
                )
                psm_models["cypher_queries"].append(index_query)
        
        # 创建Python运行时对象
        python_obj = PythonRuntimeObject(
            object_id=f"class_{type_key.lower()}",
            class_name=f"{type_key}Class",
            attributes={
                "type_key": type_key,
                "name": obj_type.name,
                "description": obj_type.description,
                "properties": {k: v.dict() for k, v in obj_type.properties.items()},
                "tags": obj_type.tags
            },
            methods=["create_instance", "validate_instance", "to_dict", "from_dict"]
        )
        psm_models["python_objects"].append(python_obj)
    
    # 2. 转换关系定义
    for rel_key, rel_def in ontology.relationships.items():
        # 创建关系约束
        constraint_query = CypherQuery(
            query=f"CREATE CONSTRAINT IF NOT EXISTS FOR ()-[r:{rel_key}]-() REQUIRE r.id IS UNIQUE",
            description=f"为{rel_key}关系创建唯一约束"
        )
        psm_models["cypher_queries"].append(constraint_query)
        
        # 创建关系类型约束
        if rel_def.source_constraint and rel_def.target_constraint:
            for source_type in rel_def.source_constraint:
                for target_type in rel_def.target_constraint:
                    validation_query = CypherQuery(
                        query=f"""
                        // 验证 {source_type}-[{rel_key}]->{target_type} 关系约束
                        MATCH (s:{source_type})-[r:{rel_key}]->(t:{target_type})
                        WHERE NOT (s:{source_type}) OR NOT (t:{target_type})
                        RETURN COUNT(r) as invalid_relationships
                        """,
                        description=f"验证{rel_key}关系类型约束"
                    )
                    psm_models["schema_validation"].append(validation_query)
    
    # 3. 转换动作类型为Python可执行代码
    for action_key, action_def in ontology.action_types.items():
        # 创建动作验证逻辑
        if action_def.validation_logic:
            validation_code = f"""
def validate_{action_key.lower()}(params):
    \"\"\"验证{action_def.name}动作\"\"\"
    # 验证逻辑: {action_def.validation_logic.get('type', 'cypher')}
    # 参数: {action_def.parameters}
    validation_result = {{
        'valid': True,
        'errors': [],
        'warnings': []
    }}
    
    # 参数验证
    for param_name, param_schema in {action_def.parameters}.items():
        if param_schema.required and param_name not in params:
            validation_result['valid'] = False
            validation_result['errors'].append(f'缺少必需参数: {{param_name}}')
    
    return validation_result
            """
            
            python_obj = PythonRuntimeObject(
                object_id=f"action_{action_key.lower()}",
                class_name=f"{action_key}Action",
                attributes={
                    "action_id": action_key,
                    "name": action_def.name,
                    "description": action_def.description,
                    "parameters": {k: v.dict() for k, v in action_def.parameters.items()},
                    "validation_logic": action_def.validation_logic,
                    "execution_chain": action_def.execution_chain
                },
                methods=["validate", "execute", "simulate", "rollback"]
            )
            psm_models["python_objects"].append(python_obj)
    
    # 4. 转换世界快照
    for snapshot_id, snapshot in ontology.world_snapshots.items():
        # 转换节点
        for node_data in snapshot.nodes:
            node_id = node_data.get("id", "") if node_data else ""
            labels = node_data.get("labels", []) if node_data else []
            properties = node_data.get("properties", {}) if node_data else {}
            
            neo4j_node = Neo4jNode(
                node_id=node_id,
                labels=labels,
                properties=properties
            )
            psm_models["neo4j_nodes"].append(neo4j_node)
        
        # 转换关系
        for link_data in snapshot.links:
            if not link_data:
                continue
                
            neo4j_rel = Neo4jRelationship(
                relationship_id=link_data.get("id", ""),
                type=link_data.get("type", ""),
                source_id=link_data.get("source", ""),
                target_id=link_data.get("target", ""),
                properties=link_data.get("properties", {})
            )
            psm_models["neo4j_relationships"].append(neo4j_rel)
    
    # 5. 转换领域概念为文档
    for concept in ontology.domain_concepts:
        concept_doc = f"""
# {concept.name}
{concept.description}

**分类**: {concept.category}
**标签**: {', '.join(concept.tags)}

## 示例
{chr(10).join(f'- {example}' for example in concept.examples)}

## 相关实体类型
{chr(10).join(f'- {type_key}' for type_key in ontology.object_types.keys() if concept.concept_id in ontology.object_types[type_key].tags)}
        """
        # 可以存储为文档文件或添加到元数据中
    
    return psm_models


def validate_ontology_integrity(ontology: OntologyModel) -> List[str]:
    """验证本体完整性"""
    errors = []
    
    # 检查类型引用
    for obj_type in ontology.object_types.values():
        if obj_type.parent_type and obj_type.parent_type not in ontology.object_types:
            errors.append(f"对象类型 {obj_type.type_key} 引用了不存在的父类型 {obj_type.parent_type}")
    
    # 检查关系约束
    for rel_key, rel_def in ontology.relationships.items():
        for source_type in rel_def.source_constraint:
            if source_type not in ontology.object_types:
                errors.append(f"关系 {rel_key} 引用了不存在的源类型 {source_type}")
        
        for target_type in rel_def.target_constraint:
            if target_type not in ontology.object_types:
                errors.append(f"关系 {rel_key} 引用了不存在的目标类型 {target_type}")
    
    # 检查动作类型
    for action_key, action_def in ontology.action_types.items():
        for actor_type in action_def.allowed_actors:
            if actor_type not in ontology.object_types:
                errors.append(f"动作 {action_key} 引用了不存在的执行者类型 {actor_type}")
        
        for target_type in action_def.allowed_targets:
            if target_type not in ontology.object_types:
                errors.append(f"动作 {action_key} 引用了不存在的目标类型 {target_type}")
    
    return errors