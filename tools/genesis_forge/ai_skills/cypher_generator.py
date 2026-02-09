"""
Cypher生成器工具链 - 提供安全的Cypher查询生成、验证和修复功能
"""

import re
from typing import Dict, List, Any, Optional, Tuple
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.core.cypher_validator import CypherValidator, CypherQueryBuilder, CypherInjectionError


class CypherGenerator:
    """Cypher生成器 - 带安全验证"""
    
    @staticmethod
    def generate_query(intent: str, context: Dict[str, Any]) -> str:
        """
        根据意图生成Cypher查询
        
        Args:
            intent: 用户意图描述
            context: 上下文信息（包含领域、schema等）
            
        Returns:
            安全的Cypher查询字符串
            
        Raises:
            CypherInjectionError: 如果生成的查询不安全
        """
        intent_lower = intent.lower()
        
        # 构建上下文元数据用于验证
        validation_context = {
            'intent': intent,
            'domain': context.get('domain', 'unknown')
        }
        
        # 匹配查询意图
        if "查找" in intent or "查询" in intent or "find" in intent_lower:
            query = CypherGenerator._generate_find_query(intent, context)
        elif "创建" in intent or "新建" in intent or "create" in intent_lower:
            query = CypherGenerator._generate_create_query(intent, context)
        elif "更新" in intent or "修改" in intent or "update" in intent_lower:
            query = CypherGenerator._generate_update_query(intent, context)
        elif "删除" in intent or "remove" in intent_lower:
            query = CypherGenerator._generate_delete_query(intent, context)
        elif "统计" in intent or "count" in intent_lower:
            query = CypherGenerator._generate_count_query(intent, context)
        else:
            query = CypherGenerator._generate_general_query(intent, context)
        
        # 验证生成的查询是否安全
        CypherValidator.validate_ai_generated_query(query, validation_context)
        
        return query
    
    @staticmethod
    def _generate_find_query(intent: str, context: Dict[str, Any]) -> str:
        """生成查找查询"""
        domain = context.get('domain', 'unknown')
        
        # 尝试从意图中提取实体类型
        entity_type = CypherGenerator._extract_entity_type(intent)
        
        if entity_type:
            builder = CypherQueryBuilder()
            builder.match(f"(n:Entity {{type: $type, domain: $domain}})", type=entity_type, domain=domain)
            builder.return_('n')
            builder.limit(100)
            builder.validate()
            query, params = builder.build()
            return query
        else:
            # 默认查询
            builder = CypherQueryBuilder()
            builder.match(f"(n:Entity {{domain: $domain}})", domain=domain)
            builder.return_('n')
            builder.limit(100)
            builder.validate()
            query, params = builder.build()
            return query
    
    @staticmethod
    def _generate_create_query(intent: str, context: Dict[str, Any]) -> str:
        """生成创建查询（受限）"""
        domain = context.get('domain', 'unknown')
        entity_type = CypherGenerator._extract_entity_type(intent) or "Entity"
        
        builder = CypherQueryBuilder()
        builder.match(f"(n:Entity {{type: $type, domain: $domain}})", type=entity_type, domain=domain)
        builder.return_('n')
        builder.limit(1)
        builder.validate()
        query, params = builder.build()
        
        # 注意：实际创建操作应该通过受控的API，而不是直接由AI生成
        # 这里只返回一个查找查询
        return query
    
    @staticmethod
    def _generate_update_query(intent: str, context: Dict[str, Any]) -> str:
        """生成更新查询（受限）"""
        domain = context.get('domain', 'unknown')
        entity_type = CypherGenerator._extract_entity_type(intent) or "Entity"
        
        builder = CypherQueryBuilder()
        builder.match(f"(n:Entity {{type: $type, domain: $domain}})", type=entity_type, domain=domain)
        builder.return_('n')
        builder.limit(1)
        builder.validate()
        query, params = builder.build()
        
        # 注意：实际更新操作应该通过受控的API，而不是直接由AI生成
        # 这里只返回一个查找查询
        return query
    
    @staticmethod
    def _generate_delete_query(intent: str, context: Dict[str, Any]) -> str:
        """
        生成删除查询（高度受限）
        
        重要：为了安全考虑，我们不直接返回删除查询
        而是返回一个查找查询，让用户确认后再执行
        """
        domain = context.get('domain', 'unknown')
        entity_type = CypherGenerator._extract_entity_type(intent) or "Entity"
        
        builder = CypherQueryBuilder()
        builder.match(f"(n:Entity {{type: $type, domain: $domain}})", type=entity_type, domain=domain)
        builder.return_('n')
        builder.limit(100)
        builder.validate()
        query, params = builder.build()
        
        # 不直接返回删除查询
        return query
    
    @staticmethod
    def _generate_count_query(intent: str, context: Dict[str, Any]) -> str:
        """生成统计查询"""
        domain = context.get('domain', 'unknown')
        entity_type = CypherGenerator._extract_entity_type(intent)
        
        builder = CypherQueryBuilder()
        if entity_type:
            builder.match(f"(n:Entity {{type: $type, domain: $domain}})", type=entity_type, domain=domain)
        else:
            builder.match(f"(n:Entity {{domain: $domain}})", domain=domain)
        builder.return_('count(n) as count')
        builder.validate()
        query, params = builder.build()
        return query
    
    @staticmethod
    def _generate_general_query(intent: str, context: Dict[str, Any]) -> str:
        """生成通用查询"""
        domain = context.get('domain', 'unknown')
        
        builder = CypherQueryBuilder()
        builder.match(f"(n:Entity {{domain: $domain}})", domain=domain)
        builder.return_('n')
        builder.limit(100)
        builder.validate()
        query, params = builder.build()
        return query
    
    @staticmethod
    def _extract_entity_type(intent: str) -> Optional[str]:
        """
        从意图中提取实体类型
        
        这是一个简单的启发式方法，实际应用中可以使用NLP
        """
        # 常见的中文实体类型映射
        entity_mapping = {
            "卡车": "Truck",
            "仓库": "Warehouse",
            "货物": "Cargo",
            "账户": "Account",
            "交易": "Transaction",
            "服务器": "Server",
            "节点": "Node",
            "实体": "Entity"
        }
        
        for zh, en in entity_mapping.items():
            if zh in intent:
                return en
        
        # 尝试提取大写单词
        words = re.findall(r'[A-Z][a-zA-Z0-9_]+', intent)
        if words:
            return words[0]
        
        return None


