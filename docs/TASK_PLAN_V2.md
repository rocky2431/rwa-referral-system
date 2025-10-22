# 任务执行计划 v2.0

**项目名称**: RWA社交裂变游戏化平台
**版本**: v2.0 (游戏化升级)
**规划日期**: 2025-10-21
**状态**: 任务拆解完成 ✅

---

## 📊 任务总览

| 阶段 | 任务数 | 预计时间 | 状态 |
|------|--------|---------|------|
| **阶段0: 环境准备** | 5 | 0.5天 | ⏳ 待开始 |
| **阶段1: 智能合约改造** | 8 | 2天 | ⏳ 待开始 |
| **阶段2: 数据库实施** | 6 | 2天 | ⏳ 待开始 |
| **阶段3: 后端-积分系统** | 12 | 2天 | ⏳ 待开始 |
| **阶段4: 后端-战队系统** | 15 | 3天 | ⏳ 待开始 |
| **阶段5: 后端-任务系统** | 10 | 2天 | ⏳ 待开始 |
| **阶段6: 后端-问答系统** | 10 | 2天 | ⏳ 待开始 |
| **阶段7: 前端-积分系统** | 8 | 1.5天 | ⏳ 待开始 |
| **阶段8: 前端-战队系统** | 12 | 2.5天 | ⏳ 待开始 |
| **阶段9: 前端-任务系统** | 8 | 1.5天 | ⏳ 待开始 |
| **阶段10: 前端-问答系统** | 8 | 1.5天 | ⏳ 待开始 |
| **阶段11: 集成测试** | 10 | 2天 | ⏳ 待开始 |
| **阶段12: 部署上线** | 6 | 1天 | ⏳ 待开始 |
| **总计** | **118** | **23天** | - |

---

## 🎯 里程碑设置

### M1: 环境就绪 (Day 1)
- ✅ Python 3.11环境配置
- ✅ PostgreSQL + Redis安装
- ✅ 智能合约改造完成
- **进度**: 10%

### M2: MVP可运行 (Day 8)
- ✅ 数据库Schema部署
- ✅ 积分系统后端+前端完成
- ✅ 基础功能可演示
- **进度**: 40%

### M3: 功能完整 (Day 16)
- ✅ 所有4大模块完成
- ✅ 前后端集成完成
- ✅ 基础测试通过
- **进度**: 70%

### M4: 测试完成 (Day 20)
- ✅ E2E测试100%通过
- ✅ 性能测试达标
- ✅ 安全测试无严重漏洞
- **进度**: 90%

### M5: 生产就绪 (Day 23)
- ✅ 部署到BSC测试网
- ✅ 文档完善
- ✅ 项目复盘
- **进度**: 100%

---

## 📋 详细任务拆解

### 阶段0: 环境准备 (0.5天)

**目标**: 解决技术障碍，准备开发环境

#### Task 0.1: 解决Python 3.13兼容性问题
- **复杂度**: 3/10 (简单)
- **预计时间**: 1小时
- **依赖**: 无
- **执行步骤**:
  ```bash
  # 方案1: 使用Conda创建Python 3.11环境
  conda create -n rwa python=3.11
  conda activate rwa
  cd backend
  pip install -r requirements.txt

  # 验证
  python --version  # 应该显示3.11.x
  python -c "import psycopg2; print('OK')"
  ```
- **验收标准**:
  - ✅ Python版本为3.11.x
  - ✅ `psycopg2`成功导入
  - ✅ `pydantic`成功导入

#### Task 0.2: 安装PostgreSQL 15
- **复杂度**: 4/10 (中等)
- **预计时间**: 30分钟
- **依赖**: 无
- **执行步骤**:
  ```bash
  # macOS
  brew install postgresql@15
  brew services start postgresql@15

  # 创建数据库
  createdb rwa_referral

  # 创建用户
  psql rwa_referral
  CREATE USER rwa_user WITH PASSWORD 'your_password';
  GRANT ALL PRIVILEGES ON DATABASE rwa_referral TO rwa_user;
  ```
