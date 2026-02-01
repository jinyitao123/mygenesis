# Project Genesis MVP Design

**Date**: 2026-02-01  
**Status**: Approved for Implementation  
**Phase**: MVP (Concept Validation)

---

## 1. Vision Statement

构建一个语义驱动的沙盒模拟引擎MVP，验证"意图→图谱→交互"的核心闭环。在这个最小化系统中，用户通过自然语言描述世界观，LLM自动生成知识图谱表示的游戏世界，玩家通过CLI与这个世界交互。

**核心价值主张**：
- 真正的生成式：每次运行世界结构都不同
- 语义理解：自然语言指令驱动游戏逻辑
- 图谱约束：硬逻辑验证（非LLM幻觉）确保一致性

---

## 2. Architecture Overview

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface (CLI)                  │
│              Colorama-enhanced terminal I/O             │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  Python Application Layer                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   main.py    │  │ graph_client │  │ llm_engine   │   │
│  │ (Game Loop)  │  │   (DAO)      │  │  (AI Layer)  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Infrastructure Layer                        │
│        Neo4j (Graph DB) + OpenAI API (LLM)              │
└─────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

- **语言**: Python 3.9+
- **图数据库**: Neo4j 5.15 (Docker)
- **LLM**: OpenAI GPT-4o / GPT-3.5-turbo
- **依赖**: neo4j-python-driver, openai, python-dotenv, colorama

---

## 3. Module Specifications

### 3.1 graph_client.py (Data Access Layer)

**职责**: 所有Neo4j交互的封装，处理Cypher查询和事务

**核心方法**:
- `clear_world()`: 清空图谱（游戏重置）
- `create_world(world_json)`: 批量创建节点和关系
- `get_player_status()`: 获取玩家状态及环境上下文
- `execute_move(target_name)`: 验证并执行移动
- `update_player_hp(delta)`: 更新血量

**Cypher模式**:
```cypher
// 玩家状态查询
MATCH (p:Player)-[:LOCATED_AT]->(loc:Location)
OPTIONAL MATCH (loc)-[:CONNECTED_TO]-(exits:Location)
OPTIONAL MATCH (entity)-[:LOCATED_AT]->(loc)
WHERE entity.id <> p.id
RETURN p, loc, collect(DISTINCT exits) as exits, collect(DISTINCT entity) as entities

// 移动验证与执行
MATCH (p:Player)-[:LOCATED_AT]->(cur), (cur)-[:CONNECTED_TO]-(tgt:Location {name: $name})
MATCH (p)-[r:LOCATED_AT]->()
DELETE r
CREATE (p)-[:LOCATED_AT]->(tgt)
```

### 3.2 llm_engine.py (Semantic Layer)

**职责**: LLM交互管理，包含提示词工程和响应解析

**核心方法**:
- `generate_world_schema(user_prompt)`: 世界观→JSON图谱
  - System Prompt定义节点类型(Player, Location, NPC, Item, Goal)
  - 强制JSON输出格式
  - 要求中文描述、英文ID

- `interpret_action(player_input, context)`: 自然语言→意图结构
  - 输入: 用户指令 + 当前状态上下文
  - 输出: `{intent, target, narrative}`
  - 支持意图: MOVE, ATTACK, LOOK, UNKNOWN

- `generate_narrative(event_type, details)`: 事件→RPG风格描述

**Prompt Engineering策略**:
- 使用`response_format={"type": "json_object"}`强制结构化输出
- Context注入当前游戏状态（位置、出口、实体列表）
- 约束目标必须在可用选项中

### 3.3 main.py (Game Loop Orchestrator)

**职责**: 协调各模块，实现游戏主循环

**流程**:
1. **初始化**: 连接Neo4j和OpenAI
2. **世界构建**: 
   - 接收用户世界观描述
   - 调用LLM生成图谱JSON
   - 清空并重建图数据库
3. **主循环** (直到game_over):
   - A. 检索上下文 (`get_player_status`)
   - B. UI展示 (位置、描述、出口、可见实体、HP)
   - C. 接收用户输入
   - D. 语义解析 (`interpret_action`)
   - E. 执行逻辑 (MOVE/ATTACK等)
   - F. 世界推演 (NPC攻击检测)
   - G. 胜利/失败判定
4. **清理**: 关闭数据库连接

**颜色编码**:
- GREEN: 系统状态/成功消息
- YELLOW: 加载/警告
- CYAN: 用户输入提示
- BLUE: 位置信息
- MAGENTA: AI旁白
- RED: 伤害/错误

---

## 4. Data Model

### 4.1 Node Labels

