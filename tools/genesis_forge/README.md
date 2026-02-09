# Genesis Forge Studio

**基于 MDA (Model-Driven Architecture) 架构的可视化仿真世界构建平台**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.4-brightgreen.svg)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0-008CC1.svg)](https://neo4j.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 项目概述

Genesis Forge Studio 是一个企业级可视化仿真世界构建平台，基于 **MDA (Model-Driven Architecture)** 架构设计。它将传统的代码编辑器升级为专业的可视化开发环境，支持游戏策划、仿真工程师等专业用户高效创建和管理复杂的仿真系统。

### 核心特性

- **🔧 MDA三层架构**: 完整的 CIM/PIM/PSM 模型转换流程
- **🎨 可视化编辑器**: 基于 Cytoscape.js 的交互式图谱编辑
- **🤖 AI Copilot**: 上下文感知的智能辅助设计
- **⚡ 实时预览**: 沙箱环境即时验证规则逻辑
- **🔗 Git-Ops 流程**: 完整的版本控制和团队协作支持
- **📊 多领域支持**: 供应链、智慧城市、医疗健康、金融风控等预置领域模板

## 🏗️ 架构设计

### MDA 三层架构

| 层次 | Genesis 对应概念 | 描述 |
|------|------------------|------|
| **CIM** (计算无关模型) | **Domain Concepts** | 业务领域的概念模型（如：供应链节点、RPG角色、智慧城市交通流） |
| **PIM** (平台无关模型) | **Ontology Layer** | 定义在 JSON/XML 中的逻辑：`Object Types`, `Action Rules`, `Synapser Patterns` |
| **PSM** (平台特定模型) | **Kernel Runtime** | 具体的执行实现：Python 对象实例、Neo4j 图数据、Cypher 查询语句 |

### 技术栈

**后端 (Flask + Pydantic)**
- **Web框架**: Flask 3.0.0
- **数据验证**: Pydantic v2
- **图数据库**: Neo4j 5.0 (通过 `genesis.kernel` 模块集成)
- **版本控制**: GitPython
- **异步任务**: Celery (可选)

**前端 (Vue 3 + TypeScript)**
- **框架**: Vue 3 + Composition API
- **语言**: TypeScript 5.0
- **构建工具**: Vite 5.0
- **状态管理**: Pinia
- **可视化**: Cytoscape.js (图谱), Monaco Editor (代码)
- **样式**: Tailwind CSS 3.0

**测试与部署**
- **后端测试**: pytest + coverage
- **前端测试**: Playwright (E2E)
- **容器化**: Docker + docker-compose
- **CI/CD**: GitHub Actions (预留)

## 📁 项目结构

```
tools/genesis_forge/
├── backend/                    # Flask 后端服务
│   ├── api/
│   │   ├── app_studio.py      # 主应用入口 (Flask App)
│   │   └── __init__.py
│   ├── core/                   # 核心引擎模块
│   │   ├── models.py          # Pydantic 数据模型定义
│   │   ├── schema_engine_v5.py    # Schema 引擎 (元模型管理)
│   │   ├── validation_engine.py   # 验证引擎 (完整性检查)
│   │   ├── mda_transformer.py     # MDA 转换器 (CIM→PIM→PSM)
│   │   ├── async_task_manager.py  # 异步任务管理
│   │   ├── cypher_validator.py    # Cypher 语法验证
│   │   ├── transaction_manager.py # 事务管理
│   │   ├── request_context.py     # 请求上下文管理
│   │   ├── exceptions.py          # 自定义异常类
│   │   └── __init__.py
│   ├── services/              # 业务服务层
│   │   ├── ontology_service.py    # 本体管理服务
│   │   ├── world_service.py       # 世界仿真服务
│   │   ├── ai_copilot_enhanced.py # AI Copilot 服务 (增强版)
│   │   ├── rule_engine.py         # ECA 规则引擎
│   │   ├── eca_rule_engine_simple.py  # 简化版规则引擎
│   │   ├── git_ops.py             # Git 操作服务
│   │   ├── domain_manager.py      # 领域管理器
│   │   ├── neo4j_loader.py        # Neo4j 数据加载器
│   │   ├── neo4j_service.py       # Neo4j 服务封装
│   │   ├── data_engine.py         # 数据引擎
│   │   └── __init__.py
│   ├── static/                 # 静态资源
│   │   └── js/
│   │       └── studio.js      # 传统前端 JavaScript
│   ├── templates/              # HTML 模板
│   │   ├── launcher.html      # 启动页面
│   │   └── studio.html        # 传统 IDE 界面
│   └── tests/                  # 后端测试
│       ├── unit/               # 单元测试
│       ├── integration/        # 集成测试
│       ├── test_frontend.py    # 前端集成测试
│       ├── test_frontend_ui.py # UI 测试
│       └── conftest.py         # pytest 配置
│
├── frontend/                   # Vue 3 现代化前端 (推荐使用)
│   ├── src/
│   │   ├── components/         # Vue 组件
│   │   │   ├── layout/        # 布局组件
│   │   │   │   ├── TopBar.vue          # 顶部工具栏
│   │   │   │   ├── SideBar.vue         # 左侧导航栏
│   │   │   │   ├── MainCanvas.vue      # 主画布区域
│   │   │   │   ├── PropertyPanel.vue   # 右侧属性面板
│   │   │   │   └── BottomPanel.vue     # 底部面板
│   │   │   ├── studio/        # 编辑器组件
│   │   │   │   ├── GraphEditor.vue     # 图谱编辑器
│   │   │   │   ├── LogicComposer.vue   # 逻辑编排器
│   │   │   │   ├── CodeEditor.vue      # 代码编辑器
│   │   │   │   └── ImportWizard.vue    # 导入向导
│   │   │   └── ui/            # UI 基础组件
│   │   │       ├── Button.vue
│   │   │       ├── Modal.vue
│   │   │       └── Tooltip.vue
│   │   ├── composables/       # Vue 组合式函数
│   │   │   ├── useCytoscape.ts  # Cytoscape.js 集成
│   │   │   ├── useMonaco.ts     # Monaco Editor 集成
│   │   │   ├── useApi.ts        # API 调用封装
│   │   │   └── useCopilot.ts    # AI Copilot 集成
│   │   ├── stores/            # Pinia 状态管理
│   │   │   ├── project.ts       # 项目状态
│   │   │   ├── editor.ts        # 编辑器状态
│   │   │   └── ui.ts           # UI 状态
│   │   ├── types/             # TypeScript 类型定义
│   │   │   ├── ontology.ts      # 本体数据类型
│   │   │   ├── api.ts           # API 接口类型
│   │   │   └── cytoscape.ts     # Cytoscape 类型
│   │   ├── assets/            # 静态资源
│   │   ├── utils/             # 工具函数
│   │   ├── App.vue            # 根组件
│   │   ├── main.ts            # 应用入口
│   │   └── style.css          # 全局样式
│   ├── tests/                 # 前端测试
│   │   └── user-journey.spec.ts  # Playwright E2E 测试
│   ├── public/                # 公共静态资源
│   ├── package.json           # 依赖配置
│   ├── vite.config.ts         # Vite 配置
│   ├── tsconfig.json          # TypeScript 配置
│   ├── playwright.config.ts   # Playwright 配置
│   └── tailwind.config.js     # Tailwind CSS 配置
│
├── domains/                    # 领域配置数据
│   └── supply_chain/          # 供应链领域示例
│       ├── config.json        # 领域配置
│       ├── schema.json        # 领域 Schema
│       ├── seed.json          # 种子数据
│       ├── actions.json       # 动作定义
│       └── patterns.json      # 模式定义
│
├── docs/                       # 项目文档
│   ├── Genesis Studio PRP.md              # 产品参考规划 (核心设计)
│   ├── Genesis Forge (Studio Edition) - 前端详细设计文档 (FDD).md
│   ├── COMPLETE_IMPLEMENTATION.md         # 完整实现总结
│   ├── DEVELOPMENT_SUMMARY.md             # 开发总结
│   ├── README_OPTIMIZATION.md             # README 优化建议
│   └── test_plan/                         # 测试计划文档
│       ├── Genesis Forge (Studio Edition) - 前端功能测试设计.md
│       ├── Genesis Forge (Studio Edition) - 测试设计规格说明书.md
│       ├── Mock LLM (Replay 模式) 实现方案.md
│       └── test_domain_fixtures 数据集方案.md
│
├── ai_skills/                  # AI Copilot 技能定义
│   ├── schema_aware_prompt.txt  # 上下文感知提示词
│   └── cypher_generator.py      # Cypher 生成器
│
├── config/                     # 配置文件
│   ├── requirements.txt       # Python 依赖列表
│   └── pytest.ini            # pytest 配置
│
├── scripts/                    # 实用脚本
│   ├── start_studio.bat      # Windows 启动脚本
│   ├── test_api.py           # API 测试脚本
│   └── test_system.py        # 系统测试脚本
│
└── README.md                   # 项目说明 (本文件)
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.10 或更高版本
- **Node.js**: 18.x 或更高版本
- **Git**: 2.30+ (用于版本控制功能)
- **Neo4j**: 5.0+ (可选，用于图数据库功能)
- **PostgreSQL**: 14+ (可选，用于事件日志和语义记忆)

### 安装步骤

1. **克隆项目并进入目录**
   ```bash
   cd tools/genesis_forge
   ```

2. **安装 Python 依赖**
   ```bash
   pip install -r config/requirements.txt
   ```

3. **安装前端依赖** (使用现代化 Vue 3 前端)
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### 启动服务

#### 选项1: 传统模式 (单进程)
```bash
# 启动 Flask 后端服务
python backend/api/app_studio.py

# 服务将在 http://localhost:5000 启动
# 访问 http://localhost:5000 使用传统界面
```

#### 选项2: 现代化开发模式 (推荐)
```bash
# 终端1: 启动 Flask 后端
python backend/api/app_studio.py

# 终端2: 启动 Vue 3 前端开发服务器
cd frontend
npm run dev

# 前端将在 http://localhost:3000 启动
# 访问 http://localhost:3000 使用现代化界面
```

#### 选项3: 使用启动脚本 (Windows)
```bash
# 双击运行 scripts/start_studio.bat
# 或从命令行执行
scripts/start_studio.bat
```

### 配置 Neo4j 连接 (可选)

如果需要图数据库功能，请配置 Neo4j 连接：

1. 确保 Neo4j 数据库正在运行
2. 在 `backend/api/app_studio.py` 中配置连接参数：
   ```python
   NEO4J_URI = "bolt://localhost:7687"
   NEO4J_USER = "neo4j"
   NEO4J_PASSWORD = "your_password"
   ```

### 运行测试

```bash
# 后端单元测试
pytest backend/tests/unit/

# 后端集成测试
pytest backend/tests/integration/

# 前端 E2E 测试 (需要先启动前端)
cd frontend
npm run test:e2e

# 运行所有测试
pytest backend/tests/
cd frontend && npm run test
```

## 🏗️ 核心架构

### MDA 三层架构实现

Genesis Forge Studio 实现了完整的 MDA (Model-Driven Architecture) 架构：

#### 1. CIM (计算无关模型) - Domain Concepts
- **定位**: 业务领域的概念模型
- **存储位置**: `domains/` 目录下的配置文件
- **示例**: 供应链节点、RPG角色、智慧城市交通流等业务概念
- **文件格式**: JSON/XML 配置文件

#### 2. PIM (平台无关模型) - Ontology Layer
- **定位**: 平台无关的逻辑定义层
- **核心组件**: 
  - `ObjectTypeDefinition`: 实体类型定义
  - `RelationshipDefinition`: 关系定义
  - `ActionTypeDefinition`: 动作类型定义
  - `WorldSnapshot`: 世界快照数据
- **技术实现**: `backend/core/` 中的核心引擎
- **业务服务**: `backend/services/` 中的原子服务

#### 3. PSM (平台特定模型) - Kernel Runtime
- **定位**: 具体平台的执行实现
- **运行时组件**:
  - Python 对象实例 (内存中的实体对象)
  - Neo4j 图数据 (持久化的图谱状态)
  - Cypher 查询语句 (图数据库操作)
  - PostgreSQL 事件日志 (审计和记忆)
- **转换机制**: `mda_transformer.py` 负责 PIM→PSM 转换

### 原子服务架构

项目采用微服务风格的模块化设计，包含以下核心服务：

#### OntologyService (本体管理服务)
- **职责**: 管理 JSON/XML 本体文件的 CRUD 操作
- **核心方法**: `load_schema()`, `save_entity()`, `get_version_history()`
- **位置**: `backend/services/ontology_service.py`

#### WorldService (世界仿真服务)
- **职责**: 与 Neo4j 交互，提供图谱预览和沙箱执行
- **核心方法**: `preview_graph()`, `validate_connectivity()`, `reset_seed_data()`
- **位置**: `backend/services/world_service.py`

#### CopilotService (智能辅助服务)
- **职责**: 集成 LLM，提供生成式设计能力
- **核心方法**: `generate_npc()`, `text_to_cypher()`, `suggest_actions()`
- **位置**: `backend/services/ai_copilot_enhanced.py`

#### RuleExecutionService (规则引擎服务)
- **职责**: 提供轻量级的 Action 模拟运行环境
- **核心方法**: `simulate_action()`, `validate_rule()`
- **位置**: `backend/services/rule_engine.py`

#### GitOpsService (Git 操作服务)
- **职责**: 版本控制和团队协作支持
- **核心方法**: `commit_changes()`, `get_history()`, `revert_to_version()`
- **位置**: `backend/services/git_ops.py`

### 前端架构设计

#### 现代化 Vue 3 架构
- **组件化设计**: 基于 Vue 3 Composition API 的模块化组件
- **状态管理**: Pinia 驱动的响应式状态管理
- **类型安全**: 完整的 TypeScript 类型定义
- **构建优化**: Vite 提供的极速热重载和构建性能

#### 核心编辑器组件
1. **GraphEditor**: 基于 Cytoscape.js 的交互式图谱编辑器
2. **LogicComposer**: 可视化 ECA 规则编排器
3. **CodeEditor**: 基于 Monaco Editor 的代码编辑器
4. **ImportWizard**: CSV/Excel 数据导入向导

#### 响应式布局系统
- **三栏布局**: 左侧导航 + 中间主画布 + 右侧属性面板
- **自适应设计**: 支持不同屏幕尺寸的响应式适配
- **深色模式**: 优先的视觉设计，减少视觉疲劳

### 数据流架构

```
用户操作 → 前端组件 → API调用 → 后端服务 → 数据验证 → 持久化存储
    ↑          ↓          ↑         ↓          ↑           ↓
状态更新 ← 响应处理 ← 结果返回 ← 业务逻辑 ← 规则执行 ← 数据加载
```

### 安全架构

#### 输入验证层
- **Schema 验证**: Pydantic 强类型数据验证
- **Cypher 注入防护**: 预编译查询和参数化语句
- **路径遍历防护**: 严格的文件路径验证

#### 错误处理系统
- **统一错误码**: `ERR_SCHEMA_01`, `ERR_CYPHER_02`, `ERR_REF_03`
- **分级处理**: 前端提示 → 日志记录 → 管理员告警
- **事务回滚**: 原子性操作保证数据一致性

### 扩展性设计

#### 插件系统架构
- **插件接口**: 标准化的插件注册和生命周期管理
- **热加载**: 运行时插件加载和卸载
- **依赖管理**: 插件间的依赖关系解析

#### 领域扩展机制
- **领域模板**: 预置的领域配置模板
- **自定义领域**: 用户自定义领域配置
- **导入导出**: 领域配置的标准化导入导出

## 📚 API 文档

### RESTful API 设计

所有 API 端点遵循 RESTful 设计原则，使用 JSON 格式进行数据交换。

#### 基础信息
- **API 版本**: v1
- **基础路径**: `/api/v1`
- **认证方式**: Session-based 认证 (预留 JWT 支持)
- **响应格式**: 统一 JSON 响应格式

### 核心 API 端点

#### 1. 领域管理 API

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/v1/domains` | 获取所有可用领域 | - | `{ "domains": ["supply_chain", "smart_city", ...] }` |
| GET | `/api/v1/{domain}/info` | 获取领域详细信息 | - | `{ "name": "...", "description": "...", "object_count": 10 }` |
| POST | `/api/v1/domains` | 创建新领域 | `{ "name": "...", "template": "..." }` | `{ "domain_id": "...", "status": "created" }` |

#### 2. 本体管理 API

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/v1/{domain}/objects` | 获取领域所有对象类型 | - | `{ "objects": [{...}, ...] }` |
| GET | `/api/v1/{domain}/objects/{type_key}` | 获取特定对象类型 | - | `{ "type_key": "...", "properties": {...} }` |
| POST | `/api/v1/{domain}/objects` | 创建/更新对象类型 | `{ "type_key": "...", "properties": {...} }` | `{ "status": "saved", "validation": {...} }` |
| DELETE | `/api/v1/{domain}/objects/{type_key}` | 删除对象类型 | - | `{ "status": "deleted" }` |
| GET | `/api/v1/{domain}/actions` | 获取所有动作类型 | - | `{ "actions": [{...}, ...] }` |
| POST | `/api/v1/{domain}/actions` | 创建/更新动作类型 | `{ "action_id": "...", "validation": "...", "rules": [...] }` | `{ "status": "saved" }` |

#### 3. 图谱数据 API

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/v1/{domain}/graph` | 获取可视化图谱数据 | - | `{ "nodes": [...], "edges": [...] }` |
| GET | `/api/v1/{domain}/graph/statistics` | 获取图谱统计信息 | - | `{ "node_count": 10, "edge_count": 15, ... }` |
| POST | `/api/v1/{domain}/graph/preview` | 预览图谱变更 | `{ "nodes": [...], "edges": [...] }` | `{ "preview": {...}, "warnings": [...] }` |
| POST | `/api/v1/{domain}/graph/validate` | 验证图谱完整性 | - | `{ "valid": true, "issues": [] }` |

#### 4. 仿真与调试 API

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/v1/simulation/sandbox/execute` | 沙箱试运行动作 | `{ "action": "ACT_ATTACK", "params": {...} }` | `{ "result": {...}, "changes": [...] }` |
| POST | `/api/v1/simulation/reset` | 重置仿真状态 | - | `{ "status": "reset" }` |
| GET | `/api/v1/simulation/state` | 获取当前仿真状态 | - | `{ "state": {...} }` |
| POST | `/api/v1/system/hot-reload` | 触发热重载 | `{ "domain": "..." }` | `{ "status": "reloaded" }` |

#### 5. AI Copilot API

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/v1/copilot/generate` | 生成内容 | `{ "type": "npc\|action\|cypher", "prompt": "..." }` | `{ "content": {...}, "suggestions": [...] }` |
| POST | `/api/v1/copilot/text-to-cypher` | 自然语言转 Cypher | `{ "text": "攻击那个兽人", "context": {...} }` | `{ "cypher": "...", "explanation": "..." }` |
| POST | `/api/v1/copilot/suggest-actions` | 推荐动作 | `{ "object_type": "...", "context": {...} }` | `{ "suggestions": [{...}, ...] }` |
| POST | `/api/v1/copilot/chat` | AI 对话 | `{ "message": "...", "history": [...] }` | `{ "response": "...", "suggestions": [...] }` |

#### 6. 规则引擎 API

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/v1/rules/simulate` | 模拟运行动作 | `{ "action_id": "...", "parameters": {...} }` | `{ "simulation_result": {...}, "predicted_changes": [...] }` |
| POST | `/api/v1/rules/validate` | 验证规则逻辑 | `{ "validation_logic": "...", "rules": [...] }` | `{ "valid": true, "errors": [] }` |
| GET | `/api/v1/rules/eca` | 获取 ECA 规则列表 | - | `{ "rules": [{...}, ...] }` |
| POST | `/api/v1/rules/eca` | 创建 ECA 规则 | `{ "event": "...", "condition": "...", "action": "..." }` | `{ "rule_id": "...", "status": "created" }` |

#### 7. 版本控制 API

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/v1/git/history` | 获取版本历史 | - | `{ "commits": [{...}, ...] }` |
| POST | `/api/v1/git/commit` | 提交变更 | `{ "message": "...", "files": [...] }` | `{ "commit_id": "...", "status": "committed" }` |
| GET | `/api/v1/git/diff` | 获取差异对比 | `{ "commit1": "...", "commit2": "..." }` | `{ "diff": {...} }` |
| POST | `/api/v1/git/revert` | 回滚到指定版本 | `{ "commit_id": "..." }` | `{ "status": "reverted" }` |

### 错误处理

#### 统一错误响应格式
```json
{
  "error": {
    "code": "ERR_SCHEMA_01",
    "message": "JSON 结构不符合 Pydantic 定义",
    "details": {
      "field": "properties",
      "issue": "缺少必需字段 'type_key'"
    },
    "timestamp": "2026-02-07T10:30:00Z"
  }
}
```

#### 常见错误代码

| 错误代码 | 类型 | 描述 | 处理建议 |
|----------|------|------|----------|
| `ERR_SCHEMA_01` | ValidationError | JSON 结构不符合 Pydantic 定义 | 检查请求体格式，确保所有必需字段都存在 |
| `ERR_CYPHER_02` | LogicError | 生成的 Cypher 语法错误 | 使用 `EXPLAIN` 预执行检查语法 |
| `ERR_REF_03` | IntegrityError | 引用了不存在的实体 ID | 运行完整性检查扫描器，列出断链 |
| `ERR_AUTH_04` | AuthenticationError | 认证失败 | 检查会话状态或重新登录 |
| `ERR_PERM_05` | PermissionError | 权限不足 | 检查用户角色和权限设置 |
| `ERR_DB_06` | DatabaseError | 数据库操作失败 | 检查数据库连接和状态 |
| `ERR_FILE_07` | FileSystemError | 文件系统操作失败 | 检查文件权限和路径有效性 |

### API 使用示例

#### 示例 1: 创建对象类型
```bash
curl -X POST http://localhost:5000/api/v1/supply_chain/objects \
  -H "Content-Type: application/json" \
  -d '{
    "type_key": "WAREHOUSE",
    "properties": {
      "name": "string",
      "capacity": "integer",
      "location": "string"
    },
    "visual_assets": ["warehouse_icon.png"],
    "tags": ["storage", "logistics"]
  }'
```

#### 示例 2: 执行沙箱仿真
```bash
curl -X POST http://localhost:5000/api/v1/simulation/sandbox/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "ACT_TRANSFER",
    "params": {
      "source": "warehouse_a",
      "target": "warehouse_b",
      "item": "widgets",
      "quantity": 100
    }
  }'
```

#### 示例 3: 使用 AI Copilot
```bash
curl -X POST http://localhost:5000/api/v1/copilot/generate \
  -H "Content-Type: application/json" \
  -d '{
    "type": "npc",
    "prompt": "创建一个中世纪村庄的铁匠NPC，有独特的性格和背景故事"
  }'
```

### 前端 API 集成

前端通过统一的 API 客户端进行调用：

```typescript
// frontend/src/composables/useApi.ts
import { useProjectStore } from '@/stores/project'

export const useApi = () => {
  const projectStore = useProjectStore()
  
  const apiClient = {
    // 获取领域列表
    async getDomains() {
      const response = await fetch('/api/v1/domains')
      return await response.json()
    },
    
    // 保存对象类型
    async saveObjectType(domain: string, objectType: ObjectTypeDefinition) {
      const response = await fetch(`/api/v1/${domain}/objects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(objectType)
      })
      return await response.json()
    },
    
    // 更多 API 方法...
  }
  
  return apiClient
}
```

## 🔧 开发指南

### 开发环境设置

1. **Python 虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r config/requirements.txt
   ```

