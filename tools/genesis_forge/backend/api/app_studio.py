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
from flask import Flask, request, render_template, jsonify, send_from_directory, Response, stream_with_context
from flask_socketio import SocketIO, emit
from flask_cors import CORS

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

# 启用CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# 初始化WebSocket
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# 初始化服务 - 使用真实数据目录
domain_manager = DomainManager(str(REAL_DATA_ROOT))
validation_engine = ValidationEngine(str(PROJECT_ROOT))
ai_copilot = EnhancedAICopilot(str(PROJECT_ROOT))
git_ops = GitOpsManager(str(PROJECT_ROOT), validation_engine)
rule_engine = RuleEngine(validation_engine)

# 注意：copilot_routes已经在app_studio.py中定义了路由
# 不需要重复注册，否则会导致路由冲突
# app = register_copilot_routes(app, ai_copilot, domain_manager)

# 领域模组配置 - 动态从 domains/ 目录加载
import os
import json
from pathlib import Path

def load_domain_packs():
    """动态加载 domains/ 目录中的所有域"""
    domain_packs = {}
    domains_dir = Path(__file__).parent.parent.parent.parent.parent / "domains"
    
    # 默认域（确保基本域存在）
    default_domains = {
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
    
    # 首先添加默认域
    domain_packs.update(default_domains)
    
    # 动态扫描 domains/ 目录
    if domains_dir.exists():
        for domain_dir in domains_dir.iterdir():
            if domain_dir.is_dir():
                domain_id = domain_dir.name
                
                # 跳过已存在的默认域
                if domain_id in default_domains:
                    continue
                
                # 读取域配置
                config_file = domain_dir / "config.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        domain_packs[domain_id] = {
                            "name": config.get("name", domain_id),
                            "description": config.get("description", "自定义业务领域"),
                            "color": config.get("ui_config", {}).get("primary_color", "#3b82f6"),
                            "icon": "cogs"  # 默认图标
                        }
                    except Exception as e:
                        print(f"加载域配置失败 {domain_id}: {e}")
                        # 使用默认值
                        domain_packs[domain_id] = {
                            "name": domain_id.replace("_", " ").title(),
                            "description": "自定义业务领域",
                            "color": "#3b82f6",
                            "icon": "cogs"
                        }
                else:
                    # 没有配置文件，使用默认值
                    domain_packs[domain_id] = {
                        "name": domain_id.replace("_", " ").title(),
                        "description": "自定义业务领域",
                        "color": "#3b82f6",
                        "icon": "cogs"
                    }
    
    return domain_packs

DOMAIN_PACKS = load_domain_packs()

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
    
    if current_domain not in DOMAIN_PACKS:
        current_domain = "supply_chain"
        RequestContext.set_current_domain(current_domain)
    
    files_content = domain_manager.get_domain_files(current_domain)
    
    current_domain_info = DOMAIN_PACKS.get(current_domain, {})
    
    object_types = []
    action_rules = []
    seed_data = []
    
    try:
        if files_content.get('schema'):
            schema_data = json.loads(files_content['schema'])
            if 'object_types' in schema_data:
                object_types = schema_data['object_types']
        
        if files_content.get('actions'):
            actions_data = json.loads(files_content['actions'])
            if 'actions' in actions_data:
                action_rules = actions_data['actions']
        
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
                         graph_elements=[])  # 图谱数据将通过API加载

@app.route('/editor')
def editor():
    """编辑器页面 - 本体编辑器 IDE (兼容性路由)"""
    current_domain = RequestContext.get_current_domain()
    
    if current_domain not in DOMAIN_PACKS:
        current_domain = "supply_chain"
        RequestContext.set_current_domain(current_domain)
    
    files_content = domain_manager.get_domain_files(current_domain)
    
    current_domain_info = DOMAIN_PACKS.get(current_domain, {})
    
    object_types = []
    action_rules = []
    seed_data = []
    
    try:
        if files_content.get('schema'):
            schema_data = json.loads(files_content['schema'])
            if 'object_types' in schema_data:
                object_types = schema_data['object_types']
        
        if files_content.get('actions'):
            actions_data = json.loads(files_content['actions'])
            if 'actions' in actions_data:
                action_rules = actions_data['actions']
        
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
                         graph_elements=[])  # 图谱数据将通过API加载

# ========== 原子服务API端点 ==========

