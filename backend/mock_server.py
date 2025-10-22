#!/usr/bin/env python3
"""
简化的Mock API服务器
用于测试前端功能，无需数据库
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uvicorn
import random
import string

app = FastAPI(title="RWA Referral Mock API")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class GenerateLinkRequest(BaseModel):
    address: str

# 生成随机邀请码
def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.get("/")
async def root():
    return {"message": "RWA Referral Mock API Server", "status": "running"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/v1/referral/generate-link")
async def generate_referral_link(request: GenerateLinkRequest):
    """生成推荐链接"""
    invite_code = generate_invite_code()
    return {
        "referral_link": f"http://localhost:5173/?ref={invite_code}",
        "invite_code": invite_code,
        "referrer_address": request.address
    }

@app.get("/api/v1/referral/user/{address}")
async def get_user_info(address: str):
    """获取用户信息（Mock数据）"""
    return {
        "address": address,
        "referrer": "0x0000000000000000000000000000000000000000",
        "reward": "0",
        "referred_count": 0,
        "last_active_timestamp": 0,
        "is_active": False
    }

@app.get("/api/v1/referral/config")
async def get_referral_config():
    """获取推荐配置"""
    return {
        "level_1_bonus_rate": 15,
        "level_2_bonus_rate": 5,
        "decimals": 10000,
        "seconds_until_inactive": 2592000,  # 30 days
        "referral_bonus": 2000  # 20%
    }

@app.get("/api/v1/dashboard/{address}")
async def get_dashboard(address: str):
    """获取仪表板数据（Mock）"""
    invite_code = generate_invite_code()
    return {
        "total_rewards": "0.0000",
        "referred_count": 0,
        "is_active": False,
        "days_since_active": 0,
        "referrer": "0x0000000000000000000000000000000000000000",
        "invite_code": invite_code,
        "referral_link": f"http://localhost:5173/?ref={invite_code}"
    }

@app.get("/api/v1/leaderboard/")
async def get_leaderboard(page: int = 1, page_size: int = 50):
    """获取排行榜（Mock数据）"""
    # 生成Mock排行榜数据
    mock_data = []
    for i in range(1, min(page_size + 1, 21)):
        mock_data.append({
            "rank": i,
            "address": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
            "total_rewards": f"{random.uniform(10, 1000):.4f}",
            "referred_count": random.randint(5, 100)
        })

    return {
        "data": mock_data,
        "total": 100,
        "page": page,
        "page_size": page_size
    }

# ==================== Points System API ====================

@app.get("/api/v1/points/{user_id}")
async def get_user_points(user_id: int):
    """获取用户积分信息"""
    return {
        "id": 1,
        "user_id": user_id,
        "available_points": random.randint(1000, 5000),
        "frozen_points": random.randint(0, 500),
        "total_earned": random.randint(5000, 10000),
        "total_spent": random.randint(1000, 3000),
        "points_from_referral": random.randint(500, 2000),
        "points_from_tasks": random.randint(1000, 3000),
        "points_from_quiz": random.randint(500, 2000),
        "points_from_team": random.randint(300, 1000),
        "points_from_purchase": random.randint(200, 800),
        "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
        "updated_at": datetime.now().isoformat()
    }

@app.get("/api/v1/points/transactions")
async def get_point_transactions(
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    transaction_type: Optional[str] = None
):
    """获取积分流水记录"""
    transaction_types = [
        "referral_reward", "task_complete", "quiz_correct", "team_reward",
        "purchase", "transfer_in", "transfer_out", "spend_item", "admin_adjust"
    ]

    mock_data = []
    for i in range(page_size):
        trans_type = transaction_type if transaction_type else random.choice(transaction_types)
        amount = random.randint(10, 500) if "reward" in trans_type or "in" in trans_type else -random.randint(10, 200)

        mock_data.append({
            "id": i + 1,
            "user_id": user_id,
            "transaction_type": trans_type,
            "amount": amount,
            "balance_after": random.randint(1000, 5000),
            "related_task_id": random.randint(1, 100) if "task" in trans_type else None,
            "related_user_id": random.randint(1, 1000) if "referral" in trans_type else None,
            "related_team_id": random.randint(1, 50) if "team" in trans_type else None,
            "related_question_id": random.randint(1, 200) if "quiz" in trans_type else None,
            "description": f"Mock transaction: {trans_type}",
            "metadata": {},
            "status": "completed",
            "created_at": (datetime.now() - timedelta(hours=i)).isoformat()
        })

    return {
        "data": mock_data,
        "total": 100,
        "page": page,
        "page_size": page_size
    }

@app.get("/api/v1/points/statistics/{user_id}")
async def get_points_statistics(user_id: int):
    """获取积分统计"""
    return {
        "user_id": user_id,
        "total_points": random.randint(3000, 8000),
        "total_earned": random.randint(5000, 10000),
        "total_spent": random.randint(1000, 3000),
        "transactions_count": random.randint(50, 200),
        "daily_earning": random.randint(50, 300),
        "weekly_earning": random.randint(500, 2000),
        "monthly_earning": random.randint(2000, 8000)
    }

# ==================== Teams System API ====================

@app.get("/api/v1/teams/")
async def get_teams(
    page: int = 1,
    page_size: int = 20,
    is_public: Optional[bool] = None
):
    """获取战队列表"""
    mock_data = []
    for i in range(1, min(page_size + 1, 11)):
        mock_data.append({
            "id": i,
            "captain_id": random.randint(1, 1000),
            "name": f"战队 {i}",
            "description": f"这是一个优秀的战队 {i}",
            "logo_url": f"https://picsum.photos/seed/{i}/200",
            "is_public": True if is_public is None else is_public,
            "require_approval": random.choice([True, False]),
            "max_members": 50,
            "member_count": random.randint(10, 50),
            "total_points": random.randint(10000, 100000),
            "active_member_count": random.randint(5, 30),
            "level": random.randint(1, 10),
            "experience": random.randint(0, 10000),
            "reward_pool": random.randint(1000, 10000),
            "last_distribution_at": datetime.now().isoformat() if random.choice([True, False]) else None,
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "disbanded_at": None
        })

    return {
        "total": 50,
        "page": page,
        "page_size": page_size,
        "data": mock_data
    }

@app.get("/api/v1/teams/{team_id}")
async def get_team(team_id: int):
    """获取战队详情"""
    return {
        "id": team_id,
        "captain_id": random.randint(1, 1000),
        "name": f"战队 {team_id}",
        "description": f"这是一个优秀的战队 {team_id}",
        "logo_url": f"https://picsum.photos/seed/{team_id}/200",
        "is_public": True,
        "require_approval": False,
        "max_members": 50,
        "member_count": random.randint(10, 50),
        "total_points": random.randint(10000, 100000),
        "active_member_count": random.randint(5, 30),
        "level": random.randint(1, 10),
        "experience": random.randint(0, 10000),
        "reward_pool": random.randint(1000, 10000),
        "last_distribution_at": datetime.now().isoformat(),
        "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
        "updated_at": datetime.now().isoformat(),
        "disbanded_at": None
    }

@app.get("/api/v1/teams/{team_id}/members")
async def get_team_members(team_id: int, status: Optional[str] = None):
    """获取战队成员列表"""
    roles = ["captain", "admin", "member"]
    statuses = ["active", "pending", "left"]

    mock_data = []
    for i in range(random.randint(5, 15)):
        member_status = status if status else random.choice(statuses)
        mock_data.append({
            "id": i + 1,
            "team_id": team_id,
            "user_id": random.randint(1, 1000),
            "role": roles[0] if i == 0 else random.choice(roles[1:]),
            "contribution_points": random.randint(100, 5000),
            "tasks_completed": random.randint(5, 50),
            "status": member_status,
            "joined_at": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            "approved_at": (datetime.now() - timedelta(days=random.randint(0, 90))).isoformat() if member_status == "active" else None,
            "left_at": None,
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            "username": f"用户{random.randint(1, 9999)}",
            "wallet_address": f"0x{''.join(random.choices('0123456789abcdef', k=40))}",
            "avatar_url": f"https://i.pravatar.cc/150?img={random.randint(1, 70)}"
        })

    return {
        "total": len(mock_data),
        "data": mock_data
    }

@app.get("/api/v1/teams/{team_id}/tasks")
async def get_team_tasks(team_id: int, status: Optional[str] = None):
    """获取战队任务列表"""
    task_types = ["daily", "weekly", "special"]
    task_statuses = ["not_started", "in_progress", "completed", "expired"]

    mock_data = []
    for i in range(random.randint(3, 10)):
        task_status = status if status else random.choice(task_statuses)
        target = random.randint(100, 1000)
        current = random.randint(0, target) if task_status != "not_started" else 0

        mock_data.append({
            "id": i + 1,
            "team_id": team_id,
            "title": f"战队任务 {i + 1}",
            "description": f"完成战队目标任务 {i + 1}",
            "task_type": random.choice(task_types),
            "target_value": target,
            "current_value": current,
            "progress_percentage": round((current / target) * 100, 2),
            "reward_points": random.randint(500, 5000),
            "bonus_points": random.randint(100, 1000),
            "is_completed": task_status == "completed",
            "status": task_status,
            "start_time": (datetime.now() - timedelta(days=7)).isoformat(),
            "end_time": (datetime.now() + timedelta(days=7)).isoformat(),
            "completed_at": datetime.now().isoformat() if task_status == "completed" else None,
            "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "updated_at": datetime.now().isoformat()
        })

    return {
        "total": len(mock_data),
        "data": mock_data
    }

# ==================== Tasks System API ====================

@app.get("/api/v1/tasks/user-tasks/user/{user_id}")
async def get_user_tasks(
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    task_type: Optional[str] = None
):
    """获取用户任务列表"""
    task_types = ["daily", "weekly", "once", "special"]
    task_statuses = ["in_progress", "completed", "claimed", "expired"]

    mock_data = []
    for i in range(min(page_size, 10)):
        task_status = status if status else random.choice(task_statuses)
        task_t = task_type if task_type else random.choice(task_types)
        target = random.randint(10, 100)
        current = random.randint(0, target)

        mock_data.append({
            "id": i + 1,
            "user_id": user_id,
            "task_id": random.randint(1, 50),
            "current_value": current,
            "target_value": target,
            "status": task_status,
            "reward_points": random.randint(50, 500),
            "bonus_points": random.randint(10, 100),
            "is_claimed": task_status == "claimed",
            "progress_percentage": round((current / target) * 100, 2),
            "is_completed": task_status in ["completed", "claimed"],
            "started_at": (datetime.now() - timedelta(days=random.randint(1, 7))).isoformat(),
            "completed_at": datetime.now().isoformat() if task_status in ["completed", "claimed"] else None,
            "claimed_at": datetime.now().isoformat() if task_status == "claimed" else None,
            "expires_at": (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat(),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 10))).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "task_metadata": None,
            "task_title": f"任务 {i + 1}",
            "task_description": f"完成任务目标 {i + 1}",
            "task_icon_url": f"https://picsum.photos/seed/{i}/64",
            "task_type": task_t
        })

    return {
        "total": 50,
        "page": page,
        "page_size": page_size,
        "data": mock_data
    }

@app.get("/api/v1/tasks/user-tasks/user/{user_id}/summary")
async def get_user_task_summary(user_id: int):
    """获取用户任务汇总"""
    total = random.randint(20, 50)
    in_progress = random.randint(5, 15)
    completed = random.randint(5, 15)
    claimed = random.randint(3, 10)
    expired = random.randint(0, 5)

    return {
        "user_id": user_id,
        "total_tasks": total,
        "in_progress_tasks": in_progress,
        "completed_tasks": completed,
        "claimed_tasks": claimed,
        "expired_tasks": expired,
        "total_points_earned": random.randint(1000, 10000),
        "total_experience_earned": random.randint(500, 5000)
    }

@app.post("/api/v1/tasks/user-tasks/{user_task_id}/claim")
async def claim_task_reward(user_task_id: int, user_id: int):
    """领取任务奖励"""
    return {
        "message": "奖励领取成功",
        "user_task_id": user_task_id,
        "user_id": user_id,
        "points_earned": random.randint(50, 500),
        "experience_earned": random.randint(20, 200)
    }

# ==================== Quiz System API ====================

@app.get("/api/v1/quiz/random")
async def get_random_question(user_id: int, difficulty: Optional[str] = None, category: Optional[str] = None):
    """获取随机题目"""
    difficulties = ["easy", "medium", "hard"]
    categories = ["区块链基础", "DeFi知识", "NFT艺术", "智能合约", "Web3技术"]

    diff = difficulty if difficulty else random.choice(difficulties)
    cat = category if category else random.choice(categories)

    options = ["A", "B", "C", "D"]
    correct = random.choice(options)

    return {
        "id": random.randint(1, 1000),
        "question_text": f"这是一道关于{cat}的{diff}难度题目？",
        "option_a": "选项 A - 答案描述",
        "option_b": "选项 B - 答案描述",
        "option_c": "选项 C - 答案描述",
        "option_d": "选项 D - 答案描述",
        "difficulty": diff,
        "category": cat,
        "tags": [cat, diff],
        "reward_points": 10 if diff == "easy" else 20 if diff == "medium" else 30,
        "hint": "这是一个提示信息",
        "explanation": f"正确答案是 {correct}，因为...",
        "source": "manual",
        "source_url": None,
        "times_answered": random.randint(10, 1000),
        "times_correct": random.randint(5, 500),
        "accuracy_rate": round(random.uniform(30, 90), 2),
        "average_answer_time": random.randint(10, 60),
        "status": "active",
        "is_active": True,
        "is_featured": random.choice([True, False]),
        "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
        "updated_at": datetime.now().isoformat()
    }

@app.post("/api/v1/quiz/submit")
async def submit_answer(user_id: int, request: dict):
    """提交答案"""
    is_correct = random.choice([True, False, True])  # 66% 正确率
    correct_answer = random.choice(["A", "B", "C", "D"])

    return {
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "points_earned": random.randint(10, 30) if is_correct else 0,
        "explanation": f"正确答案是 {correct_answer}。这是解析内容...",
        "streak_updated": is_correct,
        "new_streak": random.randint(1, 30) if is_correct else 0,
        "daily_count": random.randint(1, 5),
        "daily_limit": 5
    }

@app.get("/api/v1/quiz/statistics/user/{user_id}")
async def get_quiz_statistics(user_id: int):
    """获取用户答题统计"""
    total = random.randint(50, 500)
    correct = random.randint(30, int(total * 0.8))

    return {
        "user_id": user_id,
        "total_questions_answered": total,
        "correct_answers": correct,
        "wrong_answers": total - correct,
        "accuracy_rate": round((correct / total) * 100, 2),
        "total_points_earned": random.randint(500, 5000),
        "average_answer_time": random.randint(15, 45),
        "current_streak_days": random.randint(0, 30),
        "max_streak_days": random.randint(5, 60),
        "last_answer_date": datetime.now().isoformat(),
        "easy_answered": random.randint(20, 200),
        "easy_correct": random.randint(15, 180),
        "medium_answered": random.randint(15, 180),
        "medium_correct": random.randint(10, 140),
        "hard_answered": random.randint(10, 120),
        "hard_correct": random.randint(5, 80),
        "favorite_category": random.choice(["区块链基础", "DeFi知识", "NFT艺术"])
    }

@app.get("/api/v1/quiz/user-answers/user/{user_id}")
async def get_user_answers(
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    is_correct: Optional[bool] = None,
    difficulty: Optional[str] = None
):
    """获取用户答题记录"""
    difficulties = ["easy", "medium", "hard"]
    categories = ["区块链基础", "DeFi知识", "NFT艺术", "智能合约", "Web3技术"]

    mock_data = []
    for i in range(min(page_size, 15)):
        diff = difficulty if difficulty else random.choice(difficulties)
        correct = is_correct if is_correct is not None else random.choice([True, False, True])
        user_ans = random.choice(["A", "B", "C", "D"])
        correct_ans = user_ans if correct else random.choice([a for a in ["A", "B", "C", "D"] if a != user_ans])

        mock_data.append({
            "id": i + 1,
            "user_id": user_id,
            "question_id": random.randint(1, 1000),
            "user_answer": user_ans,
            "is_correct": correct,
            "points_earned": random.randint(10, 30) if correct else 0,
            "answer_time": random.randint(5, 60),
            "answered_at": (datetime.now() - timedelta(hours=i)).isoformat(),
            "question_text": f"这是一道关于{random.choice(categories)}的题目？",
            "difficulty": diff,
            "category": random.choice(categories),
            "correct_answer": correct_ans
        })

    return {
        "total": 100,
        "page": page,
        "page_size": page_size,
        "data": mock_data
    }

@app.get("/api/v1/quiz/daily-limit")
async def check_daily_limit(user_id: int):
    """检查每日答题限制"""
    today_count = random.randint(0, 5)
    return {
        "user_id": user_id,
        "daily_limit": 5,
        "today_count": today_count,
        "remaining_count": max(0, 5 - today_count),
        "can_answer": today_count < 5,
        "next_reset_time": (datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)).isoformat()
    }

@app.get("/api/v1/quiz/daily-session")
async def get_daily_session(user_id: int):
    """获取每日答题会话"""
    return {
        "user_id": user_id,
        "date": datetime.now().date().isoformat(),
        "questions_answered": random.randint(0, 5),
        "questions_correct": random.randint(0, 4),
        "points_earned": random.randint(0, 150),
        "session_active": True
    }

if __name__ == "__main__":
    print("🚀 启动Mock API服务器...")
    print("📍 URL: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    print("\n⚠️  注意: 这是Mock服务器，数据不会持久化\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