2. **前端开发环境**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **数据库设置** (可选)
   ```bash
   # 启动 Neo4j 数据库
   docker-compose up neo4j
   
   # 启动 PostgreSQL 数据库
   docker-compose up postgres
   ```

### 代码规范

#### 后端代码规范 (Python)
- **PEP 8 遵守**: 使用 Black 或 autopep8 格式化代码
- **类型提示**: 所有函数和方法都需要类型提示
- **文档字符串**: 使用 Google 风格文档字符串
- **异常处理**: 使用自定义异常类，避免裸露的异常

```python
# 示例：符合规范的 Python 代码
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ObjectTypeDefinition(BaseModel):
    """对象类型定义模型"""
    type_key: str = Field(..., description="对象类型唯一标识")
    properties: Dict[str, str] = Field(default_factory=dict, description="属性定义")
    visual_assets: List[str] = Field(default_factory=list, description="视觉资源")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    
    def validate_properties(self) -> bool:
        """验证属性定义是否有效"""
        # 验证逻辑
        return True
```

#### 前端代码规范 (TypeScript)
- **TypeScript 严格模式**: 启用所有严格类型检查
- **组件设计**: 使用 Composition API，避免 Options API
- **状态管理**: 使用 Pinia 进行集中状态管理
- **样式规范**: 使用 Tailwind CSS 原子类，避免自定义 CSS

