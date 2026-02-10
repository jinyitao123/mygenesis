# 环境配置指南

## 1. 环境变量配置

### 复制环境模板
```bash
cp .env.example .env
```

### 编辑环境变量
打开 `.env` 文件并配置以下必要变量：

```bash
# DeepSeek API配置（必需）
DEEPSEEK_API_KEY=your_actual_deepseek_api_key_here

# Flask应用配置
SECRET_KEY=your-secret-key-change-in-production

# Neo4j数据库配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# 其他配置使用默认值即可
```

## 2. 获取DeepSeek API密钥

1. 访问 [DeepSeek官网](https://platform.deepseek.com/)
2. 注册/登录账户
3. 进入API Keys页面
4. 创建新的API密钥
5. 复制密钥到 `DEEPSEEK_API_KEY`

## 3. 本地开发设置

### 后端服务
```bash
cd tools/genesis_forge
python -m backend.api.app_studio
```

### 前端服务
```bash
cd tools/genesis_forge/frontend
npm install
npm run dev
```

## 4. 安全注意事项

⚠️ **重要**：
- `.env` 文件包含敏感信息，**不要提交到git仓库**
- `.env.example` 是模板文件，可以提交
- 生产环境使用不同的密钥和配置
- 定期轮换API密钥

## 5. 故障排除

### AI服务不可用
检查：
1. `DEEPSEEK_API_KEY` 是否正确
2. 网络连接是否正常
3. API密钥是否有额度

### 数据库连接失败
检查：
1. Neo4j服务是否运行
2. 用户名密码是否正确
3. 端口是否被占用

## 6. 生产环境部署

生产环境需要：
1. 使用更强的 `SECRET_KEY`
2. 配置HTTPS
3. 设置适当的CORS策略
4. 使用环境变量管理配置
5. 启用日志监控
