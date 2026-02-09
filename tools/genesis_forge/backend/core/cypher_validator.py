"""
Cypher 查询安全验证器 - 防止 Cypher 注入攻击
"""
import re
from typing import List, Tuple, Optional
from core.exceptions import CypherInjectionError


class CypherValidator:
    """Cypher 查询安全验证器"""
    
    # 危险关键字黑名单
    DANGEROUS_KEYWORDS = [
        'DETACH DELETE',
        'DELETE',
        'DROP DATABASE',
        'DROP INDEX',
        'DROP CONSTRAINT',
        'CALL dbms',
        'FOREACH',
        'LOAD CSV',
        'CALL apoc',
    ]
    
    # 允许的 Cypher 关键字白名单（基础查询）
    ALLOWED_KEYWORDS = [
        'MATCH',
        'WHERE',
        'RETURN',
        'LIMIT',
        'SKIP',
        'ORDER BY',
        'WITH',
        'OPTIONAL MATCH',
        'AND',
        'OR',
        'NOT',
        'IN',
        'AS',
        'DISTINCT',
        'MERGE',
        'CREATE',
        'SET',
        'UNWIND',
        'UNION',
        'UNION ALL',
    ]
    
    @staticmethod
    def validate_query(query: str, allow_modifications: bool = False) -> Tuple[bool, Optional[str]]:
        """
        验证 Cypher 查询是否安全
        
        Args:
            query: Cypher 查询字符串
            allow_modifications: 是否允许修改操作（CREATE, SET, MERGE, DELETE）
            
        Returns:
            (是否安全, 错误消息) 元组
        """
        if not query or not query.strip():
            return False, "查询为空"
        
        # 转换为大写进行关键字检测
        query_upper = query.upper()
        
        # 检查危险关键字
        for keyword in CypherValidator.DANGEROUS_KEYWORDS:
            if keyword in query_upper:
                if not allow_modifications or keyword not in ['CREATE', 'SET', 'MERGE']:
                    return False, f"检测到危险关键字: {keyword}"
        
        # 检查 DETACH DELETE（即使允许修改操作也不允许）
        if 'DETACH DELETE' in query_upper:
            return False, "不允许使用 DETACH DELETE"
        
        # 检查未授权的存储过程调用
        if re.search(r'CALL\s+(dbms|apoc|meta|spatial)', query_upper):
            return False, "不允许调用系统存储过程"
        
        # 检查 LOAD CSV（可能用于文件读取）
        if 'LOAD CSV' in query_upper:
            return False, "不允许使用 LOAD CSV"
        
        # 检查参数化查询模式 - 确保使用 $ 参数
        # 如果查询包含字符串字面量但可能来自用户输入
        if CypherValidator._has_unsafe_string_literals(query):
            return False, "检测到潜在的不安全字符串字面量"
        
        # 检查查询长度限制
        if len(query) > 10000:
            return False, "查询过长"
        
        return True, None
    
    @staticmethod
    def _has_unsafe_string_literals(query: str) -> bool:
        """
        检查查询中是否有不安全的字符串字面量
        这不是完美的检测，但可以捕获一些常见问题
        """
        # 检测单引号字符串
        single_quote_strings = re.findall(r"'[^']*'", query)
        # 检测双引号字符串
        double_quote_strings = re.findall(r'"[^"]*"', query)
        
        # 如果查询中有多个字符串字面量，可能需要警惕
        total_strings = len(single_quote_strings) + len(double_quote_strings)
        
        # 允许一些常见的字符串字面量（如标签名、属性名）
        # 如果超过阈值，则可能存在注入风险
        if total_strings > 5:
            return True
        
        return False
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        清理查询 - 移除注释和多余空格
        注意：这不是安全功能，只是帮助规范化查询
        """
        # 移除单行注释
        query = re.sub(r'//.*$', '', query, flags=re.MULTILINE)
        # 移除多行注释
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        # 规范化空格
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    @staticmethod
    def validate_ai_generated_query(query: str, context: dict) -> bool:
        """
        验证 AI 生成的查询
        对 AI 生成的查询进行更严格的验证
        
        Args:
            query: AI 生成的 Cypher 查询
            context: 上下文信息（包含用户的原始意图等）
            
        Returns:
            是否安全
            
        Raises:
            CypherInjectionError: 如果检测到注入风险
        """
        is_safe, error_msg = CypherValidator.validate_query(query, allow_modifications=False)
        
        if not is_safe:
            raise CypherInjectionError(
                query=query[:200] + "..." if len(query) > 200 else query,
                reason=f"AI 生成的查询不安全: {error_msg}"
            )
        
        # 检查查询是否与用户的意图匹配
        # 这是一个简单的启发式检查
        if context.get('intent'):
            intent = context['intent'].lower()
            query_lower = query.lower()
            
            # 如果用户要求查找，但查询包含删除操作
            if '查找' in intent or '查询' in intent or 'find' in intent:
                if 'delete' in query_lower or 'remove' in query_lower:
                    raise CypherInjectionError(
                        query=query[:200] + "..." if len(query) > 200 else query,
                        reason="用户意图是查询，但生成了删除操作"
                    )
        
        return True
    
    @staticmethod
    def extract_used_labels(query: str) -> List[str]:
        """
        提取查询中使用的标签
        """
        # 匹配模式如 (n:Label) 或 (n:Label1:Label2)
        pattern = r'\([a-zA-Z0-9_]+:([a-zA-Z0-9_:]+)\)'
        matches = re.findall(pattern, query)
        
        labels = []
        for match in matches:
            # 处理多个标签的情况
            for label in match.split(':'):
                if label:
                    labels.append(label)
        
        return list(set(labels))
    
    @staticmethod
    def extract_used_relationships(query: str) -> List[str]:
        """
        提取查询中使用的关系类型
        """
        # 匹配模式如 -[r:REL_TYPE]- 或 -[:REL_TYPE]-
        pattern = r'\[.*?:([a-zA-Z0-9_]+)\]'
        matches = re.findall(pattern, query)
        
        return list(set(matches))


class CypherQueryBuilder:
    """安全的 Cypher 查询构建器 - 帮助防止注入"""
    
    def __init__(self):
        self.query_parts = []
        self.params = {}
    
    def match(self, pattern: str, **kwargs) -> 'CypherQueryBuilder':
        """添加 MATCH 子句"""
        self.query_parts.append(f"MATCH {pattern}")
        self.params.update(kwargs)
        return self
    
    def optional_match(self, pattern: str, **kwargs) -> 'CypherQueryBuilder':
        """添加 OPTIONAL MATCH 子句"""
        self.query_parts.append(f"OPTIONAL MATCH {pattern}")
        self.params.update(kwargs)
        return self
    
    def where(self, condition: str, **kwargs) -> 'CypherQueryBuilder':
        """添加 WHERE 子句"""
        self.query_parts.append(f"WHERE {condition}")
        self.params.update(kwargs)
        return self
    
    def return_(self, clause: str) -> 'CypherQueryBuilder':
        """添加 RETURN 子句"""
        self.query_parts.append(f"RETURN {clause}")
        return self
    
    def limit(self, limit: int) -> 'CypherQueryBuilder':
        """添加 LIMIT 子句"""
        self.query_parts.append(f"LIMIT {limit}")
        return self
    
    def order_by(self, clause: str) -> 'CypherQueryBuilder':
        """添加 ORDER BY 子句"""
        self.query_parts.append(f"ORDER BY {clause}")
        return self
    
    def build(self) -> Tuple[str, dict]:
        """
        构建查询并返回查询字符串和参数字典
        
        Returns:
            (query, params) 元组
        """
        query = " ".join(self.query_parts)
        return query, self.params
    
    def validate(self) -> bool:
        """
        验证构建的查询是否安全
        
        Returns:
            是否安全
            
        Raises:
            CypherInjectionError: 如果查询不安全
        """
        query, _ = self.build()
        is_safe, error_msg = CypherValidator.validate_query(query, allow_modifications=False)
        
        if not is_safe:
            raise CypherInjectionError(
                query=query[:200] + "..." if len(query) > 200 else query,
                reason=error_msg
            )
        
        return True
