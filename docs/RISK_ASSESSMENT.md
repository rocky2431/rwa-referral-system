# 风险评估报告

**项目**: RWA社交裂变游戏化平台 v2.0
**评估日期**: 2025-10-21
**评估人**: Ultra Project Builder Agent
**风险等级定义**: 🔴 高 | 🟡 中 | 🟢 低

---

## 📊 风险总览

| 风险类别 | 高风险 | 中风险 | 低风险 | 总计 |
|---------|-------|-------|-------|------|
| 技术风险 | 2 | 3 | 2 | 7 |
| 业务风险 | 1 | 2 | 1 | 4 |
| 安全风险 | 2 | 2 | 1 | 5 |
| 性能风险 | 0 | 2 | 2 | 4 |
| **总计** | **5** | **9** | **6** | **20** |

---

## 🔴 高风险项 (P1 - 必须立即处理)

### 技术风险

#### R-T-001: 推荐关系与战队成员的强绑定约束

**风险描述**:
- 用户需求："战队成员必须有推荐关系"
- 挑战：如何验证战队内所有成员都在同一个推荐树上？
- 问题场景：
  - 用户A推荐B、C
  - 用户D推荐E、F
  - B想创建战队并邀请C、E加入 ❌ E没有推荐关系

**影响**:
- 可能导致战队功能无法正常使用
- 用户体验受限
- 需要复杂的推荐树算法

**概率**: 90% (必然发生)

**缓解方案**:
```sql
-- 方案1: 放宽约束 (推荐)
-- 允许加入战队，但仅同推荐树成员可参与战队任务

-- 方案2: 严格验证
CREATE FUNCTION check_referral_tree_match(
    p_user_id BIGINT,
    p_team_captain_id BIGINT
) RETURNS BOOLEAN AS $$
DECLARE
    v_user_root BIGINT;
    v_captain_root BIGINT;
BEGIN
    -- 找到用户的推荐树根节点
    v_user_root := get_referral_root(p_user_id);
    v_captain_root := get_referral_root(p_team_captain_id);

    RETURN v_user_root = v_captain_root;
END;
$$ LANGUAGE plpgsql;

-- 方案3: 混合方案 (最终建议)
-- 战队分为"核心团队"和"普通成员"
-- 核心团队：必须有推荐关系，享受战队奖励池分配
-- 普通成员：无推荐关系要求，仅可参与战队活动，无奖励
```

**建议**: 采用**方案3混合方案**，既满足业务需求，又保证灵活性

---

#### R-T-002: Python 3.13兼容性问题

**风险描述**:
- 当前系统使用Python 3.13
- pydantic-core、psycopg2等核心库无法编译
- 数据库功能受阻

**影响**:
- 无法使用真实数据库
- Mock服务器不支持复杂游戏化系统

**概率**: 100% (已发生)

**缓解方案**:
```bash
# 方案1: 降级Python (推荐)
conda create -n rwa python=3.11
conda activate rwa
pip install -r backend/requirements.txt

# 方案2: Docker容器化
docker-compose up -d postgres redis
docker-compose up backend

# 方案3: 等待依赖更新 (不可行)
```

**建议**: 立即采用**方案1**，使用Python 3.11稳定环境

---

### 业务风险

#### R-B-001: 积分系统作弊风险

**风险描述**:
- 积分链下存储，缺乏区块链不可篡改特性
- 可能被恶意用户攻击：
  - 重放攻击 (重复领取任务奖励)
  - SQL注入 (篡改积分数据)
  - API重放 (重复答题)

**影响**:
- 积分系统信任度降低
- 经济模型崩溃
- 用户流失

**概率**: 70%

