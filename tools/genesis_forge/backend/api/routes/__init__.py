"""
路由模块包
统一管理所有API路由
"""

# 路由注册函数
def register_domain_routes(app, domain_manager, DOMAIN_PACKS):
    """注册领域管理路由"""
    from .domain_routes import register_domain_routes as _register
    return _register(app, domain_manager, DOMAIN_PACKS)

def register_ontology_routes(app, domain_manager, validation_engine):
    """注册本体管理路由"""
    from .ontology_routes import register_ontology_routes as _register
    return _register(app, domain_manager, validation_engine)

def register_world_routes(app, domain_manager):
    """注册世界仿真路由"""
    from .world_routes import register_world_routes as _register
    return _register(app, domain_manager)

def register_copilot_routes(app, ai_copilot, domain_manager):
    """注册AI Copilot路由"""
    from .copilot_routes import register_copilot_routes as _register
    return _register(app, ai_copilot, domain_manager)

def register_rule_routes(app, rule_engine, validation_engine):
    """注册规则引擎路由"""
    from .rule_routes import register_rule_routes as _register
    return _register(app, rule_engine, validation_engine)

def register_git_routes(app, git_ops, domain_manager):
    """注册Git操作路由"""
    from .git_routes import register_git_routes as _register
    return _register(app, git_ops, domain_manager)

def register_editor_routes(app, domain_manager):
    """注册编辑器路由"""
    from .editor_routes import register_editor_routes as _register
    return _register(app, domain_manager)

def register_htmx_routes(app, domain_manager, validation_engine, ai_copilot, git_ops, rule_engine):
    """注册HTMX路由"""
    from .htmx_routes import register_htmx_routes as _register
    return _register(app, domain_manager, validation_engine, ai_copilot, git_ops, rule_engine)

def register_page_routes(app, domain_manager, DOMAIN_PACKS):
    """注册页面路由"""
    from .page_routes import register_page_routes as _register
    return _register(app, domain_manager, DOMAIN_PACKS)

def register_all_routes(app, domain_manager, validation_engine, ai_copilot, git_ops, rule_engine, DOMAIN_PACKS):
    """注册所有路由"""
    # 注册页面路由
    app = register_page_routes(app, domain_manager, DOMAIN_PACKS)
    
    # 注册API路由
    app = register_domain_routes(app, domain_manager, DOMAIN_PACKS)
    app = register_ontology_routes(app, domain_manager, validation_engine)
    app = register_world_routes(app, domain_manager)
    app = register_copilot_routes(app, ai_copilot, domain_manager)
    app = register_rule_routes(app, rule_engine, validation_engine)
    app = register_git_routes(app, git_ops, domain_manager)
    app = register_editor_routes(app, domain_manager)
    app = register_htmx_routes(app, domain_manager, validation_engine, ai_copilot, git_ops, rule_engine)
    
    return app

__all__ = [
    'register_domain_routes',
    'register_ontology_routes',
    'register_world_routes',
    'register_copilot_routes',
    'register_rule_routes',
    'register_git_routes',
    'register_editor_routes',
    'register_htmx_routes',
    'register_page_routes',
    'register_all_routes'
]