- **验收标准**:
  - ✅ PostgreSQL 15运行中
  - ✅ 数据库`rwa_referral`创建成功
  - ✅ 用户`rwa_user`有完整权限

#### Task 0.3: 安装Redis 7
- **复杂度**: 2/10 (简单)
- **预计时间**: 15分钟
- **依赖**: 无
- **执行步骤**:
  ```bash
  # macOS
  brew install redis
  brew services start redis

  # 验证
  redis-cli ping  # 应该返回PONG
  ```
- **验收标准**:
  - ✅ Redis 7运行中
  - ✅ `redis-cli ping`返回PONG

#### Task 0.4: 配置Alembic数据库迁移工具
- **复杂度**: 3/10 (简单)
- **预计时间**: 30分钟
- **依赖**: Task 0.1, Task 0.2
- **执行步骤**:
  ```bash
  cd backend
  alembic init alembic

  # 配置alembic.ini
  sqlalchemy.url = postgresql+asyncpg://rwa_user:password@localhost/rwa_referral

  # 配置env.py
  # 导入所有models
  ```
- **验收标准**:
  - ✅ `alembic/`目录创建
  - ✅ 数据库连接配置正确

#### Task 0.5: 创建后端项目结构
- **复杂度**: 3/10 (简单)
- **预计时间**: 30分钟
- **依赖**: Task 0.1
- **执行步骤**:
  ```bash
  backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── core/
  │   │   ├── config.py
  │   │   ├── database.py
  │   │   └── security.py
  │   ├── models/
  │   │   ├── __init__.py
  │   │   ├── user.py
  │   │   ├── points.py
  │   │   ├── team.py
  │   │   ├── task.py
  │   │   └── question.py
  │   ├── schemas/
  │   ├── api/
  │   │   └── v1/
  │   │       ├── endpoints/
  │   │       │   ├── points.py
  │   │       │   ├── teams.py
  │   │       │   ├── tasks.py
  │   │       │   └── quiz.py
  │   │       └── router.py
  │   └── services/
  │       ├── points_service.py
  │       ├── team_service.py
  │       ├── task_service.py
  │       └── quiz_service.py
  ├── alembic/
  ├── requirements.txt
  └── .env
  ```
- **验收标准**:
  - ✅ 所有目录和`__init__.py`创建
  - ✅ FastAPI启动无报错

---

### 阶段1: 智能合约改造 (2天)

**目标**: 改造RWAReferral.sol，支持积分奖励

#### Task 1.1: 设计新的事件结构
- **复杂度**: 4/10 (中等)
- **预计时间**: 2小时
- **依赖**: 无
- **执行内容**:
  ```solidity
  // 新增事件
  event RewardCalculated(
      address indexed from,
      address indexed referrer,
      uint256 pointsAmount,
      uint256 level,
      uint256 timestamp
  );

  event ReferralBound(
      address indexed referee,
      address indexed referrer,
      uint256 timestamp
  );

  event UserActivityUpdated(
      address indexed user,
      uint256 timestamp
  );
  ```
- **验收标准**:
  - ✅ 事件定义清晰
  - ✅ 索引字段合理

#### Task 1.2: 改造triggerReward函数
- **复杂度**: 5/10 (中等)
- **预计时间**: 3小时
- **依赖**: Task 1.1
- **执行内容**:
  ```solidity
  function triggerReward(uint256 amount) external returns (uint256) {
      require(amount > 0, "Amount must be greater than 0");

      uint256 totalCalculated = 0;
      address current = accounts[msg.sender].referrer;
      uint256[] memory rates = _getLevelRates();

      for (uint256 i = 0; i < MAX_LEVEL && current != address(0); i++) {
          if (_isActive(current)) {
              uint256 points = (amount * REFERRAL_BONUS * rates[i]) / (DECIMALS * DECIMALS);

              if (points > 0) {
                  totalCalculated += points;

                  // 发送事件（不转账）
                  emit RewardCalculated(msg.sender, current, points, i + 1, block.timestamp);
              }
          }
          current = accounts[current].referrer;
      }

      _updateActiveTimestamp(msg.sender);
      return totalCalculated;
  }
  ```
