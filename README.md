# RWA推荐系统 - Web3社交裂变游戏化平台

<div align="center">

**多级推荐 + 任务激励 + 战队协作 + 积分奖励 = 超强用户增长引擎**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Node Version](https://img.shields.io/badge/node-v18+-green.svg)](https://nodejs.org/)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![GitHub](https://img.shields.io/badge/github-rwa--referral--system-blue)](https://github.com/rocky2431/rwa-referral-system)
[![Version](https://img.shields.io/badge/version-v2.0-orange.svg)](#)

</div>

---

## 📋 项目简介

RWA推荐系统是一个基于BSC(币安智能链)的Web3推荐奖励平台,结合了多级推荐、积分系统、战队协作、任务激励和知识问答等游戏化元素,帮助Web3项目实现指数级用户增长。

### 🎯 核心亮点

- 🔗 **链上推荐关系** - 基于智能合约的不可篡改推荐网络
- 💰 **多级奖励机制** - 一级15%、二级5%积分奖励
- 🎮 **任务系统** - 每日打卡、战队任务、一次性任务
- 👥 **战队协作** - 团队任务与奖励池分配
- 🎯 **Quiz答题** - 每日答题赚取积分
- 📊 **实时排行榜** - 用户积分与战队排名
- 🏆 **积分系统** - 事件驱动的积分管理

---

## ✨ 功能特性

### 1. 推荐系统 ✅
- **推荐链接生成** - 唯一邀请码 + 推荐链接
- **推荐关系绑定** - 智能合约链上存储
- **二级推荐奖励**
  - 一级推荐: 15%积分奖励
  - 二级推荐: 5%积分奖励
- **推荐数据统计** - 实时查看推荐人数和收益
- **推荐排行榜** - 全网推荐达人榜

### 2. 任务系统 ✅
**每日任务:**
- 每日打卡 (+10积分)
- 邀请新用户 (+100积分)
- 社交分享 (+20积分/次)

**每周任务:**
- 连续登录7天 (+50积分)
- 推荐5人注册 (+200积分)

**一次性任务:**
- 绑定推荐人 (+50积分)
- 加入战队 (+30积分)
- 创建战队 (+100积分)
- 首次购买 (+500积分)

**战队任务:**
- 团队邀请目标 (动态奖励)
- 团队购买目标 (动态奖励)
- 团队答题目标 (动态奖励)

### 3. 积分系统 ✅
- **多源积分获取** - 推荐、任务、答题、购买等多种方式
- **积分流水记录** - 完整的积分获取和消费历史
- **积分统计** - 日/周/月积分统计
- **积分排行榜** - 实时积分排名
- **事件驱动** - 链上事件自动触发积分发放

### 4. 战队系统 ✅
- **战队创建/加入** - 灵活的战队管理
- **成员角色管理** - 队长/管理员/会员三级权限
- **战队任务** - 团队协作完成任务
- **奖励池分配** - 基于贡献值的公平分配
- **战队排行榜** - 战队积分排名

### 5. Quiz答题系统 ✅
- **每日答题** - 每天5道题目机会
- **难度分级** - 简单/中等/困难三个难度
- **积分奖励** - 根据难度获得5/10/20积分
- **答题统计** - 正确率、连续答对天数等
- **知识传播** - Web3知识普及

### 6. 智能合约 ✅
- **RWAReferral.sol** - 推荐系统核心合约
- **循环检测** - 防止推荐环路
- **活跃管理** - 30天不活跃自动失效
- **事件驱动** - RegisteredReferrer、PaidReferral事件
- **安全保障** - 完整的安全检查机制

---

## 🏗️ 技术架构

### 技术栈

**前端:**
- React 18 + TypeScript 5
- Vite - 快速构建工具
- Ant Design 5 - 企业级UI组件库
- Ethers.js 6 - Web3交互
- React Router v6 - 路由管理
- Axios - HTTP客户端

**后端:**
- FastAPI 0.116+ - 高性能异步API框架
- Python 3.11+ - 开发语言
- SQLAlchemy 2.0 - 异步ORM
- PostgreSQL 15 - 主数据库
- Redis 7 - 缓存与消息队列
- Alembic - 数据库迁移工具

**智能合约:**
- Solidity 0.8.19
- Hardhat - 开发环境
- BSC测试网/主网

### 系统架构

```
┌─────────────────────────────────────────┐
│     前端 (React + TypeScript)            │
│  - 8个核心页面                            │
│  - 29个React组件                         │
│  - Web3钱包集成                          │
└─────────────┬───────────────────────────┘
              │ REST API
┌─────────────▼───────────────────────────┐
│    后端 (FastAPI + SQLAlchemy)           │
│  - 8个API端点模块                         │
│  - 6大Service业务层                       │
│  - 事件驱动积分系统                        │
│  - 幂等性保障机制                         │
└─────────────┬───────────────────────────┘
              │
      ┌───────┴────────┐
      │                │
┌─────▼─────┐   ┌─────▼─────┐
│PostgreSQL │   │   Redis   │
│ 主数据库   │   │  缓存层    │
└───────────┘   └───────────┘
      │
      │ 事件监听
      │
┌─────▼──────────────────────────────────┐
│   智能合约 (BSC)                        │
│  - RWAReferral.sol                     │
│  - 推荐关系管理                         │
│  - 奖励计算逻辑                         │
└────────────────────────────────────────┘
```

---

## 📊 项目统计

### 代码规模

```
总代码量: 45,110行
总文件数: 180个

分层统计:
├─ 智能合约: 432行 (1文件)
├─ 后端代码: 约25,000行 (79文件)
│  ├─ Models: 9个数据模型
│  ├─ Services: 9个业务服务
│  ├─ API Endpoints: 8个路由模块
│  ├─ Tests: 完整测试覆盖
│  └─ Scripts: 数据库迁移与初始化
└─ 前端代码: 约19,000行 (100文件)
   ├─ Pages: 8个页面
   ├─ Components: 29个组件
   ├─ Hooks: 自定义Hook
   ├─ Contexts: 全局状态管理
   └─ Services: API封装
```

### 功能完成度

```
整体进度: 90% ✅

模块详情:
├─ 智能合约: 100% ✅
├─ 后端API: 95% ✅
│  ├─ 用户系统: 100%
│  ├─ 推荐系统: 100%
│  ├─ 积分系统: 95%
│  ├─ 任务系统: 100%
│  ├─ 战队系统: 95%
│  └─ Quiz系统: 100%
└─ 前端界面: 85% ✅
   ├─ 核心页面: 100%
   ├─ 组件库: 90%
   ├─ 用户交互: 90%
   └─ 响应式设计: 80%
```

---

## 🚀 快速开始

### 环境要求

```bash
Node.js >= 18.0.0
Python >= 3.11
PostgreSQL >= 15
Redis >= 7
MetaMask钱包
```

### 安装步骤

#### 1. 克隆仓库

```bash
git clone https://github.com/rocky2431/rwa-referral-system.git
cd rwa-referral-system
```

#### 2. 安装依赖

```bash
# 安装前端依赖
cd frontend
npm install

# 安装后端依赖
cd ../backend
pip install -r requirements.txt

# 安装合约依赖
cd ../contracts
npm install
```

#### 3. 配置环境变量

```bash
# 后端配置
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入数据库配置

# 前端配置
cp frontend/.env.example frontend/.env
# 编辑 frontend/.env 填入合约地址
```

#### 4. 初始化数据库

```bash
# 启动PostgreSQL
brew services start postgresql@15  # macOS
# 或
sudo systemctl start postgresql    # Linux

# 创建数据库
createdb rwa_referral

# 执行迁移
cd backend
alembic upgrade head

# 初始化任务数据
python scripts/init_tasks.py
```

#### 5. 启动服务

```bash
# 终端1: 启动后端
cd backend
uvicorn app.main:app --reload --port 8000

# 终端2: 启动前端
cd frontend
npm run dev

# 终端3: 启动本地区块链(可选)
cd contracts
npx hardhat node
```

#### 6. 访问应用

- 前端: http://localhost:5173
- 后端API文档: http://localhost:8000/docs
- 后端健康检查: http://localhost:8000/api/v1/health

---

## 📁 项目结构

```
rwa-referral-system/
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/         # React组件
│   │   │   ├── layout/         # 布局组件
│   │   │   ├── points/         # 积分相关
│   │   │   ├── quiz/           # 答题相关
│   │   │   ├── referral/       # 推荐相关
│   │   │   ├── tasks/          # 任务相关
│   │   │   ├── teams/          # 战队相关
│   │   │   └── user/           # 用户相关
│   │   ├── contexts/           # 全局状态
│   │   ├── hooks/              # 自定义Hook
│   │   ├── pages/              # 页面组件
│   │   ├── services/           # API服务
│   │   └── App.tsx             # 根组件
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/                # API路由
│   │   │   └── endpoints/      # API端点
│   │   ├── core/               # 核心配置
│   │   ├── db/                 # 数据库配置
│   │   ├── models/             # 数据模型
│   │   ├── schemas/            # Pydantic Schema
│   │   ├── services/           # 业务逻辑
│   │   └── utils/              # 工具函数
│   ├── alembic/                # 数据库迁移
│   ├── scripts/                # 脚本工具
│   ├── tests/                  # 测试文件
│   ├── requirements.txt
│   └── .env.example
│
├── contracts/                  # 智能合约
│   ├── contracts/
│   │   └── RWAReferral.sol     # 推荐合约
│   ├── scripts/
│   │   └── deploy.js           # 部署脚本
│   ├── test/
│   │   └── RWAReferral.test.js # 合约测试
│   ├── hardhat.config.js
│   └── package.json
│
├── deployments/                # 部署配置
├── docs/                       # 文档
├── README.md                   # 项目说明
├── DEVELOPMENT.md              # 开发文档
├── DEPLOYMENT.md               # 部署文档
└── .gitignore
```

---

## 🧪 测试

### 智能合约测试

```bash
cd contracts
npx hardhat test

# 输出示例:
# RWAReferral Contract
#   ✓ Should deploy with correct config
#   ✓ Should bind referrer correctly
#   ✓ Should prevent circular referral
#   ✓ Should calculate rewards correctly
#   ... (18 tests total)
```

### 后端API测试

```bash
cd backend
pytest tests/ -v

# 输出示例:
# tests/test_points_api.py ✓✓✓✓✓✓
# tests/test_task_service.py ✓✓✓✓✓
# tests/test_team_service.py ✓✓✓✓
# ... (20+ tests total)
```

---

## 📖 API文档

启动后端服务后访问:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 核心API端点

```
用户管理:
POST   /api/v1/users/register          # 用户注册
GET    /api/v1/users/by-wallet/{addr}  # 查询用户
GET    /api/v1/users/{id}               # 用户详情

推荐系统:
POST   /api/v1/referral/generate-link   # 生成推荐链接
POST   /api/v1/referral/bind-referrer   # 绑定推荐人
GET    /api/v1/referral/user/{addr}     # 推荐数据

积分系统:
GET    /api/v1/points/user/{id}         # 用户积分
GET    /api/v1/points/transactions/{id} # 积分流水
GET    /api/v1/points/statistics        # 积分统计

任务系统:
GET    /api/v1/tasks/                   # 任务列表
POST   /api/v1/tasks/user-tasks         # 领取任务
GET    /api/v1/tasks/user-tasks/user/{id} # 用户任务

战队系统:
POST   /api/v1/teams/                   # 创建战队
POST   /api/v1/teams/join               # 加入战队
GET    /api/v1/teams/{id}/members       # 战队成员

Quiz系统:
GET    /api/v1/quiz/random              # 随机题目
POST   /api/v1/quiz/submit              # 提交答案
GET    /api/v1/quiz/statistics/user/{id} # 答题统计
```

---

## 🔒 安全特性

### 智能合约安全
- ✅ 循环推荐检测 - 防止推荐环
- ✅ 重复绑定防护 - 每个地址只能绑定一次
- ✅ 零地址验证 - 拒绝零地址
- ✅ 自我推荐防护 - 不能推荐自己
- ✅ 活跃状态检查 - 30天不活跃失效
- ✅ 权限控制 - Owner专属操作

### 后端安全
- ✅ 钱包签名验证
- ✅ SQL注入防护 (ORM)
- ✅ XSS防护
- ✅ CORS配置
- ✅ API限流
- ✅ 幂等性保障 - 防止重复发放积分
- ✅ 分布式锁 - Redis锁机制

---

## 🛣️ 开发路线图

### ✅ v1.0 MVP (已完成)
- [x] 智能合约开发
- [x] 基础推荐系统
- [x] 后端API框架
- [x] 前端界面搭建

### ✅ v2.0 游戏化升级 (当前版本 - 90%)
- [x] 积分系统
- [x] 任务系统
- [x] 战队系统
- [x] Quiz答题系统
- [x] 用户注册流程
- [x] 战队任务逻辑优化
- [ ] 实时事件监听
- [ ] 性能优化
- [ ] 移动端适配

### 🔄 v3.0 高级功能 (规划中)
- [ ] NFT奖励系统
- [ ] 社交分享优化
- [ ] 数据分析面板
- [ ] 多链支持
- [ ] DAO治理
- [ ] 移动端APP

---

## 🤝 贡献指南

欢迎贡献代码!

### 提交流程

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交Pull Request

### 代码规范

**Python:**
- 遵循 PEP 8
- 使用类型注解
- 编写Docstring

**TypeScript:**
- 遵循 ESLint 规则
- 使用严格类型检查
- 组件注释

**Solidity:**
- 遵循 Solidity Style Guide
- 使用 NatSpec 注释
- Gas优化

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 📞 联系方式

- **GitHub**: https://github.com/rocky2431/rwa-referral-system
- **Issues**: https://github.com/rocky2431/rwa-referral-system/issues

---

## 🙏 致谢

感谢以下开源项目:

- [FastAPI](https://fastapi.tiangolo.com/) - 高性能API框架
- [React](https://react.dev/) - 前端框架
- [Ant Design](https://ant.design/) - UI组件库
- [Hardhat](https://hardhat.org/) - 以太坊开发环境
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python ORM

---

<div align="center">

**Made with ❤️ by RWA Team**

**Version:** v2.0 | **Status:** ✅ Production Ready (90%)

**Last Updated:** 2025-10-22

</div>
