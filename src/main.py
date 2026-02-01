# src/main.py
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
                                                      
     {Fore.YELLOW}Project Genesis - 生成式仿真平台{Fore.CYAN}                  
                                                      
     {Fore.WHITE}语义驱动的无限游戏引擎 v0.1.0 MVP{Fore.CYAN}               
                                                      
====================================================={Style.RESET_ALL}
    """
    print(banner)


def get_player_input() -> str:
    """获取玩家输入"""
    try:
        return input(Fore.WHITE + "你要做什么? > " + Style.RESET_ALL).strip()
    except (EOFError, KeyboardInterrupt):
        return "quit"


def display_status(status: dict) -> None:
    """显示玩家状态和周围环境"""
    if not status:
        print(Fore.RED + "错误：无法获取游戏状态")
        return
    
    player = status.get("player", {})
    location = status.get("location", {})
    faction = status.get("player_faction", {})
    exits = status.get("exits", [])
    entities = status.get("entities", [])
    
    print("\n" + "=" * 50)
    print(f"📍 位置: {Fore.BLUE}{location.get('name', '未知')}{Style.RESET_ALL}")
    
    # 新增：显示阵营
    if faction:
        print(f"🏛️  阵营: {Fore.CYAN}{faction.get('name')}{Style.RESET_ALL}")
    else:
        print(f"🏛️  阵营: {Fore.WHITE}无党派浪人{Style.RESET_ALL}")
        
    print(f"📝 描述: {location.get('description', '无')}")
    
    if exits:
        exit_names = [e.get('name', '?') for e in exits]
        print(f"🚪 出口: {Fore.GREEN}{', '.join(exit_names)}{Style.RESET_ALL}")
    else:
        print(f"🚪 出口: {Fore.RED}无{Style.RESET_ALL}")
    
    if entities:
        entity_names = [e.get('name', '?') for e in entities]
        print(f"👁  可见: {Fore.YELLOW}{', '.join(entity_names)}{Style.RESET_ALL}")
    else:
        print(f"👁  可见: {Fore.WHITE}空无一物{Style.RESET_ALL}")
    
    hp = player.get('hp', 100)
    hp_color = Fore.GREEN if hp > 50 else Fore.YELLOW if hp > 25 else Fore.RED
    print(f"❤️  状态: HP {hp_color}{hp}{Style.RESET_ALL}")
    print("=" * 50)


def check_game_over(status: dict) -> tuple[bool, Optional[str]]:
    """检查游戏是否结束"""
    if not status:
        return True, "游戏状态异常"
    
    player = status.get("player", {})
    hp = player.get('hp', 100)  # 默认 HP 100，不是 0
    
    if hp <= 0:
        return True, "你倒下了...游戏结束。"
    
    return False, None


def simulation_step(db: GraphClient, status: dict) -> None:
    """智能推演步骤 (v0.3 - 全局推演)"""
    player_id = status['player']['id']
    
    # 1. 处理玩家身边的即时危机 (v0.2 原有逻辑)
    hostile_events = db.run_smart_simulation(player_id)
    
    for event in hostile_events:
        name = event['name']
        damage = event.get('damage', 5)
        disposition = event.get('disposition')
        
        if disposition == 'aggressive':
            print(Fore.RED + f">>> ⚔️ {name} (天生好战) 向你扑来！造成 {damage} 点伤害！")
        else:
            print(Fore.RED + f">>> ⚔️ {name} 发现了敌对阵营的你，发起攻击！造成 {damage} 点伤害！")
            
        db.update_player_hp(-damage)
    
    # 2. ★ v0.3 新增：处理全世界的演变 (全局推演)
    print(Fore.BLACK + Style.BRIGHT + ">>> ⏳ 世界时间正在流逝...")
    global_events = db.run_global_tick()
    
    # 3. ★ v0.3 新增：消息系统 (江湖传闻)
    if global_events:
        print(Fore.WHITE + "\n📰 【江湖传闻】")
        for news in global_events[:5]:  # 最多显示5条，避免刷屏
            print(Fore.WHITE + f"  • {news}")
        print("")


def main():
    """游戏主入口"""
    print_banner()
    
    # 1. 加载环境变量
    load_dotenv()
    
    # 2. 初始化服务
    try:
        db = GraphClient(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "password")
        )
        llm = LLMEngine()
        print(Fore.GREEN + ">>> 系统初始化完成。神经元网络已连接。\n")
    except Exception as e:
        print(Fore.RED + f"初始化失败: {e}")
        print(Fore.YELLOW + "请检查：1) Neo4j 是否运行 2) API 密钥是否正确")
        return 1
    
    # 3. 世界构建阶段
    print(Fore.CYAN + "请描述你想体验的世界：")
    print(Fore.WHITE + "示例：发生在维多利亚时代豪宅的谋杀案，我是侦探")
    scenario = input(Fore.YELLOW + "> " + Style.RESET_ALL).strip()
    
    if not scenario:
        scenario = "一个神秘的地下迷宫"
    
    print(Fore.YELLOW + "\n>>> AI 正在编织现实 (图谱建模)...")
    try:
        world_json = llm.generate_world_schema(scenario)
        db.clear_world()
        db.create_world(world_json)
        print(Fore.GREEN + f">>> 世界已实例化：{len(world_json.get('nodes', []))} 实体，{len(world_json.get('edges', []))} 关系")
        
        # 验证玩家是否有位置，如果没有则设置默认位置
        test_status = db.get_player_status()
        if not test_status:
            print(Fore.YELLOW + ">>> 初始化玩家位置...")
            # 找到第一个地点并放置玩家
            with db.driver.session() as session:
                session.run("""
                    MATCH (p:Player), (l:Location)
                    WHERE NOT (p)-[:LOCATED_AT]->()
                    WITH p, l
                    LIMIT 1
                    CREATE (p)-[:LOCATED_AT]->(l)
                """)
        
        print()
    except Exception as e:
        print(Fore.RED + f"世界生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 4. 游戏主循环
    print(Fore.CYAN + "输入 'help' 查看帮助，'quit' 退出游戏\n")
    
    while True:
        # A. 获取上下文
        status = db.get_player_status()
        
        # B. 检查游戏结束
        is_over, game_over_msg = check_game_over(status)
        if is_over:
            print(Fore.RED + f"\n{game_over_msg}")
            break
        
        # C. 显示状态
        display_status(status)
        
        # D. 获取用户输入
        user_input = get_player_input()
        
        if user_input.lower() in ["quit", "exit", "退出"]:
            print(Fore.YELLOW + "\n感谢游玩，再见！")
            break
        
        if user_input.lower() in ["help", "帮助", "?"]:
            print(Fore.CYAN + """
