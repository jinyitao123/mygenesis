"""
ERP 后端入口 - FastAPI 应用

基于 Genesis Kernel 的元数据驱动 ERP 系统
所有业务逻辑定义在 XML 本体中，Python 代码只负责协调
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

# 确保能导入 genesis 包
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from genesis.kernel.connectors.neo4j_connector import Neo4jConnector
from genesis.kernel.connectors.postgres_connector import PostgresConnector
from genesis.kernel.object_manager import ObjectManager
from genesis.kernel.action_driver import ActionDriver
from genesis.kernel.rule_engine import RuleEngine
from genesis.ontology.loader import OntologyLoader
from applications.game.bootstrapper import GameBootstrapper

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- 初始化 Kernel ---
def init_kernel(domain_name="supply_chain_erp"):
    """初始化 Genesis Kernel 组件"""
    logger.info(f"初始化 ERP Kernel，使用域: {domain_name}")
    
    # 0. 使用引导程序部署域
    try:
        logger.info("启动引导程序部署活动域...")
        bootstrapper = GameBootstrapper(project_root=str(Path(__file__).parent.parent.parent))
        
        # 临时设置活动域为 ERP 域
        import os
        os.environ['ACTIVE_DOMAIN'] = domain_name
        
        if not bootstrapper.deploy_active_domain():
            logger.error("引导程序部署失败")
            raise RuntimeError("域部署失败")
        
        logger.info("引导程序部署完成")
    except Exception as e:
        logger.warning(f"引导程序执行异常，尝试继续: {e}")
    
    # 1. 连接数据库
    neo4j_conn = Neo4jConnector(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "mysecretpassword")
    )
    
    # PostgreSQL 连接
    postgres_url = (
        f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'kimyitao')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'smartcleankb')}"
    )
    pg_conn = PostgresConnector(connection_url=postgres_url)

    # 2. 加载 Ontology（使用 XML 格式）
    project_root = Path(__file__).parent.parent.parent
    ontology_dir = project_root / "ontology"
    
    # 确保 ontology 目录存在
    ontology_dir.mkdir(exist_ok=True)
    
    loader = OntologyLoader(str(ontology_dir))
    load_results = loader.load_all(use_xml=True)
    
    if not all(load_results.values()):
        failed = [k for k, v in load_results.items() if not v]
        logger.error(f"Ontology 文件加载失败: {failed}")
        raise RuntimeError(f"Failed to load ontology files: {failed}")
    
    logger.info(f"Ontology 加载完成: {len(loader.get_object_types())} 对象类型, "
                f"{len(loader.get_action_types())} 动作类型")

    # 3. 初始化组件
    obj_mgr = ObjectManager(
        {
            'object_types': loader.get_object_types(),
            'link_types': loader.get_link_types()
        },
        neo4j_conn
    )
    
    rule_engine = RuleEngine(neo4j_conn, pg_conn)
    action_driver = ActionDriver(neo4j_conn, rule_engine, obj_mgr)
    
    # 加载动作定义
    actions_list = [
        {"id": k, **v}
        for k, v in loader.get_action_types().items()
    ]
    action_driver.load_actions(actions_list)
    
    # 4. 初始化种子数据（如果数据库为空）
    try:
        seed_data = loader.get_seed_data()
        seed_nodes = seed_data.get('seed_nodes', [])
        seed_links = seed_data.get('seed_links', [])
        
        logger.info(f"检查种子数据: {len(seed_nodes)} 节点, {len(seed_links)} 关系")
        
        # 创建节点
        for node in seed_nodes:
            node_type = node.get('type')
            node_id = node.get('id')
            properties = node.get('properties', {})
            properties['id'] = node_id
            
            # 检查是否已存在
            existing = obj_mgr.get_object(node_type, node_id)
            if not existing:
                obj_mgr.create_object(node_type, properties)
                logger.debug(f"创建节点: {node_type}.{node_id}")
        
        # 创建关系
        for link in seed_links:
            try:
                obj_mgr.create_link(
                    link['type'],
                    link['source'],
                    link['target']
                )
                logger.debug(f"创建关系: {link['type']} {link['source']} -> {link['target']}")
            except Exception as e:
                logger.warning(f"创建关系失败 {link}: {e}")
                
    except Exception as e:
        logger.error(f"种子数据初始化失败: {e}")
    
    return obj_mgr, action_driver

# 全局单例
try:
    obj_mgr, action_driver = init_kernel()
    logger.info("ERP Kernel 初始化成功")
except Exception as e:
    logger.error(f"ERP Kernel 初始化失败: {e}")
    obj_mgr, action_driver = None, None

# FastAPI 应用
app = FastAPI(title="Genesis ERP", version="1.0.0")

# 静态文件和模板
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 模拟当前登录用户（实际应从 Session/Token 获取）
CURRENT_USER_ID = "mgr_01"

# --- API 路由 ---
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """ERP 仪表盘"""
    if not obj_mgr:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "系统初始化失败，请检查数据库连接"
        })
    
    try:
        # 查询所有采购订单
        orders_result = obj_mgr.neo4j.run_query(
            "MATCH (o:PurchaseOrder) RETURN o ORDER BY o.id"
        )
        orders = [record['o'] for record in orders_result]
        
        # 查询员工信息
        employees_result = obj_mgr.neo4j.run_query(
            "MATCH (e:Employee) RETURN e"
        )
        employees = {record['e']['id']: record['e'] for record in employees_result}
        
        # 获取当前用户
        current_user = employees.get(CURRENT_USER_ID, {"id": CURRENT_USER_ID, "name": "未知用户"})
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "orders": orders,
            "employees": employees,
            "current_user": current_user
        })
        
    except Exception as e:
        logger.error(f"仪表盘查询失败: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"数据查询失败: {str(e)}"
        })

@app.post("/api/action/submit")
async def submit_order(request: Request):
    """执行提交动作"""
    if not action_driver:
        return JSONResponse({"success": False, "message": "系统未初始化"})
    
    try:
        data = await request.json()
        order_id = data.get("order_id")
        
        if not order_id:
            return JSONResponse({"success": False, "message": "缺少订单ID"})
        
        # 执行动作
        result = action_driver.execute("ACT_SUBMIT_ORDER", {
            "order_id": order_id
        })
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"提交订单失败: {e}")
        return JSONResponse({"success": False, "message": f"操作失败: {str(e)}"})

@app.post("/api/action/approve")
async def approve_order(request: Request):
    """执行审批动作"""
    if not action_driver:
        return JSONResponse({"success": False, "message": "系统未初始化"})
    
    try:
        data = await request.json()
        order_id = data.get("order_id")
        
        if not order_id:
            return JSONResponse({"success": False, "message": "缺少订单ID"})
        
        # 执行动作
        result = action_driver.execute("ACT_APPROVE_ORDER", {
            "order_id": order_id,
            "manager_id": CURRENT_USER_ID
        })
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"审批订单失败: {e}")
        return JSONResponse({"success": False, "message": f"操作失败: {str(e)}"})

@app.post("/api/action/reject")
async def reject_order(request: Request):
    """执行驳回动作"""
    if not action_driver:
        return JSONResponse({"success": False, "message": "系统未初始化"})
    
    try:
        data = await request.json()
        order_id = data.get("order_id")
        
        if not order_id:
            return JSONResponse({"success": False, "message": "缺少订单ID"})
        
        # 执行动作
        result = action_driver.execute("ACT_REJECT_ORDER", {
            "order_id": order_id,
            "manager_id": CURRENT_USER_ID
        })
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"驳回订单失败: {e}")
        return JSONResponse({"success": False, "message": f"操作失败: {str(e)}"})

@app.get("/api/orders")
async def get_orders():
    """获取订单列表 API"""
    if not obj_mgr:
        return JSONResponse({"success": False, "message": "系统未初始化"})
    
    try:
        orders_result = obj_mgr.neo4j.run_query(
            "MATCH (o:PurchaseOrder) RETURN o ORDER BY o.id"
        )
        orders = [record['o'] for record in orders_result]
        
        return JSONResponse({"success": True, "data": orders})
        
    except Exception as e:
        logger.error(f"获取订单列表失败: {e}")
        return JSONResponse({"success": False, "message": f"查询失败: {str(e)}"})

@app.get("/health")
async def health_check():
    """健康检查"""
    if obj_mgr and action_driver:
        try:
            # 简单查询测试数据库连接
            obj_mgr.neo4j.run_query("RETURN 1")
            return {"status": "healthy", "components": ["neo4j", "action_driver"]}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    else:
        return {"status": "unhealthy", "error": "Kernel not initialized"}

# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "服务器内部错误"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "applications.erp.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )