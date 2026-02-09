#!/usr/bin/env python3
"""
简化版图数据库初始化
"""

import sys
sys.path.append('.')
sys.path.append('./backend')

from backend.services.neo4j_service import Neo4jService

def init_graph_data():
    """初始化图数据库数据"""
    
    # 创建Neo4j服务实例
    neo4j = Neo4jService()
    
    print("连接Neo4j数据库...")
    
    # 测试连接
    try:
        result = neo4j.query("RETURN 1 as test")
        print("Neo4j连接成功")
    except Exception as e:
        print(f"Neo4j连接失败: {e}")
        return
    
    # 清空现有数据
    print("清空现有数据...")
    try:
        neo4j.query("MATCH (n) DETACH DELETE n")
        print("数据清空完成")
    except Exception as e:
        print(f"清空数据失败: {e}")
    
    # 创建供应链数据
    print("创建供应链数据...")
    
    # 创建节点
    nodes = [
        # 卡车
        ("truck_001", "TRUCK", {"label": "运输卡车A", "location": "仓库A", "status": "空闲", "capacity": 10}),
        ("truck_002", "TRUCK", {"label": "运输卡车B", "location": "仓库B", "status": "运输中", "capacity": 15}),
        
        # 仓库
        ("warehouse_001", "WAREHOUSE", {"label": "中央仓库", "location": "工业区", "capacity": 1000}),
        ("warehouse_002", "WAREHOUSE", {"label": "分拨中心", "location": "物流园", "capacity": 500}),
        
        # 包裹
        ("package_001", "PACKAGE", {"label": "电子产品包裹", "location": "仓库A", "weight": 5}),
        ("package_002", "PACKAGE", {"label": "服装包裹", "location": "仓库B", "weight": 3}),
        
        # 订单
        ("order_001", "ORDER", {"label": "电子产品订单", "customer": "客户A", "total_amount": 5000}),
        ("order_002", "ORDER", {"label": "服装订单", "customer": "客户B", "total_amount": 1200}),
        
        # 供应商
        ("supplier_001", "SUPPLIER", {"label": "电子元件供应商", "name": "华强电子", "location": "深圳"}),
        ("supplier_002", "SUPPLIER", {"label": "服装供应商", "name": "纺织集团", "location": "杭州"}),
    ]
    
    for node_id, node_type, properties in nodes:
        try:
            query = f"""
            CREATE (n:{node_type} {{id: $id}})
            SET n += $props
            RETURN n.id as id
            """
            neo4j.query(query, {"id": node_id, "props": properties})
            print(f"创建节点: {node_id} - {node_type}")
        except Exception as e:
            print(f"创建节点失败 {node_id}: {e}")
    
    # 创建关系
    relationships = [
        ("truck_001", "warehouse_001", "LOCATED_AT", {"since": "2026-02-01"}),
        ("truck_002", "warehouse_002", "LOCATED_AT", {"since": "2026-02-05"}),
        ("package_001", "warehouse_001", "CONTAINS", {}),
        ("package_002", "warehouse_002", "CONTAINS", {}),
        ("order_001", "package_001", "CONTAINS", {}),
        ("order_002", "package_002", "CONTAINS", {}),
        ("supplier_001", "order_001", "SUPPLIES", {"product_type": "电子产品"}),
        ("supplier_002", "order_002", "SUPPLIES", {"product_type": "服装"}),
        ("truck_002", "package_002", "TRANSPORTS", {"start_time": "2026-02-09 08:00"}),
    ]
    
    for source_id, target_id, rel_type, properties in relationships:
        try:
            query = f"""
            MATCH (a {{id: $source_id}})
            MATCH (b {{id: $target_id}})
            CREATE (a)-[r:{rel_type}]->(b)
            SET r += $props
            RETURN type(r) as rel_type
            """
            neo4j.query(query, {"source_id": source_id, "target_id": target_id, "props": properties})
            print(f"创建关系: {source_id} -[{rel_type}]-> {target_id}")
        except Exception as e:
            print(f"创建关系失败 {source_id}->{target_id}: {e}")
    
    # 获取统计信息
    print("\n获取图数据库统计...")
    try:
        stats_query = """
        MATCH (n)
        RETURN count(n) as node_count,
               labels(n)[0] as node_type
        ORDER BY node_type
        """
        node_stats = neo4j.query(stats_query)
        
        rel_query = """
        MATCH ()-[r]->()
        RETURN count(r) as link_count,
               type(r) as rel_type
        ORDER BY rel_type
        """
        rel_stats = neo4j.query(rel_query)
        
        print("节点统计:")
        for stat in node_stats:
            print(f"  {stat['node_type']}: {stat['node_count']} 个")
        
        print("\n关系统计:")
        for stat in rel_stats:
            print(f"  {stat['rel_type']}: {stat['link_count']} 个")
            
    except Exception as e:
        print(f"获取统计失败: {e}")
    
    print("\n图数据库初始化完成！")

if __name__ == "__main__":
    init_graph_data()