# Project Genesis - Technical Design Document
# Project Genesis - 技术设计文档

**Version**: v0.4  
**Architecture**: Enterprise Five-Layer  
**Date**: 2026-02-04

---

## 1. 架构总览 (Architecture Overview)

### 1.1 五层架构图

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 5: Presentation Layer                                      │
│   applications/game/                                             │
│   ├── game_engine.py    - 游戏核心编排                           │
│   ├── cli.py            - 命令行界面                             │
│   └── main.py           - 入口程序                               │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Ontology Layer                                          │
│   ontology/                                                      │
│   ├── object_types.json      - 实体 Schema                       │
│   ├── action_types.json      - 动作逻辑 (Validation + Rules)    │
│   ├── seed_data.json         - 初始数据                          │
│   └── synapser_patterns.json - 意图映射                          │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: Kernel Layer                                            │
│   genesis/kernel/                                                │
│   ├── synapser.py        - 意图解析器                            │
│   ├── action_driver.py   - Validation→Rules 闭环                 │
│   ├── rule_engine.py     - 多模态存储路由                        │
│   ├── object_manager.py  - 通用对象 CRUD                         │
│   ├── entity_linker.py   - 实体链接器                            │
│   ├── connectors/                                                │
│   │   ├── neo4j_connector.py    - L1: Neo4j                     │
│   │   └── postgres_connector.py - L2/L3: PostgreSQL             │
│   └── ontology/loader.py - Ontology JSON 加载器                  │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: Infrastructure Layer                                    │
│   Infrastructure                                                 │
│   ├── L1 Neo4j          - 当前状态图                             │
│   ├── L2 PostgreSQL     - 事件账本 (event_ledger)               │
│   ├── L3 PostgreSQL     - 语义记忆 (semantic_memory)            │
│   ├── L4 VictoriaMetrics- 遥测数据 (预留)                        │
│   └── L5 File           - 配置文件                               │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 核心设计原则

1. **业务逻辑数据化**: Action 定义在 JSON 中，不在 Python 代码里
2. **操作闭环**: Validation → Rules，每个 Action 必须验证后才能执行
3. **多模态存储**: 根据数据特性选择存储后端（图/关系/向量/时序）
4. **通用内核**: Kernel 层完全通用，通过 Ontology 适配不同应用场景

---

## 2. 核心组件详解 (Core Components)

### 2.1 Synapser (意图解析器)

**职责**: 自然语言 → 结构化意图 (action_id + params)

**实现**:
```python
class Synapser:
    def parse_intent(self, user_input: str, context: Dict) -> Dict:
        # 双路径解析
        # 1. Pattern 匹配 (快速)
        result = self._match_pattern(user_input, context)
        if result:
            return result
        
        # 2. LLM 解析 (备用)
        return self._parse_with_llm(user_input, context)
```

**关键优化**:
- Pattern 匹配: O(n) 复杂度，< 10ms
- Entity Linker: 同义词 + 模糊匹配 + 指代消解
- LLM 回退: 复杂语句兜底

### 2.2 ActionDriver (动作驱动器)

**职责**: 实现完整的 Validation → Rules 闭环

**执行流程**:
```
execute(action_id, params)
  ├── Stage 1: 参数验证
  │     └── 检查必需参数、类型
  ├── Stage 2: 对象引用验证
  │     └── 检查 source_id/target_id 存在性
  ├── Stage 3: Cypher 业务验证
  │     └── 检查连通性、HP、MP 等业务条件
  └── Stage 4: 执行 Rules
        ├── modify_graph → Neo4j
        ├── record_event → PostgreSQL Event Ledger
        ├── memorize → PostgreSQL + pgvector
        └── record_telemetry → VictoriaMetrics
```

**代码结构**:
```python
def execute(self, action_id: str, parameters: Dict) -> Dict:
    # 阶段 0: 检查动作存在
    action_def = self.actions_registry.get(action_id)
    
    # 阶段 1: 参数验证
    param_result = self._validate_parameters(action_def, parameters)
    
    # 阶段 2: 对象引用验证
    obj_ref_result = self._validate_object_references(action_def, parameters)
    
    # 阶段 3: Cypher 业务验证
    validation_result = self._validate_action(action_def, parameters)
    
    # 阶段 4: 执行 Rules
    # 合并验证数据到上下文
    enriched_context = {**parameters, **validation_result.get("data", {})}
    rule_reports = self.rule_engine.execute_rules(rules, enriched_context, action_id)
```

### 2.3 RuleEngine (规则引擎)

**职责**: 根据 rule.type 路由到不同存储后端

**规则类型映射**:

| Rule Type | Storage | Layer | 用途 |
|-----------|---------|-------|------|
| modify_graph | Neo4j | L1 | 修改当前状态 |
| record_event | PostgreSQL | L2 | 审计日志 |
| memorize | PostgreSQL + pgvector | L3 | 语义记忆 |
| record_telemetry | VictoriaMetrics | L4 | 遥测数据 |

