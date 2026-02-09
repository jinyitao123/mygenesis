"""
Game Bootstrapper - 游戏启动引导器

职责：
- 在游戏启动时自动部署指定的领域模块
- 将 domains/{domain}/ 下的 XML 文件复制到 ontology/ 目录
- 支持配置管理和备份机制
- 确保内核只读取 ontology/ 目录，保持架构清晰

设计原则：
1. 单向流动：domains (源) → ontology (构建产物)
2. 配置驱动：通过环境变量或 game_config.json 指定活动域
3. 安全第一：部署前备份现有 ontology 文件
4. 错误处理：部署失败时中止启动，提示用户检查
"""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class GameBootstrapper:
    """游戏启动引导器 - 负责领域模块的部署和配置管理"""

    def __init__(self, project_root: str):
        """
        初始化引导器

        Args:
            project_root: 项目根目录路径
        """
        self.root = Path(project_root)
        self.domains_dir = self.root / "domains"
        self.ontology_dir = self.root / "ontology"
        self.backup_dir = self.root / "backups"
        self.config_path = self.root / "game_config.json"

        # 必需的文件列表（必须存在于 domains/{domain}/ 目录）
        self.required_files = [
            "object_types.xml",
            "action_types.xml",
            "seed_data.xml"
        ]

        # 可选的文件列表（如果存在则复制）
        self.optional_files = [
            "synapser_patterns.xml",
            "config.json"
        ]

        # 确保目录存在
        self.backup_dir.mkdir(exist_ok=True)

    def get_active_domain(self) -> str:
        """
        获取活动域配置（环境变量优先，配置文件次之）

        Returns:
            活动域名称，默认返回 "supply_chain"
        """
        # 1. 检查环境变量
        env_domain = os.getenv("ACTIVE_DOMAIN")
        if env_domain:
            logger.info(f"使用环境变量指定的活动域: {env_domain}")
            return env_domain

        # 2. 检查配置文件
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                config_domain = config.get("active_domain")
                if config_domain:
                    logger.info(f"使用配置文件指定的活动域: {config_domain}")
                    return config_domain
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"配置文件读取失败: {e}")

        # 3. 默认值
        default_domain = "supply_chain"
        logger.info(f"使用默认活动域: {default_domain}")
        return default_domain

    def create_backup(self) -> Optional[Path]:
        """
        备份现有 ontology 目录

        Returns:
            备份目录路径，失败时返回 None
        """
        if not self.ontology_dir.exists():
            logger.info("ontology 目录不存在，无需备份")
            return None

        # 检查 ontology 目录是否为空
        if not any(self.ontology_dir.iterdir()):
            logger.info("ontology 目录为空，无需备份")
            return None

        # 创建备份目录（使用时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"ontology_backup_{timestamp}"

        try:
            # 复制整个 ontology 目录
            shutil.copytree(self.ontology_dir, backup_path)
            logger.info(f"已创建备份: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"备份失败: {e}")
            return None

    def validate_domain(self, domain_name: str) -> bool:
        """
        验证指定域是否有效

        Args:
            domain_name: 域名称

        Returns:
            是否有效
        """
        domain_path = self.domains_dir / domain_name

        if not domain_path.exists():
            logger.error(f"域目录不存在: {domain_path}")
            return False

        if not domain_path.is_dir():
            logger.error(f"域路径不是目录: {domain_path}")
            return False

        # 检查必需文件
        missing_files = []
        for filename in self.required_files:
            file_path = domain_path / filename
            if not file_path.exists():
                missing_files.append(filename)

        if missing_files:
            logger.error(f"域 {domain_name} 缺少必需文件: {missing_files}")
            return False

        logger.info(f"域验证通过: {domain_name}")
        return True

    def deploy_file(self, source_path: Path, target_path: Path) -> bool:
        """
        部署单个文件

        Args:
            source_path: 源文件路径
            target_path: 目标文件路径

        Returns:
            是否部署成功
        """
        try:
            # 确保目标目录存在
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 复制文件
            shutil.copy2(source_path, target_path)
            logger.debug(f"已部署: {source_path.name}")
            return True
        except Exception as e:
            logger.error(f"文件部署失败 {source_path.name}: {e}")
            return False

    def deploy_domain(self, domain_name: str) -> bool:
        """
        部署指定域到 ontology 目录

        Args:
            domain_name: 域名称

        Returns:
            是否部署成功
        """
        domain_path = self.domains_dir / domain_name

        # 部署必需文件
        for filename in self.required_files:
            source = domain_path / filename
            target = self.ontology_dir / filename

            if not self.deploy_file(source, target):
                logger.error(f"必需文件部署失败: {filename}")
                return False

        # 部署可选文件
        for filename in self.optional_files:
            source = domain_path / filename
            if source.exists():
                target = self.ontology_dir / filename
                self.deploy_file(source, target)
            else:
                logger.debug(f"可选文件不存在，跳过: {filename}")

        logger.info(f"域部署完成: {domain_name}")
        return True

    def cleanup_old_backups(self, retention_days: int = 7):
        """
        清理旧的备份文件

        Args:
            retention_days: 保留天数，默认7天
        """
        if not self.backup_dir.exists():
            return

        cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)

        for backup_item in self.backup_dir.iterdir():
            if backup_item.is_dir() and backup_item.name.startswith("ontology_backup_"):
                try:
                    # 从目录名解析时间戳
                    timestamp_str = backup_item.name.replace("ontology_backup_", "")
                    backup_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S").timestamp()

                    if backup_time < cutoff_time:
                        shutil.rmtree(backup_item)
                        logger.info(f"已清理旧备份: {backup_item.name}")
                except (ValueError, OSError) as e:
                    logger.warning(f"清理备份失败 {backup_item.name}: {e}")

    def deploy_active_domain(self) -> bool:
        """
        部署活动域（主入口方法）

        Returns:
            是否部署成功
        """
        try:
            # 1. 获取活动域
            active_domain = self.get_active_domain()
            logger.info(f"开始部署活动域: {active_domain}")

            # 2. 验证域
            if not self.validate_domain(active_domain):
                logger.error(f"域验证失败: {active_domain}")
                return False

            # 3. 读取配置（决定是否备份）
            backup_enabled = True
            if self.config_path.exists():
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    backup_enabled = config.get("backup_before_deploy", True)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"配置文件读取失败，使用默认设置: {e}")

            # 4. 备份现有文件
            if backup_enabled:
                backup_path = self.create_backup()
                if backup_path is None:
                    logger.warning("备份失败，但继续部署...")
            else:
                logger.info("配置禁用备份，跳过备份步骤")

            # 5. 部署域
            if not self.deploy_domain(active_domain):
                logger.error("域部署失败")
                return False

            # 6. 清理旧备份
            retention_days = 7
            if self.config_path.exists():
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    retention_days = config.get("backup_retention_days", 7)
                except (json.JSONDecodeError, KeyError):
                    pass

            self.cleanup_old_backups(retention_days)

            logger.info("引导程序执行完成")
            return True

        except Exception as e:
            logger.error(f"引导程序执行失败: {e}")
            return False

    def create_default_config(self) -> bool:
        """
        创建默认配置文件

        Returns:
            是否创建成功
        """
        default_config = {
            "active_domain": "supply_chain",
            "backup_before_deploy": True,
            "backup_retention_days": 7,
            "description": "游戏配置 - 指定活动域和备份设置"
        }

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"已创建默认配置文件: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"创建配置文件失败: {e}")
            return False

    def list_available_domains(self) -> List[str]:
        """
        列出所有可用的域

        Returns:
            域名称列表
        """
        domains = []
        if not self.domains_dir.exists():
            return domains

        for item in self.domains_dir.iterdir():
            if item.is_dir():
                # 检查是否包含必需文件
                has_required = all(
                    (item / filename).exists()
                    for filename in self.required_files
                )
                if has_required:
                    domains.append(item.name)

        return sorted(domains)

    def get_domain_info(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """
        获取域的详细信息

        Args:
            domain_name: 域名称

        Returns:
            域信息字典，失败时返回 None
        """
        domain_path = self.domains_dir / domain_name

        if not domain_path.exists():
            return None

        info = {
            "name": domain_name,
            "path": str(domain_path),
            "required_files": {},
            "optional_files": {},
            "config": None
        }

        # 检查必需文件
        for filename in self.required_files:
            file_path = domain_path / filename
            info["required_files"][filename] = {
                "exists": file_path.exists(),
                "size": file_path.stat().st_size if file_path.exists() else 0
            }

        # 检查可选文件
        for filename in self.optional_files:
            file_path = domain_path / filename
            if file_path.exists():
                info["optional_files"][filename] = {
                    "size": file_path.stat().st_size
                }

        # 读取域配置
        config_path = domain_path / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    info["config"] = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        return info