**缓解方案**:
```python
# 1. 幂等性设计
@router.post("/tasks/claim")
async def claim_task_reward(
    task_id: int,
    user_id: int,
    idempotency_key: str,  # 客户端生成唯一ID
    db: AsyncSession
):
    # 检查是否已处理
    existing = await db.execute(
        select(PointTransaction).where(
            PointTransaction.user_id == user_id,
            PointTransaction.metadata['idempotency_key'] == idempotency_key
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_claimed"}

    # 处理奖励...

# 2. 分布式锁
from redis import Redis
redis_client = Redis()

async with redis_client.lock(f"task:claim:{user_id}:{task_id}", timeout=5):
    # 处理任务奖励

# 3. 数据库事务+乐观锁
UPDATE user_points
SET available_points = available_points + 100,
    version = version + 1
WHERE user_id = 123 AND version = 5;  -- 乐观锁

# 4. 审计日志
-- 所有积分变动必须记录在 point_transactions
-- 定期审计异常积分增长
```

**建议**:
- ✅ 所有积分操作使用幂等性Key
- ✅ 关键操作添加分布式锁
- ✅ 定时审计异常数据

---

### 安全风险

#### R-S-001: 推荐奖励分配算法漏洞

**风险描述**:
- 战队加入影响推荐奖励分配
- 复杂的分配逻辑可能导致：
  - 奖励重复发放
  - 奖励计算错误
  - 奖励池余额不足

**影响**:
- 资金损失
- 用户信任危机

**概率**: 60%

**缓解方案**:
```python
# 严格的奖励分配算法
async def distribute_referral_reward(
    purchase_amount: Decimal,
    buyer_id: int,
    db: AsyncSession
) -> Dict[str, Any]:
    \"\"\"
    分配推荐奖励

    规则：
    1. 如果买家在战队中，奖励进入战队奖励池
    2. 否则，按传统方式发放给推荐人
    \"\"\"
    # 1. 获取买家信息
    buyer = await get_user(buyer_id, db)

    # 2. 检查是否在战队
    team_member = await db.execute(
        select(TeamMember).where(
            TeamMember.user_id == buyer_id,
            TeamMember.status == 'active'
        )
    )
    team_member = team_member.scalar_one_or_none()

    # 3. 计算奖励积分
    total_points = int(purchase_amount * 200)  # 假设比例

    if team_member:
        # 战队模式：奖励进入战队池
        await add_team_reward_pool(
            team_id=team_member.team_id,
            points=total_points,
            source_user_id=buyer_id,
            db=db
        )
        return {"mode": "team", "points": total_points}
    else:
        # 个人模式：发放给推荐人
        referral = await get_referral_relation(buyer_id, db)
        if not referral:
            return {"mode": "none"}

        # 一级推荐: 150积分
        await add_user_points(
            user_id=referral.referrer_id,
            points=150,
            transaction_type="referral_l1",
            related_user_id=buyer_id,
            db=db
        )

        # 二级推荐: 50积分
        referral_l2 = await get_referral_relation(referral.referrer_id, db)
        if referral_l2:
            await add_user_points(
                user_id=referral_l2.referrer_id,
                points=50,
                transaction_type="referral_l2",
                related_user_id=buyer_id,
                db=db
            )

        return {"mode": "individual", "l1": 150, "l2": 50}
```

**建议**:
- ✅ 编写完整单元测试覆盖所有场景
- ✅ 添加奖励分配日志
- ✅ 实现奖励撤销机制

---

#### R-S-002: 战队奖励池分配不公平

**风险描述**:
- 战队奖励池如何分配？按贡献？平均分配？
- 可能导致：
  - "摸鱼"成员占便宜
  - 核心成员流失
  - 战队解散

**影响**:
- 战队功能失效
- 用户体验下降

**概率**: 80%

