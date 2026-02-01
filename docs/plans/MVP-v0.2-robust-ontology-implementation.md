### 🚀 MVP v0.2 代码落地 (Copy & Paste Ready)

为了让你能最快速度跑起来，我将你计划中的三个核心文件进行了完整的代码整合。你可以直接覆盖原文件。

#### 1. `src/llm_engine.py` (升级版大脑)

更新重点：

1. 生成 Prompt 增加了 `Faction` 和 `HOSTILE_TO` 的强制要求。
2. 解析 Prompt 增加了 `TALK`, `INSPECT`, `WAIT` 的支持。

Python

```
import json
import os
from openai import OpenAI

class LLMEngine:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_world_schema(self, user_prompt):
        """生成世界初始数据的 JSON (v0.2 强壮本体版)"""
        system_prompt = """
        你是一个图数据库生成器。生成符合以下本体的游戏世界 JSON。

        # Ontology Rules
        1. 节点类型 (Labels):
           - Player: {id, name, hp=100, faction='PlayerFaction'}
           - Location: {id, name, description}
           - NPC: {id, name, hp, damage, faction, dialogue, disposition}
           - Faction: {id, name, description}
        
        2. 关系类型 (Types):
           - LOCATED_AT: (Entity) -> (Location)
           - CONNECTED_TO: (Location) -> (Location)
           - BELONGS_TO: (Player/NPC) -> (Faction)
           - HOSTILE_TO: (Faction) -> (Faction)

        3. 生成要求:
           - 必须生成 2-3 个 Faction 节点 (例如: 官府, 叛军, 平民)。
           - 每个 NPC 必须 BELONGS_TO 一个 Faction。
           - 必须生成至少一组 HOSTILE_TO 关系 (定义谁恨谁)。
           - NPC 必须有 dialogue (中文对话) 和 disposition (aggressive/neutral/friendly)。
           - 确保地图 (Location) 是连通的。

        4. 输出格式:
           纯 JSON，包含 "nodes" 和 "edges" 列表。不要使用 Markdown 代码块。
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o", # 建议使用 4o 以保证 JSON 结构稳定
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"创建一个这样的世界: {user_prompt}"}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def interpret_action(self, player_input, status):
        """
        语义层：解析用户意图 (v0.2 多意图支持版)
        """
        # 简化 status 以减少 token 消耗
        simple_status = {
            "location": status.get("location", {}).get("name"),
            "exits": [e.get("name") for e in status.get("exits", [])],
            "entities": [e.get("name") for e in status.get("entities", [])],
            "player_faction": status.get("player_faction", {}).get("name")
        }

        system_prompt = f"""
        当前状态: {json.dumps(simple_status, ensure_ascii=False)}
        用户输入: "{player_input}"
        
        任务：解析意图并返回 JSON。
        Intent 类型:
        - MOVE: 移动 (target 必须是当前 exits 中的名称)
        - TALK: 对话 (target 必须是 entities 中的 NPC 名称)
        - INSPECT: 观察 (target 可以是 location, NPC 或 item)
        - ATTACK: 攻击 (target 是 entities 中的敌人名称)
        - WAIT: 等待/跳过
        - UNKNOWN: 无法理解
        
        规则:
        1. narrative 应该是流畅的 RPG 风格中文描述。
        2. 如果意图是 UNKNOWN，narrative 说明为什么不理解。
        
        JSON 格式: {{"intent": "...", "target": "...", "narrative": "..."}}
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
```

#### 2. `src/graph_client.py` (智能图客户端)

更新重点：

1. 实现了 `run_smart_simulation`，这是本次升级的核心。
2. `get_player_status` 现在会拉取阵营信息。
3. 新增 `get_npc_dialogue`。

Python