```typescript
// 示例：符合规范的 Vue 组件
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useProjectStore } from '@/stores/project'

interface Props {
  domain: string
  objectType?: ObjectTypeDefinition
}

const props = defineProps<Props>()
const projectStore = useProjectStore()

// 响应式状态
const isLoading = ref(false)

// 计算属性
const domainInfo = computed(() => {
  return projectStore.getDomain(props.domain)
})

// 方法
const saveObjectType = async () => {
  isLoading.value = true
  try {
    await projectStore.saveObjectType(props.domain, props.objectType)
  } finally {
    isLoading.value = false
  }
}
</script>
```

### 测试指南

#### 后端测试
```bash
# 运行所有测试
pytest backend/tests/

# 运行特定测试文件
pytest backend/tests/unit/test_model_validation.py

# 生成测试覆盖率报告
pytest --cov=backend --cov-report=html backend/tests/

# 运行性能测试
pytest backend/tests/performance/ -v
```

#### 前端测试
```bash
# 运行单元测试
cd frontend
npm run test:unit

# 运行 E2E 测试
npm run test:e2e

# 运行组件测试
npm run test:components

# 生成测试报告
npm run test:report
```

### 调试技巧

#### 后端调试
1. **启用调试模式**: 设置 `FLASK_DEBUG=1` 环境变量
2. **使用调试器**: 在代码中插入 `import pdb; pdb.set_trace()`
3. **日志查看**: 查看 `backend/api/server.log` 日志文件
4. **API 测试**: 使用 `scripts/test_api.py` 进行 API 测试

