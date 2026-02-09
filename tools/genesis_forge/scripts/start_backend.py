#!/usr/bin/env python3
"""
Genesis Forge Studio 后端启动脚本

提供统一的启动接口，支持不同环境配置。
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.config import settings, Environment


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='启动 Genesis Forge Studio 后端服务')
    
    parser.add_argument(
        '--env', 
        type=str, 
        choices=['development', 'testing', 'production'],
        default='development',
        help='运行环境 (默认: development)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default=None,
        help='监听主机 (默认: 从配置读取)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='监听端口 (默认: 从配置读取)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--no-debug',
        dest='debug',
        action='store_false',
        help='禁用调试模式'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default=None,
        help='日志级别'
    )
    
    parser.set_defaults(debug=None)
    
    return parser.parse_args()


def update_settings_from_args(args):
    """根据命令行参数更新配置"""
    # 注意：由于Config类使用property装饰器，我们不能直接修改配置
    # 这里我们通过环境变量来影响配置
    if args.env:
        os.environ["APP_ENV"] = args.env
    
    if args.host:
        os.environ["HOST"] = args.host
    
    if args.port:
        os.environ["PORT"] = str(args.port)
    
    if args.debug is not None:
        os.environ["DEBUG"] = "true" if args.debug else "false"
    
    if args.log_level:
        os.environ["LOG_LEVEL"] = args.log_level


def print_startup_info():
    """打印启动信息"""
    print("=" * 60)
    print(f"Genesis Forge Studio - {settings.vite_app_title}")
    print(f"版本: 2.0.0")
    print(f"环境: {settings.app_env.value}")
    print("=" * 60)
    
    print("配置信息:")
    print(f"  主机: {settings.host}")
    print(f"  端口: {settings.port}")
    print(f"  调试模式: {settings.debug}")
    print(f"  日志级别: {settings.log_level.value}")
    print(f"  Neo4j URI: {settings.neo4j_uri}")
    print(f"  CORS 源: {', '.join(settings.cors_origins)}")
    
    print("目录信息:")
    print(f"  项目根目录: {settings.project_root}")
    print(f"  日志目录: {settings.log_dir}")
    print(f"  临时目录: {settings.temp_dir_path}")
    
    print("=" * 60)
    print("启动服务...")


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 更新配置
    update_settings_from_args(args)
    
    # 设置目录和日志
    settings.setup_directories()
    settings.setup_logging()
    
    # 打印启动信息
    print_startup_info()
    
    # 导入并启动Flask应用
    try:
        from backend.api.app_studio import app, socketio
        
        print(f"服务器启动在: http://{settings.host}:{settings.port}")
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
        print(f"导入应用失败: {e}")
        print("请确保 backend/api/app_studio.py 文件存在")
        sys.exit(1)
    except Exception as e:
        print(f"启动服务器失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()