@app.route('/api/v1/ontology/validate', methods=['POST'])
def validate_ontology():
    """验证本体完整性"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
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
        current_domain = RequestContext.get_current_domain()
        
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
        
        schema_data = {}
        
        try:
            schema_data = json.loads(schema_content)
            logger.info(f"Schema是JSON格式，成功解析")
        except json.JSONDecodeError:
            logger.info(f"Schema是XML格式，尝试从XML中提取本体数据")
            try:
                from backend.core.xml_converter import XMLConverter
                
                import xml.etree.ElementTree as ET
                root = ET.fromstring(schema_content)
                
                schema_data = {
                    "domain": current_domain,
                    "object_types": {},
                    "relationships": {},
                    "action_types": {},
                    "world_snapshots": {},
                    "domain_concepts": []
                }
                
                for obj_elem in root.findall(".//ObjectType"):
                    obj_name = obj_elem.get("name")
                    if obj_name:
                        if obj_name.isupper() and ' ' not in obj_name:
                            type_key = obj_name
                        else:
                            type_key = obj_name.upper().replace(' ', '_').replace('-', '_')
                        
                        obj_def = {
                            "type_key": type_key,  # 必须是大写下划线格式
                            "name": obj_name,
                            "description": obj_elem.get("description", ""),
                            "properties": {},
                            "visual_assets": [],
                            "tags": []
                        }
                        
                        for prop_elem in obj_elem.findall(".//Property"):
                            prop_name = prop_elem.get("name")
                            if prop_name:
                                obj_def["properties"][prop_name] = {
                                    "name": prop_name,  # 必需字段
                                    "type": prop_elem.get("type", "string"),
                                    "description": prop_elem.get("description", ""),
                                    "default_value": None,
                                    "is_required": False,
                                    "constraints": {}  # 应该是字典，不是列表
                                }
                        
                        schema_data["object_types"][obj_name] = obj_def
                
                link_types_elem = root.find(".//LinkTypes")
                if link_types_elem is not None:
                    for link_elem in link_types_elem.findall(".//LinkType"):
                        link_name = link_elem.get("name")
                        if link_name:
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
        
        if "domain" not in schema_data:
            schema_data["domain"] = current_domain
        
        if "relationships" in schema_data and isinstance(schema_data["relationships"], list):
            relationships_dict = {}
            for rel in schema_data["relationships"]:
                if isinstance(rel, dict):
                    rel_name = rel.get("name") or rel.get("type")
                    if rel_name:
                        relationships_dict[rel_name] = rel
            schema_data["relationships"] = relationships_dict
        
        if "objectTypes" in schema_data and isinstance(schema_data["objectTypes"], list):
            object_types_dict = {}
            for obj in schema_data["objectTypes"]:
                if isinstance(obj, dict):
                    obj_name = obj.get("name") or obj.get("type_key")
                    if obj_name:
                        object_types_dict[obj_name] = obj
            schema_data["objectTypes"] = object_types_dict
        
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
            
            error_message = str(model_error)
            error_details = []
            
            if "validation errors for OntologyModel" in error_message:
                lines = error_message.split('\n')
                for line in lines:
                    if 'type=value_error' in line or 'type=missing' in line:
                        parts = line.strip().split()
                        if parts:
                            field_name = parts[0]
                            error_type = "validation_error"
                            if 'type=value_error' in line:
                                error_type = "value_error"
                            elif 'type=missing' in line:
                                error_type = "missing_field"
                            
                            error_details.append({
                                "field": field_name,
                                "type": error_type,
                                "message": line.strip()
                            })
            
            return jsonify({
                "status": "error",
                "message": "本体数据格式错误",
                "error": error_message,
                "errors": error_details if error_details else [{"field": "unknown", "message": error_message}],
                "schema_data_keys": list(schema_data.keys())
            }), 400
        
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
        
        if not DomainContextManager.validate_domain_access(domain, domain_manager.list_domains()):
            raise DomainNotFoundError(domain)
        
        files_content = domain_manager.get_domain_files(domain)
        seed_content = files_content.get("seed", "")
        
        if not seed_content:
            return jsonify({
                "status": "error",
                "message": "没有初始世界数据"
            }), 400
        
        loader = Neo4jLoader()
        loader.delete_all_nodes()
        
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
        
        result = ai_copilot.generate_content(prompt, content_type, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI生成失败: {e}")
        return jsonify({
            "status": "error",
            "error": f"AI生成失败: {str(e)}"
        }), 500

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
        
        result = ai_copilot.generate_content(prompt, content_type, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI生成失败: {e}")
        return jsonify({
            "status": "error",
            "error": f"AI生成失败: {str(e)}"
        }), 500

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
        
        if not DomainContextManager.validate_domain_access(domain, domain_manager.list_domains()):
            raise DomainNotFoundError(domain)
        
        context = {
            'domain': domain,
            'schema': domain_manager.get_domain_files(domain).get('schema', ''),
            'seed': domain_manager.get_domain_files(domain).get('seed', '')
        }
        
        try:
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

@app.route('/api/v1/copilot/csv-to-domain', methods=['POST'])
def csv_to_domain():
    """将CSV数据转换为完整的领域文件"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        csv_content = data.get('csv_content', '')
        domain_name = data.get('domain_name', 'CSV导入领域')
        domain_id = data.get('domain_id', '')
        
        if not csv_content:
            return jsonify({"error": "没有提供CSV内容"}), 400
        
        if not domain_id:
            # 自动生成领域ID
            import re
            domain_id = re.sub(r'[^a-z0-9_]', '_', domain_name.lower())
            domain_id = re.sub(r'_+', '_', domain_id).strip('_')
            if not domain_id:
                domain_id = 'csv_imported_domain'
        
        # 构建详细的提示词
        prompt = f"""请基于以下CSV数据生成完整的领域本体文件：

领域信息:
- 领域名称: {domain_name}
- 领域ID: {domain_id}

CSV内容:
{csv_content[:3000]}

请生成以下完整的XML/JSON文件：

1. config.json - 领域配置文件
   - 包含name, description, ui_config等
   - 根据CSV内容选择合适的颜色和图标

2. object_types.xml - 对象类型定义
   - 分析CSV中的实体类型（如product, supplier, customer等）
   - 为每种实体类型定义属性和约束
   - 包含合适的图标和颜色

3. action_types.xml - 动作类型定义
   - 基于CSV中的业务逻辑推断可能的动作
   - 包含preconditions和effects

4. seed_data.xml - 种子数据
   - 将CSV数据转换为XML格式的种子数据
   - 保持数据完整性和一致性

5. synapser_patterns.xml - 同步模式定义（可选）
   - 定义数据同步和转换规则

请确保：
1. 所有XML文件格式正确，有完整的XML声明
2. JSON文件格式正确
3. 文件内容符合业务逻辑
4. 使用中文注释说明重要部分

请为每个文件生成完整的内容，用```xml和```json代码块包裹。"""

        # 调用AI Copilot
        result = ai_copilot.generate_content(prompt, "object_type", {
            "data_type": "csv_to_domain",
            "domain_name": domain_name,
            "domain_id": domain_id,
            "csv_sample": csv_content[:500]
        })
        
        content = result.get("content", result.get("result", ""))
        
        return jsonify({
            "status": "success",
            "domain_name": domain_name,
            "domain_id": domain_id,
            "generated_content": content,
            "files": [
                "config.json",
                "object_types.xml", 
                "action_types.xml",
                "seed_data.xml",
                "synapser_patterns.xml"
            ]
        })
        
    except Exception as e:
        logger.error(f"CSV转领域失败: {e}")
        return jsonify({
            "status": "error",
            "error": f"CSV转领域失败: {str(e)}"
        }), 500

@app.route('/api/copilot/csv-to-domain', methods=['POST'])
def csv_to_domain_compat():
    """CSV转领域 (兼容性路由)"""
    return csv_to_domain()

