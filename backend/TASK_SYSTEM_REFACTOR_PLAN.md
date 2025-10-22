# 任务系统重构计划

## 🎯 核心问题

当前任务系统存在以下问题：

1. **状态不清晰**：
   - `COMPLETED` 表示"已完成待领奖"还是"已完成已领奖"？
   - 缺少明确的"未开始"状态

2. **可重复任务逻辑混乱**：
   - 每次邀请创建新的UserTask实例
   - 导致任务列表有大量重复记录
   - 用户看到多个"邀请好友"任务，不符合直觉

3. **前端展示不直观**：
   - 缺少Tab分类（可领取/进行中/已完成）
   - 状态指示不明确
   - 缺少视觉反馈

## 📋 重构方案

### 方案A：保持现有模型，优化逻辑（推荐）

**核心思路**：
- 保持现有的 `IN_PROGRESS`/`COMPLETED`/`CLAIMED` 状态
- 添加 `completion_count` 字段记录重复完成次数
- **可重复任务只保留一个UserTask实例**
- 每次完成后：领取奖励 → 重置进度 → 状态回到 IN_PROGRESS

**状态流转**：
```
一次性任务：
IN_PROGRESS → COMPLETED → CLAIMED（终止）

可重复任务：
IN_PROGRESS → COMPLETED → CLAIMED → IN_PROGRESS（循环）
                                    ↓
                            completion_count++
```

**数据模型变更**：
```python
class UserTask(Base):
    # ... 现有字段 ...

    # 新增字段
    completion_count = Column(Integer, default=0)  # 已完成次数

    # 状态保持不变
    status: IN_PROGRESS | COMPLETED | CLAIMED | EXPIRED
```

**前端Tab分类**：
```typescript
interface TaskTabs {
  available: Task[]      // status=IN_PROGRESS && progress < target
  can_claim: Task[]      // status=COMPLETED
  completed: Task[]      // status=CLAIMED（只显示最近的，或可重复任务显示次数）
}
```

**优点**：
✅ 最小改动，不需要数据库迁移
✅ 每个任务只有一条记录，UI清晰
✅ 符合用户直觉（邀请任务只显示一次）

**缺点**：
❌ 状态流转稍微复杂（CLAIMED需要重置）

---

### 方案B：新增状态，彻底重构

**核心思路**：
- 新增 `AVAILABLE`（可领取）和 `REWARDED`（已领奖）状态
- 彻底分离"完成"和"领奖"两个概念

**状态流转**：
```
AVAILABLE → IN_PROGRESS → COMPLETED → REWARDED
```

**数据模型变更**：
```python
class UserTaskStatus(str, enum.Enum):
    AVAILABLE = "available"        # 未开始（可领取）
    IN_PROGRESS = "in_progress"    # 进行中
    COMPLETED = "completed"        # 已完成（待领奖）
    REWARDED = "rewarded"          # 已领奖
    EXPIRED = "expired"            # 已过期
```

**优点**：
✅ 状态语义清晰
✅ 与业界标准对齐（Galxe/Layer3）

**缺点**：
❌ 需要数据库迁移（ALTER TYPE ENUM）
❌ 需要更新所有相关代码
❌ 改动较大，风险较高

---

## 🎨 前端UI优化（两个方案通用）

### 1. Tab分类设计

```tsx
<Tabs defaultValue="can_claim">
  <Tab value="can_claim" badge={canClaimCount}>
    待领取 🎁
  </Tab>
  <Tab value="in_progress" badge={inProgressCount}>
    进行中 ⏳
  </Tab>
  <Tab value="completed" badge={completedCount}>
    已完成 ✅
  </Tab>
</Tabs>
```

### 2. 任务卡片设计

```tsx
<TaskCard className={`status-${task.status}`}>
  {/* 状态标签 */}
  <Badge variant={getStatusVariant(task.status)}>
    {task.status === 'completed' && '待领取'}
    {task.status === 'in_progress' && '进行中'}
    {task.status === 'claimed' && '已完成'}
  </Badge>

  {/* 任务信息 */}
  <div className="task-info">
    <h3>{task.title}</h3>
    <p>{task.description}</p>

    {/* 可重复任务显示完成次数 */}
    {task.is_repeatable && (
      <span className="completion-count">
        已完成 {task.completion_count} 次
      </span>
    )}
  </div>

  {/* 进度条 */}
  {task.status === 'in_progress' && (
    <Progress value={task.progress} max={task.target} />
  )}

  {/* 奖励展示 */}
  <div className="reward">
    💰 {task.reward_points} 积分
  </div>

  {/* 行动按钮 */}
  {task.status === 'completed' && (
    <Button variant="success" onClick={handleClaim}>
      领取奖励
    </Button>
  )}
  {task.status === 'in_progress' && (
    <span className="progress-text">
      {task.progress}/{task.target}
    </span>
  )}
</TaskCard>
```

### 3. 领取动画

```tsx
const handleClaim = async (taskId) => {
  try {
    await claimReward(taskId);

    // 🎉 庆祝动画
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });

    // 💰 积分飞入动画
    animatePoints(task.reward_points);

    // 📢 通知
    toast.success(`恭喜获得 ${task.reward_points} 积分！`);

  } catch (error) {
    toast.error('领取失败，请重试');
  }
};
```

---

## ⚡ 实施计划

### 推荐：采用方案A（最小改动）

**步骤1：数据库迁移**
- [x] 添加 `completion_count` 列
- [ ] 合并重复的 UserTask 实例（邀请任务）

**步骤2：后端代码更新**
- [ ] 修改邀请逻辑：不创建新实例，更新现有实例
- [ ] 实现领取后重置逻辑（可重复任务）
- [ ] 更新TaskService的方法

**步骤3：前端UI重构**
- [ ] 添加Tab分类组件
- [ ] 优化TaskCard组件
- [ ] 添加领取动画和反馈
- [ ] 更新API类型定义

**步骤4：测试验证**
- [ ] 测试注册任务（一次性）
- [ ] 测试邀请任务（可重复）
- [ ] 测试加入战队任务
- [ ] E2E测试完整流程

**预计时间：** 2-3小时

---

## 🤔 决策

请选择方案：

- [ ] **方案A**：保持现有模型，最小改动（推荐）
- [ ] **方案B**：彻底重构状态系统

或者您有其他建议？