```
from neo4j import GraphDatabase
import logging

class GraphClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def clear_world(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def create_world(self, world_json):
        with self.driver.session() as session:
            # 1. 创建节点
            for node in world_json.get("nodes", []):
                # 默认值处理
                props = node.get('properties', {})
                if node['label'] == 'Player' and 'hp' not in props: props['hp'] = 100
                if node['label'] == 'NPC' and 'damage' not in props: props['damage'] = 5
                
                query = f"CREATE (n:{node['label']}) SET n = $props, n.id = $id"
                session.run(query, id=node['id'], props=props)
            
            # 2. 创建关系
            for edge in world_json.get("edges", []):
                query = f"""
                MATCH (a), (b) 
                WHERE a.id = $src AND b.id = $tgt
                CREATE (a)-[r:{edge['type']}]->(b)
                SET r = $props
                """
                session.run(query, src=edge['source'], tgt=edge['target'], 
                            type=edge['type'], props=edge.get("properties", {}))

    def get_player_status(self):
        """获取玩家状态（v0.2 包含 Faction）"""
        with self.driver.session() as session:
            query = """
            MATCH (p:Player)-[:LOCATED_AT]->(loc:Location)
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(pf:Faction)
            OPTIONAL MATCH (loc)-[:CONNECTED_TO]-(exits:Location)
            OPTIONAL MATCH (entity)-[:LOCATED_AT]->(loc)
            WHERE entity.id <> p.id
            RETURN 
                p AS player,
                loc AS location,
                pf AS player_faction,
                collect(DISTINCT exits) AS exits,
                collect(DISTINCT entity) AS entities
            """
            result = session.run(query).single()
            if not result: return None
            
            return {
                "player": dict(result["player"]),
                "location": dict(result["location"]),
                "player_faction": dict(result["player_faction"]) if result["player_faction"] else None,
                "exits": [dict(n) for n in result["exits"]],
                "entities": [dict(n) for n in result["entities"]]
            }

    def get_npc_dialogue(self, npc_name):
        """获取 NPC 对话数据"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:NPC {name: $name})
                RETURN n.dialogue as dialogue, n.disposition as disposition
            """, name=npc_name).single()
            return dict(result) if result else None

    def execute_move(self, target_name):
        with self.driver.session() as session:
            check = """
            MATCH (p:Player)-[:LOCATED_AT]->(cur), (cur)-[:CONNECTED_TO]-(tgt:Location {name: $name})
            RETURN tgt
            """
            if not session.run(check, name=target_name).single():
                return False, "去不了那里，路不通。"
            
            move = """
            MATCH (p:Player)-[r:LOCATED_AT]->()
            MATCH (tgt:Location {name: $name})
            DELETE r
            CREATE (p)-[:LOCATED_AT]->(tgt)
            """
            session.run(move, name=target_name)
            return True, f"移动到了 {target_name}"

    def update_player_hp(self, delta):
        with self.driver.session() as session:
            # 这里的 id 假设只有一个 Player，生产环境应用 $pid
            session.run("MATCH (p:Player) SET p.hp = p.hp + $delta", delta=delta)

    def run_smart_simulation(self, player_id):
        """
        ★ v0.2 核心：基于图谱关系的智能推演
        """
        with self.driver.session() as session:
            query = """
            MATCH (p:Player {id: $pid})
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(pf:Faction)
            
            // 找到同房间的活着的 NPC
            MATCH (p)-[:LOCATED_AT]->(loc)<-[:LOCATED_AT]-(n:NPC)
            WHERE n.hp > 0
            
            // 查找 NPC 的阵营及其敌对关系
            OPTIONAL MATCH (n)-[:BELONGS_TO]->(nf:Faction)
            OPTIONAL MATCH (nf)-[hostile:HOSTILE_TO]->(pf)
            
            // 判定攻击条件：有敌对关系 OR NPC个性就是好战
            WITH n, hostile
            WHERE hostile IS NOT NULL OR n.disposition = 'aggressive'
            
            RETURN n.name as name, n.damage as damage, n.disposition as disposition
            """
            results = session.run(query, pid=player_id)
            return [dict(record) for record in results]
```

#### 3. `src/main.py` (游戏主循环)

更新重点：

1. UI 增加阵营显示。
2. 处理 `TALK`, `INSPECT`, `WAIT` 意图。
3. 使用 `run_smart_simulation` 替代旧逻辑。

Python

