"""
Genesis Forge Studio 配置管理系统

基于环境变量的配置管理，支持开发、测试、生产环境。
使用 python-dotenv 加载 .env 文件。
"""

import os
import logging
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Environment(str, Enum):
    """运行环境枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CacheType(str, Enum):
    """缓存类型枚举"""
    SIMPLE = "simple"
    REDIS = "redis"
    FILESYSTEM = "filesystem"


class Config:
    """
    应用配置类
    
    配置优先级：
    1. 环境变量
    2. .env 文件
    3. 默认值
    """
    
    # ========== 基础配置 ==========
    @property
    def app_env(self) -> Environment:
        """应用运行环境"""
        env_str = os.getenv("APP_ENV", "development").lower()
        try:
            return Environment(env_str)
        except ValueError:
            return Environment.DEVELOPMENT
    
    @property
    def debug(self) -> bool:
        """调试模式"""
        return os.getenv("DEBUG", "true").lower() == "true"
    
    @property
    def secret_key(self) -> str:
        """应用密钥"""
        return os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    
    @property
    def host(self) -> str:
        """应用监听主机"""
        return os.getenv("HOST", "0.0.0.0")
    
    @property
    def port(self) -> int:
        """应用监听端口"""
        return int(os.getenv("PORT", "5000"))
    
    # ========== 数据库配置 ==========
    @property
    def neo4j_uri(self) -> str:
        """Neo4j 数据库连接 URI"""
        return os.getenv("NEO4J_URI", "bolt://localhost:7687")
    
    @property
    def neo4j_user(self) -> str:
        """Neo4j 用户名"""
        return os.getenv("NEO4J_USER", "neo4j")
    
    @property
    def neo4j_password(self) -> str:
        """Neo4j 密码"""
        return os.getenv("NEO4J_PASSWORD", "password")
    
    @property
    def neo4j_database(self) -> str:
        """Neo4j 数据库名称"""
        return os.getenv("NEO4J_DATABASE", "neo4j")
    
    @property
    def neo4j_max_connection_pool_size(self) -> int:
        """Neo4j 最大连接池大小"""
        return int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50"))
    
    @property
    def neo4j_max_connection_lifetime(self) -> int:
        """Neo4j 连接最大生命周期（秒）"""
        return int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600"))
    
    # ========== 前端配置 ==========
    @property
    def vite_app_title(self) -> str:
        """前端应用标题"""
        return os.getenv("VITE_APP_TITLE", "Genesis Forge Studio")
    
    @property
    def vite_api_base_url(self) -> str:
        """前端 API 基础 URL"""
        return os.getenv("VITE_API_BASE_URL", "http://localhost:5000/api")
    
    # ========== 日志配置 ==========
    @property
    def log_level(self) -> LogLevel:
        """日志级别"""
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        try:
            return LogLevel(level_str)
        except ValueError:
            return LogLevel.INFO
    
    @property
    def log_file(self) -> str:
        """日志文件路径"""
        return os.getenv("LOG_FILE", "logs/genesis_forge.log")
    
    @property
    def log_format(self) -> str:
        """日志格式"""
        return os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # ========== 文件存储配置 ==========
    @property
    def max_content_length(self) -> int:
        """上传文件大小限制（字节）"""
        return int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024)))  # 16MB
    
    @property
    def temp_dir(self) -> str:
        """临时文件目录"""
        return os.getenv("TEMP_DIR", "temp")
    
    # ========== 安全配置 ==========
    @property
    def cors_origins(self) -> List[str]:
        """CORS 允许的源"""
        origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
        return [origin.strip() for origin in origins_str.split(",")]
    
    @property
    def session_cookie_secure(self) -> bool:
        """会话 Cookie 安全标志"""
        return os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    
    @property
    def session_cookie_httponly(self) -> bool:
        """会话 Cookie HTTP Only 标志"""
        return os.getenv("SESSION_COOKIE_HTTPONLY", "true").lower() == "true"
    
    @property
    def session_cookie_samesite(self) -> str:
        """会话 Cookie SameSite 策略"""
        return os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    
    # ========== 性能配置 ==========
    @property
    def cache_type(self) -> CacheType:
        """缓存类型"""
        cache_str = os.getenv("CACHE_TYPE", "simple").lower()
        try:
            return CacheType(cache_str)
        except ValueError:
            return CacheType.SIMPLE
    
    @property
    def cache_default_timeout(self) -> int:
        """缓存默认超时时间（秒）"""
        return int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))
    
    # ========== AI 服务配置 ==========
    @property
    def openai_api_key(self) -> Optional[str]:
        """OpenAI API 密钥"""
        return os.getenv("OPENAI_API_KEY")
    
    @property
    def openai_model(self) -> str:
        """OpenAI 模型"""
        return os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    @property
    def openai_max_tokens(self) -> int:
        """OpenAI 最大 tokens"""
        return int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    
    # ========== Git 配置 ==========
    @property
    def git_auto_commit(self) -> bool:
        """Git 自动提交"""
        return os.getenv("GIT_AUTO_COMMIT", "true").lower() == "true"
    
    @property
    def git_default_branch(self) -> str:
        """Git 默认分支"""
        return os.getenv("GIT_DEFAULT_BRANCH", "main")
    
    # ========== 测试配置 ==========
    @property
    def test_mode(self) -> bool:
        """测试模式开关"""
        return os.getenv("TEST_MODE", "false").lower() == "true"
    
    @property
    def test_neo4j_uri(self) -> str:
        """测试 Neo4j 数据库连接 URI"""
        return os.getenv("TEST_NEO4J_URI", "bolt://localhost:7688")
    
    @property
    def test_neo4j_user(self) -> str:
        """测试 Neo4j 用户名"""
        return os.getenv("TEST_NEO4J_USER", "neo4j")
    
    @property
    def test_neo4j_password(self) -> str:
        """测试 Neo4j 密码"""
        return os.getenv("TEST_NEO4J_PASSWORD", "testpassword")
    
    # ========== 计算属性 ==========
    @property
    def is_development(self) -> bool:
        """是否开发环境"""
        return self.app_env == Environment.DEVELOPMENT
    
    @property
    def is_testing(self) -> bool:
        """是否测试环境"""
        return self.app_env == Environment.TESTING
    
    @property
    def is_production(self) -> bool:
        """是否生产环境"""
        return self.app_env == Environment.PRODUCTION
    
    @property
    def project_root(self) -> Path:
        """项目根目录"""
        return Path(__file__).parent.parent.parent
    
    @property
    def log_dir(self) -> Path:
        """日志目录"""
        log_path = self.project_root / self.log_file
        return log_path.parent
    
    @property
    def temp_dir_path(self) -> Path:
        """临时目录路径"""
        return self.project_root / self.temp_dir
    
    # ========== 配置方法 ==========
    def get_neo4j_config(self, use_test_config: bool = False) -> Dict[str, Any]:
        """获取 Neo4j 配置"""
        if use_test_config or self.test_mode:
            return {
                "uri": self.test_neo4j_uri,
                "user": self.test_neo4j_user,
                "password": self.test_neo4j_password,
                "database": self.neo4j_database,
                "max_connection_pool_size": self.neo4j_max_connection_pool_size,
                "max_connection_lifetime": self.neo4j_max_connection_lifetime,
            }
        
        return {
            "uri": self.neo4j_uri,
            "user": self.neo4j_user,
            "password": self.neo4j_password,
            "database": self.neo4j_database,
            "max_connection_pool_size": self.neo4j_max_connection_pool_size,
            "max_connection_lifetime": self.neo4j_max_connection_lifetime,
        }
    
    def setup_logging(self):
        """设置日志配置"""
        # 创建日志目录
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=self.log_level.value,
            format=self.log_format,
            handlers=[
                logging.FileHandler(self.project_root / self.log_file),
                logging.StreamHandler()
            ]
        )
    
    def setup_directories(self):
        """创建必要的目录"""
        # 创建临时目录
        self.temp_dir_path.mkdir(parents=True, exist_ok=True)
        
        # 创建日志目录
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建其他必要目录
        (self.project_root / "domains").mkdir(exist_ok=True)
        (self.project_root / "ontology").mkdir(exist_ok=True)


# 全局配置实例
settings = Config()

# 导出常用配置
__all__ = [
    "Config",
    "settings",
    "Environment",
    "LogLevel",
    "CacheType",
]