这是一个基于 **MDA (Model-Driven Architecture)** 理念，结合 **Genesis Forge 优化意见** 以及 **Project Genesis 核心架构** 编写的企业级产品设计文档（PRP）。

该文档旨在将 **Genesis Forge** 从一个简单的文件编辑器升级为 **Genesis Studio**——一个全功能的、可视化、智能化的仿真世界构建平台。

---

# Genesis Forge (Studio Edition) - 产品参考规划 (PRP)

**版本**: v2.0 (Enterprise Definition)
**架构范式**: Model-Driven Architecture (MDA)
**日期**: 2026-02-06
**适用范围**: 企业级仿真/游戏开发

---

## 1. MDA 架构总览

Genesis Forge 不仅仅是代码编辑器，它是连接人类意图与仿真内核的桥梁。基于 MDA，我们将系统划分为三个核心层次，Forge 负责管理 PIM 并自动转换为 PSM。

### 1.1 MDA 架构分层模型

| MDA 层次 | Genesis 对应概念 | 描述 |
| --- | --- | --- |
| **CIM (计算无关模型)** | **Domain Concepts** | 业务领域的概念模型（如：供应链节点、RPG 角色、智慧城市交通流）。 |
| **PIM (平台无关模型)** | **Ontology Layer** | 定义在 JSON/XML 中的逻辑：`Object Types`, `Action Rules`, `Synapser Patterns`。这是 Forge 编辑的核心对象。 |
| **PSM (平台特定模型)** | **Kernel Runtime** | 具体的执行实现：Python 对象实例、Neo4j 图数据、Cypher 查询语句、Postgres 向量索引。 |

### 1.2 模型层次说明

Genesis Forge 的核心职责是提供可视化的 **PIM 编辑器**，并通过生成引擎将其转化为 **PSM**。

1. **元模型层 (Meta-Model)**: 定义“什么是实体”、“什么是动作”。由 `SchemaEngine` (Pydantic) 强约束。
2. **模型层 (Model)**: 策划/开发者创建的具体数据（如：“兽人战士”、“火球术”）。
3. **运行时层 (Runtime)**: 游戏引擎加载模型后在内存和数据库中的状态。

### 1.3 技术栈映射关系

* **前端 (Presentation)**:
* 框架: Vue.js 3 / React (组件化架构)
* 可视化: **Cytoscape.js** (图谱可视化编辑), **React Flow** (逻辑节点编排)
* 交互: Monaco Editor (代码辅助)


* **后端 (Logic)**:
* 框架: Flask (Blueprints 模块化) -> FastAPI (异步高性能)
* 校验: **Pydantic** (数据完整性验证)
* 版本控制: **GitPython** (底层 Git 集成)


* **存储 (Persistence)**:
* 文件系统 (JSON/XML Repository)
* Neo4j (预览/调试数据库)



---

## 2. 数据模型 (Data Model)

在 MDA 视角下，数据模型定义了仿真世界的静态结构。

### 2.1 核心元数据定义

**1. ObjectTypeDefinition (实体定义)**

* **用途**: 定义一类实体的模板。
* **字段**:
* `type_key` (string): 唯一标识 (e.g., "NPC_Guard")
* `properties` (dict): 属性Schema (HP, MP, Faction)
* `visual_assets` (list): 关联的前端资源
* `tags` (list): 行为标签 (e.g., "biological", "mortal")



**2. RelationshipDefinition (关系定义)**

* **用途**: 定义实体间的连接规则。
* **字段**:
* `relation_type` (e.g., "LOCATED_AT")
* `source_constraint` (e.g., ["Player", "NPC"])
* `target_constraint` (e.g., ["Location"])
* `attributes` (e.g., {"distance": "float"})



**3. WorldSnapshot (世界快照)**

* **用途**: 初始世界的实例化数据 (`seed_data`)。
* **结构**: 节点列表 + 边列表。