**缓解方案**:
```python
# 贡献值计算算法
def calculate_member_contribution(member: TeamMember) -> int:
    \"\"\"
    计算成员贡献值

    贡献值 = 任务完成数 * 10 + 购买金额(BNB) * 100 + 邀请人数 * 50
    \"\"\"
    contribution = 0

    # 1. 任务贡献
    contribution += member.tasks_completed * 10

    # 2. 购买贡献 (从积分流水统计)
    contribution += member.purchase_contribution * 100

    # 3. 邀请贡献
    contribution += member.invite_contribution * 50

    return contribution

# 奖励池分配算法
async def distribute_team_reward_pool(team_id: int, db: AsyncSession):
    \"\"\"
    每天02:00定时执行
    \"\"\"
    # 1. 获取战队信息
    team = await get_team(team_id, db)
    if team.reward_pool == 0:
        return

    # 2. 获取所有活跃成员
    members = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.status == 'active'
        )
    )
    members = members.scalars().all()

    # 3. 计算总贡献值
    total_contribution = sum(
        calculate_member_contribution(m) for m in members
    )

    if total_contribution == 0:
        return  # 无人有贡献，不分配

    # 4. 按比例分配
    for member in members:
        member_contribution = calculate_member_contribution(member)
        member_share = (member_contribution / total_contribution) * team.reward_pool

        await add_user_points(
            user_id=member.user_id,
            points=int(member_share),
            transaction_type="team_reward",
            related_team_id=team_id,
            db=db
        )

    # 5. 清空奖励池
    team.reward_pool = 0
    team.last_distribution_at = datetime.now()
    await db.commit()
```

**建议**:
- ✅ 使用加权贡献值算法
- ✅ 每日自动分配奖励池
- ✅ 提供贡献值明细查询

---

## 🟡 中风险项 (P2 - 优先处理)

### 技术风险

#### R-T-003: 数据库查询性能

**风险描述**:
- 排行榜查询需要全表扫描
- 用户任务进度查询可能很慢
- 积分流水表快速增长

**影响**:
- API响应慢 (>2s)
- 用户体验差

**概率**: 70%

**缓解方案**:
```sql
-- 1. 物化视图 (已在Schema中设计)
CREATE MATERIALIZED VIEW leaderboard_points AS ...
REFRESH MATERIALIZED VIEW CONCURRENTLY leaderboard_points;

-- 2. Redis缓存排行榜
ZADD leaderboard:points 15000 user:123
ZREVRANGE leaderboard:points 0 99 WITHSCORES  -- Top 100

-- 3. 表分区
CREATE TABLE point_transactions_2025_10 PARTITION OF point_transactions
FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

-- 4. 只读副本
-- 查询请求分流到从库
```

**建议**:
- ✅ 使用Redis缓存排行榜
- ✅ 积分流水表按月分区
- ⏳ 后期考虑读写分离

---

#### R-T-004: 定时任务刷新机制

**风险描述**:
- 每日00:00需要刷新所有用户的每日任务
- 高并发可能导致数据库压力

**影响**:
- 数据库崩溃
- 任务刷新失败

**概率**: 50%

**缓解方案**:
```python
# 分批刷新 + 消息队列
from celery import Celery

@celery.task
async def refresh_daily_tasks_batch(user_ids: List[int]):
    \"\"\"批量刷新用户每日任务\"\"\"
    async with get_db_session() as db:
        for user_id in user_ids:
            await create_daily_tasks_for_user(user_id, db)

# 主任务：分批调度
@celery.task
async def refresh_all_daily_tasks():
    \"\"\"00:00触发\"\"\"
    # 1. 获取所有活跃用户ID
    user_ids = await get_all_active_user_ids()

    # 2. 分批处理 (每批1000人)
    batch_size = 1000
    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i+batch_size]
        refresh_daily_tasks_batch.delay(batch)  # 异步执行
```

**建议**:
- ✅ 使用Celery异步任务
- ✅ 分批刷新 (1000人/批)
- ✅ 添加重试机制

---

#### R-T-005: 链上数据同步延迟

**风险描述**:
- 推荐关系存储在链上
- 每10分钟同步一次可能不及时
- 用户刚绑定推荐人，立即加入战队可能失败