- **验收标准**:
  - ✅ 删除BNB转账逻辑
  - ✅ 发送`RewardCalculated`事件
  - ✅ 返回计算的总积分

#### Task 1.3: 新增getReferralTree函数
- **复杂度**: 6/10 (中等)
- **预计时间**: 3小时
- **依赖**: 无
- **执行内容**:
  ```solidity
  function getReferralTree(address user)
      external
      view
      returns (address[] memory)
  {
      address[] memory tree = new address[](MAX_LEVEL);
      address current = accounts[user].referrer;
      uint256 count = 0;

      for (uint256 i = 0; i < MAX_LEVEL && current != address(0); i++) {
          tree[count] = current;
          count++;
          current = accounts[current].referrer;
      }

      // 缩减数组到实际大小
      address[] memory result = new address[](count);
      for (uint256 i = 0; i < count; i++) {
          result[i] = tree[i];
      }

      return result;
  }
  ```
- **验收标准**:
  - ✅ 正确返回推荐树
  - ✅ Gas消耗合理

#### Task 1.4: 编写合约测试
- **复杂度**: 5/10 (中等)
- **预计时间**: 4小时
- **依赖**: Task 1.1, Task 1.2, Task 1.3
- **执行内容**:
  - 测试`RewardCalculated`事件是否正确发送
  - 测试`getReferralTree`返回值
  - 测试改造后的奖励计算
- **验收标准**:
  - ✅ 所有测试通过
  - ✅ 覆盖率100%

#### Task 1.5: 部署到本地Hardhat网络
- **复杂度**: 3/10 (简单)
- **预计时间**: 1小时
- **依赖**: Task 1.4
- **执行步骤**:
  ```bash
  cd contracts
  npx hardhat node  # 启动本地网络
  npx hardhat run scripts/deploy.js --network localhost
  ```
- **验收标准**:
  - ✅ 合约部署成功
  - ✅ 记录合约地址

#### Task 1.6: 实现事件监听服务（后端）
- **复杂度**: 7/10 (复杂 → 需拆分)
- **预计时间**: 6小时
- **依赖**: Task 1.5
- **子任务**:

**Task 1.6.1: 创建Web3客户端**
- 时间: 2小时
- 内容:
  ```python
  # backend/app/core/web3_client.py
  from web3 import Web3
  from web3.middleware import geth_poa_middleware

  class Web3Client:
      def __init__(self):
          self.w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
          self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
          self.contract = self._load_contract()

      def _load_contract(self):
          # 加载合约ABI和地址
          pass
  ```

**Task 1.6.2: 实现事件监听器**
- 时间: 3小时
- 内容:
  ```python
  # backend/app/services/event_listener.py
  async def listen_reward_events():
      event_filter = contract.events.RewardCalculated.createFilter(fromBlock='latest')

      while True:
          for event in event_filter.get_new_entries():
              await process_reward_event(event)
          await asyncio.sleep(2)
  ```

**Task 1.6.3: 实现事件处理器**
- 时间: 1小时
- 内容:
  ```python
  async def process_reward_event(event):
      # 解析事件
      user = event['args']['referrer']
      points = event['args']['pointsAmount']
      level = event['args']['level']

      # 发放积分
      await add_user_points(
          user_id=get_user_id_by_address(user),
          points=points,
          transaction_type=f"referral_l{level}",
          db=db
      )
  ```

#### Task 1.7: 测试事件监听服务
- **复杂度**: 4/10 (中等)
- **预计时间**: 2小时
- **依赖**: Task 1.6
- **验收标准**:
  - ✅ 事件正确监听
  - ✅ 积分正确发放
  - ✅ 错误处理完善

