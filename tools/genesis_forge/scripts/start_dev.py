#!/usr/bin/env python3
"""
Genesis Forge Studio 开发环境启动脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入配置
from backend.core.config import settings

def main():
    """主函数"""
    print("=" * 60)
    print(f"启动 Genesis Forge Studio - 开发环境")
    print("=" * 60)
    
    # 设置目录和日志
    settings.setup_directories()
    settings.setup_logging()
    
    print(f"环境: {settings.app_env.value}")
    print(f"主机: {settings.host}")
    print(f"端口: {settings.port}")
    print(f"调试模式: {settings.debug}")
    print(f"日志级别: {settings.log_level.value}")
    print(f"Neo4j URI: {settings.neo4j_uri}")
    print("=" * 60)
    
    try:
        # 导入并启动Flask应用
        from backend.api.app_studio import app, socketio
        
        print(f"服务器启动在: http://{settings.host}:{settings.port}")
        print("前端开发服务器: http://localhost:3007")
        print("按 Ctrl+C 停止服务器")
        print("=" * 60)
        
        # 启动服务器
        socketio.run(
            app,
            debug=settings.debug,
            host=settings.host,
            port=settings.port,
            use_reloader=settings.debug
        )
        
    except ImportError as e:
        print(f"错误: 无法导入应用 - {e}")
        print("请确保 backend/api/app_studio.py 文件存在")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 启动服务器失败 - {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()