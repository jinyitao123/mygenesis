# 游戏启动引导程序指南

## 概述

启动引导程序（Bootstrapper）是 Project Genesis v0.4 的新增功能，负责在游戏启动时自动部署指定的领域模块到 `ontology/` 目录。它实现了 `domains (源) → ontology (构建产物)` 的单向流动架构。

## 架构设计

### 设计原则
1. **单向流动**：domains 是源文件，ontology 是构建产物
2. **配置驱动**：通过环境变量或配置文件指定活动域
3. **安全第一**：部署前备份现有 ontology 文件
4. **错误处理**：部署失败时中止启动，提示用户检查

### 文件流程
```
domains/                          ontology/
├── supply_chain/                 ├── object_types.xml (← 复制)
│   ├── object_types.xml          ├── action_types.xml (← 复制)
│   ├── action_types.xml          ├── seed_data.xml    (← 复制)
│   ├── seed_data.xml             ├── synapser_patterns.xml (← 复制，可选)
│   ├── synapser_patterns.xml     └── config.json      (← 复制，可选)
│   └── config.json
├── healthcare/
├── it_ops/
└── ...
```

## 配置系统

### 配置文件：`game_config.json`
```json
{
  "active_domain": "supply_chain",
  "backup_before_deploy": true,
  "backup_retention_days": 7
}
```

### 配置优先级
1. **环境变量** `ACTIVE_DOMAIN`（最高优先级）
2. **配置文件** `game_config.json`
3. **默认值** `"supply_chain"`

### 环境变量示例
```bash
# Windows
set ACTIVE_DOMAIN=healthcare
python -m applications.game.main

# Linux/macOS
export ACTIVE_DOMAIN=it_ops
python -m applications.game.main
```

## 使用方法

### 1. 基本使用
```bash
# 使用默认配置（supply_chain）
python -m applications.game.main

# 使用环境变量指定域
set ACTIVE_DOMAIN=healthcare
python -m applications.game.main
```

### 2. 修改配置文件
编辑 `game_config.json`：
```json
{
  "active_domain": "healthcare",
  "backup_before_deploy": true,
  "backup_retention_days": 3
}
```

### 3. 查看可用域
```python
from applications.game.bootstrapper import GameBootstrapper
bootstrapper = GameBootstrapper(project_root=".")
domains = bootstrapper.list_available_domains()
print(f"可用域: {domains}")
```

### 4. 手动部署域
```python
from applications.game.bootstrapper import GameBootstrapper
bootstrapper = GameBootstrapper(project_root=".")
success = bootstrapper.deploy_domain("healthcare")
print(f"部署结果: {success}")
```

## 文件管理

### 必需文件
每个域目录必须包含以下 XML 文件：
- `object_types.xml` - 对象类型定义
- `action_types.xml` - 动作类型定义  
- `seed_data.xml` - 种子数据

### 可选文件
- `synapser_patterns.xml` - 意图映射模式
- `config.json` - 域特定配置

### 备份机制
- **备份位置**: `backups/ontology_backup_YYYYMMDD_HHMMSS/`
- **备份时机**: 每次部署前（可配置）
- **清理策略**: 默认保留7天内的备份

## 错误处理

### 常见错误及解决方案

#### 1. 域验证失败
```
错误：域 healthcare 缺少必需文件: ['object_types.xml']
```
**解决方案**：
- 检查 `domains/healthcare/` 目录是否存在必需文件
- 运行 `validate_domains.py` 验证域文件完整性

#### 2. 备份失败
```
错误：备份失败: [Errno 13] Permission denied
```
**解决方案**：
- 检查 `backups/` 目录权限
- 在配置中禁用备份：`"backup_before_deploy": false`

#### 3. 文件复制失败
```
错误：文件部署失败 object_types.xml: [Errno 2] No such file or directory
```
**解决方案**：
- 检查源文件路径和权限
- 确保 `ontology/` 目录存在且有写入权限

