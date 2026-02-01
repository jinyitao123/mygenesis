## FEATURE:

构建 Project Genesis MVP - 一个基于知识图谱和LLM的生成式文字冒险游戏引擎。

核心功能需求：
1. **三层架构实现**：
   - Python胶水层：业务逻辑编排
   - Neo4j持久层：图数据库存储游戏世界状态
   - LLM语义层：OpenAI API驱动世界生成和意图解析

2. **上帝模式世界生成**：
   - 用户输入自然语言描述（如"充满赛博格僵尸的废弃空间站"）
   - LLM生成包含Player、Location、NPC、Item的JSON图谱结构
   - 自动创建Neo4j节点和关系

3. **基础交互系统**：
   - 支持三个原子动作：Move（移动）、Look（观察）、Attack（攻击）
   - 自然语言意图解析（如"逃到书房"→MOVE intent）
   - 图谱连通性验证（防止穿墙）

4. **CLI游戏界面**：
   - 彩色终端输出（使用colorama）
   - 实时显示位置、描述、出口、可见实体、HP
   - AI旁白叙事

5. **MVP简化机制**：
   - 基础战斗：敌对NPC自动对玩家造成伤害
   - 单玩家模式（无并发）
   - 无复杂规则引擎（Alpha阶段添加）

## EXAMPLES:

需要参考以下示例模式（存放在examples/目录）：
- `neo4j_client.py` - Neo4j连接和Cypher查询模式
- `llm_json_parser.py` - LLM结构化JSON输出处理
- `cli_game_loop.py` - 命令行游戏主循环模式
- `test_graph_ops.py` - 图数据库操作测试模式

## DOCUMENTATION:

- Neo4j Python Driver: https://neo4j.com/docs/python-manual/current/
- OpenAI API: https://platform.openai.com/docs/api-reference
- python-dotenv: https://saurabh-kumar.com/python-dotenv/
- colorama: https://pypi.org/project/colorama/

项目设计文档位于：`docs/plans/2026-02-01-project-genesis-mvp-design.md`

## OTHER CONSIDERATIONS:

1. **LLM容错**：LLM可能返回无效JSON，需要try/except捕获并回退到静态模板世界
2. **Neo4j连接**：启动时必须验证数据库连接，失败时给出清晰错误提示
3. **意图识别约束**：MOVE意图的目标必须是当前位置通过CONNECTED_TO关系可达的地点
4. **环境变量**：使用.env文件管理OPENAI_API_KEY和Neo4j连接信息，绝不硬编码
5. **中文支持**：所有用户可见字符串使用中文，但技术ID使用英文（如节点id）
6. **测试覆盖**：每个核心函数必须有pytest测试（正常用例、边界、错误）
7. **代码长度**：单文件不超过300行，过长则拆分模块
8. **错误处理**：所有外部调用（LLM API、Neo4j）必须有错误处理，不抛出未处理异常
9. **Type Hints**：所有函数必须添加类型注解
10. **Pydantic验证**：LLM返回的JSON必须经Pydantic模型验证