```
import os
import sys
import io
from typing import Optional
from dotenv import load_dotenv
from colorama import Fore, Style, init

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

init(autoreset=True)

from graph_client import GraphClient
from llm_engine import LLMEngine

def print_banner():
    print(f"""
{Fore.CYAN}=====================================================
     {Fore.YELLOW}Project Genesis v0.2 - 强壮本体版{Fore.CYAN}
     {Fore.WHITE}Ontology is Gold, Code is Cheap.{Fore.CYAN}
====================================================={Style.RESET_ALL}
    """)

def display_status(status: dict) -> None:
    if not status: return
    
    player = status.get("player", {})
    location = status.get("location", {})
    faction = status.get("player_faction", {})
    exits = status.get("exits", [])
    entities = status.get("entities", [])
    
    print("\n" + "=" * 50)
    print(f"📍 位置: {Fore.BLUE}{location.get('name')}{Style.RESET_ALL}")
    
    # 新增：显示阵营
    if faction:
        print(f"🏛️  阵营: {Fore.CYAN}{faction.get('name')}{Style.RESET_ALL}")
    else:
        print(f"🏛️  阵营: {Fore.WHITE}无党派浪人{Style.RESET_ALL}")
        
    print(f"📝 描述: {location.get('description')}")
    
    exit_names = [e.get('name') for e in exits] if exits else ["无"]
    print(f"🚪 出口: {Fore.GREEN}{', '.join(exit_names)}{Style.RESET_ALL}")
    
    entity_names = [e.get('name') for e in entities] if entities else ["空无一物"]
    print(f"👁  可见: {Fore.YELLOW}{', '.join(entity_names)}{Style.RESET_ALL}")
    
    hp = player.get('hp', 100)
    color = Fore.GREEN if hp > 50 else Fore.RED
    print(f"❤️  状态: HP {color}{hp}{Style.RESET_ALL}")
    print("=" * 50)

def simulation_step(db: GraphClient, status: dict) -> None:
    """智能推演步骤"""
    player_id = status['player']['id']
    
    # ★ 使用图逻辑查询，而非简单的 Python if-else
    events = db.run_smart_simulation(player_id)
    
    for event in events:
        name = event['name']
        damage = event.get('damage', 5)
        disposition = event.get('disposition')
        
        if disposition == 'aggressive':
            print(Fore.RED + f">>> ⚔️ {name} (天生好战) 向你扑来！造成 {damage} 点伤害！")
        else:
            print(Fore.RED + f">>> ⚔️ {name} 发现了敌对阵营的你，发起攻击！造成 {damage} 点伤害！")
            
        db.update_player_hp(-damage)

def main():
    print_banner()
    load_dotenv()
    
    try:
        db = GraphClient(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "mysecretpassword") # 确保这里密码正确
        )
        llm = LLMEngine()
    except Exception as e:
        print(Fore.RED + f"初始化失败: {e}")
        return

    # 世界构建
    print(Fore.CYAN + "请描述你想体验的世界 (例如: 战国时代，我是史官春秋):")
    scenario = input(Fore.YELLOW + "> ").strip() or "战国时代"
    
    print(Fore.YELLOW + ">>> AI 正在编织本体 (Ontology)...")
    try:
        world_json = llm.generate_world_schema(scenario)
        db.clear_world()
        db.create_world(world_json)
        print(Fore.GREEN + f">>> 世界已实例化。")
    except Exception as e:
        print(Fore.RED + f"生成失败: {e}")
        return

    # 游戏循环
    while True:
        status = db.get_player_status()
        if not status or status['player'].get('hp', 0) <= 0:
            print(Fore.RED + "\n💔 你倒下了。游戏结束。")
            break
            
        display_status(status)
        
        user_input = input(Fore.WHITE + "你要做什么? > ").strip()
        if user_input.lower() in ["quit", "exit"]: break
        if not user_input: continue
        
        # 1. 解析
        try:
            action = llm.interpret_action(user_input, status)
            print(Fore.MAGENTA + f"AI 旁白: {action.get('narrative')}")
            
            intent = action.get("intent")
            target = action.get("target")
        except:
            print(Fore.RED + "AI 大脑短路了，请重试。")
            continue

        # 2. 执行动作
        if intent == "MOVE":
            success, msg = db.execute_move(target)
            print(Fore.YELLOW + f"系统: {msg}")
            
        elif intent == "TALK":
            # ★ 新增交互
            npc_data = db.get_npc_dialogue(target)
            if npc_data:
                disposition = npc_data.get('disposition')
                color = Fore.GREEN if disposition == 'friendly' else Fore.RED if disposition == 'aggressive' else Fore.CYAN
                print(color + f"💬 [{target}]: {npc_data.get('dialogue')}")
            else:
                print(Fore.YELLOW + "系统: 这里的空气很安静。")
                
        elif intent == "INSPECT":
            print(Fore.WHITE + f"🔍 你仔细观察了 {target}，但似乎没有什么特别的发现。(Feature WIP)")
            
        elif intent == "WAIT":
            print(Fore.WHITE + "⏳ 你静观其变...")
            
        elif intent == "UNKNOWN":
            print(Fore.YELLOW + "系统: 无法理解该指令。")

        # 3. 推演
        simulation_step(db, status)

    db.close()

if __name__ == "__main__":
    main()
```

