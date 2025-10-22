# 数据库设计文档

**项目**: RWA社交裂变游戏化平台
**数据库**: PostgreSQL 15
**ORM**: SQLAlchemy 2.0
**版本**: v2.0
**更新日期**: 2025-10-21

---

## 📊 ER图概览

```
users (用户)
  ↓ 1:N
user_points (积分账户)
  ↓ 1:N
point_transactions (积分流水)

users
  ↓ N:N (through team_members)
teams (战队)
  ↓ 1:N
team_tasks (战队任务)

users
  ↓ 1:N
user_tasks (用户任务进度)
  ↓ N:1
tasks (任务配置)

users
  ↓ 1:N
user_answers (答题记录)
  ↓ N:1
questions (题库)

users
  ↓ 1:1
referral_relations (推荐关系)
```

---

## 📋 表结构详细设计

### 1. 用户相关表

#### 1.1 users (用户表)

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    wallet_address VARCHAR(42) UNIQUE NOT NULL,  -- 钱包地址 (唯一)
    username VARCHAR(50),                        -- 用户名 (可选)
    avatar_url TEXT,                             -- 头像URL
    email VARCHAR(100),                          -- 邮箱 (可选)

    -- 用户等级系统
    level INTEGER DEFAULT 1,                     -- 等级 (1-100)
    experience BIGINT DEFAULT 0,                 -- 经验值

    -- 统计数据 (冗余字段，提升查询性能)
    total_points BIGINT DEFAULT 0,               -- 总积分
    total_invited INTEGER DEFAULT 0,             -- 总邀请人数
    total_tasks_completed INTEGER DEFAULT 0,     -- 完成任务数
    total_questions_answered INTEGER DEFAULT 0,  -- 答题总数
    correct_answers INTEGER DEFAULT 0,           -- 正确答题数

    -- 活跃度
    last_active_at TIMESTAMP,                    -- 最后活跃时间
    consecutive_login_days INTEGER DEFAULT 0,    -- 连续登录天数
    last_login_date DATE,                        -- 最后登录日期

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,              -- 是否激活
    is_banned BOOLEAN DEFAULT FALSE,             -- 是否被封禁
    banned_until TIMESTAMP,                      -- 封禁到期时间

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    CONSTRAINT wallet_address_format CHECK (wallet_address ~ '^0x[a-fA-F0-9]{40}$')
);

-- 索引
CREATE INDEX idx_users_wallet ON users(wallet_address);
CREATE INDEX idx_users_level ON users(level DESC);
CREATE INDEX idx_users_total_points ON users(total_points DESC);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_last_active ON users(last_active_at);

-- 更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### 2. 积分系统表

#### 2.1 user_points (用户积分账户)

```sql
CREATE TABLE user_points (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 积分账户
    available_points BIGINT DEFAULT 0,           -- 可用积分
    frozen_points BIGINT DEFAULT 0,              -- 冻结积分
    total_earned BIGINT DEFAULT 0,               -- 累计获得
    total_spent BIGINT DEFAULT 0,                -- 累计消费

    -- 统计 (按来源)
    points_from_referral BIGINT DEFAULT 0,       -- 推荐奖励积分
    points_from_tasks BIGINT DEFAULT 0,          -- 任务获得积分
    points_from_quiz BIGINT DEFAULT 0,           -- 答题获得积分
    points_from_team BIGINT DEFAULT 0,           -- 战队奖励积分
    points_from_purchase BIGINT DEFAULT 0,       -- 购买获得积分

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT unique_user_points UNIQUE(user_id),
    CONSTRAINT points_non_negative CHECK (available_points >= 0),
    CONSTRAINT frozen_non_negative CHECK (frozen_points >= 0)
);

-- 索引
CREATE INDEX idx_user_points_user_id ON user_points(user_id);
CREATE INDEX idx_user_points_available ON user_points(available_points DESC);

-- 更新触发器
CREATE TRIGGER update_user_points_updated_at BEFORE UPDATE ON user_points
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### 2.2 point_transactions (积分流水表)

```sql
CREATE TYPE point_transaction_type AS ENUM (
    'referral_l1',        -- 一级推荐奖励
    'referral_l2',        -- 二级推荐奖励
    'task_daily',         -- 每日任务
    'task_weekly',        -- 每周任务
    'task_once',          -- 一次性任务
    'quiz_correct',       -- 答题正确
    'team_reward',        -- 战队奖励
    'purchase',           -- 购买奖励
    'admin_grant',        -- 管理员发放
    'exchange_token',     -- 兑换代币
    'spend_item'          -- 消费物品
);