**关键代码**:
```python
def execute_rule(self, rule: Dict, context: Dict, action_id: str) -> Dict:
    rule_type = rule.get('type')
    
    if rule_type == 'modify_graph':
        return self._execute_modify_graph(rule, context)  # → Neo4j
    elif rule_type == 'record_event':
        return self._execute_record_event(rule, context, action_id)  # → PostgreSQL
    elif rule_type == 'memorize':
        return self._execute_memorize(rule, context)  # → PostgreSQL + pgvector
```

### 2.4 Entity Linker (实体链接器)

**职责**: 自然语言提及 → 实体 ID

**算法**:
1. **精确匹配**: mention == entity.name
2. **包含匹配**: mention in entity.name or vice versa
3. **同义词匹配**: mention 匹配同义词库
4. **模糊匹配**: SequenceMatcher ratio > 0.6

**同义词库**:
```python
synonyms = {
    "守卫": ["守卫", "卫兵", "看守", "门卫", "守卫队长"],
    "强盗": ["强盗", "土匪", "歹徒", "贼人", "蒙面人"],
    # ...
}
```

---

## 3. 数据流 (Data Flow)

### 3.1 玩家输入处理流程

```
用户输入: "攻击那个强盗"
    │
    ▼
┌─────────────────────────────────────┐
│ Synapser.parse_intent()             │
│ - Pattern 匹配: "攻击" → ACT_ATTACK │
│ - Entity Linker: "那个强盗" → npc_bandit_1 │
└─────────────────────────────────────┘
    │
    ▼ {action_id: "ACT_ATTACK", params: {target: "npc_bandit_1"}}
┌─────────────────────────────────────┐
│ ActionDriver.execute()              │
│ - Stage 1: 参数验证                 │
│ - Stage 2: 检查 npc_bandit_1 存在   │
│ - Stage 3: Cypher 验证同地点        │
│   MATCH (p)-[:LOCATED_AT]->(l)<-[:LOCATED_AT]-(t) │
│ - Stage 4: 执行 Rules               │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ RuleEngine                          │
│ - modify_graph: SET t.hp = t.hp - 10 │
│ - record_event: 记录攻击事件        │
│ - memorize: 存储战斗记忆            │
└─────────────────────────────────────┘
    │
    ▼
反馈: "AI 旁白: 你拔剑冲向强盗..."
      "系统: 造成 10 点伤害"
```

### 3.2 世界初始化流程

```
GameEngine.initialize_world()
    │
    ├── 1. Load seed_data.json
    │
    ├── 2. For each node in seed_nodes:
    │      ObjectManager.create_object(type, properties)
    │      └── Cypher: CREATE (n:Type {properties})
    │
    ├── 3. For each link in seed_links:
    │      ObjectManager.create_link(type, source, target)
    │      └── Cypher: MATCH (s), (t) CREATE (s)-[:TYPE]->(t)
    │
    └── 4. 世界就绪
```

---

## 4. 数据模型 (Data Models)

### 4.1 Object Types (实体类型)

```json
{
  "Player": {
    "primary_key": "id",
    "properties": {
      "id": {"type": "string", "required": true},
      "name": {"type": "string", "required": true},
      "hp": {"type": "integer", "default": 100},
      "damage": {"type": "integer", "default": 10}
    }
  },
  "NPC": {
    "properties": {
      "id": {...},
      "name": {...},
      "disposition": {"enum": ["aggressive", "neutral", "friendly"]},
      "faction": {"type": "string"}
    }
  }
}
```

### 4.2 Action Types (动作类型)

```json
{
  "ACT_ATTACK": {
    "parameters": [
      {"name": "source_id", "type": "object_ref", "object_type": "Player"},
      {"name": "target_id", "type": "object_ref", "object_type": "NPC"}
    ],
    "validation": {
      "logic_type": "cypher_check",
      "statement": "MATCH (s)-[:LOCATED_AT]->(l)<-[:LOCATED_AT]-(t) RETURN count(t) > 0 as is_valid",
      "error_message": "目标不在同一地点"
    },
    "rules": [
      {
        "type": "modify_graph",
        "statement": "MATCH (t {id: $target_id}) SET t.hp = t.hp - $damage"
      },
      {
        "type": "record_event",
        "summary_template": "{source_name} 攻击了 {target_name}"
      }
    ]
  }
}
```

### 4.3 关系类型

```json
{
  "LOCATED_AT": {
    "source": "Player|NPC|Item",
    "target": "Location",
    "bidirectional": false
  },
  "CONNECTED_TO": {
    "source": "Location",
    "target": "Location",
    "bidirectional": true
  }
}
```

---

## 5. 存储层设计 (Storage Design)

### 5.1 L1: Neo4j (当前状态)

**用途**: 实时游戏状态、关系拓扑、连通性验证

**Schema**:
```cypher
// 节点
(:Player {id, name, hp, damage})
(:NPC {id, name, hp, damage, disposition, faction})
(:Location {id, name, description})
(:Faction {id, name})

// 关系
(:Player)-[:LOCATED_AT]->(:Location)
(:Location)-[:CONNECTED_TO]->(:Location)
(:NPC)-[:BELONGS_TO]->(:Faction)
```