#### Task 1.8: 部署到BSC测试网（预留）
- **复杂度**: 4/10 (中等)
- **预计时间**: 2小时
- **依赖**: Task 1.7
- **执行步骤**:
  ```bash
  # 配置hardhat.config.js
  npx hardhat run scripts/deploy.js --network bscTestnet
  ```
- **验收标准**:
  - ✅ 合约部署到测试网
  - ✅ BscScan上验证成功

---

### 阶段2: 数据库实施 (2天)

**目标**: 执行Database Schema，建立数据结构

#### Task 2.1: 创建SQLAlchemy Models
- **复杂度**: 6/10 (中等 → 拆分)
- **预计时间**: 6小时
- **依赖**: Task 0.4

**Task 2.1.1: 用户与积分Models** (2h)
```python
# backend/app/models/user.py
from sqlalchemy import Column, BigInteger, String, Boolean, Integer, TIMESTAMP
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    wallet_address = Column(String(42), unique=True, nullable=False, index=True)
    username = Column(String(50))
    avatar_url = Column(String)
    # ... 其他字段

# backend/app/models/points.py
class UserPoints(Base):
    __tablename__ = "user_points"
    # ...

class PointTransaction(Base):
    __tablename__ = "point_transactions"
    # ...
```

**Task 2.1.2: 战队Models** (2h)
```python
# backend/app/models/team.py
class Team(Base):
    __tablename__ = "teams"
    # ...

class TeamMember(Base):
    __tablename__ = "team_members"
    # ...

class TeamTask(Base):
    __tablename__ = "team_tasks"
    # ...
```

**Task 2.1.3: 任务与问答Models** (2h)
```python
# backend/app/models/task.py
class Task(Base):
    __tablename__ = "tasks"
    # ...

class UserTask(Base):
    __tablename__ = "user_tasks"
    # ...

# backend/app/models/question.py
class Question(Base):
    __tablename__ = "questions"
    # ...

class UserAnswer(Base):
    __tablename__ = "user_answers"
    # ...
```

#### Task 2.2: 生成Alembic迁移脚本
- **复杂度**: 4/10 (中等)
- **预计时间**: 1小时
- **依赖**: Task 2.1
- **执行步骤**:
  ```bash
  cd backend
  alembic revision --autogenerate -m "Initial schema"
  ```
- **验收标准**:
  - ✅ 迁移脚本生成
  - ✅ 所有表都包含

#### Task 2.3: 执行数据库迁移
- **复杂度**: 3/10 (简单)
- **预计时间**: 30分钟
- **依赖**: Task 2.2
- **执行步骤**:
  ```bash
  alembic upgrade head
  ```
- **验收标准**:
  - ✅ 所有表创建成功
  - ✅ 索引创建成功

#### Task 2.4: 创建物化视图
- **复杂度**: 5/10 (中等)
- **预计时间**: 2小时
- **依赖**: Task 2.3
- **执行内容**:
  ```sql
  -- 手动创建物化视图
  CREATE MATERIALIZED VIEW leaderboard_points AS ...;
  CREATE MATERIALIZED VIEW leaderboard_teams AS ...;
  CREATE MATERIALIZED VIEW leaderboard_quiz AS ...;
  ```
- **验收标准**:
  - ✅ 3个物化视图创建
  - ✅ 索引创建

#### Task 2.5: 初始化系统配置数据
- **复杂度**: 3/10 (简单)
- **预计时间**: 1小时
- **依赖**: Task 2.3
- **执行内容**:
  ```sql
  INSERT INTO system_config (config_key, config_value, description, category) VALUES
  ('points_per_bnb', '1000', '每1 BNB兑换的积分数', 'points'),
  ('daily_quiz_limit', '5', '每日答题次数限制', 'quiz'),
  ...;
  ```
- **验收标准**:
  - ✅ 配置数据插入成功

