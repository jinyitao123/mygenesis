这是一个针对 **Genesis Forge (Studio Edition)** 的完整、详细的 UI 自动化测试用例集。

这份测试用例设计**严格遵循前端与后端的实际联动逻辑**，涵盖了启动、编辑、可视化、AI 生成及持久化存储的全流程。特别针对此前发现的“Neo4j 连接失败”和“API 路径错误”等集成风险点进行了针对性覆盖。

您可以直接将此文档作为编写 Cypress 或 Playwright 自动化脚本的蓝本。

---

# Genesis Forge (Studio Edition) - UI 自动化集成测试用例规格书

**文档类型**: 自动化测试用例 (E2E)
**适用框架**: Cypress / Playwright
**测试环境**:

* Frontend: `http://localhost:3000` (Vue 3 Dev Server)
* Backend: `http://localhost:5000` (Flask API)
* Database: File System (JSON/XML) + Neo4j (Optional)

---

## 模块一：启动与领域加载 (Launcher & Initialization)

此模块验证前端能否正确从后端获取领域列表，并完成编辑器的初始化配置。

### TC-INIT-01: 领域列表加载与展示

* **前置条件**: 后端服务已启动，`domains/` 目录下存在 `supply_chain` 文件夹。
* **测试步骤**:
1. 访问 `http://localhost:3000/`。
2. 等待页面加载完成 (`FCP`).
3. 拦截并监听 `GET /api/v1/domains` 请求。


* **预期结果 (前端)**:
1. 页面显示“Genesis Forge”标题。
2. 显示至少一个领域卡片（如 "Supply Chain"）。
3. 卡片应包含图标、名称和描述。


* **预期结果 (后端/网络)**:
1. `GET /api/v1/domains` 返回状态码 **200 OK**。
2. 响应体 JSON 结构包含: `[{ "key": "supply_chain", "name": "Supply Chain Logistics", ... }]`。



### TC-INIT-02: 领域选择与编辑器初始化 (关键路径)

* **前置条件**: 在启动页 (Launcher)。
* **测试步骤**:
1. 点击 "Supply Chain" 领域卡片。
2. 拦截 `POST /api/domains/supply_chain` 或 `GET /api/v1/domains/supply_chain/config` (根据实际路由实现)。
3. 验证页面跳转至 `/editor` 或 `/studio`。


* **预期结果 (前端)**:
1. URL 变更为 `/editor`。
2. 顶部导航栏 (TopBar) 显示 "Domain: Supply Chain"。
3. 左侧侧边栏 (SideBar) 加载出资源树（Object Types, Actions）。
4. **关键检查**: 不应出现“配置加载失败”的红色 Toast 弹窗。


* **预期结果 (后端/联动)**:
1. 后端日志显示 `Activated domain: supply_chain`。
2. 如果缺少配置文件（如日志中提到的 `object_types.xml` 缺失），前端应弹出警告模态框提示“初始化文件缺失，是否创建默认模板？”而不是白屏。



---

## 模块二：本体管理与代码编辑 (Ontology & Editor)

此模块验证 Monaco Editor 与 Flask 后端的文件读写联动。

### TC-ONTO-01: 实体类型定义 (Schema) 的读取

* **前置条件**: 进入编辑器界面，默认选中 "Object Types" 视图。
* **测试步骤**:
1. 点击左侧侧边栏的 "Object Types"。
2. 检查中间代码编辑器 (Monaco Editor) 的内容。


* **预期结果 (前端)**:
1. 编辑器不为空，显示 XML/JSON 内容。
2. 内容应包含 `<ObjectType>` 或对应的 JSON 结构。


* **预期结果 (后端/联动)**:
1. 触发 `GET /api/v1/domains/supply_chain/objects`。
2. 响应数据与 `domains/supply_chain/schema.json` (或 xml) 文件内容一致。



### TC-ONTO-02: 代码修改与脏状态检测

