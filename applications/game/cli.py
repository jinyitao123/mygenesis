"""
Game CLI - 游戏命令行界面

职责：
- 提供彩色终端界面
- 处理用户输入和输出格式化
- 显示游戏状态和反馈
"""

import logging
from typing import Dict, Any, Optional, List

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    class _Fore:
        def __getattr__(self, name):
            return ''
    class _Style:
        def __getattr__(self, name):
            return ''
    Fore = _Fore()
    Style = _Style()

logger = logging.getLogger(__name__)


class GameCLI:
    """游戏命令行界面"""

    def __init__(self):
        """初始化 CLI"""
        self.color_enabled = COLORAMA_AVAILABLE

    def print_banner(self):
        """打印游戏启动横幅"""
        banner = """
==================================================
                                                  
     ** Project Genesis v0.4 - 重构版 **          
                                                  
     企业级五层架构 - Ontology 驱动               
                                                  
==================================================
        """
        print(f"{Fore.CYAN}{banner}{Style.RESET_ALL}")

    def print_separator(self, char: str = "=", length: int = 50):
        """打印分隔线"""
        print(char * length)

    def display_status(self, status: Dict[str, Any]):
        """
        显示玩家状态和周围环境

        Args:
            status: 包含 player, location, exits, entities, player_faction 的字典
        """
        if not status:
            print(Fore.RED + "错误：无法获取游戏状态")
            return

        player = status.get("player", {})
        location = status.get("location", {})
        exits = status.get("exits", [])
        entities = status.get("entities", [])
        faction = status.get("player_faction", {})

        self.print_separator()

        # 位置信息
        print(f"[位置] {Fore.BLUE}{location.get('name', '未知')}{Style.RESET_ALL}")
        print(f"[描述] {location.get('description', '无')}")

        # 阵营信息
        if faction:
            print(f"[阵营] {Fore.CYAN}{faction.get('name', '无')}{Style.RESET_ALL}")
        else:
            print(f"[阵营] {Fore.WHITE}无党派浪人{Style.RESET_ALL}")

        # 出口
        if exits:
            exit_names = [e.get('name', '?') for e in exits if e]
            print(f"[出口] {Fore.GREEN}{', '.join(exit_names)}{Style.RESET_ALL}")
        else:
            print(f"[出口] {Fore.RED}无{Style.RESET_ALL}")

        # 可见实体
        if entities:
            entity_names = [e.get('name', '?') for e in entities if e]
            print(f"[可见] {Fore.YELLOW}{', '.join(entity_names)}{Style.RESET_ALL}")
        else:
            print(f"[可见] {Fore.WHITE}空无一物{Style.RESET_ALL}")

        # HP 状态
        hp = player.get('hp', 0)
        if hp > 50:
            hp_color = Fore.GREEN
        elif hp > 25:
            hp_color = Fore.YELLOW
        else:
            hp_color = Fore.RED
        print(f"[状态] HP {hp_color}{hp}{Style.RESET_ALL}")

        self.print_separator()

    def print_message(self, message: str, level: str = "info"):
        """
        打印格式化消息

        Args:
            message: 消息内容
            level: 消息级别 (info, success, warning, error, narrative)
        """
        color_map = {
            "info": Fore.WHITE,
            "success": Fore.GREEN,
            "warning": Fore.YELLOW,
            "error": Fore.RED,
            "narrative": Fore.MAGENTA,
            "system": Fore.CYAN
        }

        color = color_map.get(level, Fore.WHITE)

        prefixes = {
            "info": "",
            "success": "[OK] ",
            "warning": "[WARN] ",
            "error": "[ERROR] ",
            "narrative": "AI: ",
            "system": ""
        }

        prefix = prefixes.get(level, "")
        print(f"{color}{prefix}{message}{Style.RESET_ALL}")

    def print_action_result(self, result: Dict[str, Any]):
        """
        打印动作执行结果

        Args:
            result: 动作结果字典
        """
        narrative = result.get("narrative", "")
        message = result.get("message", "")
        success = result.get("success", False)

        # 打印 AI 旁白
        if narrative:
            self.print_message(narrative, "narrative")

        # 打印系统消息
        if success:
            self.print_message(message, "success")
        else:
            self.print_message(message, "warning")

    def print_simulation_events(self, events: List[Dict[str, Any]]):
        """
        打印推演事件

        Args:
            events: 事件列表
        """
        for event in events:
            msg = event.get("message", "")
            event_type = event.get("type", "")

            if event_type == "attack":
                self.print_message(msg, "error")
            else:
                self.print_message(msg, "info")

    def get_input(self, prompt: str = "你要做什么?") -> str:
        """
        获取用户输入

        Args:
            prompt: 提示文本

        Returns:
            用户输入的字符串
        """
        try:
            return input(f"{Fore.WHITE}{prompt} > {Style.RESET_ALL}").strip()
        except (EOFError, KeyboardInterrupt):
            return "quit"

    def print_game_over(self, reason: str):
        """
        打印游戏结束信息

        Args:
            reason: 结束原因
        """
        print()
        self.print_separator("=", 50)
        print(f"{Fore.RED}[GAME OVER] {reason}{Style.RESET_ALL}")
        self.print_separator("=", 50)

    def print_help(self, help_text: str):
        """
        打印帮助信息

        Args:
            help_text: 帮助文本
        """
        print(f"{Fore.CYAN}{help_text}{Style.RESET_ALL}")

    def print_init_status(self, success: bool, message: str):
        """
        打印初始化状态

        Args:
            success: 是否成功
            message: 状态消息
        """
        if success:
            self.print_message(message, "success")
        else:
            self.print_message(message, "error")

    def confirm_action(self, prompt: str) -> bool:
        """
        确认操作

        Args:
            prompt: 确认提示

        Returns:
            是否确认
        """
        try:
            response = input(f"{Fore.YELLOW}{prompt} (y/n): {Style.RESET_ALL}").strip().lower()
            return response in ['y', 'yes', '是', '确定']
        except:
            return False

    def get_password_input(self, prompt: str) -> str:
        """
        获取密码输入（隐藏输入）

        Args:
            prompt: 提示文本

        Returns:
            用户输入的密码
        """
        try:
            import getpass
            return getpass.getpass(f"{Fore.YELLOW}{prompt}{Style.RESET_ALL}").strip()
        except:
            # 如果 getpass 不可用，回退到普通输入
            return input(f"{Fore.YELLOW}{prompt}{Style.RESET_ALL}").strip()
