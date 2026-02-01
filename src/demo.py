"""
自动演示脚本 - 无需人工输入
用于验证游戏逻辑是否正常运行
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
                                                      
     {Fore.YELLOW}Project Genesis - 生成式仿真平台{Fore.CYAN}                  
                                                      
     {Fore.WHITE}语义驱动的无限游戏引擎 v0.1.0 MVP{Fore.CYAN}               
                                                      
====================================================={Style.RESET_ALL}
    """
    print(banner)


def demo():
    """自动演示模式"""
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
        print(Fore.GREEN + ">>> 系统初始化完成。神经元网络已连接。\n")
    except Exception as e:
        print(Fore.RED + f"初始化失败: {e}")
        return 1
    
    # 3. 世界构建阶段 - 使用固定场景
    scenario = "发生在维多利亚时代豪宅的谋杀案，我是侦探"
    print(Fore.CYAN + f"使用演示场景: {scenario}")
    print(Fore.YELLOW + "\n>>> AI 正在编织现实 (图谱建模)...")
    
    try:
        world_json = llm.generate_world_schema(scenario)
        print(Fore.CYAN + f"\n生成的世界结构:")
        print(f"  - 节点数: {len(world_json.get('nodes', []))}")
        print(f"  - 关系数: {len(world_json.get('edges', []))}")
        print(f"\n节点列表:")
        for node in world_json.get('nodes', []):
            print(f"  - {node.get('label')}: {node.get('properties', {}).get('name', 'N/A')}")
        
        db.clear_world()
        db.create_world(world_json)
        print(Fore.GREEN + f"\n>>> 世界已实例化到图数据库\n")
    except Exception as e:
        print(Fore.RED + f"世界生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 4. 显示初始状态
    print(Fore.CYAN + "=== 初始游戏状态 ===")
    status = db.get_player_status()
    if status:
        print(f"位置: {status['location'].get('name')}")
        print(f"描述: {status['location'].get('description')}")
        print(f"出口: {[e.get('name') for e in status['exits']]}")
        print(f"可见: {[e.get('name') for e in status['entities']]}")
        print(f"HP: {status['player'].get('hp', 100)}")
    
    # 5. 演示动作序列
    test_actions = [
        "去书房",
        "查看四周",
        "攻击僵尸"
    ]
    
    print(Fore.CYAN + "\n=== 演示动作序列 ===")
    for action_input in test_actions:
        print(f"\n{Fore.WHITE}动作: {action_input}")
        
        # 获取最新状态
        status = db.get_player_status()
        if not status:
            print(Fore.RED + "无法获取游戏状态")
            break
        
        # 解析意图
        try:
            action = llm.interpret_action(action_input, status)
            print(Fore.MAGENTA + f"AI 旁白: {action.get('narrative', '')}")
            
            # 执行动作
            intent = action.get("intent", "UNKNOWN")
            target = action.get("target", "")
            
            if intent == "MOVE":
                success, msg = db.execute_move(target)
                print(Fore.YELLOW + f"系统: {msg}")
            elif intent == "ATTACK":
                print(Fore.RED + f">>> 你向 {target} 发起攻击！")
            elif intent == "LOOK":
                print(Fore.CYAN + "你环顾四周...")
            else:
                print(Fore.YELLOW + "未知的意图")
                
        except Exception as e:
            print(Fore.RED + f"动作执行失败: {e}")
    
    # 6. 显示最终状态
    print(Fore.CYAN + "\n=== 最终游戏状态 ===")
    status = db.get_player_status()
    if status:
        print(f"位置: {status['location'].get('name')}")
        print(f"HP: {status['player'].get('hp', 100)}")
        print(f"出口: {[e.get('name') for e in status['exits']]}")
    
    # 7. 清理
    db.close()
    print(Fore.GREEN + "\n>>> 演示完成，游戏结束")
    return 0


if __name__ == "__main__":
    sys.exit(demo())