**影响**:
- 用户体验不佳
- 功能不连贯

**概率**: 60%

**缓解方案**:
```python
# 方案1: Websocket实时监听
from web3 import Web3
from web3.middleware import geth_poa_middleware

w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# 监听事件
event_filter = contract.events.RegisteredReferrer.createFilter(fromBlock='latest')

async def listen_referral_events():
    while True:
        for event in event_filter.get_new_entries():
            # 实时同步到数据库
            await sync_referral_to_db(
                referee=event['args']['referee'],
                referrer=event['args']['referrer'],
                tx_hash=event['transactionHash'].hex()
            )
        await asyncio.sleep(2)  # 每2秒检查一次

# 方案2: 用户触发主动同步
@router.post("/sync/referral")
async def sync_my_referral(user_id: int, db: AsyncSession):
    \"\"\"用户手动同步推荐关系\"\"\"
    # 从链上读取
    referrer = await contract.functions.accounts(user_address).call()
    # 同步到数据库
    await upsert_referral_relation(user_id, referrer, db)
```

**建议**:
- ✅ 实现Websocket事件监听
- ✅ 提供手动同步接口

---

### 业务风险

#### R-B-002: 答题系统题库质量

**风险描述**:
- 用户提交题目可能质量低、有错误
- 审核不及时导致错题上线

**影响**:
- 用户答对却被判错
- 积分系统混乱

**概率**: 60%

**缓解方案**:
```python
# 1. 多人审核机制
async def approve_question(question_id: int, reviewer_id: int, db: AsyncSession):
    \"\"\"题目审核\"\"\"
    question = await get_question(question_id, db)

    # 需要至少2个管理员审核通过
    approvals = await db.execute(
        select(QuestionApproval).where(
            QuestionApproval.question_id == question_id,
            QuestionApproval.status == 'approved'
        )
    )

    if approvals.count() >= 2:
        question.status = 'approved'
        await db.commit()

# 2. 题目质量评分
async def calculate_question_quality(question_id: int, db: AsyncSession) -> float:
    \"\"\"根据答题数据评估题目质量\"\"\"
    stats = await db.execute(
        select(
            func.count(UserAnswer.id).label('total'),
            func.sum(case((UserAnswer.is_correct == True, 1), else_=0)).label('correct')
        ).where(UserAnswer.question_id == question_id)
    )
    stats = stats.one()

    # 正确率过高(>90%)或过低(<10%)的题目可能有问题
    accuracy = stats.correct / stats.total if stats.total > 0 else 0

    if accuracy > 0.9 or accuracy < 0.1:
        # 标记为需要复审
        pass

    return accuracy

# 3. 题目举报机制
async def report_question(question_id: int, user_id: int, reason: str, db: AsyncSession):
    \"\"\"用户举报错题\"\"\"
    # 记录举报
    # 超过10个举报自动下线题目
```

**建议**:
- ✅ 实现多人审核机制
- ✅ 定期分析题目质量
- ✅ 提供举报功能

---

#### R-B-003: 战队解散处理

**风险描述**:
- 战队队长退出怎么办？
- 战队成员全部离开怎么办？
- 奖励池积分如何处理？

**影响**:
- 积分损失
- 用户纠纷

**概率**: 40%

**缓解方案**:
```python
# 战队解散策略
async def handle_team_dissolution(team_id: int, db: AsyncSession):
    \"\"\"
    战队解散逻辑

    触发条件：
    1. 队长主动解散
    2. 成员数 < 3持续7天
    3. 所有成员离开
    \"\"\"
    team = await get_team(team_id, db)

    # 1. 分配剩余奖励池
    if team.reward_pool > 0:
        await distribute_team_reward_pool(team_id, db)

    # 2. 标记所有成员为left
    await db.execute(
        update(TeamMember)
        .where(TeamMember.team_id == team_id)
        .values(status='left', left_at=datetime.now())
    )

    # 3. 归档战队数据 (不删除，保留历史)
    team.is_active = False
    await db.commit()

    # 4. 发送通知
    await notify_team_members(team_id, "战队已解散，奖励池已分配")
```