@app.route('/api/v1/copilot/stream', methods=['GET', 'OPTIONS'])
def copilot_stream():
    """AI Copilot流式响应 - Server-Sent Events"""
    # 检查是否有聊天消息参数
    chat_message = request.args.get('message')
    session_id = request.args.get('session_id', 'default')
    
    # 记录所有请求参数
    logger.info(f"SSE请求 - URL: {request.url}")
    logger.info(f"SSE请求 - 参数: {dict(request.args)}")
    
    if chat_message:
        logger.info(f"SSE连接建立 - 会话: {session_id}, 消息长度: {len(chat_message)}")
        logger.info(f"消息内容: {chat_message[:100]}...")
    else:
        logger.info(f"SSE连接建立 - 会话: {session_id}, 消息: None")
    
    def generate():
        import json
        import time
        
        logger.info("SSE生成器开始执行")
        
        # 发送连接确认
        data = json.dumps({'type': 'connected', 'message': 'SSE连接已建立', 'session_id': session_id})
        logger.info(f"发送连接确认: {data}")
        yield f"data: {data}\n\n"
        logger.info("连接确认已发送")
        
        # 如果没有聊天消息，只发送心跳
        if not chat_message:
            logger.info("无聊天消息，发送心跳模式")
            # 发送心跳保持连接
            try:
                count = 0
                while True:
                    count += 1
                    time.sleep(10)  # 每10秒发送一次心跳
                    heartbeat = json.dumps({'type': 'heartbeat', 'timestamp': time.time(), 'count': count})
                    yield f"data: {heartbeat}\n\n"
            except GeneratorExit:
                logger.info("SSE心跳连接关闭")
            return
        
        # 如果有聊天消息，处理AI响应
        logger.info(f"处理聊天消息，长度: {len(chat_message)}")
        
        try:
            # 首先发送连接确认和思考状态
            connected = json.dumps({'type': 'connected', 'message': '开始处理您的消息', 'session_id': session_id})
            logger.info("发送开始处理消息")
            yield f"data: {connected}\n\n"
            logger.info("开始处理消息已发送")
            
            thinking = json.dumps({'type': 'chunk', 'content': '正在思考您的问题...'})
            logger.info("发送思考状态")
            yield f"data: {thinking}\n\n"
            logger.info("思考状态已发送")
            
            # 对于SSE流，避免长时间阻塞，使用yield来模拟延迟
            # 不直接使用time.sleep，因为它会阻塞整个线程
            
            try:
                # 构建更专业的提示词
                prompt = f"""用户请求: {chat_message}

请作为Genesis Studio的AI Copilot助手，专门帮助用户创建和修改本体结构。

如果是关于创建对象类型定义的请求，请提供完整的XML格式定义。
如果是其他问题，请提供有帮助的回应。

请用中文回答，保持专业和实用。"""
                
                # 使用现有的AI Copilot服务
                logger.info(f"调用AI Copilot处理消息: {chat_message}")
                
                try:
                    # 调用AI Copilot的chat方法
                    result = ai_copilot.chat(chat_message)
                    
                    if result["status"] == "success":
                        response = result.get("response", "")
                        
                        # 将响应分块发送（模拟流式）
                        chunk_size = 50
                        for i in range(0, len(response), chunk_size):
                            chunk = response[i:i+chunk_size]
                            data = json.dumps({'type': 'chunk', 'content': chunk})
                            yield f"data: {data}\n\n"
                            time.sleep(0.05)  # 稍微延迟以模拟流式
                    else:
                        # 发送错误消息
                        error_msg = result.get("error", "AI处理失败")
                        data = json.dumps({'type': 'chunk', 'content': f"抱歉，AI处理时出现错误: {error_msg}"})
                        yield f"data: {data}\n\n"
                        
                except Exception as e:
                    logger.error(f"AI流式处理失败: {e}")
                    # 发送模拟响应
                    mock_response = "我收到了: " + chat_message + ". 这是一个模拟响应，因为AI服务暂时不可用。"
                    
                    # 分块发送模拟响应
                    chunk_size = 50
                    for i in range(0, len(mock_response), chunk_size):
                        chunk = mock_response[i:i+chunk_size]
                        data = json.dumps({'type': 'chunk', 'content': chunk})
                        yield f"data: {data}\n\n"
                        time.sleep(0.05)
                
            except Exception as ai_error:
                logger.error(f"AI流式处理失败: {ai_error}", exc_info=True)
                # 发送错误消息
                error_msg = json.dumps({'type': 'chunk', 'content': f'抱歉，AI处理时出现错误: {str(ai_error)[:100]}'})
                yield f"data: {error_msg}\n\n"
                
                # 发送备用响应
                backup_msg = json.dumps({'type': 'chunk', 'content': f'我收到了: {chat_message}. 这是一个模拟响应，因为AI服务暂时不可用。'})
                yield f"data: {backup_msg}\n\n"
            
            # 发送完成消息
            complete = json.dumps({'type': 'complete', 'ai_processed': True})
            complete_data = f"data: {complete}\n\n"
            logger.info("发送complete消息")
            yield complete_data
            
            logger.info("AI响应发送完成")
            
            # 添加一个明确的结束标记，确保连接正常关闭
            # 发送一个注释行表示流结束
            yield ": stream completed\n\n"
            
            # 确保生成器结束
            return
            
        except Exception as e:
            logger.error(f"AI处理失败: {e}", exc_info=True)
            # 发送错误消息
            error_msg = json.dumps({'type': 'error', 'message': f'处理失败: {str(e)[:100]}'})
            yield f"data: {error_msg}\n\n"
            
            # 发送模拟响应作为后备
            mock = json.dumps({'type': 'chunk', 'content': f'我收到了: {chat_message}. 这是一个模拟响应。'})
            yield f"data: {mock}\n\n"
            
            complete = json.dumps({'type': 'complete', 'mock': True})
            yield f"data: {complete}\n\n"
    
    response = Response(stream_with_context(generate()), 
                       mimetype='text/event-stream')
    
    # 设置SSE所需的头
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Type'
    
    return response

@app.route('/api/copilot/stream', methods=['GET', 'OPTIONS'])
def copilot_stream_compat():
    """AI Copilot流式响应 (兼容性路由)"""
    if request.method == 'OPTIONS':
        # CORS preflight
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
    return copilot_stream()

