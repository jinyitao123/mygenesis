"""
Domain Manager - 领域模组管理器

职责：
1. 管理 domains/ 目录下的所有领域模组
2. 处理领域切换和文件复制
3. 提供领域配置信息
4. 支持新领域创建

设计理念：插件化架构，多租户隔离
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DomainManager:
    """领域模组管理器"""
    
    def __init__(self, project_root: str):
        """
        初始化领域管理器
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root)
        self.domains_dir = self.project_root / "domains"
        self.ontology_dir = self.project_root / "ontology"
        
        # 确保目录存在
        self.domains_dir.mkdir(exist_ok=True)
        self.ontology_dir.mkdir(exist_ok=True)
        
        # 当前激活的领域
        self.active_domain = None
        
        # 领域文件映射
        self.file_mapping = {
            "schema": "object_types.xml",
            "seed": "seed_data.xml", 
            "actions": "action_types.xml",
            "patterns": "synapser_patterns.xml"
        }
        
        logger.info(f"DomainManager initialized: domains_dir={self.domains_dir}")
    
    def list_domains(self) -> List[str]:
        """
        列出所有可用的领域模组
        
        Returns:
            领域名称列表
        """
        domains = []
        for item in os.listdir(self.domains_dir):
            domain_path = self.domains_dir / item
            if domain_path.is_dir():
                # 检查是否有配置文件
                config_file = domain_path / "config.json"
                if config_file.exists():
                    domains.append(item)
        
        # 总是包含空白项目
        if "empty" not in domains:
            domains.append("empty")
        
        return sorted(domains)
    
    def get_domain_info(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """
        获取领域模组信息
        
        Args:
            domain_name: 领域名称
            
        Returns:
            领域信息字典，如果领域不存在则返回None
        """
        domain_path = self.domains_dir / domain_name
        
        if not domain_path.exists():
            logger.warning(f"Domain not found: {domain_name}")
            return None
        
        info = {
            "id": domain_name,
            "path": str(domain_path),
            "files": {},
            "config": {}
        }
        
        # 加载配置文件
        config_file = domain_path / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    info["config"] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config for {domain_name}: {e}")
        
        # 检查文件存在性
        for file_type, filename in self.file_mapping.items():
            file_path = domain_path / filename
            info["files"][file_type] = file_path.exists()
        
        return info
    
    def activate_domain(self, domain_name: str) -> bool:
        """
        激活领域模组 - 复制文件到 ontology 目录
        
        Args:
            domain_name: 要激活的领域名称
            
        Returns:
            是否成功激活
        """
        domain_path = self.domains_dir / domain_name
        
        if not domain_path.exists():
            logger.error(f"Domain not found: {domain_name}")
            return False
        
        # 如果是空白项目，创建默认文件
        if domain_name == "empty":
            return self._create_empty_ontology()
        
        try:
            copied_files = []
            missing_files = []
            
            # 复制领域文件到 ontology 目录
            for target_type, source_filename in self.file_mapping.items():
                source_file = domain_path / source_filename
                target_file = self.ontology_dir / source_filename
                
                if source_file.exists():
                    shutil.copy2(source_file, target_file)
                    copied_files.append(source_filename)
                else:
                    missing_files.append(source_filename)
            
            # 记录结果
            if copied_files:
                logger.info(f"Activated domain '{domain_name}': copied {len(copied_files)} files")
                for f in copied_files:
                    logger.debug(f"  Copied: {f}")
            
            if missing_files:
                logger.warning(f"Domain '{domain_name}' missing files: {', '.join(missing_files)}")
            
            self.active_domain = domain_name
            logger.info(f"Activated domain: {domain_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate domain {domain_name}: {e}")
            return False
    
    def create_domain(self, domain_name: str, template: str = "empty") -> bool:
        """
        创建新的领域模组
        
        Args:
            domain_name: 新领域名称
            template: 模板类型 ("empty" 或现有领域名称)
            
        Returns:
            是否成功创建
        """
        if domain_name in self.list_domains():
            logger.error(f"Domain already exists: {domain_name}")
            return False
        
        new_domain_path = self.domains_dir / domain_name
        new_domain_path.mkdir(exist_ok=True)
        
        try:
            # 创建配置文件
            config = {
                "domain_id": domain_name,
                "name": domain_name,
                "description": f"{domain_name} 领域模组",
                "version": "1.0.0",
                "author": "Genesis Forge",
                "created_at": "2026-02-05",
                "ui_config": {
                    "primary_color": "#6b7280",
                    "secondary_color": "#9ca3af",
                    "accent_color": "#d1d5db"
                },
                "features": {
                    "object_types": [],
                    "action_types": [],
                    "relation_types": []
                }
            }
            
            config_file = new_domain_path / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 如果是基于模板创建，复制模板文件
            if template != "empty" and template in self.list_domains():
                template_path = self.domains_dir / template
                for filename in self.file_mapping.values():
                    source_file = template_path / filename
                    if source_file.exists():
                        target_file = new_domain_path / filename
                        shutil.copy2(source_file, target_file)
            
            # 否则创建空文件
            else:
                self._create_empty_files(new_domain_path)
            
            logger.info(f"Created domain: {domain_name} (template: {template})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create domain {domain_name}: {e}")
            # 清理失败创建
            if new_domain_path.exists():
                shutil.rmtree(new_domain_path)
            return False
    
    def delete_domain(self, domain_name: str) -> bool:
        """
        删除领域模组
        
        Args:
            domain_name: 要删除的领域名称
            
        Returns:
            是否成功删除
        """
        if domain_name == "empty":
            logger.error("Cannot delete 'empty' domain")
            return False
        
        domain_path = self.domains_dir / domain_name
        
        if not domain_path.exists():
            logger.error(f"Domain not found: {domain_name}")
            return False
        
        try:
            shutil.rmtree(domain_path)
            logger.info(f"Deleted domain: {domain_name}")
            
            # 如果删除的是当前激活的领域，切换到默认领域
            if self.active_domain == domain_name:
                self.activate_domain("supply_chain")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete domain {domain_name}: {e}")
            return False
    
    def get_active_domain_files(self) -> Dict[str, str]:
        """
        获取当前激活领域的文件内容
        
        Returns:
            文件类型到文件内容的映射
        """
        if not self.active_domain:
            return {}
        
        files = {}
        
        # 优先从 ontology 目录读取（激活后复制的文件）
        for file_type, filename in self.file_mapping.items():
            file_path = self.ontology_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[file_type] = f.read()
                except Exception as e:
                    logger.error(f"Failed to read {file_path}: {e}")
                    files[file_type] = ""
            else:
                # 如果 ontology 目录没有，回退到 domains 目录
                domain_path = self.domains_dir / self.active_domain
                fallback_path = domain_path / filename
                if fallback_path.exists():
                    try:
                        with open(fallback_path, 'r', encoding='utf-8') as f:
                            files[file_type] = f.read()
                    except Exception as e:
                        logger.error(f"Failed to read {fallback_path}: {e}")
                        files[file_type] = ""
                else:
                    files[file_type] = ""
        
        return files
    
    def get_domain_files(self, domain_name: str) -> Dict[str, str]:
        """
        获取指定领域的文件内容
        
        Args:
            domain_name: 领域名称
            
        Returns:
            文件类型到文件内容的映射
        """
        domain_path = self.domains_dir / domain_name
        
        if not domain_path.exists():
            logger.warning(f"Domain not found: {domain_name}")
            return {}
        
        files = {}
        
        for file_type, filename in self.file_mapping.items():
            file_path = domain_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[file_type] = f.read()
                except Exception as e:
                    logger.error(f"Failed to read {file_path}: {e}")
                    files[file_type] = ""
            else:
                files[file_type] = ""
        
        return files
    
    def save_domain_file(self, domain_name: str, file_type: str, content: str) -> bool:
        """
        保存领域文件
        
        Args:
            domain_name: 领域名称
            file_type: 文件类型 ("schema", "seed", "actions", "patterns")
            content: 文件内容
            
        Returns:
            是否成功保存
        """
        if file_type not in self.file_mapping:
            logger.error(f"Invalid file type: {file_type}")
            return False
        
        domain_path = self.domains_dir / domain_name
        if not domain_path.exists():
            logger.error(f"Domain not found: {domain_name}")
            return False
        
        filename = self.file_mapping[file_type]
        
        # 保存到 domains 目录（原始文件）
        domain_file_path = domain_path / filename
        
        # 保存到 ontology 目录（当前激活文件）
        ontology_file_path = self.ontology_dir / filename
        
        try:
            # 保存到 domains 目录
            with open(domain_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 如果当前激活的是这个领域，也保存到 ontology 目录
            if self.active_domain == domain_name:
                with open(ontology_file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            logger.info(f"Saved {filename} for domain {domain_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save {domain_file_path}: {e}")
            return False
    
    def _create_empty_ontology(self) -> bool:
        """创建空白本体文件到 ontology 目录"""
        try:
            empty_schema = """<?xml version="1.0" encoding="UTF-8"?>
<ObjectTypes domain="empty">
    <Version>1.0.0</Version>
    <Description>空白本体项目 - 从零开始定义</Description>
    
    <!-- 在此处添加您的对象类型定义 -->
    <!-- 示例：
    <ObjectType name="Entity" display_name="实体" primary_key="id" color="#3b82f6" icon="cube">
        <Property name="id" type="string" required="true" description="唯一标识符"/>
        <Property name="name" type="string" description="名称"/>
    </ObjectType>
    -->
    
    <LinkTypes>
        <!-- 在此处添加关系类型定义 -->
        <!-- 示例：
        <LinkType name="RELATED_TO" display_name="关联到" description="实体之间的关联关系" 
                  source="any" target="any" bidirectional="true" color="#6b7280"/>
        -->
    </LinkTypes>
</ObjectTypes>"""
            
            empty_seed = """<?xml version="1.0" encoding="UTF-8"?>
<World domain="empty">
    <Version>1.0.0</Version>
    <Description>空白数据项目</Description>
    
    <Nodes>
        <!-- 在此处添加节点数据 -->
    </Nodes>
    
    <Links>
        <!-- 在此处添加关系数据 -->
    </Links>
</World>"""
            
            empty_actions = """<?xml version="1.0" encoding="UTF-8"?>
<ActionTypes>
    <Version>1.0.0</Version>
    <Description>空白动作定义</Description>
    
    <!-- 在此处添加动作类型定义 -->
</ActionTypes>"""
            
            empty_patterns = """<?xml version="1.0" encoding="UTF-8"?>
<SynapserPatterns>
    <Version>1.0.0</Version>
    <Description>空白意图映射</Description>
    
    <!-- 在此处添加意图模式定义 -->
</SynapserPatterns>"""
            
            # 写入文件
            files_content = {
                "object_types.xml": empty_schema,
                "seed_data.xml": empty_seed,
                "action_types.xml": empty_actions,
                "synapser_patterns.xml": empty_patterns
            }
            
            for filename, content in files_content.items():
                file_path = self.ontology_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            self.active_domain = "empty"
            logger.info("Created empty ontology files")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create empty ontology: {e}")
            return False
    
    def _create_empty_files(self, domain_path: Path):
        """在指定路径创建空文件"""
        for filename in self.file_mapping.values():
            file_path = domain_path / filename
            if filename == "object_types.xml":
                content = f'<?xml version="1.0" encoding="UTF-8"?>\n<ObjectTypes domain="{domain_path.name}">\n</ObjectTypes>'
            elif filename == "seed_data.xml":
                content = f'<?xml version="1.0" encoding="UTF-8"?>\n<World domain="{domain_path.name}">\n</World>'
            else:
                content = f'<?xml version="1.0" encoding="UTF-8"?>\n<{filename.split(".")[0].title()}>\n</{filename.split(".")[0].title()}>'
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)