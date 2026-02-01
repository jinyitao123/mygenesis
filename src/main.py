"""
Project Genesis v0.3 - 主入口

语义驱动的仿真宇宙 - 四模块架构：
1. 动力学引擎 (ActionDriver): 执行数据驱动的规则
2. 生成引擎 (LLMEngine): 分形世界生成
3. 推演引擎 (SimulationEngine): 全局时钟和 NPC 自主行为
4. 双脑系统 (Neo4j + pgvector): 逻辑推理 + 记忆语义

升级特性：
- Action Ontology 驱动的游戏逻辑
- 分形懒加载世界生成
- 全局时钟推演系统
- 增强的双脑协同对话
"""

import os
import sys
import io
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from colorama import Fore, Style, init

# 设置 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 初始化 colorama
init(autoreset=True)

# v0.3 架构导入
from src.core import GraphClient, ActionDriver, SimulationEngine
from src.llm_engine import LLMEngine
from src.services.vector_client import VectorClient


def print_banner():
    """打印游戏启动横幅"""
    banner = f"""
{Fore.CYAN}=====================================================
                                                       
     {Fore.YELLOW}Project Genesis v0.3 - 语义驱动的仿真宇宙{Fore.CYAN}                  
                                                       
     {Fore.WHITE}Action Ontology + 分形生成 + 全局推演{Fore.CYAN}               
                                                       
====================================================={Style.RESET_ALL}
    """
    print(banner)


def get_player_input() -> str:
    """获取玩家输入"""
    try:
        return input(Fore.WHITE + "你要做什么? > " + Style.RESET_ALL).strip()
    except (EOFError, KeyboardInterrupt):
        return "quit"


def display_status(status: Optional[Dict[str, Any]]) -> None:
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
    
    # 显示阵营
    if faction:
        print(f"🏛️  阵营: {Fore.CYAN}{faction.get('name')}{Style.RESET_ALL}")
    else:
        print(f"🏛️  阵营: {Fore.WHITE}无党派浪人{Style.RESET_ALL}")
    
    # 显示详细描述
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