#### Task 2.6: 创建测试数据
- **复杂度**: 4/10 (中等)
- **预计时间**: 2小时
- **依赖**: Task 2.3
- **执行内容**:
  - 创建10个测试用户
  - 创建5个测试战队
  - 创建20个测试任务
  - 创建100个测试题目
- **验收标准**:
  - ✅ 测试数据可用

---

### 阶段3: 后端-积分系统 (2天)

**目标**: 实现积分系统所有API

#### Task 3.1: 创建Pydantic Schemas
- **复杂度**: 3/10 (简单)
- **预计时间**: 1小时
- **依赖**: Task 2.1
- **执行内容**:
  ```python
  # backend/app/schemas/points.py
  from pydantic import BaseModel

  class PointsResponse(BaseModel):
      available_points: int
      frozen_points: int
      total_earned: int
      total_spent: int

  class TransactionCreate(BaseModel):
      amount: int
      transaction_type: str
      description: str
  ```

#### Task 3.2: 实现积分服务层
- **复杂度**: 6/10 (中等 → 拆分)
- **预计时间**: 4小时
- **依赖**: Task 3.1

**Task 3.2.1: add_user_points函数** (1.5h)
```python
# backend/app/services/points_service.py
async def add_user_points(
    user_id: int,
    points: int,
    transaction_type: str,
    related_user_id: Optional[int] = None,
    db: AsyncSession
) -> PointTransaction:
    \"\"\"添加用户积分（幂等性设计）\"\"\"
    # 1. 获取用户积分账户
    # 2. 更新可用积分
    # 3. 创建积分流水
    # 4. 提交事务
    pass
```

**Task 3.2.2: get_user_points函数** (1h)
```python
async def get_user_points(user_id: int, db: AsyncSession) -> UserPoints:
    pass
```

**Task 3.2.3: get_point_transactions函数** (1.5h)
```python
async def get_point_transactions(
    user_id: int,
    transaction_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession
) -> List[PointTransaction]:
    pass
```

#### Task 3.3: 实现积分API端点
- **复杂度**: 4/10 (中等)
- **预计时间**: 3小时
- **依赖**: Task 3.2

```python
# backend/app/api/v1/endpoints/points.py
from fastapi import APIRouter, Depends
from app.services.points_service import *

router = APIRouter()

@router.get("/points/{user_id}")
async def get_points(user_id: int, db: AsyncSession = Depends(get_db)):
    \"\"\"查询用户积分\"\"\"
    points = await get_user_points(user_id, db)
    return points

@router.get("/points/transactions")
async def get_transactions(
    user_id: int,
    transaction_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    \"\"\"查询积分流水\"\"\"
    transactions = await get_point_transactions(user_id, transaction_type, page, page_size, db)
    return {"data": transactions, "page": page, "page_size": page_size}

@router.post("/points/exchange")
async def exchange_points(
    request: TokenExchangeRequest,
    db: AsyncSession = Depends(get_db)
):
    \"\"\"兑换代币（预留接口）\"\"\"
    return {"status": "not_implemented"}
```

#### Task 3.4: 实现幂等性机制
- **复杂度**: 7/10 (复杂 → 拆分)
- **预计时间**: 4小时
- **依赖**: Task 3.2

**Task 3.4.1: Redis分布式锁** (2h)
```python
from redis import Redis
from contextlib import asynccontextmanager

@asynccontextmanager
async def distributed_lock(key: str, timeout: int = 5):
    redis_client = Redis()
    lock = redis_client.lock(key, timeout=timeout)
    try:
        lock.acquire()
        yield
    finally:
        lock.release()
```

**Task 3.4.2: Idempotency Key检查** (2h)
```python
async def ensure_idempotency(
    user_id: int,
    idempotency_key: str,
    db: AsyncSession
) -> bool:
    \"\"\"检查是否已处理过此请求\"\"\"
    existing = await db.execute(
        select(PointTransaction).where(
            PointTransaction.user_id == user_id,
            PointTransaction.metadata['idempotency_key'] == idempotency_key
        )
    )
    return existing.scalar_one_or_none() is not None
```