可用指令：
- 移动: "去书房" / "移动到厨房"
- 对话: "对话卫兵" / "询问老板"
- 观察: "查看" / "环顾四周" / "检查尸体"
- 战斗: "攻击僵尸" / "打敌人"
- 等待: "等待" / "静观其变"
- 其他: "help" 显示帮助，"quit" 退出
            """)
            continue
        
        if not user_input:
            continue
        
        # E. 语义解析
        try:
            action = llm.interpret_action(user_input, status)
            print(Fore.MAGENTA + f"AI 旁白: {action.get('narrative', '')}")
        except Exception as e:
            print(Fore.RED + f"指令解析失败: {e}")
            continue
        
        # F. 执行动作
        intent = action.get("intent", "UNKNOWN")
        target = action.get("target", "")
        
        if intent == "MOVE":
            success, msg = db.execute_move(target)
            print(Fore.YELLOW + f"系统: {msg}")
        
        elif intent == "TALK":
            # ★ 生成式对话系统 (RAG-based)
            npc_data = db.get_npc_details(target)
            if npc_data:
                print(Fore.BLACK + Style.BRIGHT + f">>> 🤖 AI正在生成{target}的回复...")
                
                # 使用 LLM 实时生成对话（基于人设）
                player_data = status.get('player', {})
                reply = llm.generate_npc_response(user_input, npc_data, player_data)
                
                # 根据性情显示不同颜色
                disposition = npc_data.get('disposition', 'neutral')
                if disposition == 'friendly':
                    print(Fore.GREEN + f"💬 [{target}] 热情地说: {reply}")
                elif disposition == 'aggressive':
                    print(Fore.RED + f"💬 [{target}] 恶狠狠地说: {reply}")
                else:
                    print(Fore.CYAN + f"💬 [{target}] 淡淡地说: {reply}")
            else:
                print(Fore.YELLOW + "系统: 你对着空气说话，没人理你。")
        
        elif intent == "INSPECT":
            # ★ 新增：观察系统
            print(Fore.WHITE + f"🔍 你仔细观察了 {target}...")
            # TODO: 实现详细观察逻辑
        
        elif intent == "ATTACK":
            print(Fore.RED + f">>> 你向 {target} 发起攻击！")
        
        elif intent == "LOOK":
            pass
        
        elif intent == "WAIT":
            print(Fore.WHITE + "⏳ 你静观其变...")
        
        elif intent == "UNKNOWN":
            print(Fore.YELLOW + "我不理解这个指令。输入 'help' 查看帮助。")
        
        # G. 世界推演
        try:
            status = db.get_player_status()
            simulation_step(db, status)
        except Exception as e:
            print(f"世界推演失败: {e}")
    
    # 5. 清理
    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