## 开发指南

### 添加新域
1. 在 `domains/` 下创建新目录，如 `my_domain/`
2. 添加必需文件：`object_types.xml`, `action_types.xml`, `seed_data.xml`
3. （可选）添加可选文件：`synapser_patterns.xml`, `config.json`
4. 更新 `game_config.json` 或设置环境变量使用新域

### 扩展引导程序
引导程序采用模块化设计，易于扩展：

```python
class ExtendedBootstrapper(GameBootstrapper):
    def __init__(self, project_root: str):
        super().__init__(project_root)
        # 添加自定义功能
        
    def custom_deployment(self):
        # 实现自定义部署逻辑
        pass
```

### 集成测试
```python
def test_bootstrapper():
    """引导程序单元测试"""
    bootstrapper = GameBootstrapper(project_root=".")
    
    # 测试配置读取
    domain = bootstrapper.get_active_domain()
    assert domain in bootstrapper.list_available_domains()
    
    # 测试域验证
    assert bootstrapper.validate_domain(domain) == True
    
    # 测试部署
    success = bootstrapper.deploy_active_domain()
    assert success == True
```

## 与现有系统的兼容性

### 向后兼容
- 引导程序不影响现有 `ontology/` 中的 JSON 文件
- `OntologyLoader` 仍支持 XML/JSON 双格式
- 现有游戏逻辑无需修改

### 编辑器集成
- Genesis Forge 编辑器继续编辑 `domains/` 中的 XML 文件
- 引导程序确保编辑器的修改在游戏启动时生效
- 支持热重载（重启游戏即可应用编辑器修改）

## 性能考虑

### 启动时间
- 文件复制：< 100ms（通常 < 50ms）
- 备份操作：< 200ms（取决于文件大小）
- 总引导时间：< 500ms

### 存储空间
- 备份文件：每次备份约 20-50KB
- 默认保留7天备份：约 140-350KB
- 可配置 `backup_retention_days` 控制存储使用

## 故障排除

### 日志查看
引导程序日志输出到控制台：
```
2026-02-09 19:53:39,816 - applications.game.bootstrapper - INFO - 开始部署活动域: supply_chain
2026-02-09 19:53:39,816 - applications.game.bootstrapper - INFO - 域验证通过: supply_chain
2026-02-09 19:53:39,823 - applications.game.bootstrapper - INFO - 已创建备份: ...\backups\ontology_backup_20260209_195339
2026-02-09 19:53:39,890 - applications.game.bootstrapper - INFO - 域部署完成: supply_chain
```

### 调试模式
设置日志级别为 DEBUG 查看更多信息：
```python
import logging
logging.getLogger("applications.game.bootstrapper").setLevel(logging.DEBUG)
```

## 未来扩展

### 计划功能
1. **增量部署**：只复制修改过的文件
2. **域混合**：支持多个域的混合部署
3. **远程域**：从远程仓库下载域定义
4. **版本控制**：域文件的版本管理和回滚

### API 扩展
```python
# 未来可能的 API
bootstrapper.deploy_domain_mix(["supply_chain", "healthcare"])
bootstrapper.rollback_to_backup("20260209_195339")
bootstrapper.sync_from_remote("https://github.com/user/domains.git")
```

## 总结

启动引导程序实现了：
- ✅ **架构清晰**：domains → ontology 单向流动
- ✅ **配置灵活**：环境变量 + 配置文件
- ✅ **安全可靠**：自动备份 + 错误处理
- ✅ **易于使用**：开箱即用，无需额外配置
- ✅ **扩展性强**：模块化设计，支持未来功能

通过引导程序，Project Genesis 实现了：
- 编辑器（Genesis Forge）专注于 domains 编辑
- 内核（GameEngine）专注于 ontology 读取
- 引导程序负责 domains → ontology 的同步

这种架构分离使得系统更灵活、更稳定、更易于维护。