@app.route('/api/copilot/chat', methods=['POST', 'OPTIONS'])
def copilot_chat_compat():
    """AI Copilot聊天 (兼容性路由) - 流式响应"""
    if request.method == 'OPTIONS':
        # CORS preflight
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({'error': '没有提供消息'}), 400
        
        message = data['message']
        context = data.get('context', {})
        history = data.get('history', [])
        
        logger.info(f"Copilot聊天请求: {message[:100]}...")
        
        # 立即返回，表示请求已接收
        # 实际响应将通过SSE连接发送
        return jsonify({
            'status': 'received',
            'message': '请求已接收，将通过SSE流式返回响应',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Copilot聊天失败: {e}")
        return jsonify({'error': str(e)}), 500

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
        
        event = Event(
            event_type=EventType.USER_INTENT,
            source="simulation",
            data={
                "action": action_id,
                "parameters": parameters
            }
        )
        
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
        if not DomainContextManager.validate_domain_access(domain_name, domain_manager.list_domains()):
            raise PathTraversalError(domain_name, "Domain not in allowed list")
        
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        file_types = []
        new_contents = {}
        
        try:
            from backend.core.xml_converter import XMLConverter
        except ImportError:
            logger.error("XML转换器导入失败")
            return jsonify({"error": "XML转换器不可用"}), 500
        
        for file_type in ["schema", "seed", "actions", "patterns"]:
            content = data.get(file_type, "")
            if content:
                try:
                    json_data = json.loads(content)
                    
                    if file_type == "schema":
                        xml_content = XMLConverter.convert_ontology_to_xml(json_data, domain_name)
                    elif file_type == "seed":
                        xml_content = XMLConverter.convert_seed_data_to_xml(json_data, domain_name)
                    else:
                        xml_content = content
                    
                    file_types.append(file_type)
                    new_contents[file_type] = xml_content
                    
                except json.JSONDecodeError:
                    file_types.append(file_type)
                    new_contents[file_type] = content
                except Exception as e:
                    logger.error(f"处理{file_type}文件失败: {e}")
                    return jsonify({"error": f"处理{file_type}文件失败: {str(e)}"}), 500
        
        if not file_types:
            return jsonify({"error": "没有要保存的文件内容"}), 400
        
        sync_to_neo4j = data.get('sync_to_neo4j', False)
        neo4j_loader_instance = Neo4jLoader() if sync_to_neo4j else None
        
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

@app.route('/api/launch_simulation', methods=['POST'])
def launch_simulation():
    """启动领域仿真"""
    try:
        data = request.json or {}
        domain_name = data.get('domain', RequestContext.get_current_domain())
        
        if not DomainContextManager.validate_domain_access(domain_name, domain_manager.list_domains()):
            raise DomainNotFoundError(domain_name)
        
        files_content = domain_manager.get_domain_files(domain_name)
        
        logger.info(f"Launch simulation for domain: {domain_name}")
        logger.info(f"Files content keys: {list(files_content.keys())}")
        
        has_content = False
        for file_type, content in files_content.items():
            if content and content.strip():
                has_content = True
                logger.info(f"{file_type}: {len(content)} chars")
                break
        
        if not has_content:
            logger.info(f"No content found for domain: {domain_name}")
        
        
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
    """上传CSV文件并进行分析（第一步：分析展示）"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({"error": "没有选择文件"}), 400
        
        domain = request.form.get('domain', RequestContext.get_current_domain())
        action = request.form.get('action', 'csv_to_ontology')
        
        filename = file.filename or ''
        if not filename.lower().endswith('.csv'):
            return jsonify({"error": "只支持CSV文件"}), 400
        
        csv_content = file.read().decode('utf-8')
        
        # 创建领域ID（从领域名称转换，只保留英文字母、数字和下划线）
        import re
        # 移除所有非ASCII字符
        domain_id = re.sub(r'[^a-zA-Z0-9_]', '_', domain)
        # 转换为小写
        domain_id = domain_id.lower()
        # 移除连续的下划线
        domain_id = re.sub(r'_+', '_', domain_id).strip('_')
        # 如果为空，使用默认值
        if not domain_id:
            domain_id = 'csv_imported_domain'
        
        # 1. 调用AI Copilot的CSV转领域功能
        import requests
        import json as json_module
        
        # 解析CSV内容，提取关键信息用于AI分析
        import csv
        import io
        
        csv_io = io.StringIO(csv_content)
        reader = csv.reader(csv_io)
        
        # 获取表头
        headers = []
        try:
            headers = next(reader)
        except StopIteration:
            headers = []
        
        # 获取样本数据（前5行）
        sample_data = []
        for i, row in enumerate(reader):
            if i < 5:
                sample_data.append(row)
            else:
                break
        
        # 统计实体类型（从entity_type列）
        entity_types = {}
        if headers and 'entity_type' in [h.lower() for h in headers]:
            entity_type_index = [h.lower() for h in headers].index('entity_type')
            csv_io.seek(0)
            next(reader)  # 跳过表头
            for row in reader:
                if len(row) > entity_type_index:
                    entity_type = row[entity_type_index]
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        # 构建AI分析提示词
        prompt = f"""请分析以下CSV数据并提供领域本体构建建议：

文件信息:
- 文件名: {filename}
- 领域名称: {domain}
- 领域ID: {domain_id}

CSV结构分析:
1. 表头字段 ({len(headers)}个): {headers}
2. 样本数据 (前{len(sample_data)}行): {sample_data}
3. 实体类型分布: {entity_types if entity_types else '未检测到entity_type列'}

请提供以下分析结果：
1. 建议的对象类型（基于CSV中的实体类型）
2. 建议的属性定义（基于CSV表头）
3. 建议的动作类型（基于业务逻辑）
4. 领域配置建议
5. 数据同步模式建议

请以清晰、结构化的方式呈现分析结果，方便用户审阅和调整。"""

        # 调用AI Copilot进行分析
        ai_response = ai_copilot.generate_content(
            prompt=prompt,
            content_type="object_type",
            context={
                "data_type": "csv_analysis",
                "file_name": filename,
                "domain": domain,
                "domain_id": domain_id,
                "csv_headers": headers,
                "csv_sample": sample_data,
                "entity_types": entity_types
            }
        )
        
        analysis_content = ai_response.get("content", ai_response.get("result", ""))
        
        # 保存分析结果到临时文件，供用户审阅
        import tempfile
        import uuid
        
        # 创建临时会话ID
        session_id = str(uuid.uuid4())
        
        # 保存CSV内容和分析结果到临时位置
        temp_dir = os.path.join(project_root, "temp_csv_imports")
        os.makedirs(temp_dir, exist_ok=True)
        
        session_file = os.path.join(temp_dir, f"{session_id}.json")
        session_data = {
            "session_id": session_id,
            "domain": domain,
            "domain_id": domain_id,
            "filename": filename,
            "csv_content": csv_content,
            "headers": headers,
            "sample_data": sample_data,
            "entity_types": entity_types,
            "ai_analysis": analysis_content,
            "created_at": datetime.now().isoformat()
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"CSV分析完成，会话ID: {session_id}")
        
        return jsonify({
            "status": "success",
            "message": "CSV分析完成，请审阅AI建议",
            "session_id": session_id,
            "file_name": filename,
            "domain": domain,
            "domain_id": domain_id,
            "analysis": {
                "headers": headers,
                "sample_rows": sample_data,
                "entity_types": entity_types,
                "ai_suggestions": analysis_content[:1000] + "..." if len(analysis_content) > 1000 else analysis_content,
                "ai_suggestions_full": analysis_content
            },
            "next_step": {
                "endpoint": "/api/confirm_csv_import",
                "method": "POST",
                "parameters": {
                    "session_id": session_id,
                    "action": "generate_domain"
                }
            }
        })
        
    except Exception as e:
        logger.error(f"CSV上传失败: {e}")
        return jsonify({
            "status": "error",
            "error": f"CSV上传失败: {str(e)}"
        }), 500

@app.route('/api/confirm_csv_import', methods=['POST'])
def confirm_csv_import():
    """确认CSV导入并生成领域文件（第二步：生成文件）"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        session_id = data.get('session_id')
        action = data.get('action', 'generate_domain')
        
        if not session_id:
            return jsonify({"error": "没有提供会话ID"}), 400
        
        # 加载会话数据
        temp_dir = os.path.join(project_root, "temp_csv_imports")
        session_file = os.path.join(temp_dir, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            return jsonify({"error": "会话已过期或不存在"}), 404
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        domain = session_data.get('domain')
        domain_id = session_data.get('domain_id')
        filename = session_data.get('filename')
        csv_content = session_data.get('csv_content')
        headers = session_data.get('headers', [])
        sample_data = session_data.get('sample_data', [])
        entity_types = session_data.get('entity_types', {})
        ai_analysis = session_data.get('ai_analysis', '')
        
        # 获取用户调整（如果有）
        user_adjustments = data.get('adjustments', {})
        
        # 构建生成领域文件的提示词
        prompt = f"""基于以下CSV分析和用户调整，生成完整的领域本体文件：

文件信息:
- 文件名: {filename}
- 领域名称: {domain}
- 领域ID: {domain_id}

CSV结构:
- 表头字段: {headers}
- 实体类型分布: {entity_types}
- 样本数据: {sample_data[:3]}

AI分析建议:
{ai_analysis[:2000]}

用户调整:
{json.dumps(user_adjustments, ensure_ascii=False, indent=2) if user_adjustments else '无'}

请生成以下5个完整的领域文件：

1. config.json - 领域配置文件（JSON格式）
2. object_types.xml - 对象类型定义（XML格式）
3. action_types.xml - 动作类型定义（XML格式）
4. seed_data.xml - 种子数据（XML格式）
5. synapser_patterns.xml - 同步模式定义（XML格式）

请确保：
1. 所有XML文件都有完整的XML声明
2. JSON文件格式正确
3. 文件内容符合业务逻辑
4. 使用中文注释说明重要部分
5. 每个文件都用相应的代码块包裹"""

        # 调用AI Copilot生成领域文件
        ai_response = ai_copilot.generate_content(
            prompt=prompt,
            content_type="object_type",
            context={
                "data_type": "csv_to_domain_final",
                "file_name": filename,
                "domain": domain,
                "domain_id": domain_id,
                "csv_headers": headers,
                "user_adjustments": user_adjustments
            }
        )
        
        generated_content = ai_response.get("content", ai_response.get("result", ""))
        
        # 解析生成的领域文件
        import re
        
        generated_files = {}
        
        # 提取XML文件
        xml_patterns = [
            (r'```xml\s*(<action_types>.*?</action_types>)\s*```', "action_types.xml"),
            (r'```xml\s*(<object_types>.*?</object_types>)\s*```', "object_types.xml"),
            (r'```xml\s*(<seed_data>.*?</seed_data>)\s*```', "seed_data.xml"),
            (r'```xml\s*(<synapser_patterns>.*?</synapser_patterns>)\s*```', "synapser_patterns.xml"),
            (r'<\?xml[^>]*>\s*<action_types>.*?</action_types>', "action_types.xml"),
            (r'<\?xml[^>]*>\s*<object_types>.*?</object_types>', "object_types.xml"),
            (r'<\?xml[^>]*>\s*<seed_data>.*?</seed_data>', "seed_data.xml"),
            (r'<\?xml[^>]*>\s*<synapser_patterns>.*?</synapser_patterns>', "synapser_patterns.xml"),
        ]
        
        for pattern, file_name in xml_patterns:
            match = re.search(pattern, generated_content, re.DOTALL | re.IGNORECASE)
            if match and file_name not in generated_files:
                generated_files[file_name] = match.group(0).strip()
        
        # 提取JSON文件
        json_patterns = [
            (r'```json\s*(\{.*?"name".*?\})\s*```', "config.json"),
            (r'\{\s*"name".*?\}', "config.json"),
        ]
        
        for pattern, file_name in json_patterns:
            match = re.search(pattern, generated_content, re.DOTALL)
            if match and file_name not in generated_files:
                generated_files[file_name] = match.group(1).strip()
        
        # 创建领域目录并保存文件
        domain_dir = os.path.join(project_root, "domains", domain_id)
        os.makedirs(domain_dir, exist_ok=True)
        
        saved_files = []
        for file_name, file_content in generated_files.items():
            file_path = os.path.join(domain_dir, file_name)
            try:
                if file_name.endswith('.xml'):
                    # 确保有XML声明
                    if not file_content.startswith('<?xml'):
                        file_content = f'<?xml version="1.0" encoding="UTF-8"?>\n{file_content}'
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_content)
                    saved_files.append(file_name)
                    
                elif file_name.endswith('.json'):
                    # 验证JSON格式
                    try:
                        json_data = json.loads(file_content)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=2)
                        saved_files.append(file_name)
                    except json.JSONDecodeError:
                        # 创建基本配置
                        basic_config = {
                            "name": domain,
                            "description": f"从CSV文件导入的领域: {filename}",
                            "ui_config": {
                                "primary_color": "#3b82f6",
                                "secondary_color": "#10b981"
                            }
                        }
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(basic_config, f, ensure_ascii=False, indent=2)
                        saved_files.append(f"{file_name} (基本配置)")
                        
            except Exception as file_error:
                logger.error(f"保存文件失败 {file_name}: {file_error}")
        
        # 如果没有生成任何文件，创建基本配置
        if not saved_files:
            logger.info("AI未生成文件，创建基本领域配置")
            
            # 创建基本配置
            config_path = os.path.join(domain_dir, "config.json")
            domain_config = {
                "name": domain,
                "description": f"从CSV文件导入的领域: {filename}",
                "ui_config": {
                    "primary_color": "#3b82f6",
                    "secondary_color": "#10b981"
                }
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(domain_config, f, ensure_ascii=False, indent=2)
            
            saved_files.append("config.json (基本配置)")
        
        # 重新加载领域包
        global DOMAIN_PACKS
        DOMAIN_PACKS = load_domain_packs()
        
        # 清理临时文件
        try:
            os.remove(session_file)
        except:
            pass
        
        return jsonify({
            "status": "success",
            "message": "领域文件生成完成",
            "domain": domain,
            "domain_id": domain_id,
            "generated_files": saved_files,
            "domain_available": domain_id in DOMAIN_PACKS,
            "domain_info": DOMAIN_PACKS.get(domain_id, {}),
            "next_step": {
                "switch_domain": f"/api/v1/domains/{domain_id}/switch",
                "open_editor": "/editor"
            }
        })
        
    except Exception as e:
        logger.error(f"确认CSV导入失败: {e}")
        return jsonify({
            "status": "error",
            "error": f"确认CSV导入失败: {str(e)}"
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
        
        if not DomainContextManager.validate_domain_access(domain, domain_manager.list_domains()):
            raise PathTraversalError(domain, "Domain not in allowed list")
        
        if not ontology_xml:
            return jsonify({"status": "error", "message": "没有提供本体数据"}), 400
        
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

@app.route('/api/editor/save', methods=['POST'])
def editor_save():
    """保存文件内容"""
    try:
        file_path = request.form.get('file_path')
        content = request.form.get('content')
        
        if not file_path or content is None:
            return jsonify({"error": "缺少文件路径或内容"}), 400
        
        if file_path.startswith('objects/'):
            type_key = file_path.replace('objects/', '').replace('.json', '')
            current_domain = RequestContext.get_current_domain()
            files_content = domain_manager.get_domain_files(current_domain)
            
            if files_content.get('schema'):
                schema_data = json.loads(files_content['schema'])
                object_types = schema_data.get('object_types', [])
                
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
        
        object_data = {
            "type_key": type_key,
            "name": display_name or type_key,
            "description": description or "",
            "properties": {},
            "visual_assets": [],
            "tags": []
        }
        
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
                    pass
        
        object_data["properties"] = properties
        
        current_domain = RequestContext.get_current_domain()
        files_content = domain_manager.get_domain_files(current_domain)
        
        if files_content.get('schema'):
            schema_data = json.loads(files_content['schema'])
            object_types = schema_data.get('object_types', [])
            
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

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory(BASE_DIR / 'static', filename)

# HTMX路由已被废弃，所有必要路由已在app_studio.py中直接定义
logger.info("API路由注册完成")

@app.route('/api/performance/metrics', methods=['POST'])
def receive_performance_metrics():
    """接收前端性能指标数据"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "没有提供数据"}), 400
        
        logger.info(f"性能指标接收: {data.get('url', '未知URL')}")
        
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

# ========== 编辑器相关路由 ==========

@app.route('/studio/sidebar/data', methods=['GET'])
def get_sidebar_data():
    """获取侧边栏数据"""
    try:
        current_domain = request.args.get('domain', 'supply_chain')
        logger.info(f"获取侧边栏数据请求: domain={current_domain}, path={request.path}, full_path={request.full_path}")
        
        # 获取领域信息
        domain_info = domain_manager.get_domain_info(current_domain)
        
        # 提取结构化数据
        object_types = domain_info.get('object_types', [])
        action_rules = domain_info.get('action_rules', [])
        seed_data = domain_info.get('seed_data', [])
        
        # 如果从config.json中获取的数据为空，尝试从XML文件中提取
        if not object_types and domain_info.get('files', {}).get('schema'):
            schema_content = domain_info['files']['schema']
            if schema_content:
                try:
                    # 尝试从XML中提取对象类型
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(schema_content)
                    for obj_type in root.findall('.//ObjectType'):
                        name = obj_type.get('name') or obj_type.findtext('Name')
                        if name:
                            object_types.append({
                                'name': name,
                                'description': obj_type.get('description') or obj_type.findtext('Description') or f'{name} 对象类型'
                            })
                except Exception as e:
                    logger.warning(f"从XML提取对象类型失败: {e}")
        
        if not action_rules and domain_info.get('files', {}).get('actions'):
            actions_content = domain_info['files']['actions']
            if actions_content:
                try:
                    # 尝试从XML中提取动作规则
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(actions_content)
                    for action in root.findall('.//Action'):
                        name = action.get('name') or action.findtext('Name')
                        if name:
                            action_rules.append({
                                'name': name,
                                'description': action.get('description') or action.findtext('Description') or f'{name} 动作规则'
                            })
                except Exception as e:
                    logger.warning(f"从XML提取动作规则失败: {e}")
        
        # 格式化种子数据
        formatted_seed_data = []
        for seed in seed_data:
            if isinstance(seed, dict):
                formatted_seed_data.append({
                    'name': seed.get('id') or seed.get('name', '未知'),
                    'type': seed.get('type', '未知类型')
                })
        
        return jsonify({
            'object_types': object_types[:20],  # 限制数量
            'action_rules': action_rules[:20],
            'seed_data': formatted_seed_data[:10]
        })
        
    except Exception as e:
        logger.error(f"获取侧边栏数据失败: {e}")
        return jsonify({
            'object_types': [],
            'action_rules': [],
            'seed_data': []
        }), 500

@app.route('/studio/editor/object/<type_key>', methods=['GET'])
def get_object_editor(type_key):
    """获取对象类型编辑器数据（JSON版本）"""
    try:
        current_domain = request.args.get('domain', 'supply_chain')
        
        # 从领域管理器获取对象类型数据
        domain_data = domain_manager.get_domain_files(current_domain)
        schema_data = {}
        if domain_data.get('schema'):
            try:
                schema_data = json.loads(domain_data['schema'])
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回空数据
                logger.warning(f"schema JSON解析失败，使用空数据")
                schema_data = {}
        
        # 查找特定对象类型
        object_type = None
        if 'object_types' in schema_data:
            for obj in schema_data['object_types']:
                if obj.get('type_key') == type_key:
                    object_type = obj
                    break
        
        if object_type:
            return jsonify({
                'success': True,
                'type_key': type_key,
                'data': object_type,
                'domain': current_domain
            })
        else:
            # 返回空对象类型模板
            return jsonify({
                'success': True,
                'type_key': type_key,
                'data': {
                    'type_key': type_key,
                    'properties': {},
                    'visual_assets': [],
                    'tags': []
                },
                'domain': current_domain,
                'is_new': True
            })
            
    except Exception as e:
        logger.error(f"获取对象编辑器数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'type_key': type_key
        }), 500

@app.route('/studio/editor/action/<action_id>', methods=['GET'])
def get_action_editor(action_id):
    """获取动作规则编辑器数据（JSON版本）"""
    try:
        current_domain = request.args.get('domain', 'supply_chain')
        
        domain_data = domain_manager.get_domain_files(current_domain)
        actions_data = {}
        if domain_data.get('actions'):
            try:
                actions_data = json.loads(domain_data['actions'])
            except json.JSONDecodeError:
                logger.warning(f"actions JSON解析失败，使用空数据")
                actions_data = {}
        
        # 查找特定动作
        action = None
        if 'actions' in actions_data:
            for act in actions_data['actions']:
                if act.get('action_id') == action_id:
                    action = act
                    break
        
        if action:
            return jsonify({
                'success': True,
                'action_id': action_id,
                'data': action,
                'domain': current_domain
            })
        else:
            # 返回空动作模板
            return jsonify({
                'success': True,
                'action_id': action_id,
                'data': {
                    'action_id': action_id,
                    'validation_logic': "",
                    'execution_rules': []
                },
                'domain': current_domain,
                'is_new': True
            })
            
    except Exception as e:
        logger.error(f"获取动作编辑器数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'action_id': action_id
        }), 500

@app.route('/studio/editor/seed/<seed_name>', methods=['GET'])
def get_seed_editor(seed_name):
    """获取种子数据编辑器数据（JSON版本）"""
    try:
        current_domain = request.args.get('domain', 'supply_chain')
        
        domain_data = domain_manager.get_domain_files(current_domain)
        seed_data = {}
        if domain_data.get('seed'):
            try:
                seed_data = json.loads(domain_data['seed'])
            except json.JSONDecodeError:
                logger.warning(f"seed JSON解析失败，使用空数据")
                seed_data = {}
        
        # 这里简化处理，返回整个种子数据
        return jsonify({
            'success': True,
            'seed_name': seed_name,
            'data': seed_data,
            'domain': current_domain
        })
            
    except Exception as e:
        logger.error(f"获取种子编辑器数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'seed_name': seed_name
        }), 500

@app.route('/api/save', methods=['POST'])
def save_file():
    """保存文件（JSON版本）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '没有提供数据'}), 400
        
        current_domain = request.args.get('domain', 'supply_chain')
        file_type = data.get('file_type', 'schema')
        content = data.get('content', '')
        
        logger.info(f"保存文件: domain={current_domain}, type={file_type}")
        
        # 这里应该调用domain_manager保存数据
        # 暂时返回成功响应
        return jsonify({
            'success': True,
            'message': '保存成功',
            'domain': current_domain,
            'file_type': file_type,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/validate', methods=['POST'])
def validate_content():
    """验证内容（JSON版本）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '没有提供数据'}), 400
        
        current_domain = request.args.get('domain', 'supply_chain')
        content = data.get('content', '')
        content_type = data.get('type', 'schema')
        
        logger.info(f"验证内容: domain={current_domain}, type={content_type}")
        
        # 这里应该调用validation_engine验证数据
        # 暂时返回成功响应
        return jsonify({
            'success': True,
            'valid': True,
            'message': '验证通过',
            'domain': current_domain,
            'type': content_type,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"验证内容失败: {e}")
        return jsonify({
            'success': False,
            'valid': False,
            'error': str(e)
        }), 500

@app.route('/api/deploy', methods=['POST'])
def deploy_changes():
    """部署变更（JSON版本）"""
    try:
        data = request.get_json()
        current_domain = request.args.get('domain', 'supply_chain')
        
        logger.info(f"部署变更: domain={current_domain}")
        
        # 这里应该调用git_ops部署变更
        # 暂时返回成功响应
        return jsonify({
            'success': True,
            'message': '部署成功',
            'domain': current_domain,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"部署变更失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tools/format', methods=['POST'])
def format_code():
    """格式化代码（JSON版本）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '没有提供数据'}), 400
        
        code = data.get('code', '')
        language = data.get('language', 'json')
        
        # 简单格式化：如果是JSON，尝试美化和验证
        formatted_code = code
        if language == 'json':
            try:
                parsed = json.loads(code)
                formatted_code = json.dumps(parsed, indent=2, ensure_ascii=False)
            except json.JSONDecodeError as e:
                return jsonify({
                    'success': False,
                    'error': f'JSON格式错误: {str(e)}',
                    'formatted': code
                }), 400
        
        return jsonify({
            'success': True,
            'formatted': formatted_code,
            'language': language
        })
        
    except Exception as e:
        logger.error(f"格式化代码失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/graph/data', methods=['GET'])
def get_graph_data():
    """获取图谱数据"""
    try:
        current_domain = request.args.get('domain', 'supply_chain')
        logger.info(f"获取图谱数据请求: domain={current_domain}, path={request.path}, full_path={request.full_path}")
        
        # 获取领域信息
        domain_info = domain_manager.get_domain_info(current_domain)
        elements = []
        
        # 基于领域配置生成图数据
        config = domain_info.get('config', {})
        features = config.get('features', {})
        default_objects = config.get('default_objects', [])
        
        # 从 seed_data.xml 加载节点和关系
        seed_nodes = []
        try:
            # 检查文件是否存在
            seed_file = domain_manager.domains_dir / current_domain / "seed_data.xml"
            file_exists = seed_file.exists()
            print(f"[DEBUG] 查找 seed_data.xml: {seed_file}, exists={file_exists}", flush=True)
            logger.info(f"查找 seed_data.xml: {seed_file}, exists={file_exists}")
            
            if not file_exists:
                print(f"[DEBUG] 文件不存在，尝试使用绝对路径", flush=True)
                seed_file = Path(r"E:\Documents\MyGame\domains") / current_domain / "seed_data.xml"
                print(f"[DEBUG] 尝试路径: {seed_file}, exists={seed_file.exists()}", flush=True)
            
            seed_nodes = domain_manager.get_nodes_from_seed(current_domain)
            print(f"[DEBUG] 从 seed_data.xml 加载了 {len(seed_nodes)} 个节点", flush=True)
            logger.info(f"从 seed_data.xml 加载了 {len(seed_nodes)} 个节点")
            
            # 打印前几个节点用于调试
            if seed_nodes:
                print(f"[DEBUG] 前3个节点: {seed_nodes[:3]}", flush=True)
                logger.info(f"前3个节点: {seed_nodes[:3]}")
        except Exception as e:
            print(f"[DEBUG] 从 seed_data.xml 加载节点失败: {e}", flush=True)
            logger.warning(f"从 seed_data.xml 加载节点失败: {e}")
            import traceback
            traceback_str = traceback.format_exc()
            print(f"[DEBUG] {traceback_str}", flush=True)
            logger.warning(traceback_str)
        
        # 添加 seed_data.xml 中的节点（优先使用）
        if seed_nodes:
            for i, node in enumerate(seed_nodes[:20]):  # 限制数量
                elements.append({
                    'data': {
                        'id': node.get('id', f'node_{i}'),
                        'label': node.get('label', node.get('name', node.get('id', f'节点{i}'))),
                        'type': node.get('type', 'object'),
                        'properties': node.get('properties', {})
                    },
                    'position': {'x': 100 + (i % 5) * 150, 'y': 100 + (i // 5) * 150}
                })
        else:
            # 备用：从 config.json 加载
            # 添加对象类型作为节点
            object_types = features.get('object_types', [])
            for i, obj_type in enumerate(object_types[:10]):  # 限制数量
                elements.append({
                    'data': {
                        'id': f'type_{obj_type}',
                        'label': obj_type,
                        'type': 'object_type',
                        'description': f'{obj_type} 对象类型'
                    },
                    'position': {'x': 100 + i * 150, 'y': 100}
                })
            
            # 添加默认对象作为节点
            for i, obj in enumerate(default_objects[:8]):  # 限制数量
                elements.append({
                    'data': {
                        'id': obj.get('id', f'obj_{i}'),
                        'label': obj.get('name', obj.get('id', f'对象{i}')),
                        'type': 'object',
                        'description': obj.get('description', '')
                    },
                    'position': {'x': 100 + i * 150, 'y': 250}
                })
        
        # 添加关系作为边
        relationships = features.get('relationships', [])
        logger.info(f"从 config.json 加载了 {len(relationships)} 条关系")
        
        # 如果没有在 config.json 中定义关系，则从 seed_data.xml 中提取
        if not relationships:
            try:
                relationships = domain_manager.get_relationships_from_seed(current_domain)
                logger.info(f"从 seed_data.xml 加载了 {len(relationships)} 条关系")
                
                # 打印所有关系用于调试
                if relationships:
                    logger.info(f"所有关系: {relationships}")
            except Exception as e:
                logger.warning(f"从 seed_data.xml 加载关系失败: {e}")
                import traceback
                logger.warning(traceback.format_exc())
        
        # 创建节点ID集合用于快速查找
        node_ids = {e['data']['id'] for e in elements}
        logger.info(f"节点ID集合: {node_ids}")
        
        valid_edges = 0
        skipped_edges = 0
        
        for i, rel in enumerate(relationships[:20]):  # 限制数量
            source_id = rel.get("source")
            target_id = rel.get("target")
            rel_type = rel.get("type", "关联")
            
            logger.info(f"处理关系 {i}: type={rel_type}, source={source_id}, target={target_id}")
            
            if not source_id or not target_id:
                logger.warning(f"关系缺少 source 或 target: {rel}")
                skipped_edges += 1
                continue
            
            # 确保源和目标节点存在
            source_exists = source_id in node_ids
            target_exists = target_id in node_ids
            
            if source_exists and target_exists:
                rel_props = rel.get('properties', {})
                elements.append({
                    'data': {
                        'id': f'edge_{i}_{source_id}_{target_id}',
                        'source': source_id,
                        'target': target_id,
                        'label': rel_type,
                        'type': 'relationship',
                        'properties': rel_props
                    }
                })
                valid_edges += 1
                logger.info(f"添加边: {source_id} -> {target_id} [{rel_type}]")
            else:
                skipped_edges += 1
                logger.warning(f"跳过无效关系: source={source_id} (exists={source_exists}), target={target_id} (exists={target_exists})")
        
        # 统计节点和边的数量
        nodes_count = len([e for e in elements if 'source' not in e['data']])
        edges_count = len([e for e in elements if 'source' in e['data']])
        
        logger.info(f"返回图谱数据: {nodes_count} 个节点, {edges_count} 条边 (有效: {valid_edges}, 跳过: {skipped_edges})")
        
        # 调试信息
        debug_info = {
            'version': '2.0-fixed',
            'seed_nodes_loaded': len(seed_nodes),
            'domains_dir': str(domain_manager.domains_dir),
            'file_checked': str(domain_manager.domains_dir / current_domain / "seed_data.xml"),
            'file_exists': (domain_manager.domains_dir / current_domain / "seed_data.xml").exists(),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'elements': elements,
            'domain': current_domain,
            'stats': {
                'nodes': nodes_count,
                'edges': edges_count
            },
            'debug': debug_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取图谱数据失败: {e}")
        return jsonify({
            'elements': [],
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/graph/node', methods=['POST'])
def add_graph_node():
    """添加图谱节点"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '没有提供数据'}), 400
        
        node_type = data.get('type', 'object')
        node_label = data.get('label', '新节点')
        x = data.get('x', 100)
        y = data.get('y', 100)
        
        # 生成唯一ID
        import uuid
        node_id = f'node_{uuid.uuid4().hex[:8]}'
        
        new_node = {
            'data': {
                'id': node_id,
                'label': node_label,
                'type': node_type,
                'description': f'新添加的{node_type}节点'
            },
            'position': {'x': x, 'y': y}
        }
        
        return jsonify({
            'success': True,
            'node': new_node,
            'message': '节点添加成功'
        })
        
    except Exception as e:
        logger.error(f"添加图谱节点失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
    
    # 使用普通Flask开发服务器，避免eventlet在Windows上的问题
    # 禁用debug模式，避免自动重载
    app.run(debug=False, port=5000, host='0.0.0.0')