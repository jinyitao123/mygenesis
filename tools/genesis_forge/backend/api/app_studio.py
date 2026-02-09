"""
Genesis Studio v2.0 - 基于MDA架构的可视化仿真世界构建平台

基于PRP文档的完整实现：
1. MDA三层架构 (CIM/PIM/PSM)
2. Pydantic数据模型验证
3. ECA规则引擎
4. Cytoscape.js可视化编辑器
5. AI Copilot服务
6. Git-Ops开发流程
7. 原子服务API端点
"""

import os
import sys
import logging
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 添加backend目录到路径
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from backend.core.models import OntologyModel
from backend.core.validation_engine import ValidationEngine
from backend.core.request_context import RequestContext, DomainContextManager, current_domain
from backend.core.exceptions import (
    DomainNotFoundError, SchemaValidationError, SecurityError,
    CypherInjectionError, PathTraversalError, Neo4jError, TransactionError
)
from backend.core.transaction_manager import save_domain_config_atomic
from backend.services.rule_engine import RuleEngine, Event, EventType
from backend.services.ai_copilot_fixed import EnhancedAICopilot
from backend.services.git_ops import GitOpsManager
from backend.services.domain_manager_enhanced import EnhancedDomainManager as DomainManager
from backend.services.neo4j_loader import Neo4jLoader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 路径配置
BASE_DIR = Path(__file__).parent.parent  # backend目录
PROJECT_ROOT = BASE_DIR.parent

# 真实数据目录 - 指向 E:\Documents\MyGame
REAL_DATA_ROOT = Path(r"E:\Documents\MyGame")

# 初始化Flask应用
app = Flask(__name__, 
            template_folder=str(BASE_DIR / 'templates'),
            static_folder=str(BASE_DIR / 'static'))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB文件上传限制
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')  # Session 加密密钥

# 初始化WebSocket
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# 初始化服务 - 使用真实数据目录
domain_manager = DomainManager(str(REAL_DATA_ROOT))
validation_engine = ValidationEngine(str(PROJECT_ROOT))
ai_copilot = EnhancedAICopilot(str(PROJECT_ROOT))
git_ops = GitOpsManager(str(PROJECT_ROOT), validation_engine)
rule_engine = RuleEngine(validation_engine)

# 领域模组配置
DOMAIN_PACKS = {
    "supply_chain": {
        "name": "供应链物流系统",
        "description": "卡车、仓库、货物运输仿真",
        "color": "#f59e0b",
        "icon": "truck"
    },
    "finance_risk": {
        "name": "金融风控图谱",
        "description": "账户、交易、担保关系网络",
        "color": "#8b5cf6",
        "icon": "chart-line"
    },
    "it_ops": {
        "name": "IT运维监控",
        "description": "服务器、网络、应用监控",
        "color": "#10b981",
        "icon": "server"
    },
    "empty": {
        "name": "空白项目",
        "description": "从零开始定义新的本体",
        "color": "#6b7280",
        "icon": "file-plus"
    }
}

# ========== 路由定义 ==========

@app.route('/')
def index():
    """启动页 - 领域选择器"""
    available_domains = domain_manager.list_domains()
    
    domains_info = []
    for domain_id in available_domains:
        if domain_id in DOMAIN_PACKS:
            domains_info.append({
                "id": domain_id,
                **DOMAIN_PACKS[domain_id]
            })
    
    current_domain = RequestContext.get_current_domain()
    
    return render_template('launcher.html', 
                         domains=domains_info,
                         current_domain=current_domain)

@app.route('/studio')
def studio():
    """Genesis Studio主界面"""
    # 从 Session 获取当前领域
    current_domain = RequestContext.get_current_domain()
    
    # 验证领域是否存在
    if current_domain not in DOMAIN_PACKS:
        current_domain = "supply_chain"
        RequestContext.set_current_domain(current_domain)
    
    # 获取当前领域配置
    files_content = domain_manager.get_domain_files(current_domain)
    
    current_domain_info = DOMAIN_PACKS.get(current_domain, {})
    
    # 解析侧边栏数据
    object_types = []
    action_rules = []
    seed_data = []
    
    try:
        # 解析对象类型
        if files_content.get('schema'):
            schema_data = json.loads(files_content['schema'])
            if 'object_types' in schema_data:
                object_types = schema_data['object_types']
        
        # 解析动作规则
        if files_content.get('actions'):
            actions_data = json.loads(files_content['actions'])
            if 'actions' in actions_data:
                action_rules = actions_data['actions']
        
        # 解析种子数据
        if files_content.get('seed'):
            seed_json = json.loads(files_content['seed'])
            if 'entities' in seed_json:
                seed_data = [{'name': e.get('id', '未知')} for e in seed_json['entities'][:10]]
    except Exception as e:
        logger.warning(f"解析侧边栏数据失败: {e}")
    
    return render_template('studio.html',
                         current_domain=current_domain,
                         current_domain_name=current_domain_info.get("name", "未知领域"),
                         domain_color=current_domain_info.get("color", "#6b7280"),
                         domain_icon=current_domain_info.get("icon", "cube"),
                         object_types=object_types,
                         action_rules=action_rules,
                         seed_data=seed_data,
                         graph_elements=[])  # 图谱数据将通过HTMX加载

@app.route('/editor')
def editor():
    """编辑器页面 - 本体编辑器 IDE (兼容性路由)"""
    # 从 Session 获取当前领域
    current_domain = RequestContext.get_current_domain()
    
    # 验证领域是否存在
    if current_domain not in DOMAIN_PACKS:
        current_domain = "supply_chain"
        RequestContext.set_current_domain(current_domain)
    
    # 获取当前领域配置
    files_content = domain_manager.get_domain_files(current_domain)
    
    current_domain_info = DOMAIN_PACKS.get(current_domain, {})
    
    # 解析侧边栏数据
    object_types = []
    action_rules = []
    seed_data = []
    
    try:
        # 解析对象类型
        if files_content.get('schema'):
            schema_data = json.loads(files_content['schema'])
            if 'object_types' in schema_data:
                object_types = schema_data['object_types']
        
        # 解析动作规则
        if files_content.get('actions'):
            actions_data = json.loads(files_content['actions'])
            if 'actions' in actions_data:
                action_rules = actions_data['actions']
        
        # 解析种子数据
        if files_content.get('seed'):
            seed_json = json.loads(files_content['seed'])
            if 'entities' in seed_json:
                seed_data = [{'name': e.get('id', '未知')} for e in seed_json['entities'][:10]]
    except Exception as e:
        logger.warning(f"解析侧边栏数据失败: {e}")
    
    return render_template('studio.html',
                         current_domain=current_domain,
                         current_domain_name=current_domain_info.get("name", "未知领域"),
                         domain_color=current_domain_info.get("color", "#6b7280"),
                         domain_icon=current_domain_info.get("icon", "cube"),
                         object_types=object_types,
                         action_rules=action_rules,
                         seed_data=seed_data,
                         graph_elements=[])  # 图谱数据将通过HTMX加载