### 2.2 数据验证约束 (Constraints)

* **引用完整性**: `seed_data` 中的每个 `object_id` 必须唯一。
* **类型合规性**: 实例属性必须符合 `ObjectType` 定义的 Schema。
* **图拓扑约束**: 关系连接必须符合 `RelationshipDefinition` 的源/目标类型限制。

---

## 3. 规则模型 (Rule Model)

规则模型是 Genesis 的核心，它将业务逻辑从代码中剥离，实现了“数据驱动逻辑”。

### 3.1 规则模型架构

规则模型采用 **ECA (Event-Condition-Action)** 变体模式：
`Intent (Event) -> Validation (Condition) -> Rules (Action)`

### 3.2 核心规则详细定义 (ActionType)

每个动作 (`ActionType`) 包含以下核心组件：

1. **Signature (签名)**:
* `action_id`: 动作唯一ID (e.g., `ACT_ATTACK`)
* `parameters`: 入参定义 (e.g., `source_id`, `target_id`)


2. **Validation Logic (验证逻辑)**:
* **类型**: `CypherCheck` | `PythonExpression` (受限)
* **内容**: 定义必须为真的条件。
* *示例*: `MATCH (s {id: $source}) WHERE s.mp > 10 RETURN true`


3. **Execution Chain (执行链)**:
* 有序的原子操作列表。
* `modify_graph`: 修改 Neo4j 数据。
* `record_event`: 写入 Postgres 审计日志。
* `memorize`: 生成向量记忆。



### 3.3 规则与行为关联矩阵

| 用户意图 (Synapser) | 动作 ID (Action) | 验证层 (Validation) | 后果层 (Rules) |
| --- | --- | --- | --- |
| "攻击那个兽人" | `ACT_ATTACK` | 检查距离 < 2m | 扣除 HP, 播放动画, 记录仇恨 |
| "去村长家" | `ACT_MOVE` | 检查路径连通性 | 更新 `LOCATED_AT` 关系 |
| "制作药水" | `ACT_CRAFT` | 检查背包原料 | 删除原料, 创建新物品节点 |

---

## 4. 行为模型 (Behavior Model)

行为模型描述系统如何动态响应外部输入和内部状态变化。

### 4.1 行为模型层次结构 (Behavior Stack)

1. **L1 - 感知层 (Synapser)**: 解析自然语言，提取意图和实体参数。
2. **L2 - 决策层 (Entity Linker)**: 解决指代消解（"它"指谁）和模糊匹配。
3. **L3 - 执行层 (Action Driver)**: 事务性地执行规则链。

### 4.2 核心行为详细定义

**实体链接行为 (Entity Linking)**

* **输入**: 文本提及 ("那个守卫"), 当前上下文 (Location ID)
* **逻辑**:
1. 获取当前 Location 所有可见对象。
2. 计算文本与对象名称/同义词的相似度。
3. 返回置信度最高的 `object_id`。



**自适应反馈行为 (Adaptive Feedback)**

* **机制**: LLM 旁白生成。
* **逻辑**: 根据 Rule 执行结果（HP 变化、位置变化）生成沉浸式文本描述，而不是生硬的系统提示。

### 4.3 行为模型伪代码示例 (Action Execution Flow)

```python
def execute_behavior(user_input, context):
    # 1. 解析意图
    intent = Synapser.parse(user_input) # -> {action: "ACT_ATTACK", targets: ["orc_1"]}
    
    # 2. 实体链接确认
    target_obj = EntityLinker.resolve(intent.targets[0], context)
    
    # 3. 加载动作定义 (PIM)
    action_def = Repository.get_action(intent.action)
    
    # 4. 验证 (Validation)
    if not CypherEngine.validate(action_def.validation, params={s: context.player, t: target_obj}):
        return "动作无效：条件不满足"
        
    # 5. 执行规则 (Rules Execution)
    with Transaction():
        for rule in action_def.rules:
            if rule.type == 'modify_graph':
                Neo4j.execute(rule.statement)
            elif rule.type == 'record_event':
                AuditLog.write(rule.template)
                
    # 6. 状态回传
    return StateManager.get_changes()

```

