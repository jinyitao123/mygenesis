# Project Genesis - Product Design Document
# Project Genesis - 产品设计文档

**Version**: v0.4  
**Date**: 2026-02-04  
**Status**: Production Ready

---

## 1. 产品概述 (Product Overview)

### 1.1 产品定位
Project Genesis 是一个**企业级生成式仿真平台**，基于知识图谱 + LLM + 多模态存储构建。它不是传统游戏引擎，而是一个"世界模拟操作系统"，让 AI 生成的内容具备物理一致性和涌现性。

### 1.2 核心价值主张
- **真正的生成式**: 每次运行世界结构都不同，规则由 AI 动态生成
- **语义驱动**: 自然语言指令驱动游戏逻辑，无需硬编码
- **图谱约束**: Neo4j 硬逻辑验证确保世界一致性（防 LLM 幻觉）
- **涌现行为**: NPC 自主决策，产生不可预测但合理的故事

### 1.3 目标用户
- **游戏开发者**: 需要快速原型生成式游戏
- **AI 研究人员**: 研究多智能体涌现行为
- **叙事设计师**: 构建动态故事世界
- **教育/培训**: 创建沉浸式仿真环境

---

## 2. 核心功能 (Core Features)

### 2.1 五层架构 (Five-Layer Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 5: Presentation Layer (展示层)                              │
│   - Game CLI / Web Studio / REST API                              │
│   - 用户界面、输入输出、可视化                                     │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Ontology Layer (本体层)                                  │
│   - object_types.json: 实体定义                                   │
│   - action_types.json: 动作逻辑 (Validation + Rules)              │
│   - seed_data.json: 初始世界数据                                  │
│   - synapser_patterns.json: 意图映射                              │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: Kernel Layer (内核层)                                    │
│   - Synapser: 意图解析器 (自然语言 → Action)                      │
│   - ActionDriver: Validation → Rules 闭环执行器                   │
│   - RuleEngine: 多模态存储路由 (L1-L4)                            │
│   - ObjectManager: 通用对象 CRUD                                  │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: Infrastructure Layer (基础设施层)                        │
│   - L1 Neo4j: 当前状态图                                          │
│   - L2 PostgreSQL: 事件账本 (append-only)                         │
│   - L3 PostgreSQL + pgvector: 语义记忆                            │
│   - L4 VictoriaMetrics: 遥测数据 (预留)                           │
│   - L5 File: 配置文件                                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 关键特性

#### 2.2.1 Validation → Rules 操作闭环
**传统方式**:
```
用户输入 → 直接执行 → 副作用
```

**Genesis 方式**:
```
用户输入 → Validation (4阶段验证) → Rules (多模态存储) → 反馈

Validation 阶段:
1. 参数验证 (类型、必需性)
2. 对象引用验证 (存在性检查)
3. Cypher 业务验证 (连通性、状态)
4. 前置条件检查

Rules 阶段:
- modify_graph → Neo4j (L1)
- record_event → PostgreSQL (L2)
- memorize → PostgreSQL + pgvector (L3)
- record_telemetry → VictoriaMetrics (L4)
```

#### 2.2.2 实体链接系统 (Entity Linker)
解决自然语言模糊性问题：
- 同义词扩展（"守卫" = "卫兵" = "门卫"）
- 模糊匹配（相似度 > 0.6）
- 指代消解（"那个守卫" → 去除指代词）
- 上下文感知（仅搜索当前场景可见实体）

#### 2.2.3 意图解析双路径
1. **快速路径**: Pattern 匹配 + Entity Linking（< 10ms）
2. **智能路径**: LLM 解析（备用，处理复杂语句）

---

## 3. 用户旅程 (User Journey)

### 3.1 开发者旅程