### 5.2 L2: PostgreSQL - Event Ledger

**用途**: 审计日志、事件溯源

**Schema**:
```sql
CREATE TABLE event_ledger (
    event_id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    action_type VARCHAR(64),
    initiator_id VARCHAR(64),
    target_id VARCHAR(64),
    summary TEXT,
    context JSONB,
    changes JSONB
);
```

**特点**:
- Append-only，不可变
- JSONB 存储灵活上下文
- 支持时间范围查询

### 5.3 L3: PostgreSQL + pgvector - Semantic Memory

**用途**: 长期记忆、RAG 增强对话

**Schema**:
```sql
CREATE TABLE semantic_memory (
    memory_id UUID PRIMARY KEY,
    entity_id VARCHAR(64),
    memory_type VARCHAR(32),  -- 'dialogue', 'event', 'lore'
    content TEXT NOT NULL,
    embedding vector(768),    -- 匹配 nomic-embed-text
    importance FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memory_vec ON semantic_memory 
USING hnsw (embedding vector_cosine_ops);
```

---

## 6. API 接口 (API Interfaces)

### 6.1 GameEngine API

```python
class GameEngine:
    # 初始化
    def __init__(neo4j_conn, postgres_conn, ontology_dir)
    
    # 世界管理
    def initialize_world() -> bool
    def get_player_status() -> Dict
    
    # 游戏循环
    def process_input(user_input: str) -> Dict
    def run_simulation_tick() -> List[Event]
    def check_game_over() -> Optional[str]
```

### 6.2 ObjectManager API

```python
class ObjectManager:
    def create_object(object_type: str, properties: Dict) -> Dict
    def get_object(object_type: str, object_id: str) -> Optional[Dict]
    def update_object(object_type: str, object_id: str, properties: Dict) -> bool
    def delete_object(object_type: str, object_id: str) -> bool
    def create_link(link_type: str, source_id: str, target_id: str)
    def get_related_objects(object_type: str, object_id: str, link_type: str) -> List[Dict]
```

### 6.3 ActionDriver API

```python
class ActionDriver:
    def load_actions(actions_list: List[Dict]) -> int
    def execute(action_id: str, parameters: Dict) -> Dict:
        # Returns: {success, message, validation_data, rule_reports}
```

---

## 7. 配置 (Configuration)

### 7.1 环境变量

```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=mysecretpassword

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=genesis
POSTGRES_PASSWORD=password
POSTGRES_DB=genesis_core

# LLM API
LLM_API_KEY=kimyitao
LLM_BASE_URL=http://43.153.96.90:7860/v1beta
INTENT_MODEL=models/gemini-2.5-flash-lite
```

### 7.2 Ontology 文件

```
ontology/
├── object_types.json       # 实体 Schema
├── action_types.json       # 动作逻辑
├── seed_data.json          # 初始数据
└── synapser_patterns.json  # 意图映射
```

---

## 8. 测试策略 (Testing Strategy)

### 8.1 测试金字塔

```
        /\
       /  \    E2E 测试 (1)
      /____\       test_v04_integration.py
     /      \   
    /        \  集成测试 (3)
   /__________\    test_ontology_loader.py
  /            \   test_entity_linker.py
 /              \  test_action_driver.py
/________________\ 单元测试 (N)
                   test_synapser.py
                   test_object_manager.py
```

### 8.2 关键测试场景

**1. Ontology 验证**
- JSON Schema 有效性
- 动作定义完整性（parameters, validation, rules）
- 种子数据一致性

**2. 闭环验证**
- Validation 失败时 Rules 不执行
- Validation 成功时 Rules 顺序执行
- 验证数据正确传递到 Rules

**3. 实体链接**
- 精确匹配
- 同义词匹配
- 模糊匹配（相似度阈值）

---

## 9. 部署 (Deployment)

### 9.1 Docker Compose

```yaml
version: '3.8'
services:
  neo4j:
    image: neo4j:5.15-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/mysecretpassword

  postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=genesis
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=genesis_core
```

### 9.2 启动步骤

```bash
# 1. 启动基础设施
docker-compose up -d

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行游戏
python -m applications.game.main
```

---

## 10. 扩展性设计 (Extensibility)

### 10.1 新增动作类型

**Step 1**: 在 `action_types.json` 中添加定义

**Step 2**: 重启游戏（自动加载）

**无需修改 Python 代码！**

### 10.2 新增存储后端

在 `RuleEngine` 中添加新的 rule 类型处理：

```python
elif rule_type == 'new_storage':
    return self._execute_new_storage(rule, context)
```

### 10.3 自定义意图模式

在 `synapser_patterns.json` 中添加：

```json
"ACT_CUSTOM": {
  "keywords": ["关键词"],
  "requires_target": true,
  "target_type": "location"
}
```

---

**文档版本**: 1.0  
**最后更新**: 2026-02-04  
**技术栈**: Python 3.10+, Neo4j 5.15, PostgreSQL 16, Gemini API