---

## 5. 流程模型 (Process Model)

定义使用 Genesis Forge 进行开发的生命周期流程。

### 5.1 流程模型架构

采用 **Git-Ops** 风格的开发流程：
`Draft (UI) -> Validate (Schema) -> Commit (Git) -> Hot Reload (Engine)`

### 5.2 核心流程定义

**1. 本体开发流程 (Ontology Dev Flow)**

1. 开发者在 Forge 可视化界面新建 `ObjectType` 或 `Action`。
2. 利用 **AI Copilot** 自动补全属性和 Cypher 逻辑。
3. 在“沙箱环境”输入模拟指令测试 Action。
4. 点击“保存”，系统执行 Pydantic 校验。
5. 系统自动生成 Git Commit。

**2. 实时调试流程 (Live Ops Flow)**

1. 游戏引擎运行在 Debug 模式。
2. Forge 修改参数（如火球术伤害 20 -> 30）。
3. Forge 发送 `RELOAD_SIGNAL` 给引擎。
4. 引擎重新加载 JSON 配置（无需重启进程）。
5. 下一回合攻击立即生效。

### 5.3 流程与行为映射

| 阶段 | 开发者行为 | 系统行为 | 产物 |
| --- | --- | --- | --- |
| **设计** | 拖拽节点，连接关系 | UI 渲染图谱，AI 推荐属性 | 草稿 JSON |
| **验证** | 点击“检查一致性” | 运行 Schema 校验和孤立节点检查 | 错误报告 / 通过 |
| **发布** | 点击“部署/保存” | Git Commit, 触发热重载 | 版本化 Ontology |

---

## 6. 原子服务清单 (Atomic Services)

Genesis Forge 后端 API 重构为微服务/模块化架构。

### 6.1 本体管理服务 (OntologyService)

* **职责**: 对 JSON/XML 文件的 CRUD，包含版本控制。
* **核心方法**:
* `load_schema(domain)`: 加载特定领域的定义。
* `save_entity(type, data)`: 保存实体定义并校验。
* `get_version_history()`: 获取 Git 提交记录。



### 6.2 世界仿真服务 (WorldService)

* **职责**: 与 Neo4j 交互，提供图谱数据预览和沙箱执行。
* **核心方法**:
* `preview_graph(query)`: 返回前端可视化所需的节点/边数据。
* `validate_connectivity()`: 检查地图是否连通。
* `reset_seed_data()`: 重置世界到初始状态。



### 6.3 智能辅助服务 (CopilotService)

* **职责**: 集成 LLM，提供生成式设计能力。
* **核心方法**:
* `generate_npc(description)`: 根据描述生成 NPC JSON。
* `text_to_cypher(natural_language)`: 将“扣血”转为 `SET n.hp = n.hp - x`。
* `suggest_actions(object_type)`: 推荐该类型实体应有的动作。



### 6.4 规则引擎服务 (RuleExecutionService)

* **职责**: 在 Forge 内部提供一种轻量级的 Action 模拟运行环境（Dry Run）。
* **核心方法**:
* `simulate_action(action_id, params)`: 返回如果不报错会发生什么状态改变。



---

## 7. AI Agent 使用指南 (For Developers)

Genesis Forge 内置 "Forge Copilot" Agent，辅助开发者构建世界。

### 7.1 Skills 文件结构

AI Copilot 的能力定义在 `tools/genesis_forge/ai_skills/`：

* `schema_aware_prompt.txt`: 包含当前 Ontology 结构的 System Prompt。
* `cypher_generator.py`: 专门用于生成和修复 Cypher 语句的工具链。