#### 前端调试
1. **Vue DevTools**: 安装 Vue DevTools 浏览器扩展
2. **浏览器开发者工具**: 使用 Chrome DevTools 进行调试
3. **网络监控**: 监控 API 请求和响应
4. **状态检查**: 使用 Pinia DevTools 检查状态变化

### 性能优化

#### 后端性能优化
1. **数据库查询优化**: 使用索引，避免 N+1 查询
2. **缓存策略**: 实现 Redis 缓存层
3. **异步处理**: 使用 Celery 处理耗时任务
4. **连接池**: 配置数据库连接池

#### 前端性能优化
1. **代码分割**: 使用 Vite 的动态导入
2. **懒加载**: 组件和路由的懒加载
3. **图片优化**: 使用 WebP 格式和懒加载
4. **打包优化**: 配置 Tree Shaking 和代码压缩

## 📖 用户指南

### 快速入门教程

#### 步骤 1: 创建新领域
1. 打开 Genesis Forge Studio
2. 点击 "新建领域" 按钮
3. 输入领域名称和描述
4. 选择领域模板 (如: 供应链、智慧城市)
5. 点击 "创建" 完成

#### 步骤 2: 定义对象类型
1. 在左侧导航栏选择 "对象类型"
2. 点击 "新建对象类型"
3. 填写对象类型信息:
   - 类型键: `WAREHOUSE`
   - 属性: `name`, `capacity`, `location`
   - 视觉资源: 上传或选择图标
   - 标签: `storage`, `logistics`