* **前置条件**: 编辑器已加载内容。
* **测试步骤**:
1. 在编辑器中插入一行注释 ``。
2. 观察顶部工具栏的“保存”按钮状态。
3. 尝试刷新浏览器页面。


* **预期结果 (前端)**:
1. Tab 标签页出现未保存标记（如 `*` 号）。
2. “保存”按钮从“灰色/禁用”变为“高亮/可用”。
3. 浏览器弹出 `beforeunload` 警告：“您有未保存的更改”。



### TC-ONTO-03: 保存操作与后端持久化 (完整闭环)

* **前置条件**: 编辑器处于“脏”状态（有未保存修改）。
* **测试步骤**:
1. 点击顶部工具栏的“保存 (Save)”按钮。
2. 拦截 `POST /api/v1/domains/supply_chain/objects`。
3. 等待保存完成动画。


* **预期结果 (前端)**:
1. 保存按钮进入 Loading 状态。
2. 右上角弹出绿色 Toast: "Saved successfully"。
3. 脏状态标记消失。


* **预期结果 (后端/联动)**:
1. API 返回状态码 **200 OK**。
2. **验证文件系统**: 读取服务器磁盘上的 `domains/supply_chain/schema.json`，确认包含步骤1中插入的注释字符串。



---

## 模块三：图谱可视化与数据联动 (Graph Visualization)

此模块验证 Cytoscape.js 组件与后端 WorldService 的交互，**重点处理 Neo4j 不可用的降级情况**。

### TC-VIS-01: 图谱数据加载 (Happy Path)

* **前置条件**: 切换到 "Graph View" (图谱视图) 标签页。
* **测试步骤**:
1. 点击 "Refresh Graph" 按钮。
2. 拦截 `GET /api/v1/domains/supply_chain/graph`。


* **预期结果 (前端)**:
1. 主画布显示节点 (Node) 和连线 (Edge)。
2. 节点颜色应根据 `type` (如 Warehouse, Truck) 区分。
3. 控制台无 JS 报错。


* **预期结果 (后端/联动)**:
1. 后端 API 返回标准 JSON 格式的图数据 `{ elements: { nodes: [], edges: [] } }`。



### TC-VIS-02: Neo4j 缺失时的降级处理 (Resilience Test)

* **前置条件**: 确认后端日志显示 `Neo4j features will be disabled`。
* **测试步骤**:
1. 点击 "Execute Cypher" 或 "Live Sync" 按钮。
2. 输入查询 `MATCH (n) RETURN n`。


* **预期结果 (前端)**:
1. **不应崩溃**。
2. UI 应显示警告提示：“数据库连接不可用，当前显示为静态文件预览”或“沙箱模式运行中”。
3. 如果是静态预览，应仅显示 `seed_data.json` 中的内容。



### TC-VIS-03: 可视化编辑同步到代码

* **前置条件**: 图谱视图和代码视图分屏显示 (如有此功能)，或来回切换。
* **测试步骤**:
1. 在图谱视图中右键点击空白处 -> "Add Node"。
2. 选择类型 "Warehouse"，输入 ID "WH_TEST_001"。
3. 切换回 "Code View" (Seed Data)。


* **预期结果 (前端)**:
1. 图谱中出现新节点。
2. **联动检查**: 代码编辑器中应自动增加对应的 JSON/XML 片段 `{"id": "WH_TEST_001", "type": "Warehouse" ...}`。
3. 应用状态变为“未保存”。



---

## 模块四：AI Copilot 智能辅助 (AI Integration)

此模块验证前端 Chat 组件与后端 CopilotService 的 SSE 流式交互。

### TC-AI-01: AI 面板唤起与连接

* **前置条件**: 在编辑器界面。
* **测试步骤**:
1. 点击底部状态栏的 "AI Copilot" 图标。
2. 检查面板展开状态。


