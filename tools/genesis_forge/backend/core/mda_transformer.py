"""
MDA 架构转换器

基于PRP文档的MDA三层架构转换：
1. CIM (计算无关模型) -> PIM (平台无关模型)
2. PIM (平台无关模型) -> PSM (平台特定模型)
3. PSM (平台特定模型) -> Runtime (运行时执行)

提供完整的模型驱动架构转换能力。
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

from .models import (
    DomainConcept, ObjectTypeDefinition, RelationshipDefinition,
    ActionTypeDefinition, WorldSnapshot, OntologyModel,
    Neo4jNode, Neo4jRelationship, CypherQuery, PythonRuntimeObject,
    pim_to_psm, validate_ontology_integrity
)

logger = logging.getLogger(__name__)


class MDATransformer:
    """MDA架构转换器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.cim_concepts: Dict[str, DomainConcept] = {}
        self.pim_ontology: Optional[OntologyModel] = None
        self.psm_models: Dict[str, Any] = {}
    
    # ========== CIM层操作 ==========
    
    def load_cim_from_text(self, text: str, domain: str) -> List[DomainConcept]:
        """
        从文本中提取CIM概念
        
        Args:
            text: 包含领域概念的文本
            domain: 领域名称
            
        Returns:
            提取的领域概念列表
        """
        concepts = []
        
        # 简单实现：按行解析概念
        lines = text.strip().split('\n')
        current_concept = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('# '):
                # 新概念开始
                if current_concept:
                    concepts.append(current_concept)
                
                concept_name = line[2:].strip()
                concept_id = concept_name.lower().replace(' ', '_').replace('-', '_')
                current_concept = DomainConcept(
                    concept_id=concept_id,
                    name=concept_name,
                    description="",
                    category=domain,
                    tags=[],
                    examples=[]
                )
            elif line.startswith('- ') and current_concept:
                # 示例
                example = line[2:].strip()
                current_concept.examples.append(example)
            elif current_concept and not current_concept.description:
                # 描述
                current_concept.description = line
            elif line.startswith('tags:') and current_concept:
                # 标签
                tags = line[5:].strip().split(',')
                current_concept.tags = [tag.strip() for tag in tags]
        
        if current_concept:
            concepts.append(current_concept)
        
        # 缓存概念
        for concept in concepts:
            self.cim_concepts[concept.concept_id] = concept
        
        return concepts
    
    def cim_to_pim(self, domain: str, concepts: List[DomainConcept]) -> OntologyModel:
        """
        将CIM概念转换为PIM本体
        
        Args:
            domain: 领域名称
            concepts: 领域概念列表
            
        Returns:
            PIM本体模型
        """
        # 创建基础本体
        ontology = OntologyModel(
            domain=domain,
            version="1.0.0",
            object_types={},
            relationships={},
            action_types={},
            world_snapshots={},
            domain_concepts=concepts
        )
        
        # 根据概念生成对象类型
        for concept in concepts:
            # 为每个概念创建一个对象类型
            type_key = concept.concept_id.upper()
            
            obj_type = ObjectTypeDefinition(
                type_key=type_key,
                name=concept.name,
                description=concept.description,
                properties={
                    "id": {
                        "name": "id",
                        "type": "string",
                        "required": True,
                        "description": f"{concept.name}的唯一标识符"
                    },
                    "name": {
                        "name": "name",
                        "type": "string",
                        "required": True,
                        "description": f"{concept.name}的名称"
                    },
                    "description": {
                        "name": "description",
                        "type": "string",
                        "required": False,
                        "description": f"{concept.name}的详细描述"
                    }
                },
                visual_assets=[f"icon_{concept.concept_id}.png"],
                tags=concept.tags,
                parent_type=None,
                abstract=False
            )
            
            ontology.object_types[type_key] = obj_type
        
        # 生成基础关系
        self._generate_basic_relationships(ontology)
        
        # 生成基础动作
        self._generate_basic_actions(ontology)
        
        self.pim_ontology = ontology
        return ontology
    
    def _generate_basic_relationships(self, ontology: OntologyModel):
        """生成基础关系定义"""
        # HAS关系
        has_rel = RelationshipDefinition(
            relation_type="HAS",
            name="拥有",
            description="表示拥有关系",
            source_constraint=list(ontology.object_types.keys()),
            target_constraint=list(ontology.object_types.keys()),
            attributes={
                "since": {
                    "name": "since",
                    "type": "datetime",
                    "required": False,
                    "description": "拥有开始时间"
                }
            },
            bidirectional=False,
            cardinality="1:N"
        )
        ontology.relationships["HAS"] = has_rel
        
        # PART_OF关系
        part_of_rel = RelationshipDefinition(
            relation_type="PART_OF",
            name="属于",
            description="表示部分属于整体的关系",
            source_constraint=list(ontology.object_types.keys()),
            target_constraint=list(ontology.object_types.keys()),
            attributes={
                "role": {
                    "name": "role",
                    "type": "string",
                    "required": False,
                    "description": "在整体中的角色"
                }
            },
            bidirectional=False,
            cardinality="N:M"
        )
        ontology.relationships["PART_OF"] = part_of_rel
        
        # RELATED_TO关系
        related_rel = RelationshipDefinition(
            relation_type="RELATED_TO",
            name="相关",
            description="表示相关关系",
            source_constraint=list(ontology.object_types.keys()),
            target_constraint=list(ontology.object_types.keys()),
            attributes={
                "strength": {
                    "name": "strength",
                    "type": "float",
                    "required": False,
                    "default": 1.0,
                    "description": "关系强度"
                }
            },
            bidirectional=True,
            cardinality="N:M"
        )
        ontology.relationships["RELATED_TO"] = related_rel
    
    def _generate_basic_actions(self, ontology: OntologyModel):
        """生成基础动作定义"""
        # CREATE动作
        create_action = ActionTypeDefinition(
            action_id="ACT_CREATE",
            name="创建",
            description="创建新实体",
            parameters={
                "entity_type": {
                    "name": "entity_type",
                    "type": "string",
                    "required": True,
                    "description": "实体类型"
                },
                "properties": {
                    "name": "properties",
                    "type": "object",
                    "required": True,
                    "description": "实体属性"
                }
            },
            validation_logic={
                "type": "cypher",
                "query": "RETURN true"
            },
            execution_chain=[
                {
                    "type": "create_node",
                    "template": "CREATE (n:{entity_type} $properties) RETURN n"
                }
            ],
            allowed_actors=["SYSTEM", "ADMIN"],
            allowed_targets=[],
            cooldown=None,
            cost=None
        )
        ontology.action_types["ACT_CREATE"] = create_action
        
        # UPDATE动作
        update_action = ActionTypeDefinition(
            action_id="ACT_UPDATE",
            name="更新",
            description="更新实体属性",
            parameters={
                "entity_id": {
                    "name": "entity_id",
                    "type": "string",
                    "required": True,
                    "description": "实体ID"
                },
                "updates": {
                    "name": "updates",
                    "type": "object",
                    "required": True,
                    "description": "更新内容"
                }
            },
            validation_logic={
                "type": "cypher",
                "query": "MATCH (n) WHERE n.id = $entity_id RETURN n IS NOT NULL as exists"
            },
            execution_chain=[
                {
                    "type": "update_node",
                    "template": "MATCH (n) WHERE n.id = $entity_id SET n += $updates RETURN n"
                }
            ],
            allowed_actors=["SYSTEM", "ADMIN"],
            allowed_targets=list(ontology.object_types.keys()),
            cooldown=None,
            cost=None
        )
        ontology.action_types["ACT_UPDATE"] = update_action
    
    # ========== PIM层操作 ==========
    
    def load_pim_from_json(self, json_data: Dict[str, Any]) -> OntologyModel:
        """
        从JSON加载PIM本体
        
        Args:
            json_data: JSON数据
            
        Returns:
            PIM本体模型
        """
        try:
            ontology = OntologyModel(**json_data)
            
            # 验证本体完整性
            errors = validate_ontology_integrity(ontology)
            if errors:
                logger.warning(f"本体完整性警告: {errors}")
            
            self.pim_ontology = ontology
            return ontology
            
        except Exception as e:
            logger.error(f"加载PIM本体失败: {e}")
            raise
    
    def save_pim_to_json(self, ontology: OntologyModel, file_path: Path) -> bool:
        """
        将PIM本体保存为JSON文件
        
        Args:
            ontology: PIM本体模型
            file_path: 保存路径
            
        Returns:
            是否成功
        """
        try:
            # 转换为字典
            data = ontology.dict()
            
            # 保存为JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"PIM本体已保存到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存PIM本体失败: {e}")
            return False
    
    def pim_to_psm(self, ontology: Optional[OntologyModel] = None) -> Dict[str, Any]:
        """
        将PIM本体转换为PSM模型
        
        Args:
            ontology: PIM本体模型（如为None则使用缓存的）
            
        Returns:
            PSM模型字典
        """
        if ontology is None:
            if self.pim_ontology is None:
                raise ValueError("没有可用的PIM本体")
            ontology = self.pim_ontology
        
        # 使用models.py中的转换函数
        psm_models = pim_to_psm(ontology)
        
        # 添加额外转换
        self._enhance_psm_models(psm_models, ontology)
        
        self.psm_models = psm_models
        return psm_models
    
    def _enhance_psm_models(self, psm_models: Dict[str, Any], ontology: OntologyModel):
        """增强PSM模型"""
        # 添加初始化脚本
        init_script = CypherQuery(
            query="""
            // Genesis Studio 初始化脚本
            // 领域: {domain}
            // 版本: {version}
            // 生成时间: {timestamp}
            
            // 清理旧数据（可选）
            // MATCH (n) DETACH DELETE n
            
            // 创建约束和索引
            // （由pim_to_psm自动生成）
            """.format(
                domain=ontology.domain,
                version=ontology.version,
                timestamp=datetime.now().isoformat()
            ),
            description="领域初始化脚本",
            parameters={}
        )
        psm_models["cypher_queries"].insert(0, init_script)
        
        # 添加验证脚本
        validation_script = PythonRuntimeObject(
            object_id="validation_engine",
            class_name="ValidationEngine",
            attributes={
                "domain": ontology.domain,
                "object_types": list(ontology.object_types.keys()),
                "relationships": list(ontology.relationships.keys()),
                "action_types": list(ontology.action_types.keys())
            },
            methods=[
                "validate_node",
                "validate_relationship", 
                "validate_action",
                "check_integrity"
            ]
        )
        psm_models["python_objects"].append(validation_script)
    
    # ========== PSM层操作 ==========
    
    def generate_neo4j_import_script(self, psm_models: Dict[str, Any]) -> str:
        """
        生成Neo4j导入脚本
        
        Args:
            psm_models: PSM模型
            
        Returns:
            Cypher导入脚本
        """
        script_lines = []
        
        # 添加约束和索引
        for cypher_query in psm_models.get("cypher_queries", []):
            if isinstance(cypher_query, CypherQuery):
                script_lines.append(f"// {cypher_query.description}")
                script_lines.append(cypher_query.query + ";")
                script_lines.append("")
        
        # 添加节点
        if psm_models.get("neo4j_nodes"):
            script_lines.append("// 导入节点")
            for node in psm_models["neo4j_nodes"]:
                if isinstance(node, Neo4jNode):
                    labels_str = ":".join(node.labels)
                    props_str = json.dumps(node.properties, ensure_ascii=False)
                    script_lines.append(f"CREATE (n:{labels_str} {props_str});")
            script_lines.append("")
        
        # 添加关系
        if psm_models.get("neo4j_relationships"):
            script_lines.append("// 导入关系")
            for rel in psm_models["neo4j_relationships"]:
                if isinstance(rel, Neo4jRelationship):
                    props_str = json.dumps(rel.properties, ensure_ascii=False)
                    script_lines.append(
                        f"MATCH (source {{id: '{rel.source_id}'}}), "
                        f"(target {{id: '{rel.target_id}'}}) "
                        f"CREATE (source)-[r:{rel.type} {props_str}]->(target);"
                    )
        
        return "\n".join(script_lines)
    
    def generate_python_runtime_code(self, psm_models: Dict[str, Any]) -> str:
        """
        生成Python运行时代码
        
        Args:
            psm_models: PSM模型
            
        Returns:
            Python代码
        """
        code_lines = [
            "# -*- coding: utf-8 -*-",
            "\"\"\"",
            "Genesis Studio 运行时代码",
            "自动生成的Python运行时类",
            "\"\"\"",
            "",
            "import json",
            "from datetime import datetime",
            "from typing import Dict, List, Any, Optional",
            "",
            ""
        ]
        
        # 生成类定义
        for py_obj in psm_models.get("python_objects", []):
            if isinstance(py_obj, PythonRuntimeObject):
                class_code = f"""
class {py_obj.class_name}:
    \"\"\"{py_obj.object_id.replace('_', ' ').title()}\"\"\"
    
    def __init__(self):
        self.object_id = "{py_obj.object_id}"
        {chr(10).join(f'        self.{k} = {repr(v)}' for k, v in py_obj.attributes.items())}
    
    {chr(10).join(f'    def {method}(self, *args, **kwargs):' + chr(10) + f'        \"\"\"{method}方法\"\"\"' + chr(10) + f'        # TODO: 实现{method}逻辑' + chr(10) + f'        pass' for method in py_obj.methods)}
"""
                code_lines.append(class_code)
        
        # 生成工厂函数
        code_lines.append("""
def create_runtime_objects():
    \"\"\"创建运行时对象工厂\"\"\"
    objects = {}
""")
        
        for py_obj in psm_models.get("python_objects", []):
            if isinstance(py_obj, PythonRuntimeObject):
                code_lines.append(f'    objects["{py_obj.object_id}"] = {py_obj.class_name}()')
        
        code_lines.append("""
    return objects

if __name__ == "__main__":
    # 测试运行时对象
    runtime_objects = create_runtime_objects()
    print(f"创建了 {len(runtime_objects)} 个运行时对象")
    for obj_id, obj in runtime_objects.items():
        print(f"  - {obj_id}: {obj.__class__.__name__}")
""")
        
        return "\n".join(code_lines)
    
    # ========== 完整转换流程 ==========
    
    def full_mda_transformation(self, domain: str, cim_text: str) -> Dict[str, Any]:
        """
        完整的MDA转换流程
        
        Args:
            domain: 领域名称
            cim_text: CIM文本描述
            
        Returns:
            转换结果
        """
        logger.info(f"开始MDA转换流程 - 领域: {domain}")
        
        # 1. CIM -> PIM
        logger.info("步骤1: 从文本提取CIM概念")
        concepts = self.load_cim_from_text(cim_text, domain)
        logger.info(f"提取了 {len(concepts)} 个领域概念")
        
        logger.info("步骤2: CIM -> PIM 转换")
        pim_ontology = self.cim_to_pim(domain, concepts)
        logger.info(f"生成了PIM本体: {len(pim_ontology.object_types)} 个对象类型, "
                   f"{len(pim_ontology.relationships)} 个关系, "
                   f"{len(pim_ontology.action_types)} 个动作")
        
        # 2. PIM -> PSM
        logger.info("步骤3: PIM -> PSM 转换")
        psm_models = self.pim_to_psm(pim_ontology)
        logger.info(f"生成了PSM模型: {len(psm_models.get('cypher_queries', []))} 个Cypher查询, "
                   f"{len(psm_models.get('python_objects', []))} 个Python对象")
        
        # 3. 生成输出
        logger.info("步骤4: 生成输出文件")
        
        result = {
            "domain": domain,
            "cim_concepts": [c.dict() for c in concepts],
            "pim_ontology": pim_ontology.dict(),
            "psm_models_summary": {
                "cypher_queries": len(psm_models.get("cypher_queries", [])),
                "python_objects": len(psm_models.get("python_objects", [])),
                "neo4j_nodes": len(psm_models.get("neo4j_nodes", [])),
                "neo4j_relationships": len(psm_models.get("neo4j_relationships", []))
            },
            "neo4j_script": self.generate_neo4j_import_script(psm_models),
            "python_code": self.generate_python_runtime_code(psm_models)
        }
        
        logger.info("MDA转换流程完成")
        return result