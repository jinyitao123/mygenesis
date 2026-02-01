"""
Project Genesis - 日志配置模块

提供统一的日志配置，支持：
1. 模块化日志记录
2. 不同日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
3. 控制台和文件输出
4. 结构化日志格式
5. 日志轮转和归档
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class GenesisLogger:
    """Project Genesis 日志管理器"""
    
    # 日志级别映射
    LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    # 模块颜色映射（用于控制台输出）
    MODULE_COLORS = {
        'main': '\033[94m',      # 蓝色
        'graph': '\033[92m',     # 绿色
        'llm': '\033[95m',       # 紫色
        'vector': '\033[93m',    # 黄色
        'simulation': '\033[96m', # 青色
        'action': '\033[91m',    # 红色
        'embedding': '\033[90m', # 灰色
        'default': '\033[0m'     # 默认
    }
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        """
        初始化日志管理器
        
        Args:
            log_dir: 日志目录
            log_level: 日志级别
        """
        self.log_dir = Path(log_dir)
        self.log_level = self.LEVELS.get(log_level.upper(), logging.INFO)
        
        # 创建日志目录
        self.log_dir.mkdir(exist_ok=True)
        
        # 初始化根日志器
        self._setup_root_logger()
        
        # 已配置的日志器缓存
        self._configured_loggers = {}
    
    def _setup_root_logger(self):
        """设置根日志器"""
        # 清除现有的处理器
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # 设置根日志器级别
        root_logger.setLevel(self.log_level)
        
        # 创建日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 文件处理器（按天轮转）
        log_file = self.log_dir / f"genesis_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 错误日志处理器（单独记录 ERROR 及以上级别）
        error_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.handlers.TimedRotatingFileHandler(
            error_file,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
    
    def get_logger(self, module_name: str, use_color: bool = True) -> logging.Logger:
        """
        获取指定模块的日志器
        
        Args:
            module_name: 模块名称
            use_color: 是否在控制台使用颜色
            
        Returns:
            配置好的日志器
        """
        # 如果已经配置过，直接返回
        if module_name in self._configured_loggers:
            return self._configured_loggers[module_name]
        
        # 创建新的日志器
        logger = logging.getLogger(f"genesis.{module_name}")
        
        # 如果使用颜色，添加彩色格式化器
        if use_color and sys.stdout.isatty():
            self._add_color_formatter(logger, module_name)
        
        # 缓存日志器
        self._configured_loggers[module_name] = logger
        
        return logger
    
    def _add_color_formatter(self, logger: logging.Logger, module_name: str):
        """为日志器添加彩色格式化器"""
        # 获取模块颜色
        color = self.MODULE_COLORS.get(module_name, self.MODULE_COLORS['default'])
        reset = '\033[0m'
        
        # 彩色格式化器
        class ColorFormatter(logging.Formatter):
            def format(self, record):
                # 根据级别添加颜色
                if record.levelno >= logging.ERROR:
                    level_color = '\033[91m'  # 红色
                elif record.levelno >= logging.WARNING:
                    level_color = '\033[93m'  # 黄色
                elif record.levelno >= logging.INFO:
                    level_color = '\033[92m'  # 绿色
                else:
                    level_color = '\033[90m'  # 灰色
                
                # 格式化消息
                record.module_color = color
                record.level_color = level_color
                record.reset = reset
                
                # 使用父类格式化
                message = super().format(record)
                return message
        
        # 为每个处理器添加彩色格式化器
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                formatter = ColorFormatter(
                    '%(module_color)s[%(name)s]%(reset)s %(level_color)s%(levelname)s%(reset)s: %(message)s',
                    datefmt='%H:%M:%S'
                )
                handler.setFormatter(formatter)
    
    def set_level(self, level: str):
        """
        设置日志级别
        
        Args:
            level: 日志级别字符串
        """
        log_level = self.LEVELS.get(level.upper(), logging.INFO)
        self.log_level = log_level
        
        # 更新根日志器级别
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # 更新所有处理器级别
        for handler in root_logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.setLevel(log_level)
            elif isinstance(handler, logging.StreamHandler):
                handler.setLevel(log_level)
    
    def log_system_info(self):
        """记录系统信息"""
        logger = self.get_logger('system')
        
        # 系统信息
        import platform
        import socket
        
        system_info = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'hostname': socket.gethostname(),
            'working_dir': os.getcwd(),
            'log_dir': str(self.log_dir.absolute())
        }
        
        logger.info("系统启动信息: %s", system_info)
        
        # 环境变量（敏感信息已过滤）
        env_vars = {k: v for k, v in os.environ.items() 
                   if not any(secret in k.lower() for secret in ['key', 'pass', 'secret', 'token'])}
        logger.debug("环境变量: %s", {k: v for k, v in env_vars.items() if k.startswith(('NEO4J', 'PG', 'LLM', 'CHAT', 'EMBED'))})
    
    def log_module_start(self, module_name: str, config: Optional[Dict[str, Any]] = None):
        """
        记录模块启动信息
        
        Args:
            module_name: 模块名称
            config: 模块配置信息
        """
        logger = self.get_logger(module_name)
        logger.info(f"模块启动: {module_name}")
        if config:
            logger.debug(f"模块配置: {config}")
    
    def log_module_error(self, module_name: str, error: Exception, context: str = ""):
        """
        记录模块错误信息
        
        Args:
            module_name: 模块名称
            error: 异常对象
            context: 错误上下文
        """
        logger = self.get_logger(module_name)
        error_msg = f"{context}: {type(error).__name__}: {str(error)}"
        logger.error(error_msg, exc_info=True)
    
    def log_performance(self, module_name: str, operation: str, duration: float, 
                       details: Optional[Dict[str, Any]] = None):
        """
        记录性能信息
        
        Args:
            module_name: 模块名称
            operation: 操作名称
            duration: 耗时（秒）
            details: 详细信息
        """
        logger = self.get_logger(module_name)
        
        if duration > 1.0:
            level = logging.WARNING
        elif duration > 0.5:
            level = logging.INFO
        else:
            level = logging.DEBUG
        
        message = f"性能统计 - {operation}: {duration:.3f}s"
        if details:
            message += f" | 详情: {details}"
        
        logger.log(level, message)


# 全局日志管理器实例
_log_manager: Optional[GenesisLogger] = None


def setup_logging(log_dir: str = "logs", log_level: str = "INFO") -> GenesisLogger:
    """
    设置全局日志配置
    
    Args:
        log_dir: 日志目录
        log_level: 日志级别
        
    Returns:
        日志管理器实例
    """
    global _log_manager
    _log_manager = GenesisLogger(log_dir, log_level)
    return _log_manager


def get_logger(module_name: str, use_color: bool = True) -> logging.Logger:
    """
    获取日志器（便捷函数）
    
    Args:
        module_name: 模块名称
        use_color: 是否使用颜色
        
    Returns:
        日志器实例
    """
    global _log_manager
    if _log_manager is None:
        # 使用默认配置初始化
        _log_manager = setup_logging()
    
    return _log_manager.get_logger(module_name, use_color)


def log_system_info():
    """记录系统信息（便捷函数）"""
    global _log_manager
    if _log_manager is None:
        _log_manager = setup_logging()
    
    _log_manager.log_system_info()


# 预定义的模块日志器（便于导入使用）
def get_main_logger():
    """获取主程序日志器"""
    return get_logger('main')

def get_graph_logger():
    """获取图数据库日志器"""
    return get_logger('graph')

def get_llm_logger():
    """获取LLM引擎日志器"""
    return get_logger('llm')

def get_vector_logger():
    """获取向量数据库日志器"""
    return get_logger('vector')

def get_simulation_logger():
    """获取模拟引擎日志器"""
    return get_logger('simulation')

def get_action_logger():
    """获取动作驱动日志器"""
    return get_logger('action')

def get_embedding_logger():
    """获取嵌入服务日志器"""
    return get_logger('embedding')


if __name__ == "__main__":
    # 测试日志系统
    setup_logging(log_level="DEBUG")
    log_system_info()
    
    # 测试不同模块的日志
    logger = get_main_logger()
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    
    # 测试性能日志
    import time
    start = time.time()
    time.sleep(0.1)
    _log_manager.log_performance('test', 'sleep操作', time.time() - start)