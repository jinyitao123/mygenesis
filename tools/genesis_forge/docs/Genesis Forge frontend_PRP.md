这是一个基于 **HTMX + Alpine.js** 轻量化技术栈的 **Genesis Forge (Studio Edition)** 前端完整产品参考规划 (PRP) 与交互设计方案。

本方案旨在不引入 Node.js/Webpack 复杂构建流程的前提下，实现媲美原生 IDE 的流畅交互体验。

---

# Genesis Forge (Studio Edition) - 前端产品参考规划 (PRP)

**版本**: v2.0 (Lightweight Studio)
**架构模式**: Server-Driven UI (HATEOAS)
**核心理念**: 后端控制逻辑，前端只负责渲染与微交互。

## 1. 架构总览 (Architecture Overview)

采用 **"The HOWL Stack"** (Hypertext On Whatever Language)，利用 Python Flask 的强大渲染能力，结合现代浏览器特性。

* **HTML over the Wire (HTMX)**: 负责所有与服务器的数据交换（页面切换、表单提交、局部刷新）。不再传输 JSON，而是直接传输渲染好的 HTML 片段。
* **Behavior (Alpine.js)**: 负责“纯前端”的微交互（下拉菜单、Tab 切换、Modal 弹窗、拖拽状态），替代 Vue/React。
* **Styling (Tailwind CSS)**: 原子化 CSS，通过 CDN 或预处理文件引入，实现 IDE 级的深色模式界面。
* **Specialized Islands (专业组件)**:
* **Cytoscape.js**: 封装在 Alpine 组件中，负责 L1 图谱可视化。
* **Monaco Editor**: 封装在 Alpine 组件中，负责 L4 Ontology 代码编辑。



---

## 2. 核心界面布局 (UI Layout)

采用经典的 **IDE 三栏布局**，最大化工作区域。

### 2.1 全局框架 (`base.html`)

* **Top Bar (顶部指令栏)**:
* **左侧**: Logo + 当前领域面包屑 (如 `Supply Chain > dev`).
* **中间**: 全局搜索框 (支持命令模式 `> reload`).
* **右侧**: 状态指示器 (Git 分支、内存占用)、"Deploy" 按钮、"Hot Reload" 按钮。


* **Side Bar (左侧资源树)**:
* 可折叠文件树：`Object Types`, `Action Rules`, `Seed Data`。
* 资产库：可拖拽的实体模板 (用于图谱编辑)。


* **Main Stage (主工作区)**:
* 多 Tab 页签容器。
* 支持 **Split View (分屏)**: 左侧代码，右侧图谱预览。


* **Bottom Panel (底部面板)**:
* 可折叠。包含 `Console Logs` (WebSocket 实时日志), `AI Copilot` 对话框, `Validation` 错误列表。



---

## 3. 交互功能详细设计 (Interaction Design)

### 3.1 启动与领域管理 (Launcher)

* **交互目标**: 零等待感的领域切换。
* **实现逻辑**:
* 点击领域卡片时，触发 `hx-post="/api/switch_domain"`。
* 服务器设置 Session 并返回 `HX-Redirect: /studio/workspace`。
* **视觉反馈**: 卡片按下时有轻微下沉动画，加载时显示顶部进度条 (NProgress)。



### 3.2 资源管理器 (Resource Explorer)

* **交互目标**: 清晰的层级导航，支持右键菜单。
* **Alpine.js 实现**:
* 使用 `x-data="{ expanded: {} }"` 管理文件夹的折叠/展开状态。
* 点击文件时，触发 `hx-get="/studio/editor/file?path=..."`，目标指向 `hx-target="#main-stage"`。


* **文件状态**:
* 未保存文件显示小圆点 `●`。
* Git 修改过的文件显示颜色标记 (黄色/绿色)。



### 3.3 双模编辑器 (Dual-Mode Editor) - **核心难点**

这是 IDE 的灵魂，需要代码与图谱的实时联动。

#### A. 代码编辑模式 (Monaco Island)

* **初始化**: 页面加载时从 CDN 拉取 Monaco Loader。
* **HTMX 集成**:
* 创建一个隐藏的 `<textarea name="content">` 用于 HTMX 表单提交。
* Monaco 的 `onDidChangeModelContent` 事件同步更新 textarea 的值。


* **保存交互**:
* `Ctrl+S` 拦截：触发隐藏表单的 `hx-post="/api/save_file"`。
* **反馈**: 顶部 Save 按钮从 "灰色" -> "转圈" -> "绿色对勾"。



#### B. 图谱可视化模式 (Cytoscape Island)

* **交互**:
* **拖拽添加**: 从 Side Bar 拖拽一个 "NPC" 图标进入 Canvas，释放时触发 Alpine 事件，在 Canvas 坐标处创建节点，并后台调用 `POST /api/graph/node`。
* **连线**: 鼠标悬停节点边缘，拖出线条连接另一节点。


* **数据同步**:
* 当代码编辑器修改 XML/JSON 后，服务器返回 header `HX-Trigger: reload-graph`。
* 图谱组件监听 `body` 上的 `reload-graph` 事件，自动重新 fetch 图数据并增量更新布局（保持用户当前的缩放位置）。



