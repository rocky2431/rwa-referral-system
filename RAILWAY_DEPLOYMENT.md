# Railway部署指南 - 后端+数据库

## 📋 部署概览

Railway将部署以下服务:
1. **FastAPI后端** - Python Web服务
2. **PostgreSQL数据库** - 主数据库
3. **Redis** - 缓存服务

---

## 🚀 部署步骤

### 第一步: 注册Railway账号

1. 访问 [https://railway.app](https://railway.app)
2. 使用GitHub账号登录
3. 验证邮箱

### 第二步: 创建新项目

1. 点击 **"New Project"**
2. 选择 **"Deploy from GitHub repo"**
3. 选择仓库: `rocky2431/rwa-referral-system`
4. Railway会自动检测到Python项目

### 第三步: 配置服务

#### 1. 添加PostgreSQL数据库

1. 在项目页面点击 **"+ New"**
2. 选择 **"Database"** → **"PostgreSQL"**
3. Railway会自动创建数据库并生成连接信息

#### 2. 添加Redis

1. 再次点击 **"+ New"**
2. 选择 **"Database"** → **"Redis"**
3. Railway会自动创建Redis实例

#### 3. 配置后端环境变量

点击FastAPI服务,进入 **"Variables"** 标签,添加以下环境变量:

```env
# 应用配置
APP_NAME=RWA Referral System
DEBUG=False
API_V1_PREFIX=/api/v1
SECRET_KEY=your-production-secret-key-change-this-to-random-string

# 数据库配置 (Railway会自动注入DATABASE_URL,但我们需要自定义格式)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis配置 (从Railway Redis服务获取)
REDIS_URL=${{Redis.REDIS_URL}}

# 或者手动配置Redis
REDIS_HOST=${{Redis.REDIS_HOST}}
REDIS_PORT=${{Redis.REDIS_PORT}}
REDIS_PASSWORD=${{Redis.REDIS_PASSWORD}}

# Web3配置
BSC_NETWORK=testnet
BSC_TESTNET_RPC_URL=https://data-seed-prebsc-1-s1.binance.org:8545
BSC_MAINNET_RPC_URL=https://bsc-dataseed1.binance.org
REFERRAL_CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000

# CORS配置 (⚠️ 重要!必须包含Vercel前端域名)
CORS_ORIGINS=https://socialtest2-86rmmtqhg-rocky2431s-projects.vercel.app,https://socialtest2.vercel.app,http://localhost:5173

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 推荐系统配置
LEVEL_1_BONUS_RATE=15
LEVEL_2_BONUS_RATE=5
INACTIVE_DAYS=30
```

**重要说明:**
- `${{Postgres.DATABASE_URL}}` - Railway自动注入,指向PostgreSQL
- `${{Redis.REDIS_URL}}` - Railway自动注入,指向Redis
- `CORS_ORIGINS` - 必须包含Vercel前端的完整域名
- `SECRET_KEY` 和 `JWT_SECRET_KEY` - 使用强随机字符串

### 第四步: 配置构建和启动命令

在FastAPI服务的 **"Settings"** 中:

**Build Command:**
```bash
pip install -r backend/requirements.txt
```

**Start Command:**
```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Root Directory:** 留空或设为 `/`

### 第五步: 初始化数据库

部署成功后,需要运行数据库迁移:

1. 在Railway Dashboard中,找到FastAPI服务
2. 进入 **"Deployments"** 标签
3. 点击最新部署旁的 **"View Logs"**
4. 如果需要手动运行迁移,使用Railway CLI:

```bash
# 安装Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 链接到项目
railway link

# 运行迁移命令
railway run python backend/scripts/init_db.py
```

或者通过Railway Shell:
1. 在服务页面,点击右上角 **"..."** → **"Shell"**
2. 运行: `cd backend && python scripts/init_db.py`

---

## 🔧 验证部署

### 1. 检查服务状态

Railway部署完成后,会提供一个公开URL,类似:
```
https://your-app-name.up.railway.app
```

访问以下端点验证:
- `GET /` - 健康检查
- `GET /health` - 详细健康检查
- `GET /docs` - API文档(Swagger)

### 2. 测试API

```bash
# 健康检查
curl https://your-app-name.up.railway.app/health

# 预期响应:
{
  "status": "healthy",
  "database": "connected",
  "blockchain": "connected"
}
```

### 3. 检查数据库连接

在Railway Dashboard中:
1. 点击PostgreSQL服务
2. 进入 **"Query"** 标签
3. 运行: `SELECT * FROM users LIMIT 5;`

---

## 🔄 更新Vercel环境变量

后端部署成功后,需要更新Vercel前端的API地址:

### 方法1: 通过Vercel Dashboard

1. 访问 https://vercel.com/rocky2431s-projects/socialtest2/settings/environment-variables
2. 找到 `VITE_API_BASE_URL`
3. 更新为Railway提供的URL: `https://your-app-name.up.railway.app/api/v1`
4. 重新部署前端: `vercel --prod`

### 方法2: 通过CLI

```bash
cd /Users/rocky243/Desktop/paimon.dex/socialtest2

# 删除旧值
vercel env rm VITE_API_BASE_URL production

# 添加新值
vercel env add VITE_API_BASE_URL production
# 输入: https://your-app-name.up.railway.app/api/v1

# 重新部署
vercel --prod
```

---

## 📊 监控和日志

### 查看实时日志

1. 在Railway Dashboard中,点击FastAPI服务
2. 进入 **"Deployments"** 标签
3. 点击最新部署的 **"View Logs"**

### 监控资源使用

1. 进入服务的 **"Metrics"** 标签
2. 查看CPU、内存、网络使用情况

---

## 🐛 常见问题

### Q1: 数据库连接失败

**检查:**
1. 确认PostgreSQL服务已启动
2. 检查 `DATABASE_URL` 环境变量是否正确
3. 查看后端日志是否有连接错误

**解决:**
```bash
# 在Railway Shell中测试连接
railway run python -c "from app.db.database import engine; print(engine.connect())"
```

### Q2: CORS错误

**症状:** 前端显示 `Access-Control-Allow-Origin` 错误

**解决:**
1. 检查 `CORS_ORIGINS` 环境变量是否包含Vercel域名
2. 确保包含完整的协议和域名(https://...)
3. 重启后端服务

### Q3: 构建失败

**检查:**
1. 确认 `backend/requirements.txt` 存在
2. 检查Python版本兼容性
3. 查看构建日志中的具体错误

**解决:**
- 在 **"Settings"** → **"Environment"** 中指定Python版本
- 添加 `runtime.txt` 文件: `python-3.11`

### Q4: Redis连接失败

**解决:**
- 确认Redis服务已创建
- 检查 `REDIS_URL` 或 `REDIS_HOST/PORT` 环境变量
- 后端会在Redis不可用时继续运行(无缓存模式)

---

## 💰 费用说明

### Railway免费额度

- ✅ **$5免费额度** - 每月自动刷新
- ✅ **PostgreSQL** - 包含在免费额度内
- ✅ **Redis** - 包含在免费额度内
- ✅ **FastAPI服务** - 包含在免费额度内

**使用建议:**
- 开发/测试阶段: 免费额度足够
- 生产环境: 建议升级到Hobby计划($5/月)

---

## 🔐 安全建议

1. **环境变量管理**
   - 使用强随机字符串作为SECRET_KEY
   - 不要在代码中硬编码敏感信息
   - 定期轮换密钥

2. **CORS配置**
   - 仅允许信任的域名
   - 不要使用通配符 `*`

3. **数据库安全**
   - Railway自动提供SSL连接
   - 定期备份数据库
   - 限制数据库访问权限

---

## 📚 相关资源

- [Railway文档](https://docs.railway.app/)
- [Railway CLI](https://docs.railway.app/develop/cli)
- [FastAPI部署指南](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL on Railway](https://docs.railway.app/databases/postgresql)

---

## 🆘 获取帮助

- Railway Discord: https://discord.gg/railway
- Railway社区: https://community.railway.app
- 项目Issues: https://github.com/rocky2431/rwa-referral-system/issues

---

**部署完成后,记得测试完整的前端→后端→数据库流程!** 🎉