**建议**:
- ✅ 制定完整解散流程
- ✅ 奖励池优先分配
- ✅ 保留历史数据

---

### 性能风险

#### R-P-001: 积分流水表膨胀

**风险描述**:
- `point_transactions`表增长快
- 每个用户每天可能产生10+条记录
- 1万用户 × 10条/天 × 365天 = 3650万条/年

**影响**:
- 查询变慢
- 存储成本增加

**概率**: 90%

**缓解方案**:
```sql
-- 1. 表分区 (已在Schema中)
CREATE TABLE point_transactions (
    id BIGSERIAL,
    ...
) PARTITION BY RANGE (created_at);

-- 2. 定期归档
-- 超过1年的数据迁移到归档表
INSERT INTO point_transactions_archive
SELECT * FROM point_transactions
WHERE created_at < NOW() - INTERVAL '1 year';

DELETE FROM point_transactions
WHERE created_at < NOW() - INTERVAL '1 year';

-- 3. 索引优化
CREATE INDEX idx_point_tx_created_date
ON point_transactions (DATE(created_at));
```

**建议**:
- ✅ 使用表分区
- ✅ 定期归档历史数据
- ⏳ 考虑使用时序数据库

---

## 🟢 低风险项 (P3 - 可延后处理)

### 技术风险

#### R-T-006: 前端状态管理复杂度

**风险**: 新增4大模块，状态管理可能混乱

**缓解**: 使用Zustand集中管理状态

---

#### R-T-007: API版本兼容性

**风险**: 频繁迭代可能导致API不兼容

**缓解**: 使用API版本控制 `/api/v1`, `/api/v2`

---

### 安全风险

#### R-S-003: 用户隐私保护

**风险**: 钱包地址、答题记录等敏感数据泄露

**缓解**: 数据脱敏、HTTPS加密、访问日志

---

### 性能风险

#### R-P-002: 前端资源加载慢

**风险**: 新增页面导致首屏加载慢

**缓解**: 代码分割、懒加载、CDN加速

---

#### R-P-003: WebSocket连接数过多

**风险**: 实时通知导致服务器压力大

**缓解**: 使用Redis Pub/Sub + 长轮询

---

## 📋 风险缓解优先级

### 立即执行 (本周)
1. ✅ R-T-002: 解决Python兼容性 (切换到Python 3.11)
2. ✅ R-T-001: 设计推荐关系与战队的绑定策略
3. ✅ R-B-001: 实现积分系统幂等性设计

### 优先执行 (下周)
4. ✅ R-S-001: 编写推荐奖励分配算法单元测试
5. ✅ R-S-002: 实现战队奖励池分配算法
6. ✅ R-T-004: 配置Celery定时任务框架

### 持续关注
7. 监控数据库查询性能
8. 定期审计积分异常数据
9. 收集用户反馈优化题库

---

## 📊 风险矩阵

```
影响 ↑
高  │ R-T-001  R-B-001  R-S-001
    │ R-T-002  R-S-002
中  │ R-T-003  R-T-004  R-T-005
    │ R-B-002  R-B-003
低  │ R-T-006  R-T-007  R-S-003
    │ R-P-002  R-P-003
    └─────────────────────→ 概率
       低      中      高
```

---

## ✅ 风险管理计划

### 定期评审
- **每周**: 检查P1高风险项进展
- **每两周**: 更新风险清单
- **每月**: 生成风险报告

### 应急预案
- **数据库故障**: 自动切换到只读副本
- **积分异常**: 立即暂停积分发放，回滚交易
- **战队冲突**: 人工介入调解

---

**报告结束**

**下一步行动**: 请查看 [需求文档](./REQUIREMENTS.md) 了解功能详情
