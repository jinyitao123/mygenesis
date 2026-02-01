"""调试数据库状态"""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# 连接数据库
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "mysecretpassword")
)

with driver.session() as session:
    # 1. 检查所有节点
    print("=== 所有节点 ===")
    result = session.run("MATCH (n) RETURN n.id as id, n.name as name, labels(n) as labels")
    for record in result:
        print(f"  {record['labels']}: {record['id']} - {record['name']}")
    
    # 2. 检查所有关系
    print("\n=== 所有关系 ===")
    result = session.run("""
        MATCH (a)-[r]->(b) 
        RETURN a.name as from, type(r) as rel, b.name as to
    """)
    for record in result:
        print(f"  {record['from']} --[{record['rel']}]--> {record['to']}")
    
    # 3. 检查玩家状态
    print("\n=== 玩家状态查询 ===")
    result = session.run("""
        MATCH (p:Player)-[:LOCATED_AT]->(loc:Location)
        RETURN p.name as player, loc.name as location
    """)
    found = False
    for record in result:
        print(f"  玩家: {record['player']} 在 {record['location']}")
        found = True
    
    if not found:
        print("  未找到玩家的 LOCATED_AT 关系！")
        
        # 检查是否有 Player 节点
        print("\n=== 检查 Player 节点 ===")
        result = session.run("MATCH (p:Player) RETURN p.id as id, p.name as name")
        for record in result:
            print(f"  Player: {record['id']} - {record['name']}")
        
        # 检查是否有 Location 节点
        print("\n=== 检查 Location 节点 ===")
        result = session.run("MATCH (l:Location) RETURN l.id as id, l.name as name")
        for record in result:
            print(f"  Location: {record['id']} - {record['name']}")

driver.close()
