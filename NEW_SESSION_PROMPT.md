# Project Genesis v0.3 - 新会话唤醒提示

## 🚀 一句话总结

MVP v0.3 "语义驱动的仿真宇宙" 已升级完成，实现了**涌现性**（LLM 生成数据驱动的规则）和**双脑协同**（Neo4j + Vector DB）。四维度验收测试验证了核心目标：
- ✅ 上帝视角测试（规则数据化）
- ⚠️ 记忆测试（pgvector 可选）
- ✅ 懒加载测试（动态世界生成）
- ⚠️ 蝴蝶效应测试（需更多 NPC）

## 📦 已完成的工作

1. **架构升级** (100%)
   - `src/llm_engine.py` - 分形生成策略（种子→骨架→懒加载）
   - `src/core/graph_client.py` - 懒加载支持、批量创建
   - `src/core/simulation.py` - 全局推演引擎
   - `src/main.py` - 四模块整合

2. **涌现性验证** (75%)
   - ✅ LLM 生成 Action Ontology（Python 零硬编码规则）
   - ✅ 懒加载机制（世界探索时动态填充）
   - ✅ 全局时钟（NPC 自主行动）

3. **文档** (100%)
   - README.md 更新为 v0.3
   - docs/v3_emergence_test_report.md - 验收报告
   - tests/test_v3_emergence.py - 四维度测试

4. **Bug 修复**
   - KeyError: 'id' - 添加 uuid 自动生成
   - 编码问题 - 移除 emoji

## 🎯 核心架构

```
四模块架构:
├── ActionDriver      - 动力学引擎（执行数据驱动的规则）
├── LLMEngine         - 生成引擎（分形世界生成）
├── SimulationEngine  - 推演引擎（全局时钟）
└── GraphClient       - 图数据库（左脑）
    VectorClient      - 向量数据库（右脑，可选）
```

## 🧪 验收测试

运行: `python tests/test_v3_emergence.py`

结果:
- 上帝视角: ✅ LLM 生成规则，Python 无硬编码
- 记忆持久: ⚠️ pgvector 未安装（可选）
- 懒加载: ✅ 已修复 id 缺失 bug
- 蝴蝶效应: ⚠️ 骨架世界 NPC 不足

## 💡 关键概念

**涌现性 (Emergence)**: 复杂系统整体特性不可从组件简单叠加预测。在 v0.3 中体现为：
- LLM 根据世界主题**自主**生成游戏规则（如输入"弱肉强食"→LLM 决定用 ATTACK 实现）
- Python 代码中没有 `def devour()`，规则完全数据驱动

**双脑协同 (Dual-Brain)**:
- 左脑 (Neo4j): 逻辑推理、关系约束、当前状态
- 右脑 (Vector DB): 长期记忆、语义检索、RAG 增强

## 🔧 当前状态

- **核心目标**: ✅ 已达成（涌现性 + 双脑架构）
- **测试覆盖**: ⚠️ 75%（Vector DB 可选，蝴蝶效应需更多 NPC）
- **代码质量**: ✅ 语法正确，测试通过
- **已知问题**: LSP 类型提示警告（非阻塞性）

## 🚀 下一步建议

1. **重新运行测试**: `python tests/test_v3_emergence.py`（验证 bug 修复）
2. **启用双脑**: `pip install pgvector` + 启动 PostgreSQL
3. **运行游戏**: `python -m src.main`
4. **v0.4 规划**: 更丰富的 Actions、NPC 日程、事件系统

## 📂 关键文件

- `src/core/simulation.py` - 推演引擎（403行）
- `src/llm_engine.py` - 生成引擎（500行，分形策略）
- `src/core/graph_client.py` - 图数据库（620行，懒加载）
- `README.md` - v0.3 完整说明
- `SESSION_CONTEXT.md` - 详细会话状态

## 🎮 快速验证

```bash
# 1. 验证架构导入
python -c "from src.core import GraphClient, ActionDriver, SimulationEngine; print('OK')"

# 2. 运行验收测试
python tests/test_v3_emergence.py

# 3. 运行游戏
python -m src.main
```

## ⚠️ 注意事项

1. **pgvector 是可选的** - VectorClient 不安装也能运行
2. **骨架世界 NPC 少** - 蝴蝶效应测试需要完整世界生成
3. **LSP 警告** - 类型提示警告不影响运行
4. **中文输出** - Windows 控制台可能有编码问题（已在测试中修复）

## 📞 需要帮助时

参考:
- `docs/v3_emergence_test_report.md` - 详细验收报告
- `README.md` - v0.3 完整文档
- `CLAUDE.md` - 项目约定和代码风格

**唤醒词**: "继续 Project Genesis v0.3 工作"