### 7.2 AI 处理用户请求的流程

1. **Context Loading**: 用户在编辑“兽人”时调用 AI，AI 自动加载“兽人”的现有属性作为上下文。
2. **Intent Analysis**: 识别用户是想“生成描述”、“生成属性”还是“生成动作逻辑”。
3. **Structured Output**: 强制 LLM 输出符合 JSON Schema 的格式（使用 Gemini 的 JSON Mode）。

### 7.3 AI 读取 Skills 的优先级

1. **User Constraints**: 用户在对话框输入的具体指令。
2. **Domain Rules**: 当前领域特定的风格指南（如：中世纪魔幻 vs 赛博朋克）。
3. **Schema Definition**: 必须遵守的硬性数据结构。

### 7.4 AI 操作示例

* **Prompt**: "帮我给这个兽人加一个狂暴技能，血量低于 30% 时伤害翻倍。"
* **AI Output (Action JSON)**:
```json
{
  "name": "Passive: Berserk",
  "validation": "MATCH (s) WHERE s.hp < s.max_hp * 0.3 RETURN true",
  "rules": [{"type": "modify_graph", "statement": "SET s.damage = s.damage * 2"}]
}

```



---

## 8. API 完整参考

RESTful API 设计，用于前端与 Forge 后端通信。

### 8.1 本体管理 API (Ontology)

* `GET /api/v1/domains`: 列出所有可用领域。
* `GET /api/v1/{domain}/objects`: 获取该领域所有对象类型。
* `POST /api/v1/{domain}/objects`: 创建/更新对象类型。
* *Body*: `{ "key": "Orc", "properties": {...} }`


* `GET /api/v1/{domain}/graph`: 获取可视化用的图数据 (Nodes/Edges)。

### 8.2 仿真与调试 API (Simulation)

* `POST /api/v1/simulation/sandbox/execute`: 沙箱试运行动作。
* *Body*: `{ "action": "ACT_ATTACK", "params": {...} }`


* `POST /api/v1/system/hot-reload`: 触发游戏引擎重载配置。

### 8.3 Copilot API

* `POST /api/v1/copilot/generate`: 生成内容。
* *Body*: `{ "type": "npc | action | cypher", "prompt": "..." }`



---

## 9. 错误处理

### 9.1 常见错误及处理

| 错误代码 | 错误类型 | 描述 | 处理方案 |
| --- | --- | --- | --- |
| `ERR_SCHEMA_01` | **ValidationError** | JSON 结构不符合 Pydantic 定义 | 前端高亮错误字段，禁止保存 |
| `ERR_CYPHER_02` | **LogicError** | 生成的 Cypher 语法错误 | 通过 `EXPLAIN` 预执行检查语法 |
| `ERR_REF_03` | **IntegrityError** | 引用了不存在的实体 ID | 运行完整性检查扫描器，列出断链 |

### 9.2 AI 错误回复模板

当 AI Copilot 无法生成有效代码时：

> "我理解您想要实现 [功能]，但当前的 Ontology 定义不支持 [属性]。建议先在 ObjectType 中添加该属性，或者我可以为您生成修改建议。"

---

## 10. 最佳实践

### 10.1 用户输入规范化

* **原子化提交**: 鼓励用户每次只修改一个 ObjectType 或 Action，避免大规模变更导致冲突。
* **ID 命名规范**: 强制使用大写下划线格式（如 `NPC_VILLAGER`），系统自动转换非法字符。

### 10.2 分步确认 (Step-by-Step Validation)

1. **Schema Check**: 输入框失去焦点时立即校验格式。
2. **Logic Check**: 保存时校验 Cypher 语法。
3. **Integration Check**: 部署时校验图谱完整性（是否有孤岛节点）。

---

**附录**:

* [Technical Design v0.4](cite: TECHNICAL_DESIGN.md)
* [Product Design v0.4](cite: PRODUCT_DESIGN.md)