# ========== 原子服务API端点 ==========

# 1. 本体管理服务 (OntologyService)
@app.route('/api/v1/ontology/validate', methods=['POST'])
def validate_ontology():
    """验证本体完整性"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        # 验证JSON Schema
        valid, errors = validation_engine.validate_json_schema(data, OntologyModel)
        
        if valid:
            return jsonify({
                "status": "success",
                "message": "本体验证通过"
            })
        else:
            return jsonify({
                "status": "error",
                "error_code": "ERR_SCHEMA_01",
                "errors": errors
            }), 400
            
    except Exception as e:
        logger.error(f"本体验证失败: {e}")
        return jsonify({"error": f"本体验证失败: {str(e)}"}), 500

@app.route('/api/v1/ontology/integrity', methods=['GET'])
def check_ontology_integrity():
    """检查本体完整性"""
    try:
        # 获取当前领域
        current_domain = RequestContext.get_current_domain()
        
        # 获取当前领域文件
        files_content = domain_manager.get_domain_files(current_domain)
        logger.info(f"获取领域 {current_domain} 的文件，keys: {list(files_content.keys())}")
        
        schema_content = files_content.get("schema", "")
        if schema_content:
            logger.info(f"Schema内容长度: {len(schema_content)} 字符")
            logger.info(f"Schema内容前200字符: {schema_content[:200] if len(schema_content) > 200 else schema_content}")
        
        if not schema_content:
            return jsonify({
                "status": "error",
                "message": f"领域 {current_domain} 没有Schema定义"
            }), 400
        
        # 解析并验证 - 支持XML和JSON格式
        schema_data = {}
        
        try:
            # 首先尝试解析为JSON
            schema_data = json.loads(schema_content)
            logger.info(f"Schema是JSON格式，成功解析")
        except json.JSONDecodeError:
            # 如果不是JSON，尝试解析为XML
            logger.info(f"Schema是XML格式，尝试从XML中提取本体数据")
            try:
                # 使用XML转换器从XML中提取数据
                from backend.core.xml_converter import XMLConverter
                
                # XML文件包含对象类型定义，需要转换为OntologyModel格式
                # 首先，尝试从XML中提取基本信息
                import xml.etree.ElementTree as ET
                root = ET.fromstring(schema_content)
                
                # 构建基本的schema数据 - 符合OntologyModel要求
                schema_data = {
                    "domain": current_domain,
                    "object_types": {},
                    "relationships": {},
                    "action_types": {},
                    "world_snapshots": {},
                    "domain_concepts": []
                }
                
                # 从XML中提取对象类型 - 符合ObjectTypeDefinition模型
                for obj_elem in root.findall(".//ObjectType"):
                    obj_name = obj_elem.get("name")
                    if obj_name:
                        # 构建符合ObjectTypeDefinition要求的数据结构
                        obj_def = {
                            "type_key": obj_name,  # OntologyModel期望type_key字段
                            "name": obj_name,
                            "description": obj_elem.get("description", ""),
                            "properties": {},
                            "visual_assets": [],
                            "tags": []
                        }
                        
                        # 提取属性 - 符合PropertyDefinition模型
                        for prop_elem in obj_elem.findall(".//Property"):
                            prop_name = prop_elem.get("name")
                            if prop_name:
                                # 构建符合PropertyDefinition要求的数据结构
                                obj_def["properties"][prop_name] = {
                                    "name": prop_name,  # 必需字段
                                    "type": prop_elem.get("type", "string"),
                                    "description": prop_elem.get("description", ""),
                                    "default_value": None,
                                    "is_required": False,
                                    "constraints": []
                                }
                        
                        schema_data["object_types"][obj_name] = obj_def
                
                # 从XML中提取关系类型 - 符合RelationshipDefinition模型
                link_types_elem = root.find(".//LinkTypes")
                if link_types_elem is not None:
                    for link_elem in link_types_elem.findall(".//LinkType"):
                        link_name = link_elem.get("name")
                        if link_name:
                            # 构建符合RelationshipDefinition要求的数据结构
                            schema_data["relationships"][link_name] = {
                                "relation_type": link_name,  # 必需字段
                                "name": link_name,
                                "source_type": link_elem.get("source", "Unknown"),
                                "target_type": link_elem.get("target", "Unknown"),
                                "description": link_elem.get("description", ""),
                                "properties": {},
                                "constraints": []
                            }
                
                logger.info(f"从XML中提取了 {len(schema_data['object_types'])} 个对象类型和 {len(schema_data['relationships'])} 个关系类型")
                
            except Exception as xml_error:
                logger.error(f"XML解析失败: {xml_error}")
                return jsonify({
                    "status": "error",
                    "message": f"领域 {current_domain} 的Schema既不是有效的JSON也不是有效的XML格式: {str(xml_error)}"
                }), 400
        
        # 确保数据符合OntologyModel要求
        # 1. 添加domain字段（如果缺失）
        if "domain" not in schema_data:
            schema_data["domain"] = current_domain
        
        # 2. 转换relationships为字典（如果是列表）
        if "relationships" in schema_data and isinstance(schema_data["relationships"], list):
            relationships_dict = {}
            for rel in schema_data["relationships"]:
                if isinstance(rel, dict):
                    rel_name = rel.get("name") or rel.get("type")
                    if rel_name:
                        relationships_dict[rel_name] = rel
            schema_data["relationships"] = relationships_dict
        
        # 3. 转换objectTypes为字典（如果是列表）
        if "objectTypes" in schema_data and isinstance(schema_data["objectTypes"], list):
            object_types_dict = {}
            for obj in schema_data["objectTypes"]:
                if isinstance(obj, dict):
                    obj_name = obj.get("name") or obj.get("type_key")
                    if obj_name:
                        object_types_dict[obj_name] = obj
            schema_data["objectTypes"] = object_types_dict
        
        # 4. 确保其他字段存在
        if "object_types" not in schema_data and "objectTypes" in schema_data:
            schema_data["object_types"] = schema_data["objectTypes"]
        
        if "action_types" not in schema_data:
            schema_data["action_types"] = {}
        
        if "world_snapshots" not in schema_data:
            schema_data["world_snapshots"] = {}
        
        if "domain_concepts" not in schema_data:
            schema_data["domain_concepts"] = []
        
        try:
            ontology = OntologyModel(**schema_data)
        except Exception as model_error:
            logger.error(f"OntologyModel创建失败: {model_error}")
            return jsonify({
                "status": "error",
                "message": f"本体数据格式错误: {str(model_error)}",
                "schema_data_keys": list(schema_data.keys())
            }), 400
        
        # 验证完整性
        errors = validation_engine.validate_reference_integrity(
            schema_data, ontology
        )
        
        if errors:
            return jsonify({
                "status": "warning",
                "error_code": "ERR_REF_03",
                "errors": errors
            })
        else:
            return jsonify({
                "status": "success",
                "message": "本体完整性检查通过"
            })
            
    except Exception as e:
        logger.error(f"完整性检查失败: {e}")
        return jsonify({"error": f"完整性检查失败: {str(e)}"}), 500

# 2. 世界仿真服务 (WorldService)
@app.route('/api/v1/world/preview', methods=['GET'])
def preview_world():
    """预览世界图谱"""
    try:
        node_type = request.args.get('type', None)
        limit = int(request.args.get('limit', 100))
        domain = request.args.get('domain', RequestContext.get_current_domain())
        
        loader = Neo4jLoader()
        graph_data = loader.query_graph(node_type=node_type, limit=limit, domain=domain)
        
        return jsonify({
            "status": "success",
            "data": graph_data
        })
        
    except Neo4jError as e:
        logger.error(f"世界预览失败: {e.message}")
        return jsonify(e.to_dict()), 500
    except Exception as e:
        logger.error(f"世界预览失败: {e}")
        return jsonify({"error": f"世界预览失败: {str(e)}"}), 500

@app.route('/api/v1/world/validate-connectivity', methods=['GET'])
def validate_connectivity():
    """验证图谱连通性"""
    try:
        loader = Neo4jLoader()
        
        # 检查是否有孤岛节点
        query = """
        MATCH (n)
        WHERE NOT (n)--()
        RETURN n.id as isolated_node, labels(n) as node_type
        LIMIT 10
        """
        
        if loader.neo4j is None:
            return jsonify({
                "status": "warning",
                "message": "Neo4j 未连接，无法检查连通性"
            })
        
        result = loader.query_graph(limit=10)
        isolated_nodes = [
            {"id": node.get("id"), "node_type": node.get("type")}
            for node in result.get("nodes", [])
            if not any(
                link["source"] == node.get("id") or link["target"] == node.get("id")
                for link in result.get("links", [])
            )
        ]
        
        if isolated_nodes:
            return jsonify({
                "status": "warning",
                "message": f"发现 {len(isolated_nodes)} 个孤岛节点",
                "isolated_nodes": isolated_nodes
            })
        else:
            return jsonify({
                "status": "success",
                "message": "图谱连通性良好"
            })
            
    except Exception as e:
        logger.error(f"连通性验证失败: {e}")
        return jsonify({"error": f"连通性验证失败: {str(e)}"}), 500

@app.route('/api/v1/world/reset', methods=['POST'])
def reset_world():
    """重置世界到初始状态"""
    try:
        data = request.json or {}
        domain = data.get('domain', RequestContext.get_current_domain())
        
        # 验证领域访问权限
        if not DomainContextManager.validate_domain_access(domain, domain_manager.list_domains()):
            raise DomainNotFoundError(domain)
        
        # 获取指定领域的seed数据
        files_content = domain_manager.get_domain_files(domain)
        seed_content = files_content.get("seed", "")
        
        if not seed_content:
            return jsonify({
                "status": "error",
                "message": "没有初始世界数据"
            }), 400
        
        # 清空Neo4j并重新加载
        loader = Neo4jLoader()
        loader.delete_all_nodes()
        
        # 重新加载seed数据
        stats = loader.load_to_neo4j(seed_content, clear_existing=False)
        
        return jsonify({
            "status": "success",
            "message": "世界重置成功",
            "stats": stats
        })
        
    except DomainNotFoundError as e:
        logger.error(f"领域不存在: {e.domain_name}")
        return jsonify(e.to_dict()), 404
    except Neo4jError as e:
        logger.error(f"世界重置失败: {e.message}")
        return jsonify(e.to_dict()), 500
    except Exception as e:
        logger.error(f"世界重置失败: {e}")
        return jsonify({"error": f"世界重置失败: {str(e)}"}), 500

# 3. 智能辅助服务 (CopilotService)
@app.route('/api/v1/copilot/generate', methods=['POST'])
def copilot_generate():
    """AI Copilot生成内容"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        prompt = data.get('prompt', '')
        content_type = data.get('type', 'object_type')
        context = data.get('context', {})
        
        if not prompt:
            return jsonify({"error": "没有提供提示词"}), 400
        
        # 调用AI Copilot
        result = ai_copilot.generate_content(prompt, content_type, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI生成失败: {e}")
        return jsonify({
            "status": "error",
            "error": f"AI生成失败: {str(e)}"
        }), 500

# AI Copilot兼容性路由
@app.route('/api/copilot/generate', methods=['POST'])
def copilot_generate_compat():
    """AI Copilot生成内容 (兼容性路由)"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        prompt = data.get('prompt', '')
        content_type = data.get('type', 'object_type')
        context = data.get('context', {})
        
        if not prompt:
            return jsonify({"error": "没有提供提示词"}), 400
        
        # 调用AI Copilot
        result = ai_copilot.generate_content(prompt, content_type, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI生成失败: {e}")
        return jsonify({
            "status": "error",
            "error": f"AI生成失败: {str(e)}"
        }), 500

# 简化的AI生成路由
@app.route('/api/ai_generate', methods=['POST'])
def ai_generate():
    """AI生成内容 (简化路由)"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        prompt = data.get('prompt', '')
        content_type = data.get('type', 'object_type')
        domain = data.get('domain', RequestContext.get_current_domain())
        
        if not prompt:
            return jsonify({"error": "没有提供提示词"}), 400
        
        # 验证领域访问权限
        if not DomainContextManager.validate_domain_access(domain, domain_manager.list_domains()):
            raise DomainNotFoundError(domain)
        
        # 构建上下文
        context = {
            'domain': domain,
            'schema': domain_manager.get_domain_files(domain).get('schema', ''),
            'seed': domain_manager.get_domain_files(domain).get('seed', '')
        }
        
        try:
            # 调用AI Copilot
            result = ai_copilot.generate_content(prompt, content_type, context)
            
            content = result.get("content", result.get("result", ""))
            
            if content:
                return jsonify({
                    "status": "success",
                    "result": content,
                    "type": content_type,
                    "domain": domain
                })
        except Exception as ai_error:
            logger.warning(f"AI服务调用失败，使用模拟结果: {ai_error}")
        
        # AI服务失败时返回模拟结果
        mock_result = generate_mock_result(prompt, content_type)
        return jsonify({
            "status": "success",
            "result": mock_result,
            "type": content_type,
            "domain": domain,
            "mock": True
        })
        
    except DomainNotFoundError as e:
        logger.error(f"领域不存在: {e.domain_name}")
        return jsonify(e.to_dict()), 404
    except Exception as e:
        logger.error(f"AI生成失败: {e}")
        return jsonify({
            "status": "error",
            "error": f"AI生成失败: {str(e)}"
        }), 500

def generate_mock_result(prompt, content_type):
    """生成模拟的AI结果"""
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if content_type == 'object_type':
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<ObjectType name="NewEntity{timestamp.replace('-', '').replace(':', '').replace(' ', '')}" 
           icon="cube" color="#3b82f6" primary_key="id" description="AI生成的实体类型">
    <Property name="id" type="string" required="true" description="唯一标识符"/>
    <Property name="name" type="string" required="true" description="名称"/>
    <Property name="description" type="string" required="false" description="描述"/>
    <Property name="created_at" type="datetime" required="false" default="now()" description="创建时间"/>
</ObjectType>'''
    
    elif content_type == 'relationship':
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<LinkType name="HAS_RELATIONSHIP{timestamp.replace('-', '').replace(':', '').replace(' ', '')}" 
         source="EntityA" target="EntityB" color="#10b981" description="AI生成的关系类型">
    <Property name="strength" type="integer" required="false" default="1" description="关系强度"/>
    <Property name="created_at" type="datetime" required="false" default="now()" description="创建时间"/>
</LinkType>'''
    
    elif content_type == 'action':
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<ActionType name="AI_Generated_Action" description="AI生成的动作类型">
    <Trigger type="condition" expression="always_true"/>
    <Effect type="log" message="执行AI生成的动作：{prompt}"/>
    <Effect type="update" target="current" property="last_action" value="AI_Generated_Action"/>
</ActionType>'''
    
    elif content_type == 'cypher':
        return f'''// AI生成的Cypher查询
// 提示词: {prompt}
// 生成时间: {timestamp}

MATCH (n:Entity)
WHERE n.description CONTAINS '{prompt[:20]}...'
RETURN n
LIMIT 10'''
    
    elif content_type == 'description':
        return f"""AI生成的描述（基于提示词："{prompt}"）：

这是一个由AI自动生成的描述内容。内容涉及{prompt}相关的内容，由Genesis Studio AI Copilot在{timestamp}生成。

特点：
- 智能分析用户需求
- 自动生成相关内容
- 支持多种内容类型
- 可直接应用到项目中"""
    
    else:
        return f"""AI生成的结果（类型: {content_type}）

提示词: {prompt}
生成时间: {timestamp}

这是一个模拟的AI生成结果。在实际部署中，此内容将由AI服务根据您的需求生成。"""

@app.route('/api/v1/copilot/text-to-cypher', methods=['POST'])
def text_to_cypher():
    """自然语言转Cypher"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        natural_language = data.get('text', '')
        context = data.get('context', {})
        
        if not natural_language:
            return jsonify({"error": "没有提供文本"}), 400
        
        result = ai_copilot.text_to_cypher(natural_language, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"文本转Cypher失败: {e}")
        return jsonify({"error": f"文本转Cypher失败: {str(e)}"}), 500

@app.route('/api/v1/copilot/suggest-actions', methods=['POST'])
def suggest_actions():
    """为对象类型推荐动作"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        object_type = data.get('object_type', '')
        context = data.get('context', {})
        
        if not object_type:
            return jsonify({"error": "没有提供对象类型"}), 400
        
        suggestions = ai_copilot.suggest_actions(object_type, context)
        
        return jsonify({
            "status": "success",
            "suggestions": suggestions
        })
        
    except Exception as e:
        logger.error(f"动作推荐失败: {e}")
        return jsonify({"error": f"动作推荐失败: {str(e)}"}), 500

# 4. 规则引擎服务 (RuleExecutionService)
@app.route('/api/v1/rules/simulate', methods=['POST'])
def simulate_action():
    """模拟运行动作"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        action_id = data.get('action_id', '')
        parameters = data.get('parameters', {})
        
        if not action_id:
            return jsonify({"error": "没有提供动作ID"}), 400
        
        # 创建模拟事件
        event = Event(
            event_type=EventType.USER_INTENT,
            source="simulation",
            data={
                "action": action_id,
                "parameters": parameters
            }
        )
        
        # 处理事件
        results = rule_engine.process_event(event, parameters)
        
        return jsonify({
            "status": "success",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"动作模拟失败: {e}")
        return jsonify({"error": f"动作模拟失败: {str(e)}"}), 500

@app.route('/api/v1/rules/validate', methods=['POST'])
def validate_rule():
    """验证规则"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        cypher_query = data.get('cypher_query', '')
        
        if not cypher_query:
            return jsonify({"error": "没有提供Cypher查询"}), 400
        
        # 验证Cypher语法
        valid, errors = validation_engine.validate_cypher_query(cypher_query)
        
        if valid:
            return jsonify({
                "status": "success",
                "message": "Cypher语法验证通过"
            })
        else:
            return jsonify({
                "status": "error",
                "error_code": "ERR_CYPHER_02",
                "errors": errors
            }), 400
            
    except Exception as e:
        logger.error(f"规则验证失败: {e}")
        return jsonify({"error": f"规则验证失败: {str(e)}"}), 500

# 5. Git-Ops服务
@app.route('/api/v1/git/status', methods=['GET'])
def git_status():
    """获取Git状态"""
    try:
        status = git_ops.get_git_status()
        
        return jsonify({
            "status": "success",
            "data": status
        })
        
    except Exception as e:
        logger.error(f"获取Git状态失败: {e}")
        return jsonify({"error": f"获取Git状态失败: {str(e)}"}), 500

@app.route('/api/v1/git/commit', methods=['POST'])
def git_commit():
    """创建Git提交"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        message = data.get('message', '')
        files = data.get('files', None)
        skip_validation = data.get('skip_validation', False)
        
        if not message:
            return jsonify({"error": "没有提供提交消息"}), 400
        
        result = git_ops.create_commit(message, files, skip_validation)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"创建提交失败: {e}")
        return jsonify({"error": f"创建提交失败: {str(e)}"}), 500

@app.route('/api/v1/git/hot-reload', methods=['POST'])
def hot_reload():
    """触发热重载"""
    try:
        data = request.json or {}
        domain_name = data.get('domain', RequestContext.get_current_domain())
        
        # 验证领域访问权限
        if not DomainContextManager.validate_domain_access(domain_name, domain_manager.list_domains()):
            raise DomainNotFoundError(domain_name)
        
        result = git_ops.trigger_hot_reload(domain_name)
        
        return jsonify(result)
        
    except DomainNotFoundError as e:
        logger.error(f"领域不存在: {e.domain_name}")
        return jsonify(e.to_dict()), 404
    except Exception as e:
        logger.error(f"热重载失败: {e}")
        return jsonify({"error": f"热重载失败: {str(e)}"}), 500

# 6. 领域管理服务
@app.route('/api/v1/domains', methods=['GET'])
def list_domains_api():
    """获取所有领域"""
    try:
        available_domains = domain_manager.list_domains()
        
        domains = []
        for domain_id in available_domains:
            if domain_id in DOMAIN_PACKS:
                domain_info = DOMAIN_PACKS[domain_id]
                domains.append({
                    "id": domain_id,
                    "name": domain_info["name"],
                    "description": domain_info["description"],
                    "color": domain_info["color"],
                    "icon": domain_info["icon"]
                })
        
        return jsonify({
            "status": "success",
            "domains": domains,
            "current_domain": RequestContext.get_current_domain()
        })
        
    except Exception as e:
        logger.error(f"获取领域列表失败: {e}")
        return jsonify({"error": f"获取领域列表失败: {str(e)}"}), 500
@app.route('/api/v1/git/rollback', methods=['POST'])
def git_rollback():
    """回滚到指定提交"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        commit_id = data.get('commit_id', 'HEAD~1')
        
        # 执行Git回滚
        success, output = git_ops._run_git_command(['reset', '--hard', commit_id])
        
        if success:
            return jsonify({
                "success": True,
                "message": f"已回滚到提交 {commit_id}",
                "output": output
            })
        else:
            return jsonify({"error": f"回滚失败: {output}"}), 500
            
    except Exception as e:
        logger.error(f"Git回滚失败: {e}")
        return jsonify({"error": f"Git回滚失败: {str(e)}"}), 500

@app.route('/api/v1/git/branches', methods=['GET'])
def git_branches():
    """获取所有分支"""
    try:
        success, output = git_ops._run_git_command(['branch', '-a'])
        if success:
            branches = [b.strip() for b in output.split('\n') if b.strip()]
            return jsonify({
                "success": True,
                "branches": branches
            })
        else:
            return jsonify({"error": f"获取分支失败: {output}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/git/diff', methods=['GET'])
def git_diff():
    """获取文件差异"""
    try:
        # 获取特定文件的差异或所有文件的差异
        file_path = request.args.get('file', '')
        
        if file_path:
            success, output = git_ops._run_git_command(['diff', 'HEAD', '--', file_path])
        else:
            success, output = git_ops._run_git_command(['diff', 'HEAD'])
        
        if success:
            return jsonify({
                "success": True,
                "diff": output
            })
        else:
            return jsonify({"error": f"获取差异失败: {output}"}), 500
    except Exception as e:
        logger.error(f"Git差异获取失败: {e}")
        return jsonify({"error": f"Git差异获取失败: {str(e)}"}), 500


@app.route('/api/v1/git/revert', methods=['POST'])
def git_revert():
    """撤销更改"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        file_path = data.get('file_path', '')
        
        if not file_path:
            return jsonify({"error": "需要提供文件路径"}), 400
        
        # 执行Git撤销
        success, output = git_ops._run_git_command(['checkout', '--', file_path])
        
        if success:
            return jsonify({
                "success": True,
                "message": f"已撤销文件 {file_path} 的更改",
                "output": output
            })
        else:
            return jsonify({"error": f"撤销失败: {output}"}), 500
            
    except Exception as e:
        logger.error(f"Git撤销失败: {e}")
        return jsonify({"error": f"Git撤销失败: {str(e)}"}), 500


@app.route('/api/v1/domains/<domain_name>/switch', methods=['POST'])
def switch_domain_api(domain_name):
    """切换领域"""
    try:
        if domain_name not in DOMAIN_PACKS:
            return jsonify({"error": f"未知领域: {domain_name}"}), 404
        
        success = domain_manager.activate_domain(domain_name)
        
        if success:
            # 使用 Session 存储当前领域，而不是全局变量
            RequestContext.set_current_domain(domain_name)
            
            return jsonify({
                "status": "success",
                "message": f"已切换到 {DOMAIN_PACKS[domain_name]['name']}",
                "domain": domain_name
            })
        else:
            return jsonify({"error": f"切换领域失败: {domain_name}"}), 500
            
    except Exception as e:
        logger.error(f"切换领域失败: {e}")
        return jsonify({"error": f"切换领域失败: {str(e)}"}), 500

# 兼容性路由 - 支持旧版本前端
@app.route('/api/domains', methods=['GET'])
def list_domains_compat():
    """获取所有可用领域模组 (兼容性路由)"""
    try:
        available_domains = domain_manager.list_domains()
        
        domains = []
        for domain_id in available_domains:
            if domain_id in DOMAIN_PACKS:
                domain_info = DOMAIN_PACKS[domain_id]
                domains.append({
                    "id": domain_id,
                    "name": domain_info["name"],
                    "description": domain_info["description"],
                    "color": domain_info["color"],
                    "icon": domain_info["icon"],
                    "exists": True
                })
        
        return jsonify({
            "status": "success",
            "domains": domains,
            "current_domain": RequestContext.get_current_domain()
        })
        
    except Exception as e:
        logger.error(f"获取领域列表失败: {e}")
        return jsonify({"error": f"获取领域列表失败: {str(e)}"}), 500

@app.route('/api/domains/<domain_name>', methods=['POST'])
def switch_domain_compat(domain_name):
    """切换领域模组 (兼容性路由)"""
    try:
        if domain_name not in DOMAIN_PACKS:
            return jsonify({"error": f"未知领域: {domain_name}"}), 404
        
        success = domain_manager.activate_domain(domain_name)
        
        if success:
            # 使用 Session 存储当前领域
            RequestContext.set_current_domain(domain_name)
            
            return jsonify({
                "status": "success",
                "message": f"已切换到 {DOMAIN_PACKS[domain_name]['name']}",
                "domain": domain_name,
                "domain_info": DOMAIN_PACKS[domain_name]
            })
        else:
            return jsonify({"error": f"切换领域失败: {domain_name}"}), 500
            
    except Exception as e:
        logger.error(f"切换领域失败: {e}")
        return jsonify({"error": f"切换领域失败: {str(e)}"}), 500

@app.route('/api/domains/<domain_name>/config', methods=['GET'])
def get_domain_config_compat(domain_name):
    """获取领域模组配置 (兼容性路由)"""
    try:
        # 路径遍历防护
        if not DomainContextManager.validate_domain_access(domain_name, domain_manager.list_domains()):
            raise PathTraversalError(domain_name, "Domain not in allowed list")
        
        files_content = domain_manager.get_domain_files(domain_name)
        return jsonify({
            "status": "success",
            "config": files_content
        })
        
    except PathTraversalError as e:
        logger.error(f"路径遍历检测: {e.details.get('path')}")
        return jsonify(e.to_dict()), 403
    except Exception as e:
        logger.error(f"获取领域配置失败: {e}")
        return jsonify({"error": f"获取领域配置失败: {str(e)}"}), 500

@app.route('/api/domains/<domain_name>/save', methods=['POST'])
def save_domain_config_compat(domain_name):
    """保存领域模组配置 (兼容性路由) - 原子性保存"""
    try:
        # 路径遍历防护
        if not DomainContextManager.validate_domain_access(domain_name, domain_manager.list_domains()):
            raise PathTraversalError(domain_name, "Domain not in allowed list")
        
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        # 提取要保存的文件
        file_types = []
        new_contents = {}
        
        # 导入XML转换器
        try:
            from backend.core.xml_converter import XMLConverter
        except ImportError:
            logger.error("XML转换器导入失败")
            return jsonify({"error": "XML转换器不可用"}), 500
        
        for file_type in ["schema", "seed", "actions", "patterns"]:
            content = data.get(file_type, "")
            if content:
                try:
                    # 尝试解析JSON内容
                    json_data = json.loads(content)
                    
                    # 根据文件类型转换为XML
                    if file_type == "schema":
                        # 本体数据转换为object_types.xml
                        xml_content = XMLConverter.convert_ontology_to_xml(json_data, domain_name)
                    elif file_type == "seed":
                        # 种子数据转换为seed_data.xml
                        xml_content = XMLConverter.convert_seed_data_to_xml(json_data, domain_name)
                    else:
                        # 其他文件类型保持原样
                        xml_content = content
                    
                    file_types.append(file_type)
                    new_contents[file_type] = xml_content
                    
                except json.JSONDecodeError:
                    # 如果不是JSON，保持原样
                    file_types.append(file_type)
                    new_contents[file_type] = content
                except Exception as e:
                    logger.error(f"处理{file_type}文件失败: {e}")
                    return jsonify({"error": f"处理{file_type}文件失败: {str(e)}"}), 500
        
        if not file_types:
            return jsonify({"error": "没有要保存的文件内容"}), 400
        
        # 判断是否需要同步到 Neo4j
        sync_to_neo4j = data.get('sync_to_neo4j', False)
        neo4j_loader_instance = Neo4jLoader() if sync_to_neo4j else None
        
        # 使用原子性保存
        result = save_domain_config_atomic(
            domain_manager=domain_manager,
            domain_name=domain_name,
            file_types=file_types,
            new_contents=new_contents,
            sync_to_neo4j=sync_to_neo4j,
            neo4j_loader=neo4j_loader_instance
        )
        
        return jsonify(result)
        
    except PathTraversalError as e:
        logger.error(f"路径遍历检测: {e.details.get('path')}")
        return jsonify(e.to_dict()), 403
    except TransactionError as e:
        logger.error(f"事务失败，已回滚: {e.message}")
        return jsonify(e.to_dict()), 500
    except Exception as e:
        logger.error(f"保存领域配置失败: {e}")
        return jsonify({"error": f"保存领域配置失败: {str(e)}"}), 500

# 7. 仿真启动服务
@app.route('/api/launch_simulation', methods=['POST'])
def launch_simulation():
    """启动领域仿真"""
    try:
        data = request.json or {}
        domain_name = data.get('domain', RequestContext.get_current_domain())
        
        # 验证领域访问权限
        if not DomainContextManager.validate_domain_access(domain_name, domain_manager.list_domains()):
            raise DomainNotFoundError(domain_name)
        
        # 获取当前领域配置
        files_content = domain_manager.get_domain_files(domain_name)
        
        logger.info(f"Launch simulation for domain: {domain_name}")
        logger.info(f"Files content keys: {list(files_content.keys())}")
        
        # 检查是否有文件内容
        has_content = False
        for file_type, content in files_content.items():
            if content and content.strip():
                has_content = True
                logger.info(f"{file_type}: {len(content)} chars")
                break
        
        if not has_content:
            logger.info(f"No content found for domain: {domain_name}")
        
        # 这里可以添加仿真启动逻辑
        # 例如：启动独立的仿真进程、初始化仿真环境等
        
        return jsonify({
            "status": "success",
            "message": f"仿真启动成功",
            "domain_name": domain_name,
            "domain_info": DOMAIN_PACKS.get(domain_name, {}),
            "has_files": has_content
        })
        
    except DomainNotFoundError as e:
        logger.error(f"领域不存在: {e.domain_name}")
        return jsonify(e.to_dict()), 404
    except Exception as e:
        logger.error(f"仿真启动失败: {e}")
        return jsonify({
            "status": "error",
            "error": f"仿真启动失败: {str(e)}"
        }), 500

@app.route('/api/upload/csv', methods=['POST'])
def upload_csv():
    """上传CSV文件并转换为本体"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({"error": "没有选择文件"}), 400
        
        domain = request.form.get('domain', RequestContext.get_current_domain())
        action = request.form.get('action', 'csv_to_ontology')
        
        # 验证文件类型
        filename = file.filename or ''
        if not filename.lower().endswith('.csv'):
            return jsonify({"error": "只支持CSV文件"}), 400
        
        # 读取CSV内容
        csv_content = file.read().decode('utf-8')
        
        # 调用AI分析CSV并生成本体 - 使用object_type内容类型
        ai_response = ai_copilot.generate_content(
            prompt=f"""请将以下CSV数据转换为本体结构：
文件: {filename}
内容:
{csv_content}

要求：
1. 识别实体类型和属性
2. 建议关系类型
3. 生成JSON格式的本体定义
4. 适合领域: {domain}""",
            content_type="object_type",
            context={
                "data_type": "csv_to_ontology",
                "file_name": filename,
                "domain": domain,
                "csv_content": csv_content[:1000]  # 限制长度
            }
        )
        
        # 解析AI响应
        content = ai_response.get('content', '')
        
        # 尝试提取JSON格式的本体定义
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            ontology_json = json_match.group(1)
        else:
            # 如果没有找到JSON块，使用整个内容
            ontology_json = content
        
        return jsonify({
            "status": "success",
            "message": "CSV分析完成",
            "file_name": filename,
            "domain": domain,
            "analysis": content,
            "ontology": ontology_json if ontology_json else None
        })
        
    except Exception as e:
        logger.error(f"CSV上传失败: {e}")
        return jsonify({
            "status": "error",
            "error": f"CSV上传失败: {str(e)}"
        }), 500

@app.route('/api/save_ontology', methods=['POST'])
def save_ontology():
    """保存本体数据"""
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "没有提供数据"}), 400
        
        domain = data.get('domain', RequestContext.get_current_domain())
        ontology_xml = data.get('ontology_xml', '')
        
        # 路径遍历防护
        if not DomainContextManager.validate_domain_access(domain, domain_manager.list_domains()):
            raise PathTraversalError(domain, "Domain not in allowed list")
        
        if not ontology_xml:
            return jsonify({"status": "error", "message": "没有提供本体数据"}), 400
        
        # 保存到领域目录
        success = domain_manager.save_domain_file(domain, "seed", ontology_xml)
        
        if success:
            logger.info(f"Saved ontology for domain: {domain}")
            return jsonify({
                "status": "success",
                "message": "本体数据保存成功",
                "domain": domain
            })
        else:
            return jsonify({
                "status": "error",
                "message": "本体数据保存失败"
            }), 500
            
    except PathTraversalError as e:
        logger.error(f"路径遍历检测: {e.details.get('path')}")
        return jsonify(e.to_dict()), 403
    except Exception as e:
        logger.error(f"保存本体失败: {e}")
        return jsonify({
            "status": "error",
            "message": f"保存失败: {str(e)}"
        }), 500

# 8. 图谱数据服务 (保留原有API兼容性)
@app.route('/api/graph', methods=['GET'])
def get_graph():
    """获取图谱数据"""
    try:
        node_type = request.args.get('type', None)
        limit = int(request.args.get('limit', 100))
        
        loader = Neo4jLoader()
        graph_data = loader.query_graph(node_type=node_type, limit=limit)
        
        return jsonify(graph_data)
        
    except Exception as e:
        logger.error(f"获取图谱失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "nodes": [],
            "links": []
        }), 500

@app.route('/api/graph/stats', methods=['GET'])
def get_graph_stats():
    """获取图谱统计"""
    try:
        loader = Neo4jLoader()
        stats = loader.get_graph_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"获取图谱统计失败: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# 编辑器API端点
@app.route('/api/editor/save', methods=['POST'])
def editor_save():
    """保存文件内容"""
    try:
        file_path = request.form.get('file_path')
        content = request.form.get('content')
        
        if not file_path or content is None:
            return jsonify({"error": "缺少文件路径或内容"}), 400
        
        # 解析文件路径，确定保存位置
        if file_path.startswith('objects/'):
            # 保存对象类型
            type_key = file_path.replace('objects/', '').replace('.json', '')
            current_domain = RequestContext.get_current_domain()
            files_content = domain_manager.get_domain_files(current_domain)
            
            # 更新schema中的对象类型
            if files_content.get('schema'):
                schema_data = json.loads(files_content['schema'])
                object_types = schema_data.get('object_types', [])
                
                # 查找并更新或添加对象类型
                updated = False
                for i, obj in enumerate(object_types):
                    if obj.get('type_key') == type_key:
                        object_types[i] = json.loads(content)
                        updated = True
                        break
                
                if not updated:
                    object_types.append(json.loads(content))
                
                schema_data['object_types'] = object_types
                success = domain_manager.save_domain_file(current_domain, 'schema', json.dumps(schema_data, indent=2))
                
                if success:
                    return jsonify({"status": "success", "message": "对象类型保存成功"})
                else:
                    return jsonify({"error": "保存失败"}), 500
        
        return jsonify({"error": "不支持的文件类型"}), 400
        
    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        return jsonify({"error": f"保存失败: {str(e)}"}), 500

@app.route('/api/editor/save/object', methods=['POST'])
def save_object():
    """保存对象类型（表单方式）"""
    try:
        type_key = request.form.get('type_key')
        display_name = request.form.get('display_name')
        description = request.form.get('description')
        
        if not type_key:
            return jsonify({"error": "缺少类型键"}), 400
        
        # 构建对象类型数据
        object_data = {
            "type_key": type_key,
            "name": display_name or type_key,
            "description": description or "",
            "properties": {},
            "visual_assets": [],
            "tags": []
        }
        
        # 处理属性
        property_names = request.form.getlist('property_name[]')
        property_types = request.form.getlist('property_type[]')
        property_defaults = request.form.getlist('property_default[]')
        
        properties = {}
        for i in range(len(property_names)):
            if property_names[i]:
                prop_name = property_names[i]
                prop_type = property_types[i] if i < len(property_types) else "string"
                prop_default = property_defaults[i] if i < len(property_defaults) else ""
                
                properties[prop_name] = prop_type
                if prop_default:
                    # 这里可以添加默认值处理逻辑
                    pass
        
        object_data["properties"] = properties
        
        # 保存到领域
        current_domain = RequestContext.get_current_domain()
        files_content = domain_manager.get_domain_files(current_domain)
        
        if files_content.get('schema'):
            schema_data = json.loads(files_content['schema'])
            object_types = schema_data.get('object_types', [])
            
            # 查找并更新或添加对象类型
            updated = False
            for i, obj in enumerate(object_types):
                if obj.get('type_key') == type_key:
                    object_types[i] = object_data
                    updated = True
                    break
            
            if not updated:
                object_types.append(object_data)
            
            schema_data['object_types'] = object_types
            success = domain_manager.save_domain_file(current_domain, 'schema', json.dumps(schema_data, indent=2))
            
            if success:
                return jsonify({"status": "success", "message": "对象类型保存成功"})
            else:
                return jsonify({"error": "保存失败"}), 500
        else:
            return jsonify({"error": "没有找到schema文件"}), 400
        
    except Exception as e:
        logger.error(f"保存对象失败: {e}")
        return jsonify({"error": f"保存失败: {str(e)}"}), 500

@app.route('/api/editor/validate', methods=['POST'])
def editor_validate():
    """验证内容"""
    try:
        content = request.form.get('content')
        
        if not content:
            return jsonify({"error": "没有提供内容"}), 400
        
        # 尝试解析JSON
        try:
            data = json.loads(content)
            return jsonify({
                "status": "success", 
                "message": "JSON格式正确",
                "data": data
            })
        except json.JSONDecodeError as e:
            return jsonify({
                "status": "error",
                "message": f"JSON格式错误: {str(e)}",
                "line": e.lineno,
                "column": e.colno
            }), 400
            
    except Exception as e:
        logger.error(f"验证失败: {e}")
        return jsonify({"error": f"验证失败: {str(e)}"}), 500

# 测试页面
@app.route('/test')
def test_page():
    """测试页面"""
    return render_template('test.html')

@app.route('/simple-test')
def simple_test():
    """简单测试页面"""
    return render_template('simple_test.html')

@app.route('/editor-simple')
def editor_simple():
    """简化编辑器页面"""
    return render_template('editor_simple.html')

@app.route('/api/test')
def api_test():
    """测试API"""
    return "<div class='p-4 bg-green-100 rounded'>HTMX 请求成功！时间: " + datetime.now().strftime("%H:%M:%S") + "</div>"

# 静态文件服务
@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory(BASE_DIR / 'static', filename)

# 导入HTMX路由
try:
    # 使用绝对导入
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from htmx_routes import register_htmx_routes
    app = register_htmx_routes(app, domain_manager, validation_engine, ai_copilot, git_ops, rule_engine)
    logger.info("HTMX路由注册成功")
except ImportError as e:
    logger.warning(f"HTMX路由导入失败: {e}")
except Exception as e:
    logger.error(f"HTMX路由注册失败: {e}")

# 性能监控端点
@app.route('/api/performance/metrics', methods=['POST'])
def receive_performance_metrics():
    """接收前端性能指标数据"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        # 记录性能数据
        logger.info(f"性能指标接收: {data.get('url', '未知URL')}")
        
        # 提取关键指标
        metrics = data.get('metrics', {})
        page_load = metrics.get('pageLoad', {})
        
        if page_load:
            logger.info(f"页面加载时间: {page_load.get('total', 0)}ms")
            
            # 检查是否超过阈值
            if page_load.get('total', 0) > 3000:  # 3秒阈值
                logger.warning(f"页面加载时间超过阈值: {page_load.get('total', 0)}ms")
        
        # 记录慢速资源
        slow_resources = metrics.get('resourceTiming', [])
        slow_resources = [r for r in slow_resources if r.get('duration', 0) > 1000]
        
        if slow_resources:
            logger.warning(f"发现 {len(slow_resources)} 个慢速资源")
            for resource in slow_resources[:3]:  # 只记录前3个
                logger.warning(f"  慢速资源: {resource.get('name', '未知')} - {resource.get('duration', 0)}ms")
        
        return jsonify({"status": "success", "message": "性能数据已接收"})
        
    except Exception as e:
        logger.error(f"性能数据接收失败: {e}")
        return jsonify({"error": f"性能数据接收失败: {str(e)}"}), 500


# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "未找到资源"}), 404

@app.errorhandler(DomainNotFoundError)
def handle_domain_not_found(error):
    return jsonify(error.to_dict()), 404

@app.errorhandler(PathTraversalError)
def handle_path_traversal(error):
    return jsonify(error.to_dict()), 403

@app.errorhandler(SecurityError)
def handle_security_error(error):
    return jsonify(error.to_dict()), 403

@app.errorhandler(SchemaValidationError)
def handle_schema_validation(error):
    return jsonify(error.to_dict()), 400

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"内部服务器错误: {error}")
    return jsonify({"error": "内部服务器错误"}), 500

# ========== WebSocket事件处理器 ==========

@socketio.on('connect')
def handle_connect():
    """WebSocket连接建立"""
    logger.info(f"WebSocket客户端连接")
    emit('message', {'type': 'connected', 'message': 'WebSocket连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket连接断开"""
    logger.info(f"WebSocket客户端断开")

@socketio.on('console_message')
def handle_console_message(data):
    """处理控制台消息"""
    logger.info(f"收到控制台消息: {data}")
    # 广播给所有客户端
    emit('console_output', {'message': data.get('message', '')}, broadcast=True)

# 后台线程发送模拟控制台输出
def send_console_updates():
    """定期发送控制台更新"""
    import time
    while True:
        time.sleep(5)
        socketio.emit('console_output', {
            'message': f'[系统] 服务器运行正常 - {time.strftime("%H:%M:%S")}',
            'type': 'system'
        })

# 启动后台线程
console_thread = threading.Thread(target=send_console_updates, daemon=True)
console_thread.start()

# 启动应用
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Genesis Studio v2.0 (MDA Architecture)")
    logger.info("=" * 60)
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info("Domain Context: Session-based (multi-user safe)")
    logger.info("=" * 60)
    logger.info("Available Services:")
    logger.info("  ✓ Ontology Management Service")
    logger.info("  ✓ World Simulation Service")
    logger.info("  ✓ AI Copilot Service")
    logger.info("  ✓ Rule Engine Service")
    logger.info("  ✓ Git-Ops Service")
    logger.info("=" * 60)
    logger.info("Starting Flask server with WebSocket support on http://localhost:5000")
    logger.info("Press Ctrl+C to stop")
    
    socketio.run(app, debug=True, port=5000, host='0.0.0.0')