"""
MVP v0.3 全局推演演示
展示 NPC 自主移动、视野外战斗、传闻系统
"""
import os
import sys
import io
from typing import Optional
from dotenv import load_dotenv
from colorama import Fore, Style, init

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 初始化 colorama
init(autoreset=True)

from graph_client import GraphClient
from llm_engine import LLMEngine


def print_banner():
    """打印游戏启动横幅"""
    banner = f"""
{Fore.CYAN}=====================================================
     {Fore.YELLOW}Project Genesis v0.3 - 全局推演版{Fore.CYAN}
     {Fore.WHITE}世界自己运转，故事自然涌现{Fore.CYAN}
====================================================={Style.RESET_ALL}
    """
    print(banner)


def demo():
    """v0.3 全局推演演示"""
    print_banner()
    
    # 1. 加载环境变量
    load_dotenv()
    
    # 2. 初始化服务
    try:
        db = GraphClient(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "mysecretpassword")
        )
        llm = LLMEngine()
        print(Fore.GREEN + ">>> 系统初始化完成。全局推演引擎已启动。\n")
    except Exception as e:
        print(Fore.RED + f"初始化失败: {e}")
        return 1
    
    # 3. 世界构建阶段
    scenario = "战国时代，七雄争霸，我是史官记录历史"
    print(Fore.CYAN + f"使用演示场景: {scenario}")
    print(Fore.YELLOW + "\n>>> AI 正在编织现实 (生成阵营与NPC)...")
    
    try:
        world_json = llm.generate_world_schema(scenario)
        db.clear_world()
        db.create_world(world_json)
        
        # 验证玩家位置
        test_status = db.get_player_status()
        if not test_status:
            with db.driver.session() as session:
                session.run("""
                    MATCH (p:Player), (l:Location)
                    WHERE NOT (p)-[:LOCATED_AT]->()
                    WITH p, l LIMIT 1
                    CREATE (p)-[:LOCATED_AT]->(l)
                """)
        
        print(Fore.GREEN + f">>> 世界已实例化：{len(world_json.get('nodes', []))} 实体，{len(world_json.get('edges', []))} 关系\n")
    except Exception as e:
        print(Fore.RED + f"世界生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 4. 显示初始状态
    print(Fore.CYAN + "=== 初始世界状态 ===")
    status = db.get_player_status()
    if status:
        print(f"位置: {status['location'].get('name')}")
        faction = status.get('player_faction', {})
        if faction:
            print(f"阵营: {faction.get('name')}")
        print(f"出口: {[e.get('name') for e in status['exits']]}")
        print(f"可见: {[e.get('name') for e in status['entities']]}")
        print(f"HP: {status['player'].get('hp', 100)}")
    
    # 5. 演示：玩家多次行动，观察世界变化
    print(Fore.CYAN + "\n=== 演示：玩家行动与世界推演 ===")
    print(Fore.WHITE + "(展示 v0.3 核心特性：即使你不动，世界也在变化)\n")
    
    actions = ["查看四周", "等待", "等待", "去集市", "等待"]
    
    for i, action_input in enumerate(actions, 1):
        print(f"\n{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"{Fore.WHITE}第 {i} 回合: {action_input}")
        print(f"{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # 获取当前状态
        status = db.get_player_status()
        if not status:
            print(Fore.RED + "无法获取游戏状态")
            break
        
        # 显示当前位置
        print(f"\n{Fore.CYAN}当前位置: {status['location'].get('name')}")
        print(f"可见: {[e.get('name') for e in status['entities']]}")
        
        # 解析意图（简化处理）
        if action_input == "查看四周":
            print(Fore.CYAN + "你环顾四周，观察周围的动静...")
        elif action_input.startswith("去"):
            target = action_input.replace("去", "").strip()
            success, msg = db.execute_move(target)
            print(Fore.YELLOW + f"系统: {msg}")
        elif action_input == "等待":
            print(Fore.WHITE + "⏳ 你选择静观其变...")
        
        # ★ v0.3 核心：全局推演
        print(Fore.BLACK + Style.BRIGHT + "\n>>> ⏳ 世界时间正在流逝...")
        
        # 玩家身边的即时事件
        player_id = status['player']['id']
        hostile_events = db.run_smart_simulation(player_id)
        for event in hostile_events:
            print(Fore.RED + f">>> ⚔️ {event['name']} 攻击了你！造成 {event['damage']} 点伤害！")
            db.update_player_hp(-event['damage'])
        
        # ★ 全局推演（NPC移动 + 视野外战斗）
        global_events = db.run_global_tick()
        
        # 显示传闻
        if global_events:
            print(Fore.WHITE + "\n📰 【江湖传闻】")
            for news in global_events:
                print(Fore.WHITE + f"  • {news}")
        else:
            print(Fore.WHITE + "\n📰 【江湖传闻】")
            print(Fore.WHITE + "  • 今天没什么大事发生...")
        
        # 显示更新后的状态
        status = db.get_player_status()
        if status:
            print(f"\n{Fore.CYAN}位置: {status['location'].get('name')}")
            print(f"可见: {[e.get('name') for e in status['entities']]}")
            print(f"HP: {status['player'].get('hp', 100)}")
    
    # 6. 演示结束
    print(Fore.YELLOW + "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(Fore.GREEN + "演示完成！")
    print(Fore.WHITE + "\nv0.3 核心特性展示：")
    print("  • NPC 自主移动（30%概率随机游走）")
    print("  • 视野外战斗（NPC在玩家不在场时互殴）")
    print("  • 传闻系统（远处事件以传闻形式传播）")
    print("  • 涌现叙事（世界自我运转产生故事）")
    
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(demo())