**Step 1: 定义 Ontology** (5分钟)
```json
// action_types.json
{
  "ACT_CAST_FIREBALL": {
    "display_name": "火球术",
    "parameters": ["source_id", "target_id"],
    "validation": {
      "logic_type": "cypher_check",
      "statement": "MATCH (s {id: $source_id}) WHERE s.mp >= 10 RETURN true as is_valid"
    },
    "rules": [
      {"type": "modify_graph", "statement": "MATCH (t {id: $target_id}) SET t.hp = t.hp - 20"},
      {"type": "modify_graph", "statement": "MATCH (s {id: $source_id}) SET s.mp = s.mp - 10"},
      {"type": "record_event", "summary_template": "{source_name} 对 {target_name} 施放火球术"}
    ]
  }
}
```

**Step 2: 运行** (无需代码)
```bash
python -m applications.game.main
```

**Step 3: 玩家自然语言输入**
```
玩家: "对那个强盗施放火球术"
系统: 自动解析意图 → 验证 MP ≥ 10 → 执行扣血/扣蓝 → 记录事件
```

### 3.2 玩家旅程

```
1. 启动游戏 → 加载 Ontology → 初始化世界
2. 观察状态 (位置、出口、可见实体)
3. 自然语言输入 ("去藏书室"、"攻击守卫")
4. 意图解析 → 验证 → 执行 → 世界推演
5. 接收反馈 (成功/失败消息、AI 旁白、HP 变化)
6. 循环直到游戏结束
```

---

## 4. 竞品分析 (Competitive Analysis)

| 特性 | 传统文字游戏 | ChatGPT RPG | **Genesis v0.4** |
|------|------------|-------------|-----------------|
| 世界一致性 | ❌ 无 | ⚠️ 依赖模型记忆 | ✅ **Neo4j 硬约束** |
| 规则修改 | ❌ 改代码 | ❌ 重训练 | ✅ **改 JSON** |
| 涌现性 | ❌ 预设 | ⚠️ 幻觉风险 | ✅ **数据驱动** |
| 可观测性 | ❌ 难调试 | ❌ 黑盒 | ✅ **图谱可视化** |
| 多模态存储 | ❌ 单一 | ❌ 单一 | ✅ **L1-L4分层** |

**差异化优势**:
- 唯一结合 "LLM 语义理解 + 图谱硬约束" 的架构
- 业务逻辑完全数据化，零代码修改即可变更游戏规则

---

## 5. 成功指标 (Success Metrics)

### 5.1 技术指标
- ✅ 意图解析准确率: > 90% (Pattern) / > 85% (LLM)
- ✅ 图谱查询延迟: < 500ms
- ✅ 意图解析延迟: < 2s (LLM) / < 10ms (Pattern)
- ✅ 世界初始化时间: < 10s

### 5.2 体验指标
- ✅ 无需编程即可创建新动作类型
- ✅ 新增动作生效时间: < 5分钟 (仅改 JSON)
- ✅ 调试友好: Neo4j Browser 可视化世界状态

---

## 6. 路线图 (Roadmap)

### v0.4 (当前) - 企业级架构 ✅
- ✅ 五层架构重构
- ✅ Ontology 数据化
- ✅ Validation → Rules 闭环
- ✅ 实体链接系统

### v0.5 - 增强仿真
- 多玩家支持
- 时间系统（昼夜循环）
- NPC 日程/目标系统
- Web UI 可视化

### v0.6 - 生态扩展
- Ontology 市场（分享动作模板）
- 插件系统
- 多模态生成（图片/TTS）
- 云端托管

---

## 7. 商业模式 (可选)

### 7.1 开源核心
- Genesis Kernel (MIT License)
- 基础 Ontology 模板

### 7.2 商业增值
- **Genesis Studio**: Web 可视化编辑器
- **Cloud Hosting**: 托管世界服务器
- **Marketplace**: Ontology 模板交易
- **Enterprise**: SLA 支持、定制开发

---

**文档版本**: 1.0  
**最后更新**: 2026-02-04  
**作者**: AI Assistant