* **预期结果 (前端)**:
1. 底部面板向上滑出。
2. 输入框自动聚焦。
3. 显示欢迎语：“我是 Genesis Copilot，请问有什么可以帮您？”



### TC-AI-02: 自然语言生成请求 (API Key 缺失场景)

* **前置条件**: 后端日志显示 `CHAT_API_KEY 未设置`。
* **测试步骤**:
1. 在 AI 输入框输入：“帮我生成一个兽人战士 NPC”。
2. 点击发送。
3. 拦截 `POST /api/v1/copilot/generate`。


* **预期结果 (前端)**:
1. 消息气泡显示“思考中...”。
2. 随后显示错误消息：“服务未配置 API Key，无法调用模型。” 或显示 **Mock 数据**（如果处于开发模式）。
3. **关键点**: 前端不应一直卡在 Loading 状态。


* **预期结果 (后端/联动)**:
1. 后端应返回 401 或 503 状态码，或返回包含 error message 的 JSON。



### TC-AI-03: 文本转 Cypher (Mock/Happy Path)

* **前置条件**: 假设后端已配置 Mock LLM 或真实 Key。
* **测试步骤**:
1. 输入：“查询所有生命值小于 50 的单位”。
2. 点击发送。


* **预期结果 (前端)**:
1. AI 回复框中显示生成的 Cypher 代码块：`MATCH (n:Unit) WHERE n.hp < 50 RETURN n`。
2. 代码块旁应有 "Run" 或 "Insert to Editor" 按钮。
3. 点击 "Insert" 后，代码自动插入到当前光标位置。



---

## 模块五：Git-Ops 版本控制 (Version Control)

### TC-GIT-01: 提交更改 (Commit)

* **前置条件**: 已保存一些更改，工作区是 clean 的。
* **测试步骤**:
1. 点击顶部工具栏的 "Git" 图标 -> "Commit"。
2. 在弹窗中输入提交信息 "Automated Test Commit"。
3. 点击确认。
4. 拦截 `POST /api/v1/git/commit`。


* **预期结果 (前端)**:
1. 显示提交进度条。
2. 成功后提示 "Commit Hash: a1b2c3d..."。


* **预期结果 (后端/联动)**:
1. 后端调用 `gitpython` 完成提交。
2. 验证 `.git/HEAD` 发生了变化。



---

## 模块六：错误处理与边界测试 (Error Handling)

### TC-ERR-01: 后端服务断连

* **前置条件**: 正常打开编辑器。
* **测试步骤**:
1. **手动停止 Flask 后端服务** (模拟服务器崩溃)。
2. 在前端点击“保存”按钮。


* **预期结果 (前端)**:
1. 请求超时或立即失败。
2. 界面弹出红色错误：“连接服务器失败 (Network Error)”。
3. **数据保护**: 编辑器内容**不应清空**，允许用户复制备份。



### TC-ERR-02: 404 路由容错

* **前置条件**: 前端代码中某个 API 地址写错 (模拟当前日志中的 404 情况)。
* **测试步骤**:
1. 触发该功能 (如点击 "Hot Reload")。
2. 后端返回 404 Not Found。


* **预期结果 (前端)**:
1. UI 优雅降级：按钮恢复可点击状态，提示“功能暂时不可用”。
2. 控制台打印详细错误路径，方便开发者调试。



### TC-ERR-03: 非法数据校验

* **前置条件**: Schema 定义 `age` 必须为数字。
* **测试步骤**:
1. 在 JSON 编辑器中将 `age` 修改为 `"unknown"` (字符串)。
2. 点击保存。


* **预期结果 (前端)**:
1. 保存失败。
2. 底部 "Validation" 面板自动弹出。
3. 显示错误详情：`Line 15: "age" expected integer, got string`。


* **预期结果 (后端/联动)**:
1. 后端 Pydantic 校验抛出 `ValidationError`。
2. API 返回 400 Bad Request 及错误详情列表。