CREATE TABLE point_transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 交易信息
    transaction_type point_transaction_type NOT NULL,
    amount BIGINT NOT NULL,                      -- 积分变动 (正数=获得, 负数=消费)
    balance_after BIGINT NOT NULL,               -- 交易后余额

    -- 关联信息
    related_task_id BIGINT,                      -- 关联任务ID
    related_user_id BIGINT REFERENCES users(id), -- 关联用户 (推荐人/被推荐人)
    related_team_id BIGINT,                      -- 关联战队ID
    related_question_id BIGINT,                  -- 关联题目ID

    -- 元数据
    description TEXT,                            -- 描述
    metadata JSONB,                              -- 额外数据 (灵活扩展)

    -- 状态
    status VARCHAR(20) DEFAULT 'completed',      -- completed/pending/cancelled

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT amount_not_zero CHECK (amount != 0)
);

-- 索引
CREATE INDEX idx_point_tx_user_id ON point_transactions(user_id);
CREATE INDEX idx_point_tx_type ON point_transactions(transaction_type);
CREATE INDEX idx_point_tx_created_at ON point_transactions(created_at DESC);
CREATE INDEX idx_point_tx_related_user ON point_transactions(related_user_id);
CREATE INDEX idx_point_tx_metadata ON point_transactions USING GIN(metadata);
```

---

### 3. 战队系统表

#### 3.1 teams (战队表)

```sql
CREATE TABLE teams (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,            -- 战队名称
    description TEXT,                            -- 战队描述
    logo_url TEXT,                               -- 战队Logo

    -- 队长
    captain_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,

    -- 统计数据
    member_count INTEGER DEFAULT 1,              -- 成员数量
    total_points BIGINT DEFAULT 0,               -- 战队总积分
    active_member_count INTEGER DEFAULT 0,       -- 活跃成员数

    -- 战队等级
    level INTEGER DEFAULT 1,                     -- 战队等级
    experience BIGINT DEFAULT 0,                 -- 战队经验值

    -- 奖励池
    reward_pool BIGINT DEFAULT 0,                -- 奖励池积分
    last_distribution_at TIMESTAMP,              -- 上次分配时间

    -- 设置
    is_public BOOLEAN DEFAULT TRUE,              -- 是否公开
    require_approval BOOLEAN DEFAULT FALSE,      -- 是否需要审批
    min_level_required INTEGER DEFAULT 1,        -- 最低等级要求

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_teams_captain ON teams(captain_id);
CREATE INDEX idx_teams_total_points ON teams(total_points DESC);
CREATE INDEX idx_teams_member_count ON teams(member_count DESC);
CREATE INDEX idx_teams_created_at ON teams(created_at);
CREATE INDEX idx_teams_name ON teams(name);

-- 更新触发器
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### 3.2 team_members (战队成员表)

```sql
CREATE TYPE team_member_role AS ENUM ('captain', 'admin', 'member');
CREATE TYPE team_member_status AS ENUM ('active', 'pending', 'rejected', 'left');

CREATE TABLE team_members (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 角色
    role team_member_role DEFAULT 'member',

    -- 贡献统计
    contribution_points BIGINT DEFAULT 0,        -- 贡献积分
    tasks_completed INTEGER DEFAULT 0,           -- 完成任务数

    -- 状态
    status team_member_status DEFAULT 'pending',

    -- 时间
    joined_at TIMESTAMP,                         -- 加入时间
    approved_at TIMESTAMP,                       -- 批准时间
    left_at TIMESTAMP,                           -- 离开时间

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT unique_team_user UNIQUE(team_id, user_id)
);

-- 索引
CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
CREATE INDEX idx_team_members_role ON team_members(role);
CREATE INDEX idx_team_members_status ON team_members(status);
CREATE INDEX idx_team_members_contribution ON team_members(contribution_points DESC);

-- 更新触发器
CREATE TRIGGER update_team_members_updated_at BEFORE UPDATE ON team_members
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### 3.3 team_tasks (战队任务表)

```sql
CREATE TYPE team_task_status AS ENUM ('active', 'completed', 'expired', 'cancelled');

CREATE TABLE team_tasks (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,

    -- 任务信息
    title VARCHAR(100) NOT NULL,
    description TEXT,
    task_type VARCHAR(50),                       -- 任务类型

    -- 目标
    target_value INTEGER NOT NULL,               -- 目标值 (如：邀请50人)
    current_value INTEGER DEFAULT 0,             -- 当前进度

    -- 奖励
    reward_points BIGINT NOT NULL,               -- 奖励积分
    bonus_points BIGINT DEFAULT 0,               -- 额外奖励

    -- 时间
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,

    -- 状态
    status team_task_status DEFAULT 'active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_team_tasks_team_id ON team_tasks(team_id);
CREATE INDEX idx_team_tasks_status ON team_tasks(status);
CREATE INDEX idx_team_tasks_end_time ON team_tasks(end_time);

-- 更新触发器
CREATE TRIGGER update_team_tasks_updated_at BEFORE UPDATE ON team_tasks
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### 4. 任务系统表

#### 4.1 tasks (任务配置表)

```sql
CREATE TYPE task_type AS ENUM ('daily', 'weekly', 'once', 'team');
CREATE TYPE task_trigger AS ENUM ('auto', 'manual', 'event');

CREATE TABLE tasks (
    id BIGSERIAL PRIMARY KEY,

    -- 任务基本信息
    task_key VARCHAR(50) UNIQUE NOT NULL,        -- 任务唯一标识 (如: daily_signin)
    title VARCHAR(100) NOT NULL,                 -- 任务标题
    description TEXT,                            -- 任务描述
    icon_url TEXT,                               -- 图标URL

    -- 任务类型
    task_type task_type NOT NULL,
    trigger_type task_trigger DEFAULT 'manual',

    -- 目标配置
    target_type VARCHAR(50),                     -- 目标类型 (invite_users/share/purchase)
    target_value INTEGER DEFAULT 1,              -- 目标值

    -- 奖励配置
    reward_points INTEGER NOT NULL,              -- 奖励积分
    reward_experience INTEGER DEFAULT 0,         -- 奖励经验值
    bonus_multiplier DECIMAL(3,2) DEFAULT 1.0,   -- 奖励倍数

    -- 限制条件
    min_level_required INTEGER DEFAULT 1,        -- 最低等级要求
    max_completions_per_user INTEGER,            -- 每用户最大完成次数

    -- 优先级和排序
    priority INTEGER DEFAULT 0,                  -- 优先级 (越大越靠前)
    sort_order INTEGER DEFAULT 0,                -- 排序

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    is_visible BOOLEAN DEFAULT TRUE,

    -- 时间配置
    start_time TIMESTAMP,                        -- 任务开始时间
    end_time TIMESTAMP,                          -- 任务结束时间

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_tasks_task_key ON tasks(task_key);
CREATE INDEX idx_tasks_type ON tasks(task_type);
CREATE INDEX idx_tasks_active ON tasks(is_active, is_visible);
CREATE INDEX idx_tasks_priority ON tasks(priority DESC);

-- 更新触发器
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### 4.2 user_tasks (用户任务进度表)

```sql
CREATE TYPE user_task_status AS ENUM ('in_progress', 'completed', 'claimed', 'expired');

CREATE TABLE user_tasks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,

    -- 进度
    current_value INTEGER DEFAULT 0,             -- 当前进度
    target_value INTEGER NOT NULL,               -- 目标值 (复制自tasks)

    -- 状态
    status user_task_status DEFAULT 'in_progress',

    -- 奖励
    reward_points INTEGER NOT NULL,              -- 奖励积分
    bonus_points INTEGER DEFAULT 0,              -- 额外奖励
    is_claimed BOOLEAN DEFAULT FALSE,            -- 是否已领取

    -- 时间
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,                      -- 完成时间
    claimed_at TIMESTAMP,                        -- 领取时间
    expires_at TIMESTAMP,                        -- 过期时间

    -- 元数据
    metadata JSONB,                              -- 额外数据

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT unique_user_task_daily UNIQUE(user_id, task_id, expires_at)  -- 每日任务唯一
);

-- 索引
CREATE INDEX idx_user_tasks_user_id ON user_tasks(user_id);
CREATE INDEX idx_user_tasks_task_id ON user_tasks(task_id);
CREATE INDEX idx_user_tasks_status ON user_tasks(status);
CREATE INDEX idx_user_tasks_expires_at ON user_tasks(expires_at);
CREATE INDEX idx_user_tasks_user_status ON user_tasks(user_id, status);

-- 更新触发器
CREATE TRIGGER update_user_tasks_updated_at BEFORE UPDATE ON user_tasks
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

### 5. 问答系统表

#### 5.1 questions (题库表)

```sql
CREATE TYPE question_difficulty AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE question_source AS ENUM ('admin', 'user_submit', 'api');
CREATE TYPE question_status AS ENUM ('pending', 'approved', 'rejected', 'active', 'disabled');

CREATE TABLE questions (
    id BIGSERIAL PRIMARY KEY,

    -- 题目内容
    question_text TEXT NOT NULL,                 -- 题目
    option_a VARCHAR(200) NOT NULL,              -- 选项A
    option_b VARCHAR(200) NOT NULL,              -- 选项B
    option_c VARCHAR(200),                       -- 选项C (可选)
    option_d VARCHAR(200),                       -- 选项D (可选)
    correct_answer CHAR(1) NOT NULL,             -- 正确答案 (A/B/C/D)

    -- 难度与分类
    difficulty question_difficulty NOT NULL,
    category VARCHAR(50),                        -- 分类 (Web3/DeFi/NFT等)
    tags VARCHAR(100)[],                         -- 标签数组

    -- 奖励
    reward_points INTEGER NOT NULL,              -- 答对奖励积分

    -- 来源
    source question_source DEFAULT 'admin',
    submitted_by BIGINT REFERENCES users(id),    -- 提交者

    -- 统计
    total_answers INTEGER DEFAULT 0,             -- 回答次数
    correct_answers INTEGER DEFAULT 0,           -- 正确次数
    accuracy_rate DECIMAL(5,2),                  -- 正确率 (自动计算)

    -- 审核
    status question_status DEFAULT 'pending',
    reviewed_by BIGINT REFERENCES users(id),     -- 审核者
    reviewed_at TIMESTAMP,
    reject_reason TEXT,

    -- 时效
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT correct_answer_valid CHECK (correct_answer IN ('A', 'B', 'C', 'D'))
);

-- 索引
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_category ON questions(category);
CREATE INDEX idx_questions_status ON questions(status);
CREATE INDEX idx_questions_tags ON questions USING GIN(tags);
CREATE INDEX idx_questions_accuracy ON questions(accuracy_rate);

-- 更新触发器
CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON questions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### 5.2 user_answers (答题记录表)

```sql
CREATE TABLE user_answers (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id BIGINT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,

    -- 答题信息
    user_answer CHAR(1) NOT NULL,                -- 用户答案
    is_correct BOOLEAN NOT NULL,                 -- 是否正确

    -- 时间
    answer_time INTEGER,                         -- 答题耗时 (秒)
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 奖励
    points_earned INTEGER DEFAULT 0,             -- 获得积分

    -- 日期 (用于限制每日答题次数)
    answer_date DATE DEFAULT CURRENT_DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT user_answer_valid CHECK (user_answer IN ('A', 'B', 'C', 'D'))
);

-- 索引
CREATE INDEX idx_user_answers_user_id ON user_answers(user_id);
CREATE INDEX idx_user_answers_question_id ON user_answers(question_id);
CREATE INDEX idx_user_answers_date ON user_answers(answer_date);
CREATE INDEX idx_user_answers_user_date ON user_answers(user_id, answer_date);
CREATE INDEX idx_user_answers_correct ON user_answers(is_correct);
```

#### 5.3 daily_quiz_sessions (每日答题会话表)

```sql
CREATE TABLE daily_quiz_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_date DATE DEFAULT CURRENT_DATE,

    -- 统计
    questions_answered INTEGER DEFAULT 0,        -- 已答题数
    correct_count INTEGER DEFAULT 0,             -- 正确数
    total_points_earned INTEGER DEFAULT 0,       -- 总积分

    -- 时间
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT unique_user_quiz_date UNIQUE(user_id, session_date),
    CONSTRAINT max_questions CHECK (questions_answered <= 5)
);

