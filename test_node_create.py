"""测试节点创建"""
import os
from dotenv import load_dotenv
from src.graph_client import GraphClient

load_dotenv()

db = GraphClient(
    "bolt://localhost:7687",
    "neo4j",
    "mysecretpassword"
)

# 清除测试数据
with db.driver.session() as session:
    session.run("MATCH (n:test_node) DETACH DELETE n")

# 测试创建节点
test_node = {
    "id": "test_001",
    "label": "test_node",
    "name": "测试节点",
    "hp": 100,
    "description": "这是一个测试"
}

print("创建节点:")
print(f"  输入: {test_node}")

with db.driver.session() as session:
    # 使用修复后的逻辑
    node_id = test_node.get("id")
    label = test_node.get("label", "Entity")
    
    if "properties" in test_node:
        properties = test_node["properties"]
    else:
        properties = {k: v for k, v in test_node.items() if k not in ["id", "label"]}
    
    print(f"  提取的属性: {properties}")
    
    query = f"CREATE (n:{label} {{id: $id}}) SET n += $props"
    print(f"  查询: {query}")
    print(f"  参数: id={node_id}, props={properties}")
    
    session.run(query, id=node_id, props=properties)
    print("  创建完成")

# 验证
print("\n验证创建的节点:")
with db.driver.session() as session:
    result = session.run("MATCH (n:test_node) RETURN n.id, n.name, n.hp, n.description")
    for record in result:
        print(f"  id={record['n.id']}, name={record['n.name']}, hp={record['n.hp']}, desc={record['n.description']}")

db.close()
print("\n测试完成!")
