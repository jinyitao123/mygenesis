# Genesis Forge Studio - HTMX + Alpine.js 前端实现

基于PRP文档的完整HTMX前端实现，采用Server-Driven UI架构。

## 架构概述

### 技术栈
- **HTMX**: HTML over the Wire，负责所有服务器通信
- **Alpine.js**: 客户端微交互和状态管理
- **Tailwind CSS**: 原子化CSS框架
- **Monaco Editor**: 代码编辑器（通过CDN加载）
- **Cytoscape.js**: 图谱可视化库
- **Flask + Jinja2**: 服务器端渲染

### 核心设计理念
1. **Server-Driven UI**: 后端控制UI状态，前端只负责渲染
2. **HTML over the Wire**: 传输渲染好的HTML片段，而非JSON数据
3. **渐进增强**: 基础功能无需JavaScript，增强功能使用Alpine.js
4. **实时交互**: 通过HTMX和SSE实现实时更新

## 项目结构

```
backend/templates/
├── base.html                    # 基础模板（包含所有JS/CSS依赖）
├── studio.html                  # 主IDE界面
├── components/                  # 可复用组件
│   ├── sidebar.html            # 左侧资源树
│   ├── editor_pane.html        # 代码编辑器面板
│   ├── graph_pane.html         # 图谱可视化面板
│   └── ai_panel.html           # AI Copilot面板
└── fragments/                  # HTMX片段模板
    ├── editor_content.html     # 编辑器内容片段
    ├── toast.html             # 通知消息片段
    └── validation_results.html # 验证结果片段

backend/api/
├── app_studio.py              # 主Flask应用
└── htmx_routes.py            # HTMX专用路由
```

## 核心功能实现

### 1. IDE三栏布局
- **顶部工具栏**: Logo、面包屑、全局搜索、状态指示器
- **左侧边栏**: 可折叠资源树、资产库拖拽
- **主工作区**: 多标签页（代码/图谱/分屏）
- **底部面板**: 可折叠控制台、AI Copilot、验证结果

### 2. 双模编辑器联动
- **代码编辑器**: Monaco Editor集成，支持JSON/XML语法高亮
- **图谱可视化**: Cytoscape.js交互式图谱
- **实时同步**: 代码修改触发图谱刷新事件

### 3. AI Copilot面板
- **SSE流式响应**: 实时打字机效果
- **上下文感知**: 自动加载当前编辑上下文
- **代码建议**: 一键应用到编辑器

### 4. HTMX API设计
所有API返回HTML片段而非JSON：

| 端点 | 方法 | 返回内容 | HTMX动作 |
|------|------|----------|-----------|
| `/studio/editor/object/<type>` | GET | 编辑器HTML片段 | `hx-target="#editor-container"` |
| `/api/save` | POST | Toast通知片段 | `hx-swap="none"` (OOB更新) |
| `/api/validate` | POST | 验证结果片段 | 更新底部面板 |
| `/api/graph/data` | GET | Cytoscape JSON数据 | 图谱组件内部使用 |
| `/api/copilot/stream` | GET | SSE事件流 | `hx-ext="sse"` |

## 交互效果

### 脏数据检查
- Monaco Editor内容变化时标记为脏数据
- 尝试离开页面时弹出确认对话框
- 保存按钮状态实时更新

### 实时验证
- 代码保存时自动验证语法
- 验证错误自动打开底部面板
- 点击错误项跳转到对应代码行

### 智能反馈
- Toast通知系统（成功/警告/错误）
- 加载进度条（NProgress集成）
- 操作状态实时反馈

## 开发指南

### 启动开发服务器
```bash
# 方法1: 使用启动脚本
scripts/start_htmx_studio.bat

# 方法2: 手动启动
cd tools/genesis_forge/backend/api
python app_studio.py
```

访问 http://localhost:5000/studio 进入IDE界面。

### 添加新组件
1. 在 `templates/components/` 创建组件HTML
2. 使用Alpine.js管理组件状态
3. 通过HTMX属性定义服务器交互
4. 在 `htmx_routes.py` 添加对应的API端点

### 扩展API
1. 返回HTML片段而非JSON
2. 使用HTMX响应头触发客户端事件
3. 支持OOB（Out of Band）更新多个元素

## 性能优化

### 前端优化
- **CDN加载**: 所有第三方库通过CDN加载
- **按需加载**: Monaco Editor按需初始化
- **本地存储**: Copilot对话历史本地保存
- **防抖处理**: 搜索和验证操作防抖

### 后端优化
- **片段缓存**: 常用HTML片段缓存
- **流式响应**: AI Copilot使用SSE流
- **增量更新**: 图谱数据增量刷新
- **连接池**: 数据库连接复用

## 浏览器兼容性

- Chrome 90+ ✓
- Firefox 88+ ✓
- Safari 14+ ✓
- Edge 90+ ✓

## 与Vue版本的对比

| 特性 | HTMX版本 | Vue 3版本 |
|------|----------|-----------|
| 构建复杂度 | 无需构建步骤 | 需要Webpack/Vite |
| 学习曲线 | 低（HTML/CSS为主） | 中（需要Vue知识） |
| 状态管理 | Alpine.js + 服务器状态 | Pinia + Vuex |
| 类型安全 | 有限（JS） | 完整（TypeScript） |
| 实时更新 | HTMX + SSE | WebSocket + Vue响应式 |
| 部署大小 | ~500KB (CDN) | ~2MB+ (打包后) |
| 开发速度 | 极快（即时反馈） | 快（热重载） |

## 未来扩展

### 计划功能
1. **离线支持**: Service Worker缓存
2. **插件系统**: 可扩展的编辑器插件
3. **团队协作**: 实时协同编辑
4. **主题系统**: 可切换的UI主题
5. **移动适配**: 响应式移动端界面

### 性能改进
1. **预加载**: 关键资源预加载
2. **代码分割**: 按需加载编辑器组件
3. **Web Workers**: 复杂计算后台执行
4. **IndexedDB**: 本地数据缓存

## 故障排除

### 常见问题

**Q: Monaco Editor无法加载**
A: 检查网络连接，确保能访问CDN：https://unpkg.com/monaco-editor

**Q: HTMX请求失败**
A: 检查后端路由是否正确注册，查看浏览器控制台错误

**Q: Alpine.js组件不工作**
A: 确保Alpine.js已正确加载，检查组件初始化代码

**Q: SSE连接断开**
A: 检查服务器SSE端点，确保连接保持活跃

### 调试技巧
1. 使用浏览器开发者工具查看HTMX请求
2. 检查Alpine.js组件状态
3. 查看Flask服务器日志
4. 使用HTMX开发者工具扩展

## 贡献指南

1. 遵循现有代码风格（HTMX属性优先）
2. 新功能先实现服务器端逻辑
3. 保持HTML片段的独立性
4. 添加相应的测试用例

## 许可证

MIT License - 详见LICENSE文件