4. 点击 "保存"

#### 步骤 3: 创建世界数据
1. 切换到 "图谱编辑器" 视图
2. 从左侧工具箱拖拽对象到画布
3. 连接对象创建关系
4. 设置对象属性值
5. 点击 "验证" 检查数据完整性

#### 步骤 4: 定义动作规则
1. 切换到 "规则编排器" 视图
2. 创建新规则: `ACT_TRANSFER`
3. 定义验证逻辑 (Cypher 查询)
4. 定义执行规则 (修改图数据)
5. 使用 AI Copilot 辅助生成逻辑

#### 步骤 5: 测试与部署
1. 切换到 "沙箱仿真" 视图
2. 输入测试指令: "从仓库A转移100个部件到仓库B"
3. 观察仿真结果和状态变化
4. 点击 "部署" 保存到版本控制系统
5. 触发 "热重载" 使变更生效

### 高级功能

#### AI Copilot 使用技巧
1. **上下文感知**: AI 会自动加载当前编辑对象的上下文
2. **自然语言转代码**: 输入 "创建攻击动作，需要检查距离和MP"
3. **代码优化**: 让 AI 优化现有的 Cypher 查询
4. **批量生成**: 使用 AI 批量生成相似的对象类型

#### 团队协作流程
1. **分支管理**: 每个功能使用独立的分支开发
2. **代码审查**: 通过 Pull Request 进行代码审查
3. **版本发布**: 使用 Git 标签管理版本发布
4. **冲突解决**: 可视化工具帮助解决合并冲突