| Label | 属性 | 说明 |
|-------|------|------|
| Player | id, name, hp | 玩家实体，全局唯一 |
| Location | id, name, description | 游戏场景/房间 |
| NPC | id, name, description, damage | 非玩家角色 |
| Item | id, name, description | 可交互物品 |
| Goal | id, name, description | 胜利条件 |

### 4.2 Relationship Types

| Type | 源→目标 | 说明 |
|------|---------|------|
| LOCATED_AT | Entity→Location | 实体位于某地 |
| CONNECTED_TO | Location↔Location | 地点间通路（双向） |
| HAS_GOAL | Player→Goal | 玩家目标 |

### 4.3 JSON Schema示例

```json
{
  "nodes": [
    {"id": "player_1", "label": "Player", "properties": {"name": "侦探", "hp": 100}},
    {"id": "lobby", "label": "Location", "properties": {"name": "大厅", "description": "维多利亚式豪宅入口"}},
    {"id": "killer", "label": "NPC", "properties": {"name": "杀手", "damage": 15}}
  ],
  "edges": [
    {"source": "player_1", "target": "lobby", "type": "LOCATED_AT"},
    {"source": "killer", "target": "lobby", "type": "LOCATED_AT"},
    {"source": "lobby", "target": "library", "type": "CONNECTED_TO"}
  ]
}
```

---

## 5. Error Handling & Edge Cases

### 5.1 已知风险与缓解

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| LLM返回无效JSON | 世界生成失败 | try/except包装，失败时回退到静态模板 |
| Neo4j连接失败 | 游戏无法启动 | 启动时验证连接，提供清晰错误提示 |
| 意图解析失败 | 玩家指令无响应 | 返回友好提示"我不理解"并继续循环 |
| 图谱查询空结果 | UI显示异常 | 优雅降级显示"此处一片虚无" |
| 关系验证失败 | 玩家穿墙 | Cypher查询强制验证连通性 |

### 5.2 技术债务

- MVP中NPC战斗逻辑过度简化（自动扣血），Alpha阶段需引入GOAP规划
- 无并发控制（单玩家假设），V1.0需考虑多玩家/多会话
- 意图识别准确率依赖prompt质量，需持续优化

---

## 6. Testing Strategy

### 6.1 验证方法

**手工测试场景**:
1. 生化危机主题（恐怖生存）
2. 赛博朋克主题（科幻都市）
3. 中世纪主题（奇幻冒险）

**验证 checklist**:
- [ ] 每次运行生成结构不同的世界
- [ ] 节点和关系正确创建（Neo4j Browser目视检查）
- [ ] 意图识别准确率 > 90%（20条测试指令统计）
- [ ] 移动被图谱约束（尝试前往无连接的房间应失败）
- [ ] NPC战斗触发正确

### 6.2 性能基准

- 意图解析延迟: < 2s (LLM API调用)
- 图谱查询延迟: < 500ms (本地Neo4j)
- 世界生成时间: < 10s (包含LLM生成+图创建)

---

## 7. Success Criteria

MVP成功的定义：

1. **功能闭环**: 用户能完成"描述世界→生成图谱→移动探索→战斗交互"全流程
2. **生成多样性**: 相同提示词运行3次，生成的世界结构明显不同
3. **逻辑一致性**: 玩家无法移动到无连接的房间（图谱约束生效）
4. **意图理解**: 20条标准测试指令中至少18条被正确解析（90%准确率）
5. **可观测性**: 通过Neo4j Browser能可视化查看生成的世界图谱

---

## 8. Future Considerations (Post-MVP)

**Alpha阶段 (Agentic Simulation)**:
- 引入Faction, Quest, Knowledge节点类型
- NPC GOAP自主决策（寻路、目标驱动）
- 记忆系统（RAG向量检索）
- 复杂规则引擎（钥匙→门）

**Beta阶段 (Visualization)**:
- React + D3.js前端
- 实时图谱可视化（侦探线索墙风格）
- 多模态生成（Stable Diffusion场景图、TTS音效）

**V1.0阶段 (Ecosystem)**:
- 世界存档/读档（图谱序列化）
- 本体市场（模组分享）
- 多智能体推演（纯AI自主运行）

---

## 9. Development Workflow

**环境启动**:
```bash
docker-compose up -d  # 启动Neo4j
pip install -r requirements.txt
cd src && python main.py
```

**开发迭代**:
1. 修改代码 → 重启main.py测试
2. 图结构变更 → 游戏自动重建世界
3. Neo4j调试 → 访问 http://localhost:7474

---

**文档版本**: 1.0  
**作者**: AI Assistant + User  
**最后更新**: 2026-02-01