def check_game_over(status: Optional[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
    """检查游戏是否结束"""
    if not status:
        return True, "游戏状态异常"
    
    player = status.get("player", {})
    hp = player.get('hp', 100)
    
    if hp <= 0:
        return True, "你倒下了...游戏结束。"
    
    return False, None


def execute_action_v3(
    action: Dict[str, Any],
    action_driver: ActionDriver,
    graph: GraphClient,
    status: Dict[str, Any]
) -> str:
    """v0.3 动作执行器 - 使用 ActionDriver
    
    将 LLM 解析的意图转换为 ActionDriver 可执行的 Action。
    
    Args:
        action: LLM 解析的意图
        action_driver: 动力学引擎
        graph: 图数据库客户端
        status: 当前状态
        
    Returns:
        执行结果描述
    """
    intent = action.get("intent", "UNKNOWN")
    target = action.get("target", "")
    
    player_id = status.get("player", {}).get("id", "player1")
    
    if intent == "MOVE":
        # 移动仍由 GraphClient 处理（需要连通性验证）
        success, msg = graph.execute_move(target)
        return msg
    
    elif intent == "TALK":
        return f"你尝试与 {target} 对话"
    
    elif intent == "ATTACK":
        # 查找目标 NPC ID
        target_id = None
        for entity in status.get("entities", []):
            if entity.get("name") == target:
                target_id = entity.get("id")
                break
        
        if target_id:
            # 使用 ActionDriver 执行攻击
            success, msg = action_driver.execute_action("ATTACK", player_id, target_id)
            return msg
        else:
            return f"找不到目标: {target}"
    
    elif intent == "INSPECT":
        return f"你仔细观察了 {target}"
    
    elif intent == "WAIT":
        return "你静观其变..."
    
    elif intent == "UNKNOWN":
        return action.get("narrative", "无法理解这个指令")
    
    return f"执行了 {intent}"


def simulation_step_v3(
    simulation: SimulationEngine,
    graph: GraphClient,
    status: Dict[str, Any]
) -> None:
    """v0.3 推演步骤 - 使用 SimulationEngine
    
    执行全局时钟推演，显示传闻。
    
    Args:
        simulation: 推演引擎
        graph: 图数据库客户端
        status: 当前状态
    """
    location_id = status.get("location", {}).get("id")
    
    # 1. 处理玩家身边的即时危机（智能仿真）
    player_id = status['player']['id']
    hostile_events = graph.run_smart_simulation(player_id)
    
    for event in hostile_events:
        name = event['name']
        damage = event.get('damage', 5)
        disposition = event.get('disposition')
        
        if disposition == 'aggressive':
            print(Fore.RED + f">>> ⚔️ {name} (天生好战) 向你扑来！造成 {damage} 点伤害！")
        else:
            print(Fore.RED + f">>> ⚔️ {name} 发现了敌对阵营的你，发起攻击！造成 {damage} 点伤害！")
        
        graph.update_player_hp(-damage)
    
    # 2. v0.3 核心：全局时钟推演
    print(Fore.BLACK + Style.BRIGHT + ">>> ⏳ 世界时间正在流逝...")
    rumors = simulation.run_tick(location_id)
    
    # 3. 显示传闻
    if rumors:
        print(Fore.WHITE + "\n📰 【江湖传闻】")
        for news in rumors[:5]:  # 最多显示5条
            print(Fore.WHITE + f"  • {news}")
        print("")
    
    # 4. 显示世界状态摘要（调试用，可选）
    world_summary = simulation.get_world_summary()
    logger = __import__('logging').getLogger(__name__)
    logger.debug(f"世界状态: {world_summary}")


def main():
    """游戏主入口 v0.3"""
    print_banner()
    
    # 1. 加载环境变量
    load_dotenv()
    
    # 2. 初始化 v0.3 四模块系统
    try:
        # 图数据库客户端（左脑 - 逻辑推理）
        graph = GraphClient(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "mysecretpassword")
        )
        
        # 动力学引擎（Action Driver）
        action_driver = ActionDriver(graph.get_driver())
        
        # 推演引擎（全局时钟）
        simulation = SimulationEngine(graph, action_driver)
        
        # 记忆系统（右脑 - 语义记忆）
        try:
            memory_db = VectorClient()
            print(Fore.GREEN + ">>> 右脑记忆系统已启动")
        except Exception as e:
            print(Fore.YELLOW + f">>> 右脑记忆系统未启动: {e}")
            memory_db = None
        
        # LLM 引擎（生成引擎）
        llm = LLMEngine()
        
        print(Fore.GREEN + ">>> v0.3 四模块系统初始化完成：")
        print(Fore.GREEN + "  🧠 左脑(Neo4j): 逻辑推理引擎")
        print(Fore.GREEN + "  ⚡ ActionDriver: 动力学引擎")
        print(Fore.GREEN + "  ⏰ SimulationEngine: 全局推演引擎")
        print(Fore.GREEN + "  🧠 右脑(Postgres): 记忆语义引擎\n")
        
    except Exception as e:
        print(Fore.RED + f"初始化失败: {e}")
        print(Fore.YELLOW + "请检查：1) Neo4j 是否运行 2) API 密钥是否正确")
        import traceback
        traceback.print_exc()
        return 1
    
    # 3. 世界构建阶段
    print(Fore.CYAN + "请描述你想体验的世界：")
    print(Fore.WHITE + "示例：发生在维多利亚时代豪宅的谋杀案，我是侦探")
    scenario = input(Fore.YELLOW + "> " + Style.RESET_ALL).strip()
    
    if not scenario:
        scenario = "一个神秘的地下迷宫"
    
    # 存储世界种子（用于懒加载）
    world_seed = None
    
    print(Fore.YELLOW + "\n>>> AI 正在编织现实 (分形生成)...")
    try:
        # v0.3: 生成世界种子
        world_seed = llm.generate_world_seed(scenario)
        
        # v0.3: 生成世界骨架
        world_json = llm.generate_world_skeleton(world_seed)
        
        # 清空并创建世界
        graph.clear_world()
        
        # 使用新的批量创建方法
        node_stats = graph.create_nodes_from_json(world_json.get("nodes", []))
        edge_stats = graph.create_relationships_from_json(world_json.get("edges", []))
        
        # 生成 Action Ontology
        actions = llm.generate_action_ontology(world_seed)
        action_count = action_driver.load_actions(actions)
        
        print(Fore.GREEN + f">>> 世界已实例化：")
        print(Fore.GREEN + f"  - {node_stats['created']} 节点（{node_stats['skipped']} 跳过）")
        print(Fore.GREEN + f"  - {edge_stats['created']} 关系（{edge_stats['skipped']} 跳过）")
        print(Fore.GREEN + f"  - {action_count} 个 Action 规则已加载")
        
        # 验证玩家位置
        test_status = graph.get_player_status()
        if not test_status:
            print(Fore.YELLOW + ">>> 初始化玩家位置...")
            with graph.driver.session() as session:
                session.run("""
                    MATCH (p:Player), (l:Location)
                    WHERE NOT (p)-[:LOCATED_AT]->()
                    WITH p, l LIMIT 1
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
        status = graph.get_player_status()
        
        # B. 检查游戏结束
        is_over, game_over_msg = check_game_over(status)
        if is_over:
            print(Fore.RED + f"\n{game_over_msg}")
            break
        
        # C. v0.3: 懒加载检查
        if world_seed and status:
            location_id = status.get("location", {}).get("id")
            if location_id:
                was_expanded = simulation.check_lazy_loading(location_id, world_seed)
                if was_expanded:
                    # 重新获取状态以显示新内容
                    status = graph.get_player_status()
        
        # D. 显示状态
        display_status(status)
        
        # E. 获取用户输入
        user_input = get_player_input()
        
        if user_input.lower() in ["quit", "exit", "退出"]:
            print(Fore.YELLOW + "\n感谢游玩，再见！")
            break
        
        if user_input.lower() in ["help", "帮助", "?"]:
            available_actions = action_driver.get_available_actions_desc()
            print(Fore.CYAN + f"""
可用指令：
- 移动: "去书房" / "移动到厨房"
- 对话: "对话卫兵" / "询问老板"
- 观察: "查看" / "环顾四周" / "检查尸体"
- 战斗: "攻击僵尸" / "打敌人"
- 等待: "等待" / "静观其变"

已加载的 Action: {available_actions}
- 其他: "help" 显示帮助，"quit" 退出
            """)
            continue
        
        if not user_input:
            continue
        
        # F. 语义解析
        try:
            # v0.3: 注入可用 Action 列表
            context = status.copy() if status else {}
            context["available_actions"] = list(action_driver.actions_registry.keys())
            
            action = llm.interpret_action(user_input, context)
            print(Fore.MAGENTA + f"AI 旁白: {action.get('narrative', '')}")
        except Exception as e:
            print(Fore.RED + f"指令解析失败: {e}")
            continue
        
        # G. v0.3: 使用 ActionDriver 执行动作
        try:
            if status:
                result_msg = execute_action_v3(action, action_driver, graph, status)
                if result_msg:
                    print(Fore.YELLOW + f"系统: {result_msg}")
        except Exception as e:
            print(Fore.RED + f"动作执行失败: {e}")
        
        # H. 特殊处理：对话系统（双脑协同）
        if action.get("intent") == "TALK" and memory_db and status:
            target = action.get("target", "")
            npc_data = graph.get_npc_details_by_name(target)
            
            if npc_data:
                # 检索记忆
                print(Fore.BLACK + Style.BRIGHT + f">>> 🧠 右脑检索记忆中...")
                try:
                    memories = memory_db.search_memory(
                        f"关于 {target} 的信息: {user_input}",
                        limit=3
                    )
                    memory_context = "\n".join(memories) if memories else "暂无相关记忆"
                    
                    if memories:
                        print(Fore.BLACK + Style.BRIGHT + f">>> 💭 回忆起 {len(memories)} 条相关记忆")
                except Exception as e:
                    memory_context = ""
                    logger = __import__('logging').getLogger(__name__)
                    logger.debug(f"记忆检索失败: {e}")
                
                # 生成回复
                print(Fore.BLACK + Style.BRIGHT + f">>> 🤖 生成回复中...")
                player_data = status.get('player', {})
                reply = llm.generate_npc_response(
                    user_input,
                    npc_data,
                    player_data,
                    memory_context=memory_context
                )
                
                # 显示回复
                disposition = npc_data.get('disposition', 'neutral')
                if disposition == 'friendly':
                    print(Fore.GREEN + f"💬 [{target}] 热情地说: {reply}")
                elif disposition == 'aggressive':
                    print(Fore.RED + f"💬 [{target}] 恶狠狠地说: {reply}")
                else:
                    print(Fore.CYAN + f"💬 [{target}] 淡淡地说: {reply}")
                
                # 存入记忆
                try:
                    full_log = f"玩家对 {target} 说: '{user_input}'。{target} 回答: '{reply}'"
                    memory_db.add_memory(
                        full_log,
                        meta={"source": "dialogue", "npc": target, "location": status.get('location', {}).get('name')}
                    )
                except Exception as e:
                    logger = __import__('logging').getLogger(__name__)
                    logger.debug(f"记忆存储失败: {e}")
            else:
                print(Fore.YELLOW + "系统: 你对着空气说话，没人理你。")
        
        # I. v0.3: 世界推演
        try:
            if status:
                simulation_step_v3(simulation, graph, status)
        except Exception as e:
            logger = __import__('logging').getLogger(__name__)
            logger.error(f"世界推演失败: {e}")
    
    # 5. 清理
    graph.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