-- 索引
CREATE INDEX idx_quiz_sessions_user_date ON daily_quiz_sessions(user_id, session_date);
```

---

### 6. 推荐关系表 (从链上同步)

#### 6.1 referral_relations (推荐关系表)

```sql
CREATE TABLE referral_relations (
    id BIGSERIAL PRIMARY KEY,
    referee_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,      -- 被推荐人
    referrer_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,    -- 推荐人

    -- 链上数据
    blockchain_tx_hash VARCHAR(66),              -- 绑定交易hash
    blockchain_block_number BIGINT,              -- 区块号

    -- 层级
    level INTEGER DEFAULT 1,                     -- 推荐层级 (1=直接, 2=二级)

    -- 统计
    total_rewards_given BIGINT DEFAULT 0,        -- 累计给推荐人的奖励

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,

    -- 时间
    bound_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 最后同步时间

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT unique_referee UNIQUE(referee_id),
    CONSTRAINT no_self_referral CHECK (referee_id != referrer_id)
);

-- 索引
CREATE INDEX idx_referral_referrer ON referral_relations(referrer_id);
CREATE INDEX idx_referral_referee ON referral_relations(referee_id);
CREATE INDEX idx_referral_level ON referral_relations(level);
CREATE INDEX idx_referral_blockchain_tx ON referral_relations(blockchain_tx_hash);
```

---

### 7. 系统配置表

#### 7.1 system_config (系统配置表)

```sql
CREATE TABLE system_config (
    id BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,      -- 配置键
    config_value TEXT NOT NULL,                  -- 配置值 (JSON格式)
    description TEXT,                            -- 描述

    -- 分类
    category VARCHAR(30),                        -- 分类 (points/tasks/quiz/team)

    -- 时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_system_config_key ON system_config(config_key);
CREATE INDEX idx_system_config_category ON system_config(category);

-- 更新触发器
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 初始化配置数据
INSERT INTO system_config (config_key, config_value, description, category) VALUES
('points_per_bnb', '1000', '每1 BNB兑换的积分数', 'points'),
('daily_quiz_limit', '5', '每日答题次数限制', 'quiz'),
('quiz_time_limit', '30', '答题时间限制(秒)', 'quiz'),
('referral_l1_points', '150', '一级推荐奖励积分', 'points'),
('referral_l2_points', '50', '二级推荐奖励积分', 'points'),
('team_min_members', '3', '战队最少成员数', 'team'),
('task_daily_signin_points', '10', '每日签到奖励', 'tasks'),
('task_invite_friend_points', '100', '邀请好友奖励', 'tasks'),
('consecutive_login_7days_bonus', '50', '连续7天登录额外奖励', 'tasks');
```

---

## 🔐 安全性设计

### 数据安全
1. **敏感数据加密**: 用户邮箱等字段考虑加密存储
2. **钱包地址校验**: 正则表达式验证以太坊地址格式
3. **积分防篡改**: 所有积分变动必须通过`point_transactions`记录

### 性能优化
1. **冗余字段**: `users.total_points`, `teams.member_count`等减少JOIN查询
2. **分区表**: `point_transactions`按月分区，提升查询性能
3. **物化视图**: 排行榜等频繁查询数据使用物化视图

### 索引策略
1. **复合索引**: `user_tasks(user_id, status)` 优化常见查询
2. **部分索引**: `WHERE is_active = TRUE` 减少索引大小
3. **GIN索引**: JSONB字段使用GIN索引

---

## 📈 数据统计视图

### 排行榜物化视图

```sql
-- 积分排行榜
CREATE MATERIALIZED VIEW leaderboard_points AS
SELECT
    u.id,
    u.wallet_address,
    u.username,
    u.avatar_url,
    u.level,
    u.total_points,
    u.total_invited,
    ROW_NUMBER() OVER (ORDER BY u.total_points DESC, u.created_at ASC) as rank
FROM users u
WHERE u.is_active = TRUE AND u.is_banned = FALSE
ORDER BY u.total_points DESC
LIMIT 1000;

CREATE UNIQUE INDEX idx_leaderboard_points_id ON leaderboard_points(id);
CREATE INDEX idx_leaderboard_points_rank ON leaderboard_points(rank);

-- 定时刷新 (每小时)
-- 在定时任务中执行: REFRESH MATERIALIZED VIEW CONCURRENTLY leaderboard_points;
```

```sql
-- 战队排行榜
CREATE MATERIALIZED VIEW leaderboard_teams AS
SELECT
    t.id,
    t.name,
    t.logo_url,
    t.member_count,
    t.active_member_count,
    t.total_points,
    t.level,
    u.username as captain_name,
    ROW_NUMBER() OVER (ORDER BY t.total_points DESC, t.created_at ASC) as rank
FROM teams t
JOIN users u ON t.captain_id = u.id
WHERE t.is_active = TRUE
ORDER BY t.total_points DESC
LIMIT 500;

CREATE UNIQUE INDEX idx_leaderboard_teams_id ON leaderboard_teams(id);
CREATE INDEX idx_leaderboard_teams_rank ON leaderboard_teams(rank);
```

```sql
-- 答题王排行榜
CREATE MATERIALIZED VIEW leaderboard_quiz AS
SELECT
    u.id,
    u.wallet_address,
    u.username,
    u.avatar_url,
    u.total_questions_answered,
    u.correct_answers,
    CASE
        WHEN u.total_questions_answered > 0
        THEN ROUND((u.correct_answers::decimal / u.total_questions_answered * 100), 2)
        ELSE 0
    END as accuracy_rate,
    ROW_NUMBER() OVER (ORDER BY u.correct_answers DESC, accuracy_rate DESC) as rank
FROM users u
WHERE u.is_active = TRUE AND u.total_questions_answered > 0
ORDER BY u.correct_answers DESC
LIMIT 500;

CREATE UNIQUE INDEX idx_leaderboard_quiz_id ON leaderboard_quiz(id);
CREATE INDEX idx_leaderboard_quiz_rank ON leaderboard_quiz(rank);
```

---

## 🔄 数据迁移策略

### Alembic版本管理

```bash
# 初始化Alembic
alembic init alembic

# 创建迁移脚本
alembic revision --autogenerate -m "Initial schema"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

### 数据同步计划

1. **链上→链下同步**:
   - 监听智能合约事件 `RegisteredReferrer`
   - 每10分钟批量同步到 `referral_relations` 表

2. **冗余字段更新**:
   - 使用触发器自动更新 `users.total_points`
   - 定时任务更新 `teams.member_count`

---

## 📝 备注

### 数据库连接配置
```python
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/rwa_referral"
POOL_SIZE = 20
MAX_OVERFLOW = 10
POOL_PRE_PING = True
```

### 性能基准
- 预期并发用户: 10,000+
- 预期QPS: 1,000+
- 数据保留期: 永久保留用户数据，积分流水保留2年

### 扩展计划
- 积分过期策略 (可选)
- 积分兑换代币功能
- NFT激励系统
- 战队战斗系统

---

**版权所有 © 2025 RWA Launchpad Team**
