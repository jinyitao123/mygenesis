这是一个为 **Genesis Forge/Engine** 设计的标准 `test_domain_fixtures` 数据集方案。该数据集旨在覆盖常见的边界情况（Edge Cases）和压力测试场景，用于 CI/CD 流程中的自动化测试初始化。

建议将此文件夹放置在 `MyGame/domains/test_fixtures/` 目录下。

### 1. 目录结构

```text
MyGame/domains/test_fixtures/
├── config.json              # 基础配置
├── object_types.json        # 定义包含极端情况的实体结构
├── seed_data.json           # 包含循环引用、超长文本、特殊字符的实例
├── action_types.json        # 用于触发边界条件的动作
└── synapser_patterns.json   # 简单的映射配置

```

---

### 2. 配置文件 (config.json)

定义该领域的元数据。

```json
{
  "domain_id": "test_fixtures",
  "domain_name": "Automated Testing Fixtures",
  "description": "A synthetic domain for unit testing, stress testing, and edge case validation.",
  "version": "1.0.0",
  "strict_mode": true
}

```

---

### 3. 实体类型定义 (object_types.json)

定义了专门用于测试的实体类型，包含各种数据类型的属性，并不设默认值以测试空值处理。

```json
{
  "TEST_CHAOS_ENTITY": {
    "display_name": "Chaos Entity",
    "description": "An entity designed to hold edge case data values.",
    "primary_key": "id",
    "properties": {
      "id": { "type": "string", "required": true },
      "name": { "type": "string", "required": true },
      "huge_text_field": { "type": "string", "required": false },
      "risk_value": { "type": "integer", "required": false },
      "is_active": { "type": "boolean", "default": true },
      "metadata": { "type": "json", "required": false }
    }
  },
  "TEST_GRAPH_NODE": {
    "display_name": "Graph Node",
    "description": "Used to test topology, cycles, and depth.",
    "properties": {
      "id": { "type": "string", "required": true },
      "weight": { "type": "integer", "default": 1 }
    }
  }
}

```

---

### 4. 种子数据 (seed_data.json) - **核心测试用例**

这是 Fixture 的核心，包含了具体的边缘情况数据。

```json
{
  "nodes": [
    {
      "type": "TEST_CHAOS_ENTITY",
      "properties": {
        "id": "node_normal",
        "name": "Normal Node",
        "risk_value": 50,
        "huge_text_field": "Short text."
      }
    },
    {
      "type": "TEST_CHAOS_ENTITY",
      "properties": {
        "id": "node_max_boundary",
        "name": "Boundary Values",
        "risk_value": 2147483647,
        "huge_text_field": "Boundary check for max integer."
      }
    },
    {
      "type": "TEST_CHAOS_ENTITY",
      "properties": {
        "id": "node_long_text",
        "name": "Long Text Holder",
        "risk_value": 0,
        "huge_text_field": "LOREM_IPSUM_REPEAT_1000_TIMES..." 
        // 实际文件中应生成 10KB+ 的字符串
      }
    },
    {
      "type": "TEST_CHAOS_ENTITY",
      "properties": {
        "id": "node_special_chars",
        "name": "Inject & Unicode",
        "huge_text_field": "测试中文 🤖 Emoji ' OR 1=1; -- DROP TABLE; <script>alert(1)</script> \\n \\t \\u0000"
      }
    },
    {
      "type": "TEST_CHAOS_ENTITY",
      "properties": {
        "id": "node_empty_props",
        "name": "Empty Attributes",
        "huge_text_field": "",
        "risk_value": null
      }
    },
    { "type": "TEST_GRAPH_NODE", "properties": { "id": "cycle_A" } },
    { "type": "TEST_GRAPH_NODE", "properties": { "id": "cycle_B" } },
    { "type": "TEST_GRAPH_NODE", "properties": { "id": "cycle_C" } },
    { "type": "TEST_GRAPH_NODE", "properties": { "id": "self_ref_node" } },
    { "type": "TEST_GRAPH_NODE", "properties": { "id": "isolate_node" } }
  ],
  "relationships": [
    {
      "type": "CONNECTED_TO",
      "source": "cycle_A",
      "target": "cycle_B",
      "properties": { "type": "circular_link_1" }
    },
    {
      "type": "CONNECTED_TO",
      "source": "cycle_B",
      "target": "cycle_C",
      "properties": { "type": "circular_link_2" }
    },
    {
      "type": "CONNECTED_TO",
      "source": "cycle_C",
      "target": "cycle_A",
      "properties": { "type": "circular_link_3" } 
      // ⚠️ 构成 A->B->C->A 闭环，测试递归查询是否死循环
    },
    {
      "type": "CONNECTED_TO",
      "source": "self_ref_node",
      "target": "self_ref_node",
      "properties": { "type": "self_reference" }
      // ⚠️ 自引用测试
    }
  ]
}

```

---

### 5. 动作定义 (action_types.json)

定义用于触发这些边缘情况的动作，用于集成测试。

```json
{
  "ACT_TEST_CYCLE": {
    "display_name": "Test Cycle Traversal",
    "parameters": ["start_node_id"],
    "validation": {
      "logic_type": "cypher_check",
      "statement": "MATCH (n {id: $start_node_id}) RETURN n IS NOT NULL"
    },
    "rules": [
      {
        "type": "modify_graph",
        "statement": "MATCH (n {id: $start_node_id})-[:CONNECTED_TO*1..5]->(m) SET m.visited = true"
        // 测试 Cypher 是否能在环状结构中正确终止 (*1..5 限制)
      }
    ]
  },
  "ACT_TEST_INJECTION": {
    "display_name": "Test Injection Output",
    "parameters": ["target_id"],
    "validation": {
      "logic_type": "cypher_check",
      "statement": "MATCH (n {id: $target_id}) RETURN true"
    },
    "rules": [
      {
        "type": "record_event",
        "summary_template": "Read value: {target_name}" 
        // 验证日志系统是否正确转义特殊字符
      }
    ]
  }
}

```

---

### 6. 使用说明 (Usage in Automation)

在编写 Python 测试脚本（如 `pytest`）时，可以使用 `fixtures` 加载此数据集：

```python
# test_integration_fixtures.py

import pytest
from genesis.kernel.game_engine import GameEngine

@pytest.fixture
def fixture_engine():
    # 指向 test_fixtures 目录初始化引擎
    engine = GameEngine(domain_path="domains/test_fixtures")
    engine.initialize_world()
    return engine

def test_circular_reference_safety(fixture_engine):
    """验证在环状结构中执行查询不会导致栈溢出或无限循环"""
    result = fixture_engine.process_input("Trigger cycle test on cycle_A")
    assert result['status'] == 'success'
    # 验证是否正确处理了深度限制
    
def test_special_characters_rendering(fixture_engine):
    """验证特殊字符和注入攻击字符串被安全处理"""
    node = fixture_engine.object_manager.get("node_special_chars")
    assert "DROP TABLE" in node['huge_text_field']
    # 确保没有实际执行 SQL 删除操作

```