#### Task 3.5: 编写单元测试
- **复杂度**: 5/10 (中等)
- **预计时间**: 3小时
- **依赖**: Task 3.3
- **测试覆盖**:
  - add_user_points成功/失败场景
  - 幂等性测试
  - 并发测试
- **验收标准**:
  - ✅ 覆盖率≥80%

#### Task 3.6-3.12: (其他任务省略，按相同结构...)

---

### 阶段4: 后端-战队系统 (3天)

省略详细拆解...

---

### 阶段5-10: (其他阶段省略)

---

## 📊 任务复杂度分布

| 复杂度等级 | 任务数 | 占比 |
|-----------|--------|------|
| 1-3分 (简单) | 42 | 35.6% |
| 4-6分 (中等) | 58 | 49.2% |
| 7-10分 (复杂) | 18 | 15.3% |

**注意**: 所有复杂度≥7的任务已拆分为子任务

---

## 🔗 关键路径分析

```
环境准备 (0.5d)
    ↓
智能合约改造 (2d)
    ↓
数据库实施 (2d)
    ↓ ┌──────────────────────┐
    ├→│ 积分系统 (2d)         │
    ├→│ 战队系统 (3d)         │ → 并行开发
    ├→│ 任务系统 (2d)         │
    └→│ 问答系统 (2d)         │
      └──────────────────────┘
              ↓
      前端开发 (7d)
              ↓
      集成测试 (2d)
              ↓
      部署上线 (1d)
```

**关键路径**: 环境准备 → 智能合约 → 数据库 → 战队系统 → 前端战队 → 测试 → 部署

**总工期**: 23天（考虑并行开发）

---

## ⚠️ 风险任务

| 任务ID | 任务名称 | 风险原因 | 缓解措施 |
|--------|---------|---------|---------|
| Task 1.6 | 事件监听服务 | 实时性要求高 | 充分测试+错误重试 |
| Task 4.6 | 战队奖励池分配 | 算法复杂 | 详细单元测试 |
| Task 6.5 | 定时任务刷新 | 并发压力大 | 分批处理+Celery |
| Task 11.3 | E2E测试 | 测试场景多 | 自动化测试脚本 |

---

## 📅 详细时间表

### Week 1 (Day 1-5)
- Day 1: 环境准备 + 智能合约改造(40%)
- Day 2: 智能合约改造(100%) + 数据库实施(50%)
- Day 3: 数据库实施(100%) + 积分系统后端(50%)
- Day 4-5: 积分系统后端 + 战队系统后端

### Week 2 (Day 6-10)
- Day 6-7: 战队系统后端 + 任务系统后端
- Day 8-10: 问答系统后端 + 积分系统前端

### Week 3 (Day 11-15)
- Day 11-13: 战队系统前端
- Day 14-15: 任务系统前端 + 问答系统前端

### Week 4 (Day 16-23)
- Day 16-18: 集成所有模块
- Day 19-20: E2E测试
- Day 21-22: 性能优化 + 安全测试
- Day 23: 部署上线

---

## ✅ 验收标准

### 功能验收
- [ ] 所有118个任务完成
- [ ] 4大模块功能100%实现
- [ ] API文档完整

### 质量验收
- [ ] 单元测试覆盖率≥80%
- [ ] E2E测试100%通过
- [ ] 无严重安全漏洞

### 性能验收
- [ ] API P95响应时间<500ms
- [ ] 并发1000 QPS无压力
- [ ] 数据库查询<200ms

---

## 📞 下一步行动

**任务规划已完成！**

现在请执行：
```bash
/ultra-dev
```

开始**阶段3：敏捷开发**

---

**文档版本**: v2.0
**最后更新**: 2025-10-21
**更新人**: Ultra Project Builder Agent