#### 性能监控
1. **实时监控**: 查看系统性能和资源使用情况
2. **错误追踪**: 集中化的错误日志和追踪
3. **用户行为分析**: 分析用户操作模式和优化点
4. **容量规划**: 基于使用数据的容量规划建议

## 🔗 相关资源

### 文档链接
- [产品设计文档](../docs/PRODUCT_DESIGN.md) - 完整的产品设计说明
- [技术设计文档](../docs/TECHNICAL_DESIGN.md) - 详细的技术架构设计
- [API 参考文档](./docs/API_REFERENCE.md) - 完整的 API 接口文档
- [开发指南](./docs/DEVELOPER_GUIDE.md) - 开发者指南和最佳实践

### 外部资源
- [Cytoscape.js 文档](https://js.cytoscape.org/) - 图谱可视化库文档
- [Vue 3 官方文档](https://vuejs.org/guide/) - Vue 3 框架指南
- [Neo4j Cypher 手册](https://neo4j.com/docs/cypher-manual/current/) - Cypher 查询语言参考
- [Pydantic 文档](https://docs.pydantic.dev/latest/) - 数据验证库文档

### 社区支持
- **GitHub Issues**: 报告问题和功能请求
- **Discord 社区**: 实时交流和问题讨论
- **Stack Overflow**: 技术问题解答
- **邮件列表**: 项目更新和公告

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献指南

我们欢迎各种形式的贡献！请查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解如何参与项目开发。

### 贡献流程
1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

### 行为准则
请阅读 [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) 了解我们的行为准则。

## 📞 联系方式

- **项目维护者**: Genesis Forge Team
- **问题反馈**: [GitHub Issues](https://github.com/your-org/genesis-forge/issues)
- **电子邮件**: genesis-forge@example.com
- **官方网站**: https://genesis-forge.example.com

---

**Genesis Forge Studio** - 构建智能仿真世界的未来 🚀

*最后更新: 2026-02-07*
