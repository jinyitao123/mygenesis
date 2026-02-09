这是针对 **Project Genesis** 设计的 **Mock LLM (Replay 模式)** 实现方案。该方案通过拦截 LLM API 调用，实现了“录制/回放”机制，既能显著降低回归测试成本，又能确保每日构建（Daily Build）时的真实性验证。

### 1. 设计架构 (Architecture)

采用了 **拦截器模式 (Interceptor Pattern)**，在测试运行时动态替换 `Synapser._call_api` 方法。

* **Mode: REPLAY (默认)**
* 读取本地 JSON 缓存文件。
* 根据 `hash(prompt + model)` 查找缓存。
* 如果命中，直接返回录制好的响应（耗时 < 10ms，零 Token 消耗）。
* 如果未命中，抛出 `CacheMissError`（防止静默失败）。


* **Mode: RECORD**
* 调用真实 LLM API。
* 将 `(prompt, response)` 写入本地 JSON 缓存。
* 用于生成或更新测试数据。


* **Mode: REAL (Daily Build)**
* 直接透传调用真实 API，不读取也不写入缓存。
* 用于验证 LLM 模型本身的能力变更或 API 兼容性。



### 2. 核心实现代码

建议在 `tests/utils/` 目录下创建 `llm_mocker.py`。

```python
# tests/utils/llm_mocker.py

import json
import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("LLMMocker")

class LLMReplay:
    def __init__(self, cache_file: str = "tests/fixtures/llm_cache.json"):
        self.mode = os.getenv("LLM_TEST_MODE", "REPLAY").upper()  # REPLAY | RECORD | REAL
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, Any] = {}
        self._load_cache()
        
        logger.info(f"LLM Replay initialized in [{self.mode}] mode. Cache: {self.cache_file}")

    def _load_cache(self):
        """加载缓存文件"""
        if self.mode in ["REPLAY", "RECORD"] and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except json.JSONDecodeError:
                logger.warning("LLM Cache file is corrupt, starting empty.")
                self.cache = {}

    def _save_cache(self):
        """保存缓存文件"""
        if self.mode == "RECORD":
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2, sort_keys=True)

    def _generate_key(self, model: str, prompt: str) -> str:
        """生成唯一的缓存 Key"""
        # 组合模型和提示词，防止不同模型的响应混淆
        content = f"{model}:{prompt}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def mock_call_api(self, original_method):
        """
        生成用于替换 Synapser._call_api 的 Mock 函数
        
        Args:
            original_method: 原始的 _call_api 方法（用于 RECORD/REAL 模式调用）
        """
        def wrapper(instance, model: str, prompt: str) -> str:
            if self.mode == "REAL":
                # 每日构建模式：直接穿透
                return original_method(model, prompt)

            key = self._generate_key(model, prompt)

            # REPLAY 模式：查缓存
            if self.mode == "REPLAY":
                if key in self.cache:
                    logger.debug(f"LLM Cache HIT: {key}")
                    return self.cache[key]
                else:
                    error_msg = (
                        f"LLM Cache MISS for key {key}.\n"
                        f"Prompt snippet: {prompt[:50]}...\n"
                        f"Please run tests with LLM_TEST_MODE=RECORD to update cache."
                    )
                    raise ValueError(error_msg)

            # RECORD 模式：调用并保存
            if self.mode == "RECORD":
                logger.info(f"Recording LLM response for {key}...")
                response_text = original_method(model, prompt)
                self.cache[key] = response_text
                self._save_cache()
                return response_text
            
            return ""

        return wrapper

```

### 3. Pytest 集成 (Fixture)

在 `tests/conftest.py` 中配置 Fixture，自动应用 Mock。