class CypherQueryExecutor:
    """安全的 Cypher 查询执行器"""
    
    def __init__(self, neo4j_connector):
        """
        初始化执行器
        
        Args:
            neo4j_connector: Neo4j 连接器实例
        """
        self.neo4j = neo4j_connector
    
    def execute_safe_query(self, query: str, params: dict = None, allow_modifications: bool = False) -> List[Dict]:
        """
        执行安全的查询
        
        Args:
            query: Cypher 查询字符串
            params: 查询参数字典
            allow_modifications: 是否允许修改操作
            
        Returns:
            查询结果列表
            
        Raises:
            CypherInjectionError: 如果查询不安全
            Neo4jError: 如果查询执行失败
        """
        # 验证查询
        is_safe, error_msg = CypherValidator.validate_query(query, allow_modifications)
        
        if not is_safe:
            raise CypherInjectionError(
                query=query[:200] + "..." if len(query) > 200 else query,
                reason=error_msg
            )
        
        # 执行查询
        try:
            if params:
                result = self.neo4j.run_query(query, params)
            else:
                result = self.neo4j.run_query(query)
            
            return [dict(record) for record in result]
        except Exception as e:
            from backend.core.exceptions import Neo4jError
            raise Neo4jError(f"查询执行失败: {str(e)}", query=query[:200])
