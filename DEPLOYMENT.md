# 部署文档 (Deployment Guide)

> **版本:** v2.0-beta
> **更新日期:** 2025-10-21
> **面向对象:** 运维工程师、DevOps
> **当前部署状态:** v1.0 ✅ 测试网已部署 | v2.0 🔄 开发中

本文档提供RWA Launchpad社交裂变平台的完整部署指南，涵盖测试环境、生产环境和Docker容器化部署。

---

## 📑 目录

- [部署概览](#部署概览)
- [环境要求](#环境要求)
- [部署前准备](#部署前准备)
- [v1.0 MVP部署](#v10-mvp部署)
- [v2.0游戏化升级部署](#v20游戏化升级部署)
- [智能合约部署](#智能合约部署)
- [Docker容器化部署](#docker容器化部署)
- [监控与日志](#监控与日志)
- [备份与恢复](#备份与恢复)
- [安全配置](#安全配置)
- [故障排查](#故障排查)

---

## 🎯 部署概览

### 当前部署状态

| 环境 | v1.0 MVP | v2.0 游戏化 | 备注 |
|------|----------|-------------|------|
| **本地开发** | ✅ 已配置 | 🔄 开发中 | Python 3.13兼容性问题 |
| **BSC测试网** | ✅ 已部署 | ⏳ 待部署 | 合约地址: 0x... |
| **测试服务器** | ⏳ 待部署 | ⏳ 待部署 | 需配置PostgreSQL+Redis |
| **生产环境** | ⏳ 待部署 | ⏳ 待部署 | 计划中 |

### 部署架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                │
│  Web浏览器 + MetaMask钱包                                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                     负载均衡层                               │
│  Nginx/Cloudflare (HTTPS + CDN + WAF)                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼───────┐  ┌────────▼────────┐
│   前端服务     │  │    后端服务      │
│  React SPA    │  │   FastAPI       │
│  Ant Design   │  │   Python 3.11   │
│  (静态资源)    │  │   (API Server)  │
└───────────────┘  └─────────┬───────┘
                             │
               ┌─────────────┼─────────────┐
               │             │             │
        ┌──────▼──────┐ ┌───▼────┐ ┌─────▼──────┐
        │ PostgreSQL  │ │ Redis  │ │ BSC节点    │
        │   15.x      │ │  7.x   │ │ (RPC)      │
        │ (主数据库)  │ │(缓存+锁)│ │ (链上数据) │
        └─────────────┘ └────────┘ └────────────┘
```

### 版本差异对比

| 组件 | v1.0 MVP | v2.0 游戏化 |
|------|----------|-------------|
| **智能合约** | RWAReferral.sol (BSC测试网) | 保持不变 ✅ |
| **后端框架** | FastAPI + SQLite/PostgreSQL | FastAPI + PostgreSQL 15 (必需) |
| **缓存层** | 可选 | Redis 7 (必需，幂等性) |
| **事件监听** | 无 | event_listener.py 服务 (新增) |
| **数据库表** | 3-5张表 | 13张表 + 3个视图 |
| **前端路由** | 3个页面 | 8个页面 |

---

## 🔧 环境要求

### 硬件要求

| 组件 | 开发环境 | 测试环境 | 生产环境 |
|------|---------|---------|----------|
| **CPU** | 2核 | 4核 | 8核+ |
| **内存** | 4GB | 8GB | 16GB+ |
| **存储** | 20GB SSD | 50GB SSD | 200GB+ SSD |
| **带宽** | 10Mbps | 50Mbps | 100Mbps+ |

### 软件要求（关键）

| 软件 | v1.0 要求 | v2.0 要求 | 备注 |
|------|----------|----------|------|
| **操作系统** | Ubuntu 20.04+ | Ubuntu 22.04 LTS | 推荐 |
| **Node.js** | >= 20.0 | **>= 24.7.0** | 前端构建 |
| **Python** | >= 3.9 | **== 3.11.x** | ⚠️ 不支持3.13 |
| **PostgreSQL** | 可选 (SQLite) | **>= 15** | v2.0必需 |
| **Redis** | 可选 | **>= 7** | v2.0必需（幂等性） |
| **Nginx** | >= 1.18 | **>= 1.24** | 反向代理 |
| **Docker** | >= 20.10 (可选) | >= 24.0 (推荐) | 容器化部署 |

### ⚠️ 关键环境限制

```bash
# Python版本限制（重要！）
Python 3.13 ❌  # psycopg2-binary编译失败
Python 3.12 ⚠️  # 未充分测试
Python 3.11 ✅  # 推荐版本
Python 3.10 ⚠️  # 可用但不推荐

# 数据库版本
PostgreSQL 15+ ✅  # v2.0必需
PostgreSQL 14   ⚠️  # 可用但缺少部分特性
SQLite         ❌  # v2.0不支持（需要异步）

# Redis版本
Redis 7.x  ✅  # 推荐
Redis 6.x  ⚠️  # 可用但建议升级
```

---

## 📋 部署前准备

### 1. 服务器基础配置

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y \
    git curl wget \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg lsb-release

# 配置时区
sudo timedatectl set-timezone Asia/Shanghai

# 配置防火墙（生产环境）
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### 2. 安装Python 3.11（必须）

```bash
# Ubuntu 22.04自带Python 3.10，需要安装3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# 验证版本
python3.11 --version  # 应显示 Python 3.11.x

# 设置为默认（可选）
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### 3. 安装Node.js 24.x

```bash
# 添加NodeSource仓库
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -

# 安装Node.js
sudo apt install -y nodejs

# 验证版本
node --version   # 应显示 v24.x.x
npm --version    # 应显示 10.x.x
```

### 4. 安装PostgreSQL 15

```bash
# 添加PostgreSQL仓库
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# 安装PostgreSQL 15
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 验证版本
sudo -u postgres psql -c "SELECT version();"
```

### 5. 安装Redis 7

```bash
# 添加Redis仓库
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

# 安装Redis 7
sudo apt update
sudo apt install -y redis

# 启动服务
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 验证版本
redis-cli --version  # 应显示 redis-cli 7.x.x

# 测试连接
redis-cli ping  # 应返回 PONG
```

### 6. 克隆项目

```bash
# 选择部署目录
cd /var/www  # 生产环境
# 或
cd ~/projects  # 开发环境

# 克隆代码
git clone <repository-url> socialtest2
cd socialtest2

# 检查分支
git branch -a
git checkout main  # 或 develop
```

---

## 🏗️ v1.0 MVP部署

### v1.0部署检查清单

v1.0 MVP功能较为简单，可使用SQLite或PostgreSQL：

- [x] **智能合约** - 已部署到BSC测试网 ✅
- [x] **后端API** - 基础推荐接口 ✅
- [x] **前端页面** - Home、Dashboard、Leaderboard ✅
- [ ] **测试服务器部署** - 待部署
- [ ] **生产环境部署** - 待部署

### 1. 配置智能合约

v1.0的智能合约已部署到BSC测试网，合约地址：

```bash
# 编辑 backend/.env
BSC_RPC_URL=https://data-seed-prebsc-1-s1.binance.org:8545
REFERRAL_CONTRACT_ADDRESS=0x...  # 实际合约地址
CHAIN_ID=97  # BSC测试网
```

### 2. 部署后端（v1.0）

```bash
cd backend

# 创建Python 3.11虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env

# v1.0可以使用SQLite（简单）
# DATABASE_URL=sqlite:///./referral.db

# 或PostgreSQL（推荐）
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/referral_db

# 数据库迁移（v1.0基础表）
alembic upgrade head

# 启动后端
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 部署前端（v1.0）

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
nano .env

# v1.0配置示例
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_CONTRACT_ADDRESS=0x...
VITE_CHAIN_ID=97

# 构建生产版本
npm run build

# 预览（可选）
npm run preview
```

### 4. 配置Nginx（v1.0）

```nginx
# /etc/nginx/sites-available/socialtest2-v1
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/socialtest2/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/socialtest2-v1 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. 配置Systemd服务（v1.0）

```ini
# /etc/systemd/system/socialtest2-backend-v1.service
[Unit]
Description=RWA Referral Backend v1.0
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/socialtest2/backend
Environment="PATH=/var/www/socialtest2/backend/venv/bin"
ExecStart=/var/www/socialtest2/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start socialtest2-backend-v1
sudo systemctl enable socialtest2-backend-v1
sudo systemctl status socialtest2-backend-v1
```

---

## 🎮 v2.0游戏化升级部署

### v2.0部署检查清单

v2.0增加了游戏化功能，**必须使用PostgreSQL 15 + Redis 7**：

- [x] **数据库Schema** - 13张表设计完成 ✅
- [x] **后端服务** - 4大模块代码完成85%+ ✅
- [x] **幂等性机制** - idempotency.py完成 ✅
- [x] **API端点测试** - 20个测试100%通过 ✅
  - [x] 积分兑换API (4个测试)
  - [x] 积分统计API (2个测试)
  - [x] 战队角色API (6个测试)
  - [x] 积分查询API (8个测试)
- [x] **PostgreSQL安装** - 测试环境已安装 ✅
- [x] **Redis安装** - 测试环境已安装 ✅
- [ ] **事件监听服务** - 50%完成 🔄
- [ ] **前端v2.0页面** - 80%完成 🔄
- [ ] **测试服务器部署** - 待部署
- [ ] **生产环境部署** - 待部署

### ⚠️ v2.0部署前置条件（必须满足）

```bash
# 1. 检查Python版本
python3 --version  # 必须是 3.11.x

# 2. 检查PostgreSQL
psql --version  # 必须是 15.x

# 3. 检查Redis
redis-cli --version  # 必须是 7.x

# 4. 检查PostgreSQL连接
sudo -u postgres psql -c "SELECT version();"

# 5. 检查Redis连接
redis-cli ping  # 应返回 PONG
```

### 1. 创建数据库和用户

```bash
# 连接PostgreSQL
sudo -u postgres psql

# 创建数据库和用户
CREATE DATABASE socialtest2_db;
CREATE USER socialtest2_user WITH PASSWORD 'your_secure_password';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE socialtest2_db TO socialtest2_user;

-- 切换到新数据库
\c socialtest2_db

-- 授予schema权限
GRANT ALL ON SCHEMA public TO socialtest2_user;

-- 退出
\q
```

### 2. 配置环境变量（v2.0）

```bash
cd backend
cp .env.example .env
nano .env
```

**v2.0 `.env` 完整配置：**

```env
# 应用配置
APP_NAME="RWA Launchpad Social Gamification Platform"
APP_VERSION="v2.0-beta"
DEBUG=False  # 生产环境设为False
SECRET_KEY="your-secret-key-change-this-in-production"

# API配置
API_V1_PREFIX="/api/v1"
BACKEND_CORS_ORIGINS=["http://localhost:5173", "https://your-domain.com"]

# 数据库配置（v2.0必需PostgreSQL）
DATABASE_URL=postgresql+asyncpg://socialtest2_user:your_secure_password@localhost:5432/socialtest2_db

# Redis配置（v2.0必需）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # 如果设置了密码

# 幂等性配置
IDEMPOTENCY_TTL=604800  # 7天，单位：秒

# Web3配置
BSC_RPC_URL=https://data-seed-prebsc-1-s1.binance.org:8545
BSC_TESTNET_RPC_URL=https://data-seed-prebsc-1-s1.binance.org:8545
BSC_MAINNET_RPC_URL=https://bsc-dataseed1.binance.org
REFERRAL_CONTRACT_ADDRESS=0x...  # 智能合约地址
CHAIN_ID=97  # 97=BSC测试网, 56=BSC主网

# 事件监听配置（v2.0新增）
EVENT_LISTENER_ENABLED=True
EVENT_LISTENER_POLL_INTERVAL=5  # 秒
EVENT_LISTENER_START_BLOCK=latest  # 或具体区块号

# 安全配置
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 日志配置
LOG_LEVEL=INFO  # DEBUG/INFO/WARNING/ERROR
LOG_FILE=/var/log/socialtest2/backend.log
```

### 3. 执行数据库迁移（v2.0）

```bash
cd backend
source venv/bin/activate

# 检查迁移状态
alembic current

# 查看待执行的迁移
alembic history

# 执行v2.0数据库迁移
alembic upgrade head

# 验证表是否创建成功
psql -U socialtest2_user -d socialtest2_db -c "\dt"

# 应该看到以下表：
# users
# user_points
# point_transactions
# referral_relations
# teams
# team_members
# team_tasks
# tasks
# user_task_completions
# quiz_questions
# user_quiz_answers
# ...等
```

### 4. 配置Redis（v2.0）

```bash
# 编辑Redis配置
sudo nano /etc/redis/redis.conf

# v2.0推荐配置
# 内存限制（根据服务器配置调整）
maxmemory 1gb
maxmemory-policy allkeys-lru

# 持久化（AOF模式，保证数据不丢失）
appendonly yes
appendfsync everysec

# 密码保护（生产环境必须设置）
requirepass your_redis_password

# 监听地址（仅本地访问）
bind 127.0.0.1

# 保存配置并重启
sudo systemctl restart redis-server

# 验证
redis-cli
# 如果设置了密码
AUTH your_redis_password
PING  # 应返回 PONG
```

### 5. 启动事件监听服务（v2.0新增）

v2.0的核心功能之一是**链上事件监听**，需要单独运行：

```bash
cd backend
source venv/bin/activate

# 测试运行
python -m app.services.event_listener

# 应该看到类似输出：
# INFO:event_listener:Starting event listener...
# INFO:event_listener:Listening for RewardCalculated events from block 12345678
# INFO:event_listener:Listening...
```

**配置Systemd服务（生产环境）：**

```ini
# /etc/systemd/system/socialtest2-event-listener.service
[Unit]
Description=RWA Social Gamification Event Listener
After=network.target postgresql.service redis-server.service
Requires=postgresql.service redis-server.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/socialtest2/backend
Environment="PATH=/var/www/socialtest2/backend/venv/bin"
ExecStart=/var/www/socialtest2/backend/venv/bin/python -m app.services.event_listener
Restart=always
RestartSec=10

# 日志配置
StandardOutput=append:/var/log/socialtest2/event-listener.log
StandardError=append:/var/log/socialtest2/event-listener-error.log

[Install]
WantedBy=multi-user.target
```

```bash
# 创建日志目录
sudo mkdir -p /var/log/socialtest2
sudo chown www-data:www-data /var/log/socialtest2

# 启动服务
sudo systemctl daemon-reload
sudo systemctl start socialtest2-event-listener
sudo systemctl enable socialtest2-event-listener
sudo systemctl status socialtest2-event-listener

# 查看日志
sudo journalctl -u socialtest2-event-listener -f
```

### 6. 启动后端API服务（v2.0）

```ini
# /etc/systemd/system/socialtest2-backend-v2.service
[Unit]
Description=RWA Social Gamification Backend v2.0
After=network.target postgresql.service redis-server.service
Requires=postgresql.service redis-server.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/socialtest2/backend
Environment="PATH=/var/www/socialtest2/backend/venv/bin"

# 生产环境：多worker模式
ExecStart=/var/www/socialtest2/backend/venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info

Restart=always
RestartSec=10

# 日志配置
StandardOutput=append:/var/log/socialtest2/backend.log
StandardError=append:/var/log/socialtest2/backend-error.log

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start socialtest2-backend-v2
sudo systemctl enable socialtest2-backend-v2
sudo systemctl status socialtest2-backend-v2
```

### 7. 部署前端（v2.0）

```bash
cd frontend

# 配置环境变量
cp .env.example .env.production
nano .env.production

# v2.0配置示例
VITE_API_BASE_URL=https://api.your-domain.com/api/v1
VITE_CONTRACT_ADDRESS=0x...
VITE_CHAIN_ID=97  # BSC测试网

# 构建生产版本
npm run build

# dist目录包含优化后的静态文件
ls -lh dist/
```

### 8. 配置Nginx（v2.0完整配置）

```nginx
# /etc/nginx/sites-available/socialtest2-v2
upstream backend_v2 {
    # 后端负载均衡（如果有多个实例）
    server 127.0.0.1:8000;
    # server 127.0.0.1:8001;
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS主配置
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL证书配置（Let's Encrypt）
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # 前端静态文件
    location / {
        root /var/www/socialtest2/frontend/dist;
        try_files $uri $uri/ /index.html;

        # 缓存配置
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端API代理
    location /api {
        proxy_pass http://backend_v2;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查端点
    location /health {
        proxy_pass http://backend_v2/health;
        access_log off;
    }

    # 日志配置
    access_log /var/log/nginx/socialtest2_access.log;
    error_log /var/log/nginx/socialtest2_error.log;
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/socialtest2-v2 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 配置Let's Encrypt SSL
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 9. v2.0服务健康检查

```bash
# 检查所有v2.0服务状态
sudo systemctl status socialtest2-backend-v2
sudo systemctl status socialtest2-event-listener
sudo systemctl status postgresql
sudo systemctl status redis-server
sudo systemctl status nginx

# 检查端口监听
sudo netstat -tlnp | grep -E '8000|5432|6379|80|443'

# 测试后端API
curl http://localhost:8000/health

# 测试Redis连接
redis-cli ping

# 测试PostgreSQL连接
psql -U socialtest2_user -d socialtest2_db -c "SELECT COUNT(*) FROM users;"

# 查看事件监听器日志
sudo journalctl -u socialtest2-event-listener -n 50 --no-pager

# 查看后端日志
sudo journalctl -u socialtest2-backend-v2 -n 50 --no-pager
```

---

## 📜 智能合约部署

### BSC测试网部署（v1.0 + v2.0通用）

v1.0和v2.0使用相同的智能合约`RWAReferral.sol`，已部署到BSC测试网。

#### 1. 配置Hardhat

```bash
cd contracts
npm install

# 配置环境变量
cp .env.example .env
nano .env
```

```env
# BSC测试网
BSC_TESTNET_RPC_URL=https://data-seed-prebsc-1-s1.binance.org:8545
BSC_TESTNET_CHAIN_ID=97

# BSC主网（生产环境）
BSC_MAINNET_RPC_URL=https://bsc-dataseed1.binance.org
BSC_MAINNET_CHAIN_ID=56

# 部署账户私钥（注意安全！）
PRIVATE_KEY=your_private_key_here

# BscScan API密钥（用于验证合约）
BSCSCAN_API_KEY=your_bscscan_api_key
```

#### 2. 部署到测试网

```bash
cd contracts

# 编译合约
npx hardhat compile

# 运行测试（本地）
npx hardhat test

# 部署到BSC测试网
npx hardhat run scripts/deploy.js --network bscTestnet

# 输出示例：
# RWAReferral deployed to: 0x5FbDB2315678afecb367f032d93F642f64180aa3
# Transaction hash: 0xabc123...
```

#### 3. 验证合约

```bash
# 在BscScan上验证合约源码
npx hardhat verify --network bscTestnet <CONTRACT_ADDRESS>

# 成功后可在BscScan查看：
# https://testnet.bscscan.com/address/<CONTRACT_ADDRESS>
```

#### 4. 更新环境变量

```bash
# 更新后端.env
nano backend/.env
REFERRAL_CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3

# 更新前端.env
nano frontend/.env.production
VITE_CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3
```

### BSC主网部署（生产环境）

```bash
# ⚠️ 警告：主网部署前必须完成以下检查
# 1. 合约代码已审计
# 2. 充分测试（测试网运行≥1个月）
# 3. 准备足够的BNB作为gas费
# 4. 使用硬件钱包管理私钥

# 部署到BSC主网
npx hardhat run scripts/deploy.js --network bscMainnet

# 验证合约
npx hardhat verify --network bscMainnet <CONTRACT_ADDRESS>

# 主网浏览器：
# https://bscscan.com/address/<CONTRACT_ADDRESS>
```

---

## 🐳 Docker容器化部署

### 方案1: Docker Compose（推荐开发/测试）

#### 1. 项目结构

```
socialtest2/
├── docker-compose.yml           # 主配置文件
├── docker-compose.prod.yml      # 生产环境覆盖配置
├── backend/
│   ├── Dockerfile
│   └── ...
├── frontend/
│   ├── Dockerfile
│   └── ...
└── nginx/
    ├── Dockerfile
    └── nginx.conf
```

#### 2. Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    container_name: socialtest2_postgres
    environment:
      POSTGRES_DB: socialtest2_db
      POSTGRES_USER: socialtest2_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/alembic/versions:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    networks:
      - socialtest2_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U socialtest2_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: socialtest2_redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - socialtest2_network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # 后端API服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: socialtest2_backend
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql+asyncpg://socialtest2_user:${DB_PASSWORD}@postgres:5432/socialtest2_db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - BSC_RPC_URL=${BSC_RPC_URL}
      - REFERRAL_CONTRACT_ADDRESS=${REFERRAL_CONTRACT_ADDRESS}
    volumes:
      - ./backend:/app
      - /app/venv  # 忽略本地venv
    ports:
      - "8000:8000"
    networks:
      - socialtest2_network
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # 事件监听服务
  event_listener:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: socialtest2_event_listener
    depends_on:
      - backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://socialtest2_user:${DB_PASSWORD}@postgres:5432/socialtest2_db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - BSC_RPC_URL=${BSC_RPC_URL}
      - REFERRAL_CONTRACT_ADDRESS=${REFERRAL_CONTRACT_ADDRESS}
      - EVENT_LISTENER_ENABLED=true
    volumes:
      - ./backend:/app
    networks:
      - socialtest2_network
    command: python -m app.services.event_listener
    restart: always

  # 前端（Nginx + React SPA）
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_BASE_URL=${VITE_API_BASE_URL}
        - VITE_CONTRACT_ADDRESS=${REFERRAL_CONTRACT_ADDRESS}
        - VITE_CHAIN_ID=${VITE_CHAIN_ID}
    container_name: socialtest2_frontend
    depends_on:
      - backend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro  # SSL证书（生产环境）
    networks:
      - socialtest2_network

networks:
  socialtest2_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

#### 3. 后端Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令（可被docker-compose覆盖）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 4. 前端Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:24-alpine AS builder

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建参数
ARG VITE_API_BASE_URL
ARG VITE_CONTRACT_ADDRESS
ARG VITE_CHAIN_ID

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_CONTRACT_ADDRESS=$VITE_CONTRACT_ADDRESS
ENV VITE_CHAIN_ID=$VITE_CHAIN_ID

# 构建生产版本
RUN npm run build

# 生产阶段：Nginx
FROM nginx:1.24-alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY nginx/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
```

#### 5. 启动Docker Compose

```bash
# 创建.env文件
cp .env.example .env
nano .env

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f event_listener

# 执行数据库迁移
docker-compose exec backend alembic upgrade head

# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎！）
docker-compose down -v
```

---

## 📊 监控与日志

### 1. 应用日志配置

#### 后端日志（Python Logging）

```python
# backend/app/core/logging.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """配置应用日志"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "/var/log/socialtest2/backend.log")

    # 创建日志目录
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 文件处理器（滚动日志，每个文件10MB，保留10个文件）
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=10
    )
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
```

#### Nginx访问日志

```nginx
# /etc/nginx/nginx.conf
http {
    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
}
```

### 2. 日志轮转（Logrotate）

```bash
# /etc/logrotate.d/socialtest2
/var/log/socialtest2/*.log {
    daily                   # 每天轮转
    rotate 30               # 保留30天
    compress                # 压缩旧日志
    delaycompress           # 延迟压缩（第二次轮转时压缩）
    notifempty              # 空文件不轮转
    create 0640 www-data www-data  # 创建新文件的权限
    sharedscripts           # 所有日志轮转后执行一次脚本
    postrotate
        systemctl reload socialtest2-backend-v2 > /dev/null 2>&1 || true
        systemctl reload socialtest2-event-listener > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

### 3. 性能监控

#### Prometheus + Grafana（推荐）

```bash
# 安装Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.40.0/prometheus-2.40.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# 配置prometheus.yml
scrape_configs:
  - job_name: 'socialtest2_backend'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']  # postgres_exporter

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']  # redis_exporter

# 启动Prometheus
./prometheus --config.file=prometheus.yml
```

#### 后端健康检查端点

```python
# backend/app/api/endpoints/health.py
from fastapi import APIRouter
from app.core.database import engine
from app.core.redis import redis_client

router = APIRouter()

@router.get("/health")
async def health_check():
    """健康检查端点"""
    checks = {
        "status": "ok",
        "database": "unknown",
        "redis": "unknown"
    }

    # 检查数据库
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        checks["status"] = "degraded"

    # 检查Redis
    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        checks["status"] = "degraded"

    return checks
```

---

## 💾 备份与恢复

### 1. PostgreSQL数据库备份

#### 手动备份

```bash
# 备份整个数据库
pg_dump -U socialtest2_user -d socialtest2_db -F c -f backup_$(date +%Y%m%d_%H%M%S).dump

# 备份为SQL文件（可读）
pg_dump -U socialtest2_user -d socialtest2_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 仅备份Schema
pg_dump -U socialtest2_user -d socialtest2_db --schema-only > schema.sql

# 仅备份数据
pg_dump -U socialtest2_user -d socialtest2_db --data-only > data.sql
```

#### 自动备份脚本

```bash
#!/bin/bash
# /usr/local/bin/backup-socialtest2-db.sh

BACKUP_DIR="/backups/socialtest2/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="socialtest2_db"
DB_USER="socialtest2_user"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
pg_dump -U $DB_USER -d $DB_NAME -F c | gzip > $BACKUP_DIR/backup_$DATE.dump.gz

# 检查备份是否成功
if [ $? -eq 0 ]; then
    echo "$(date): Backup successful - backup_$DATE.dump.gz" >> $BACKUP_DIR/backup.log
else
    echo "$(date): Backup FAILED!" >> $BACKUP_DIR/backup.log
    exit 1
fi

# 删除30天前的备份
find $BACKUP_DIR -name "*.dump.gz" -mtime +30 -delete

# 备份到远程（可选）
# rsync -avz $BACKUP_DIR backup-server:/remote/backup/path/
```

```bash
# 设置执行权限
sudo chmod +x /usr/local/bin/backup-socialtest2-db.sh

# 添加到Crontab（每天凌晨2点备份）
sudo crontab -e
0 2 * * * /usr/local/bin/backup-socialtest2-db.sh
```

### 2. 数据库恢复

```bash
# 从自定义格式备份恢复
pg_restore -U socialtest2_user -d socialtest2_db -c backup_20250121_020000.dump

# 从SQL文件恢复
psql -U socialtest2_user -d socialtest2_db < backup_20250121_020000.sql

# 创建新数据库并恢复
createdb -U socialtest2_user socialtest2_db_restore
pg_restore -U socialtest2_user -d socialtest2_db_restore backup_20250121_020000.dump
```

### 3. Redis备份

```bash
# Redis自动持久化（AOF模式）
# 已在redis.conf配置：
# appendonly yes
# appendfsync everysec

# 手动触发RDB快照
redis-cli BGSAVE

# 备份RDB文件
cp /var/lib/redis/dump.rdb /backups/redis/dump_$(date +%Y%m%d).rdb

# 备份AOF文件
cp /var/lib/redis/appendonly.aof /backups/redis/appendonly_$(date +%Y%m%d).aof
```

### 4. 应用代码备份

```bash
# Git仓库已经是最好的备份
git push origin main

# 额外本地备份
tar -czf /backups/socialtest2/code_$(date +%Y%m%d).tar.gz /var/www/socialtest2

# 备份到远程服务器
rsync -avz /var/www/socialtest2 backup-server:/remote/backup/path/
```

---

## 🔐 安全配置

### 1. 防火墙配置（UFW）

```bash
# 重置防火墙规则
sudo ufw --force reset

# 默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许SSH（修改默认端口更安全）
sudo ufw allow 22/tcp
# 或自定义端口
# sudo ufw allow 2222/tcp

# 允许HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 限制PostgreSQL访问（仅本地）
# sudo ufw deny 5432/tcp  # 外部无法访问

# 限制Redis访问（仅本地）
# sudo ufw deny 6379/tcp  # 外部无法访问

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status verbose
```

### 2. PostgreSQL安全配置

```bash
# 编辑pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf

# 仅允许本地连接
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   socialtest2_db  socialtest2_user                        md5
host    socialtest2_db  socialtest2_user    127.0.0.1/32        md5

# 禁止远程连接（生产环境推荐）
# host    all             all             0.0.0.0/0               reject
```

### 3. Redis安全配置

```bash
# 编辑redis.conf
sudo nano /etc/redis/redis.conf

# 1. 设置强密码
requirepass your_very_strong_redis_password_here

# 2. 绑定本地地址
bind 127.0.0.1 ::1

# 3. 禁用危险命令
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG "CONFIG_RENAMED_COMMAND"

# 4. 启用Protected Mode
protected-mode yes

# 重启Redis
sudo systemctl restart redis-server
```

### 4. 应用安全配置

#### 环境变量保护

```bash
# 设置.env文件权限
chmod 600 backend/.env
chmod 600 frontend/.env.production

# 属主设置
chown www-data:www-data backend/.env
```

#### 密钥管理

```bash
# 生成强密钥
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 使用环境变量管理敏感信息
# 不要在代码中硬编码密钥！

# 生产环境使用密钥管理服务
# - AWS Secrets Manager
# - Azure Key Vault
# - HashiCorp Vault
```

### 5. 安全检查清单

- [ ] **系统安全**
  - [ ] 系统已更新到最新版本
  - [ ] SSH禁用密码登录，仅使用密钥
  - [ ] 修改SSH默认端口（22 → 自定义）
  - [ ] 配置fail2ban防止暴力破解
  - [ ] 启用UFW防火墙

- [ ] **数据库安全**
  - [ ] PostgreSQL仅监听本地
  - [ ] 使用强密码
  - [ ] 定期备份并测试恢复
  - [ ] 启用SSL连接（生产环境）

- [ ] **Redis安全**
  - [ ] 设置强密码
  - [ ] 仅绑定本地地址
  - [ ] 禁用危险命令
  - [ ] 启用AOF持久化

- [ ] **Web安全**
  - [ ] 启用HTTPS（Let's Encrypt）
  - [ ] 配置安全头（HSTS、CSP等）
  - [ ] 实施API速率限制
  - [ ] 配置WAF（Cloudflare/AWS WAF）

- [ ] **应用安全**
  - [ ] 所有敏感信息存储在环境变量
  - [ ] 使用参数化查询（防SQL注入）
  - [ ] 输入验证和清理
  - [ ] CORS正确配置
  - [ ] 实施身份验证和授权

- [ ] **智能合约安全**
  - [ ] 合约代码已审计（生产环境必须）
  - [ ] 测试网充分测试
  - [ ] 实施紧急暂停机制
  - [ ] 多签管理员权限

---

## 🔍 故障排查

### 常见部署问题

#### 问题1: Python 3.13兼容性错误

**症状：**
```bash
error: subprocess-exited-with-error
× Preparing metadata (pyproject.toml) did not run successfully.
│ exit code: 1
╰─> error: command 'clang' failed: No such file or directory
    note: This error originates from psycopg2-binary.
```

**原因：** `psycopg2-binary` 2.9.9不支持Python 3.13

**解决方案：**
```bash
# 方案1: 降级到Python 3.11（推荐）
sudo apt install python3.11 python3.11-venv
python3.11 -m venv venv
source venv/bin/activate
python --version  # 验证为3.11.x

# 方案2: 使用psycopg3（需要代码修改，不推荐）
pip install "psycopg[binary]>=3.0"
```

#### 问题2: PostgreSQL连接失败

**症状：**
```python
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**排查步骤：**
```bash
# 1. 检查PostgreSQL是否运行
sudo systemctl status postgresql

# 2. 检查监听端口
sudo netstat -tlnp | grep 5432

# 3. 测试连接
psql -U socialtest2_user -d socialtest2_db -h localhost

# 4. 检查pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf
# 确保有：
# host    socialtest2_db  socialtest2_user    127.0.0.1/32        md5

# 5. 重启PostgreSQL
sudo systemctl restart postgresql
```

#### 问题3: Redis连接失败

**症状：**
```python
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

**排查步骤：**
```bash
# 1. 检查Redis是否运行
sudo systemctl status redis-server

# 2. 测试连接
redis-cli ping  # 应返回 PONG

# 3. 如果设置了密码
redis-cli
AUTH your_redis_password
PING

# 4. 检查Redis配置
sudo nano /etc/redis/redis.conf
# 确保：
# bind 127.0.0.1 ::1
# protected-mode yes

# 5. 重启Redis
sudo systemctl restart redis-server
```

#### 问题4: 事件监听服务无法启动

**症状：**
```bash
sudo systemctl status socialtest2-event-listener
● socialtest2-event-listener.service - RWA Social Gamification Event Listener
   Loaded: loaded
   Active: failed (Result: exit-code)
```

**排查步骤：**
```bash
# 1. 查看详细日志
sudo journalctl -u socialtest2-event-listener -n 100 --no-pager

# 2. 检查常见问题
# - DATABASE_URL配置是否正确
# - REDIS_HOST配置是否正确
# - BSC_RPC_URL是否可访问
# - REFERRAL_CONTRACT_ADDRESS是否正确

# 3. 手动测试运行
cd /var/www/socialtest2/backend
source venv/bin/activate
python -m app.services.event_listener

# 4. 检查RPC节点连接
python -c "from web3 import Web3; w3 = Web3(Web3.HTTPProvider('https://data-seed-prebsc-1-s1.binance.org:8545')); print('Connected:', w3.is_connected())"
```

#### 问题5: Alembic数据库迁移失败

**症状：**
```bash
alembic.util.exc.CommandError: Target database is not up to date.
```

**解决方案：**
```bash
# 1. 查看当前迁移状态
alembic current

# 2. 查看迁移历史
alembic history

# 3. 查看待执行的迁移
alembic heads

# 4. 如果是开发环境，可以重置数据库
sudo -u postgres psql
DROP DATABASE socialtest2_db;
CREATE DATABASE socialtest2_db;
GRANT ALL PRIVILEGES ON DATABASE socialtest2_db TO socialtest2_user;
\q

# 重新迁移
cd backend
source venv/bin/activate
alembic upgrade head

# 5. 如果是生产环境，逐步迁移
alembic upgrade +1  # 升级一个版本
# 检查无误后
alembic upgrade head  # 升级到最新
```

#### 问题6: 前端无法连接后端API

**症状：**
- 浏览器Console显示CORS错误
- 或显示"Network Error"

**排查步骤：**
```bash
# 1. 检查后端是否运行
curl http://localhost:8000/health

# 2. 检查Nginx配置
sudo nginx -t
sudo systemctl status nginx

# 3. 检查CORS配置
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 检查前端环境变量
nano frontend/.env.production
# VITE_API_BASE_URL应该正确

# 5. 检查Nginx代理配置
sudo nano /etc/nginx/sites-enabled/socialtest2-v2
# location /api { proxy_pass http://localhost:8000; ... }
```

#### 问题7: SSL证书配置失败

**症状：**
```bash
certbot: error: The requested nginx plugin does not appear to be installed
```

**解决方案：**
```bash
# 1. 安装certbot nginx插件
sudo apt install -y certbot python3-certbot-nginx

# 2. 确保域名已正确解析到服务器IP
nslookup your-domain.com

# 3. 确保Nginx配置正确
sudo nginx -t

# 4. 申请证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 5. 测试自动续期
sudo certbot renew --dry-run
```

### 性能优化建议

#### 数据库查询优化

```sql
-- 查看慢查询
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
WHERE mean_time > 100  -- 超过100ms的查询
ORDER BY total_time DESC
LIMIT 20;

-- 查看缺少索引的表
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY n_distinct DESC;

-- 创建索引
CREATE INDEX idx_point_transactions_user_created ON point_transactions(user_id, created_at DESC);
CREATE INDEX idx_teams_total_points ON teams(total_points DESC);
```

#### Redis缓存策略

```python
# 积分余额缓存（减少数据库查询）
async def get_user_points_cached(user_id: int) -> dict:
    cache_key = f"user:points:{user_id}"

    # 尝试从Redis获取
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # 从数据库查询
    points = await get_user_points_from_db(user_id)

    # 缓存5分钟
    await redis.setex(cache_key, 300, json.dumps(points))

    return points
```

---

## 📞 获取支持

### 遇到部署问题？

1. **查看本文档** - 故障排查部分
2. **查看日志** - `sudo journalctl -u <service-name> -n 100`
3. **搜索GitHub Issues** - 类似问题可能已有解决方案
4. **提交Issue** - 包含详细的环境信息和错误日志
5. **联系运维团队** - devops@example.com

### 提交Issue时请包含：

- **环境信息**
  - OS版本：`lsb_release -a`
  - Python版本：`python3 --version`
  - PostgreSQL版本：`psql --version`
  - Redis版本：`redis-cli --version`

- **错误信息**
  - 完整的错误日志
  - 相关配置文件内容（隐藏敏感信息）

- **复现步骤**
  - 详细的操作步骤
  - 期望结果 vs 实际结果

---

## 📝 部署检查清单

### v1.0 MVP部署清单

- [ ] **环境准备**
  - [ ] Ubuntu 22.04安装完成
  - [ ] Node.js 24.x安装完成
  - [ ] Python 3.11安装完成
  - [ ] 防火墙配置完成

- [ ] **智能合约**
  - [ ] 合约已部署到BSC测试网
  - [ ] 合约地址已验证
  - [ ] 测试通过（18个测试用例）

- [ ] **后端部署**
  - [ ] 虚拟环境创建完成
  - [ ] 依赖安装完成
  - [ ] .env配置完成
  - [ ] 数据库迁移完成
  - [ ] Systemd服务配置完成
  - [ ] 后端服务启动成功

- [ ] **前端部署**
  - [ ] 依赖安装完成
  - [ ] .env.production配置完成
  - [ ] 生产构建完成
  - [ ] Nginx配置完成
  - [ ] 前端访问正常

- [ ] **集成测试**
  - [ ] MetaMask连接测试
  - [ ] 推荐绑定功能测试
  - [ ] 奖励计算功能测试
  - [ ] 排行榜功能测试

### v2.0游戏化部署清单

- [ ] **环境准备（v2.0特有）**
  - [ ] PostgreSQL 15安装完成
  - [ ] Redis 7安装完成
  - [ ] PostgreSQL数据库创建完成
  - [ ] Redis配置完成（密码、持久化）

- [ ] **数据库配置**
  - [ ] PostgreSQL用户创建完成
  - [ ] 数据库迁移完成（13张表）
  - [ ] 索引创建完成
  - [ ] 数据库权限配置完成

- [ ] **后端部署（v2.0扩展）**
  - [ ] .env配置完成（PostgreSQL + Redis）
  - [ ] 幂等性服务测试通过
  - [ ] 积分服务测试通过
  - [ ] 后端API服务启动成功
  - [ ] 事件监听服务启动成功

- [ ] **前端部署（v2.0扩展）**
  - [ ] v2.0新页面构建完成
  - [ ] 积分页面测试
  - [ ] 战队页面测试
  - [ ] 任务页面测试
  - [ ] 问答页面测试

- [ ] **监控与日志**
  - [ ] 日志目录创建完成
  - [ ] Logrotate配置完成
  - [ ] 健康检查端点正常
  - [ ] 监控工具配置完成（可选）

- [ ] **备份与安全**
  - [ ] 数据库自动备份配置完成
  - [ ] 备份恢复测试通过
  - [ ] 防火墙规则配置完成
  - [ ] SSL证书配置完成（生产环境）
  - [ ] 密钥管理配置完成

---

**更新日期:** 2025-10-21
**版本:** v2.0-beta
**维护者:** RWA Launchpad运维团队

*本文档随项目持续更新，建议定期查看最新版本。*