```python
# tests/conftest.py

import pytest
from genesis.kernel.synapser import Synapser
from tests.utils.llm_mocker import LLMReplay

# 初始化全局 Mocker
llm_mocker = LLMReplay(cache_file="tests/fixtures/llm_responses.json")

@pytest.fixture(autouse=True)
def mock_llm_api(monkeypatch):
    """
    自动拦截所有测试中的 LLM 调用
    """
    # 获取原始未绑定的方法
    original_call_api = Synapser._call_api
    
    # 创建绑定实例的 wrapper
    # 注意：_call_api 是实例方法，original_method 在 wrapper 中被调用时需要处理 self
    
    def side_effect(self, model, prompt):
        # 定义一个简单的 lambda 或局部函数来适配 LLMReplay 的接口
        # 这里我们需要传入一个能真正执行调用的闭包
        def real_executor(m, p):
            # 使用 requests 真正调用 API (复制原 Synapser._call_api 的核心逻辑或直接调用)
            # 更好的方式是：在 patch 之前保留原始方法的引用
            return original_call_api(self, m, p)
            
        return llm_mocker.mock_call_api(real_executor)(self, model, prompt)

    # 应用 Monkeypatch
    monkeypatch.setattr(Synapser, "_call_api", side_effect)

```

### 4. 使用示例与工作流

#### 场景 A：编写新测试（Record Mode）

当你开发新功能或编写新测试用例时，本地还没有对应的 LLM 响应缓存。

1. **设置环境变量**：
```bash
export LLM_TEST_MODE=RECORD
export LLM_API_KEY=your_real_key

```


2. **运行测试**：
```bash
pytest tests/test_synapser.py

```


3. **结果**：测试会慢（因为调用了真实 API），但会在 `tests/fixtures/llm_responses.json` 中生成缓存条目。

#### 场景 B：常规回归测试（Replay Mode）

CI/CD 中的普通 Push 或 MR Check，以及开发者的日常运行。

1. **设置环境变量**（默认）：
```bash
export LLM_TEST_MODE=REPLAY
# 不需要 API Key

```


2. **运行测试**：
```bash
pytest tests/

```


3. **结果**：测试极快，完全确定性，无网络依赖。如果遇到未录制的 Prompt，测试会报错提示。

#### 场景 C：每日构建（Daily Build / Real Mode）

每晚运行，确保 Prompt 依然能被新版本的模型正确理解。

1. **CI 配置**：
```bash
export LLM_TEST_MODE=REAL
export LLM_API_KEY=secret_key

```


2. **运行测试**：
```bash
pytest tests/

```


3. **结果**：验证整个链路的真实有效性。

### 5. 缓存文件管理 (`llm_responses.json`)

这个 JSON 文件应当**提交到 Git 仓库**中。

```json
{
  "a1b2c3d4...": "{\"action_id\": \"ACT_ATTACK\", \"target\": \"npc_orc_1\", \"narrative\": \"你挥剑砍向兽人\"}",
  "e5f6g7h8...": "{\"action_id\": \"ACT_MOVE\", \"target\": \"loc_library\", \"narrative\": \"你走进藏书室\"}"
}

```

### 6. 扩展建议：模糊匹配

当前的 Hash 匹配非常严格（Prompt 差一个标点符号都会导致 Cache Miss）。为了提高鲁棒性，可以在 `REPLAY` 模式下增加**语义模糊匹配**（可选）：

* 如果精确 Hash 未命中，计算输入 Prompt 与缓存中 Key 对应的 Prompt 的 Levenshtein 距离。
* 如果相似度 > 98%，则复用缓存并打印警告。
* *注意：这会增加测试框架的复杂性，建议仅在 Prompt 经常微调的阶段使用。*

### 7. 针对 `Synapser` 的特定测试用例

```python
# tests/test_synapser.py

def test_synapser_fallback_to_llm(mock_llm_api):
    """
    测试当 Pattern 匹配失败时，LLM 能正确解析意图。
    该测试在 REPLAY 模式下不需要真实网络。
    """
    synapser = Synapser()
    context = {
        "location": {"name": "大厅"},
        "entities": ["守卫"],
        "available_actions": ["ACT_ATTACK"]
    }
    
    # 这一步在 RECORD 模式下会调用 API 并保存
    # 在 REPLAY 模式下会直接读取 JSON
    result = synapser.parse_intent("痛扁那个守卫", context)
    
    assert result["action_id"] == "ACT_ATTACK"
    assert result["params"]["target_name"] == "守卫"

```