"""
Main Entry - 游戏入口

Project Genesis v0.4 - 重构版游戏主程序

用法:
    python -m applications.game.main
    或
    cd applications/game && python main.py
"""

import os
import sys
import logging
from pathlib import Path

# Reason: 确保能找到 genesis 模块
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from genesis.kernel.connectors.neo4j_connector import Neo4jConnector
from genesis.kernel.connectors.postgres_connector import PostgresConnector
from applications.game.game_engine import GameEngine
from applications.game.cli import GameCLI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """游戏主入口"""
    cli = GameCLI()
    cli.print_banner()

    # 1. 初始化数据库连接
    try:
        # 使用 Docker 容器中的正确默认值
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "mysecretpassword")
        
        cli.print_message(f"连接 Neo4j: {neo4j_uri} (用户: {neo4j_user})", "info")
        
        neo4j_conn = Neo4jConnector(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password
        )

        postgres_url = (
            f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'kimyitao')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'smartcleankb')}"
        )
        
        cli.print_message(f"连接 PostgreSQL: localhost:5432", "info")
        postgres_conn = PostgresConnector(connection_url=postgres_url)

        cli.print_init_status(True, ">>> 系统初始化完成。神经元网络已连接。")
    except Exception as e:
        cli.print_init_status(False, f">>> 初始化失败: {e}")
        cli.print_message("请检查：1) Neo4j 是否运行 2) PostgreSQL 是否运行 3) 配置是否正确", "error")
        return 1

    # 2. 初始化游戏引擎
    try:
        # 使用绝对路径确保能找到 ontology 文件
        project_root = Path(__file__).parent.parent.parent
        ontology_dir = str(project_root / "ontology")
        
        # 默认使用 XML，但可以通过环境变量切换
        use_xml = os.getenv("USE_XML", "true").lower() in ("true", "1", "yes", "y")
        
        engine = GameEngine(
            neo4j_conn=neo4j_conn,
            postgres_conn=postgres_conn,
            ontology_dir=ontology_dir,
            use_xml=use_xml
        )

        # 初始化世界
        if not engine.initialize_world():
            cli.print_message("世界初始化失败", "error")
            return 1

        mode = "XML" if use_xml else "JSON"
        cli.print_init_status(True, f">>> 世界已实例化 (使用 {mode} 本体数据)")
    except Exception as e:
        cli.print_init_status(False, f">>> 游戏引擎初始化失败: {e}")
        return 1

    # 3. 游戏主循环
    cli.print_message("输入 'help' 查看帮助，'quit' 退出游戏\n", "system")

    while True:
        # A. 获取游戏状态
        status = engine.get_player_status()

        # B. 检查游戏结束
        game_over_reason = engine.check_game_over()
        if game_over_reason:
            cli.print_game_over(game_over_reason)
            break

        # C. 显示状态
        if status:
            cli.display_status(status)
        else:
            cli.print_message("无法获取游戏状态", "error")
            break

        # D. 获取用户输入
        user_input = cli.get_input()

        # E. 处理特殊指令
        if user_input.lower() in ["quit", "exit", "退出"]:
            cli.print_message("感谢游玩，再见！", "success")
            break

        if user_input.lower() in ["help", "帮助", "?"]:
            cli.print_help(engine.get_help_text())
            continue

        if not user_input:
            continue

        # F. 处理输入
        try:
            result = engine.process_input(user_input)
            cli.print_action_result(result)
        except Exception as e:
            logger.error(f"处理输入时出错: {e}")
            cli.print_message(f"指令处理失败: {e}", "error")
            continue

        # G. 世界推演 (仅在动作成功时)
        if result.get("success"):
            try:
                events = engine.run_simulation_tick()
                cli.print_simulation_events(events)
            except Exception as e:
                logger.error(f"世界推演时出错: {e}")

    # 4. 清理
    neo4j_conn.close()
    postgres_conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