### 3.4 AI 智能副驾驶 (Copilot Panel)

* **交互目标**: 流式打字机效果，上下文感知。
* **HTMX + SSE 实现**:
* 利用 `hx-ext="sse"` 连接 `/api/copilot/stream`。
* 用户输入 Prompt 后，后端推送一个个 `<div>` 片段追加到聊天窗口。


* **Actionable UI**:
* AI 回复中生成的 Cypher 代码块带有 "Apply" 按钮。
* 点击 "Apply" 触发 Alpine 逻辑，将代码直接插入到 Monaco 编辑器的光标处。



---

## 4. API 接口设计 (HTML Fragment Oriented)

接口不再返回 JSON 数据，而是直接返回 Jinja2 渲染好的 HTML 片段。

| Endpoint | Method | Response (HTML Fragment) | HTMX Action |
| --- | --- | --- | --- |
| `/studio/sidebar` | GET | `<ul>` 文件树列表 | `hx-trigger="load"` |
| `/studio/editor/code` | GET | `<div id="monaco-container">` + 初始值的 hidden input | `hx-target="#main-pane"` |
| `/studio/editor/graph` | GET | `<div id="cy-container">` + 初始化脚本 | `hx-target="#main-pane"` |
| `/api/save` | POST | Toast Notification HTML (`<div class="toast success">Saved!</div>`) | `hx-swap="none"` (仅通过 OOB 更新状态栏) |
| `/api/validate` | POST | Validation List Items (`<li>Error 1...</li>`) | 更新底部面板 |

---

## 5. 关键交互效果实现目标 (Interaction Goals)

### 5.1 "无刷新" 体验 (The SPA Feel)

* **目标**: 用户在切换文件、保存、运行仿真时，浏览器地址栏不闪烁，页面不白屏。
* **手段**: 全局使用 HTMX 的 `hx-boost="true"`，拦截所有链接点击，转换为 AJAX 请求并替换 `<body>` 内容。

### 5.2 实时脏数据检查 (Dirty State)

* **场景**: 用户修改了 XML 但未保存，试图切换领域。
* **效果**:
* Alpine 监听编辑器 `change` 事件，设置 `isDirty = true`。
* 全局拦截跳转链接：如果 `isDirty` 为真，弹出原生 `confirm` 或自定义 Modal。
* "Save" 按钮高亮变为橙色。



### 5.3 沉浸式图谱操作 (Immersive Graph Ops)

* **场景**: 在几百个节点的图谱中操作。
* **效果**:
* **LOD (Level of Detail)**: 缩小时只显示节点圆点，放大时显示详细属性和标签 (Cytoscape 样式优化)。
* **Focus Mode**: 点击某个节点，其余非邻接节点半透明化 (Dimming)。



### 5.4 智能反馈 (Smart Feedback)

* **场景**: 用户写错了 Cypher 语法。
* **效果**:
* 后端 Validation Engine 捕获错误。
* 返回带有 `HX-Trigger: open-bottom-panel` 的响应。
* 底部面板自动展开，显示红色错误条目，点击条目自动跳转到代码出错行。



---

## 6. 前端代码结构示例 (Project Structure)

```text
templates/
├── layout.html            # 引入 htmx.js, alpine.js, tailwind, monaco-loader
├── components/
│   ├── sidebar.html       # htmx-boost 链接
│   ├── navbar.html        # 全局状态
│   ├── editor_pane.html   # 包含 Monaco 初始化 JS
│   ├── graph_pane.html    # 包含 Cytoscape 初始化 JS
│   └── ai_panel.html      # SSE 连接区域
└── fragments/             # 专门用于 HTMX 局部替换的片段
    ├── file_tree.html
    ├── validation_result.html
    └── toast.html

```

### 核心代码片段示例 (Graph Pane)

```html
<div 
    class="w-full h-full relative bg-gray-900"
    x-data="{
        cy: null,
        init() {
            // 1. 初始化 Cytoscape
            this.cy = cytoscape({
                container: this.$refs.cy,
                elements: {{ graph_json | tojson }}, // Flask 注入初始数据
                style: [ ... ]
            });
            
            // 2. 监听来自 HTMX 的刷新事件
            document.body.addEventListener('reload-graph', (evt) => {
                this.refreshData();
            });
        },
        refreshData() {
            fetch('/api/graph/data').then(res => res.json()).then(data => {
                this.cy.json(data);
                this.cy.layout({ name: 'cola', animate: true }).run();
            });
        }
    }"
    x-init="init()"
>
    <div x-ref="cy" class="absolute inset-0"></div>
    
    <div class="absolute top-4 right-4 flex gap-2">
        <button @click="cy.fit()" class="btn-icon">Fit</button>
        <button hx-post="/api/graph/layout" hx-swap="none" class="btn-icon">Save Layout</button>
    </div>
</div>

```

此方案完美契合项目“轻量级、企业级功能”的目标，开发效率极高（Python 全栈即可掌控），且维护成本远低于 React/Vue 项目。