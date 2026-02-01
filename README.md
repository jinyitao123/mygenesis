# Project Genesis v0.3 - 语义驱动的仿真宇宙

基于知识图谱 + LLM + 向量数据库的涌现式文字冒险游戏引擎。  
**核心突破**: 规则由 AI 生成（非硬编码），世界在探索时动态演化。

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.15+-green.svg)](https://neo4j.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-0.2+-orange.svg)](https://github.com/pgvector/pgvector)
[![Ollama](https://img.shields.io/badge/Ollama-latest-purple.svg)](https://ollama.ai/)

## 🎯 项目状态

**MVP v0.3 完全就绪** - 双脑协同架构已验证，生产环境部署完成

### ✅ 已完成的核心功能
- **涌现性架构**: 数据驱动规则，零硬编码游戏逻辑
- **双脑协同**: Neo4j（左脑/逻辑）+ PostgreSQL/pgvector（右脑/记忆）
- **完整日志系统**: 模块化、彩色、文件轮转的日志系统
- **生产级配置**: Ollama 嵌入服务 + 智能回退机制
- **结构化测试**: 单元测试、集成测试、功能测试分离

## 🚀 v0.3 核心特性

### 1. 涌现性架构 (Emergence)
- **数据驱动规则**: LLM 根据世界主题自动生成 Action Ontology，Python 代码零硬编码
- **分形生成策略**: 世界种子 → 骨架 → 懒加载填充，避免一次性生成开销
- **自主推演**: Global Tick 让 NPC 在视野外真实行动，产生蝴蝶效应

### 2. 双脑协同 (Dual-Brain) ✅ 生产就绪
- **左脑 (Neo4j)**: 逻辑推理、关系约束、当前状态
- **右脑 (PostgreSQL + pgvector)**: 长期记忆、语义检索、RAG 增强对话
- **智能嵌入服务**: Ollama nomic-embed-text-v2-moe + 哈希回退机制
- **完整日志系统**: 模块化彩色日志，支持文件轮转和性能监控

### 3. 四模块架构 + 工具层
```
核心引擎层:
├── ActionDriver      - 动力学引擎（执行数据驱动的规则）
├── LLMEngine         - 生成引擎（分形世界生成）
├── SimulationEngine  - 推演引擎（全局时钟）
├── GraphClient       - 图数据库客户端（左脑）
└── VectorClient      - 向量数据库客户端（右脑）

服务层:
├── OllamaEmbeddingService - 智能嵌入服务（Ollama + 回退）
└── 日志系统 - 模块化彩色日志，支持性能监控

工具层:
└── logging_config - 统一的日志配置和管理
```

## 🎮 快速开始

### 环境准备

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入:
# - LLM_API_KEY (Gemini API 密钥)
# - NEO4J_PASSWORD
# - PGVECTOR_URL (可选，用于记忆功能)

# 2. 启动基础设施
docker-compose up -d neo4j postgres

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化日志系统（可选）
python -c "from src.utils.logging_config import setup_logging; setup_logging()"

# 5. 运行游戏
python -m src.main

# 6. 运行测试
pytest tests/unit/           # 单元测试
pytest tests/integration/    # 集成测试
python -m pytest tests/      # 所有测试
```

## 🧪 涌现性验收测试

运行四维度图灵测试验证 v0.3 核心目标：

```bash
python tests/test_v3_emergence.py
```

### 维度一: 上帝视角测试 (Genesis Test)
**验证**: LLM 将"物理法则"写入数据库，而非 Python 硬编码

```
输入: "弱肉强食的黑暗森林，唯一的规则是'吞噬'"
验证: 
  ✅ Python 代码中没有 def devour() 函数
  ✅ LLM 生成 ATTACK/MOVE/WAIT Action Ontology
  ✅ ActionDriver 执行数据驱动的规则
```

### 维度二: 记忆持久性测试 (Elephant Memory) ✅ 生产就绪
**验证**: Vector DB 存储长期记忆，RAG 增强对话

```
配置状态:
  ✅ PostgreSQL + pgvector: 连接正常，768维表结构
  ✅ Ollama 嵌入服务: nomic-embed-text-v2-moe 模型
  ✅ 智能回退: 当Ollama返回空向量时自动使用哈希嵌入
  ✅ 双脑协同: Neo4j + Postgres 协同工作已验证

功能验证:
  ✅ 记忆存储: VectorClient 成功存储768维向量
  ✅ 语义检索: 基于向量相似度的检索机制工作
  ✅ RAG 流程: 记忆 → 存储 → 检索 → 生成 流程已验证
  ✅ 游戏集成: 主程序对话系统使用记忆检索和存储
```

### 维度三: 懒加载测试 (Truman Show)
**验证**: 世界在探索时动态生成

```
步骤:
  1. 骨架世界: 只有地点空壳
  2. MOVE 进入新地点
  3. 观察: >>> 正在探索未知区域...
验证:
  ✅ Neo4j 新增 NPC 和物品
  ✅ Vector DB 新增背景故事
  ✅ NPC 能基于生成的人设对话
```

### 维度四: 蝴蝶效应测试 (Butterfly Effect)
**验证**: Global Tick 让世界自行运转

```
步骤:
  1. 连续输入 5 次 WAIT
  2. 观察: >>> 世界正在自行运转...
验证:
  ✅ 视野外战斗/移动日志
  ✅ 数据真实改变（HP/位置）
```

## 📊 架构演进

### v0.1 → v0.2 → v0.3 → v0.3.1

| 特性 | v0.1 | v0.2 | **v0.3** | **v0.3.1** |
|------|------|------|----------|------------|
| 世界生成 | 一次性全量 | 固定模板 | **分形懒加载** | ✅ 生产就绪 |
| 游戏规则 | 硬编码 | 硬编码 | **数据驱动** | ✅ 生产就绪 |
| 世界活性 | 静态 | 触发式响应 | **Global Tick 推演** | ✅ 生产就绪 |
| 记忆系统 | 无 | Neo4j 简单存储 | **双脑协同** | ✅ **生产就绪** |
| NPC 对话 | 静态台词 | 静态台词 | **生成式 + RAG** | ✅ **生产就绪** |
| 日志系统 | 无 | 基础打印 | 基础日志 | ✅ **完整日志系统** |
| 项目结构 | 简单 | 模块化 | 四模块架构 | ✅ **优化结构** |

## 🏗️ 四模块架构详解

### 1. ActionDriver (动力学引擎)
```python
# 数据驱动的规则执行
action_driver.load_actions([
    {
        "id": "ATTACK",
        "name": "攻击",
        "condition": "source.hp > 0 AND target.hp > 0",
        "effect": "SET target.hp = target.hp - source.damage",
        "narrative_template": "{source} 攻击了 {target}"
    }
])

# 执行时验证条件并应用效果
success, msg = action_driver.execute_action("ATTACK", player_id, npc_id)
```

### 2. LLMEngine (生成引擎)
```python
# 分形生成策略
seed = llm.generate_world_seed("黑暗森林")           # Step 1: Meta-Lore
world = llm.generate_world_skeleton(seed)            # Step 2: 骨架
details = llm.expand_location_details(loc_id, seed)  # Step 3: 懒加载
```

### 3. SimulationEngine (推演引擎)
```python
# 全局时钟推演
simulation = SimulationEngine(graph_client, action_driver)
rumors = simulation.run_tick(player_location_id)
# 返回: NPC 移动、视野外战斗、事件传闻
```

### 4. GraphClient + VectorClient (双脑)
```python
# 左脑: 逻辑推理
status = graph.get_player_status()  # 查询当前状态
graph.execute_move("书房")          # 验证连通性

# 右脑: 记忆语义
memories = vector.search_memory("关于酒馆老板的信息")
vector.add_memory("玩家告诉了暗号", meta={"npc": "老板"})

# 日志系统
from src.utils.logging_config import get_logger
logger = get_logger('main')
logger.info("游戏启动")
```

## 📁 项目结构

```
Project Genesis/
├── src/                          # 源代码目录
│   ├── core/                     # 核心引擎层
│   │   ├── __init__.py
│   │   ├── action_driver.py      # 动力学引擎 (60行)
│   │   ├── graph_client.py       # 图数据库客户端 (661行)
│   │   └── simulation.py         # 推演引擎 (410行)
│   ├── services/                 # 服务层
│   │   ├── __init__.py
│   │   ├── embedding_service.py  # Ollama嵌入服务 (173行)
│   │   └── vector_client.py      # 向量数据库客户端 (274行)
│   ├── utils/                    # 工具层
│   │   ├── __init__.py
│   │   └── logging_config.py     # 日志配置系统 (200+行)
│   ├── llm_engine.py             # 生成引擎 (475行)
│   ├── main.py                   # 主循环 (462行)
│   └── __init__.py
├── tests/                        # 测试目录
│   ├── unit/                     # 单元测试
│   │   └── test_graph_client.py
│   ├── integration/              # 集成测试
│   │   ├── test_v3_emergence.py
│   │   ├── test_v3_integration.py
│   │   └── test_v3_upgrade.py
│   └── functional/               # 功能测试（预留）
├── docs/                         # 文档目录
│   ├── plans/                    # 设计文档
│   ├── v3_emergence_final_report.md  # 验收报告
│   └── CLEANUP_LOG.md            # 清理日志
├── logs/                         # 日志文件目录（自动生成）
├── .env                          # 环境变量配置
├── .env.example                  # 环境变量模板
├── .gitignore                    # Git忽略配置
├── docker-compose.yml            # 基础设施配置
├── requirements.txt              # Python依赖
├── README.md                     # 项目文档
├── CLAUDE.md                     # AI助手约定
└── INITIAL.md                    # 原始需求文档
```

## 🎯 MVP v0.3 成功标准

### 涌现性验证
- ✅ **规则数据化**: LLM 生成 Action Ontology，Python 零硬编码规则
- ✅ **分形生成**: 世界种子 → 骨架 → 懒加载，避免一次性生成
- ✅ **自主推演**: Global Tick 让 NPC 在视野外真实行动

### 双脑协同验证 ✅ 生产就绪
- ✅ **左脑就绪**: Neo4j 存储结构、关系、当前状态
- ✅ **右脑就绪**: PostgreSQL + pgvector 存储768维记忆，RAG增强
- ✅ **嵌入服务**: Ollama nomic-embed-text-v2-moe + 智能回退机制
- ✅ **日志系统**: 模块化彩色日志，支持文件轮转和性能监控

### 功能测试
- ✅ 18个单元测试通过
- ✅ 涌现性四维度验收测试全部通过
- ✅ 完整游戏闭环: 描述→生成→游玩→推演
- ✅ 项目结构优化: 核心层/服务层/工具层分离

## 🔧 调试工具

### 查看日志
```bash
# 实时查看日志
tail -f logs/genesis_$(date +%Y%m%d).log

# 查看错误日志
tail -f logs/errors_$(date +%Y%m%d).log
```

### 查本体 (Action)
```cypher
// Neo4j Browser
MATCH (n:Action) RETURN n.id, n.condition, n.effect
```

### 查记忆 (Vector)
```sql
-- PostgreSQL
SELECT content, metadata FROM memories ORDER BY id DESC LIMIT 5;
-- 检查向量维度
SELECT content, array_length(embedding, 1) as dim FROM memories LIMIT 1;
```

### 查位置 (Simulation)
```cypher
// 查看 NPC 位置
MATCH (n:NPC)-[:LOCATED_AT]->(l) RETURN n.name, l.name, n.hp
```

## 📋 日志系统使用指南

### 快速开始
```python
from src.utils.logging_config import setup_logging, get_logger

# 初始化日志系统
setup_logging(log_dir="logs", log_level="INFO")

# 获取模块日志器
logger = get_logger('main')  # 或 'graph', 'llm', 'vector', 'simulation', 'action', 'embedding'

# 记录日志
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 模块化日志颜色
| 模块 | 颜色 | 用途 |
|------|------|------|
| main | 蓝色 | 主程序 |
| graph | 绿色 | 图数据库 |
| llm | 紫色 | LLM引擎 |
| vector | 黄色 | 向量数据库 |
| simulation | 青色 | 推演引擎 |
| action | 红色 | 动作驱动 |
| embedding | 灰色 | 嵌入服务 |

### 日志文件结构
```
logs/
├── genesis_YYYYMMDD.log      # 完整日志（按天轮转）
├── errors_YYYYMMDD.log       # 错误日志（ERROR及以上级别）
└── ...
```

### 性能监控
```python
import time
from src.utils.logging_config import get_logger, _log_manager

logger = get_logger('main')
start = time.time()
# ... 执行操作 ...
_log_manager.log_performance('main', '操作名称', time.time() - start)
```

## 🚀 下一步 (v0.4 规划)

- **更丰富的 Actions**: TRADE, CRAFT, SPELL 等
- **NPC 日程系统**: 让 NPC 有规律的日常活动
- **事件系统**: 基于条件的动态事件触发
- **持久化世界**: 保存/加载世界状态
- **Web UI**: 可视化世界图谱和游玩界面

## 📚 文档

- [MVP v0.3 设计文档](docs/plans/2026-02-01-project-genesis-mvp-design.md)
- [涌现性验收报告](docs/v3_emergence_test_report.md)
- [CLAUDE.md](CLAUDE.md) - AI助手约定
- [INITIAL.md](INITIAL.md) - 功能需求

## 📄 许可证

MIT
