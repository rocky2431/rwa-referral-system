import axios, { AxiosInstance, AxiosError } from 'axios'
import toast from 'react-hot-toast'

// API响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 推荐链接响应
export interface GenerateLinkResponse {
  referral_link: string
  invite_code: string
  referrer_address: string
}

// 用户信息响应
export interface UserInfoResponse {
  address: string
  referrer: string
  reward: string
  referred_count: number
  last_active_timestamp: number
  is_active: boolean
}

// 推荐配置响应
export interface ReferralConfigResponse {
  level_1_bonus_rate: number
  level_2_bonus_rate: number
  decimals: number
  seconds_until_inactive: number
  referral_bonus: number
}

// 仪表板数据响应
export interface DashboardResponse {
  total_rewards: string
  referred_count: number
  is_active: boolean
  days_since_active: number
  referrer: string
  invite_code: string
  referral_link: string
}

// 排行榜条目
export interface LeaderboardEntry {
  rank: number
  address: string
  total_rewards: string
  referred_count: number
}

// 排行榜响应
export interface LeaderboardResponse {
  data: LeaderboardEntry[]
  total: number
  page: number
  page_size: number
}

// ================ 用户管理类型定义 ================

// 用户注册请求
export interface UserRegisterRequest {
  wallet_address: string
  username?: string
  avatar_url?: string
  email?: string
}

// 用户基础响应
export interface UserResponse {
  id: number
  wallet_address: string
  username: string
  avatar_url?: string
  email?: string
  level: number
  experience: number
  total_points: number
  total_invited: number
  total_tasks_completed: number
  total_questions_answered: number
  correct_answers: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// 用户详细响应
export interface UserDetailResponse extends UserResponse {
  last_active_at?: string
  consecutive_login_days: number
  last_login_date?: string
  is_banned: boolean
  banned_until?: string
}

// 钱包地址查询响应
export interface UserByWalletResponse {
  exists: boolean
  user_id?: number
  wallet_address: string
  username?: string
  level?: number
  total_points?: number
}

// 用户信息更新请求
export interface UserUpdateRequest {
  username?: string
  avatar_url?: string
  email?: string
}

// ================ 积分系统类型定义 ================

// 用户积分信息
export interface UserPointsResponse {
  id: number
  user_id: number
  available_points: number
  frozen_points: number
  total_earned: number
  total_spent: number
  points_from_referral: number
  points_from_tasks: number
  points_from_quiz: number
  points_from_team: number
  points_from_purchase: number
  created_at: string
  updated_at: string
}

// 积分流水记录
export interface PointTransactionResponse {
  id: number
  user_id: number
  transaction_type: string
  amount: number
  balance_after: number
  related_task_id?: number
  related_user_id?: number
  related_team_id?: number
  related_question_id?: number
  description?: string
  metadata?: Record<string, any>
  status: string
  created_at: string
}

// 积分历史响应（分页）
export interface PointsHistoryResponse {
  data: PointTransactionResponse[]
  total: number
  page: number
  page_size: number
}

// 积分统计
export interface PointsStatistics {
  user_id: number
  total_points: number
  total_earned: number
  total_spent: number
  transactions_count: number
  daily_earning: number
  weekly_earning: number
  monthly_earning: number
}

// ================ 战队系统类型定义 ================

// 战队成员角色
export enum TeamMemberRole {
  CAPTAIN = 'captain',
  ADMIN = 'admin',
  MEMBER = 'member'
}

// 战队成员状态
export enum TeamMemberStatus {
  PENDING = 'pending',
  ACTIVE = 'active',
  REJECTED = 'rejected',
  LEFT = 'left'
}

// 战队任务状态
export enum TeamTaskStatus {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  EXPIRED = 'expired'
}

// 战队基础信息
export interface TeamResponse {
  id: number
  captain_id: number
  name: string
  description?: string
  logo_url?: string
  is_public: boolean
  require_approval: boolean
  max_members: number
  member_count: number
  total_points: number
  active_member_count: number
  level: number
  experience: number
  reward_pool: number
  last_distribution_at?: string
  created_at: string
  updated_at: string
  disbanded_at?: string
}

// 战队详细信息
export interface TeamDetailResponse extends TeamResponse {
  captain_name?: string
  captain_wallet?: string
}

// 战队列表响应（分页）
export interface TeamListResponse {
  total: number
  page: number
  page_size: number
  data: TeamResponse[]
}

// 创建战队请求
export interface TeamCreateRequest {
  name: string
  description?: string
  logo_url?: string
  is_public?: boolean
  require_approval?: boolean
  max_members?: number
}

// 更新战队请求
export interface TeamUpdateRequest {
  name?: string
  description?: string
  logo_url?: string
  is_public?: boolean
  require_approval?: boolean
  max_members?: number
}

// 战队成员响应
export interface TeamMemberResponse {
  id: number
  team_id: number
  user_id: number
  role: TeamMemberRole
  contribution_points: number
  tasks_completed: number
  status: TeamMemberStatus
  joined_at?: string
  approved_at?: string
  left_at?: string
  created_at: string
}

// 战队成员详细信息
export interface TeamMemberDetailResponse extends TeamMemberResponse {
  username?: string
  wallet_address?: string
  avatar_url?: string
}

// 战队成员列表响应
export interface TeamMemberListResponse {
  total: number
  data: TeamMemberDetailResponse[]
}

// 战队任务响应
export interface TeamTaskResponse {
  id: number
  team_id: number
  title: string
  description?: string
  task_type: string
  target_value: number
  current_value: number
  progress_percentage: number
  reward_points: number
  bonus_points: number
  is_completed: boolean
  status: TeamTaskStatus
  start_time: string
  end_time: string
  completed_at?: string
  created_at: string
  updated_at: string
}

// 战队任务列表响应
export interface TeamTaskListResponse {
  total: number
  data: TeamTaskResponse[]
}

// 战队排行榜项
export interface TeamLeaderboardItem {
  rank: number
  team_id: number
  team_name: string
  team_logo_url?: string
  total_points: number
  member_count: number
  level: number
  captain_name?: string
}

// 战队排行榜响应
export interface TeamLeaderboardResponse {
  total: number
  page: number
  page_size: number
  data: TeamLeaderboardItem[]
}

// 战队统计
export interface TeamStatistics {
  team_id: number
  total_members: number
  active_members: number
  total_points: number
  total_tasks: number
  completed_tasks: number
  reward_pool: number
  average_contribution: number
}

// ================ Quiz 系统类型定义 ================

// 题目难度
export enum QuestionDifficulty {
  EASY = 'easy',
  MEDIUM = 'medium',
  HARD = 'hard'
}

// 题目来源
export enum QuestionSource {
  MANUAL = 'manual',
  IMPORTED = 'imported',
  GENERATED = 'generated'
}

// 题目状态
export enum QuestionStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  ARCHIVED = 'archived'
}

// 题目响应（不含答案）
export interface QuestionResponse {
  id: number
  question_text: string
  option_a: string
  option_b: string
  option_c?: string
  option_d?: string
  difficulty: QuestionDifficulty
  category?: string
  tags?: string[]
  reward_points: number
  hint?: string
  explanation?: string
  source: QuestionSource
  source_url?: string
  times_answered: number
  times_correct: number
  accuracy_rate: number
  average_answer_time?: number
  status: QuestionStatus
  is_active: boolean
  is_featured: boolean
  created_at: string
  updated_at: string
}

// 答案提交请求
export interface AnswerSubmit {
  question_id: number
  user_answer: string
  answer_time?: number
}

// 答题结果响应
export interface AnswerResult {
  is_correct: boolean
  correct_answer: string
  points_earned: number
  explanation?: string
  streak_updated: boolean
  new_streak: number
  daily_count: number
  daily_limit: number
}

// 用户答题记录详细信息
export interface UserAnswerDetailResponse {
  id: number
  user_id: number
  question_id: number
  user_answer: string
  is_correct: boolean
  points_earned: number
  answer_time?: number
  answered_at: string
  question_text?: string
  difficulty?: QuestionDifficulty
  category?: string
  correct_answer?: string
}

// 用户答题统计
export interface QuizStatistics {
  user_id: number
  total_questions_answered: number
  correct_answers: number
  wrong_answers: number
  accuracy_rate: number
  total_points_earned: number
  average_answer_time?: number
  current_streak_days: number
  max_streak_days: number
  last_answer_date?: string
  easy_answered: number
  easy_correct: number
  medium_answered: number
  medium_correct: number
  hard_answered: number
  hard_correct: number
  favorite_category?: string
}

// 答题排行榜项
export interface QuizRankingItem {
  rank: number
  user_id: number
  username?: string
  wallet_address?: string
  avatar_url?: string
  total_correct: number
  accuracy_rate: number
  total_points: number
  current_streak: number
}

// 每日答题会话
export interface DailySession {
  user_id: number
  date: string
  questions_answered: number
  questions_correct: number
  points_earned: number
  session_active: boolean
}

// 每日答题限制检查
export interface DailyLimit {
  user_id: number
  daily_limit: number
  today_count: number
  remaining_count: number
  can_answer: boolean
  next_reset_time: string
}

// 分页题目列表响应
export interface PaginatedQuestionResponse {
  total: number
  page: number
  page_size: number
  data: QuestionResponse[]
}

// 分页答题记录响应
export interface PaginatedUserAnswerResponse {
  total: number
  page: number
  page_size: number
  data: UserAnswerDetailResponse[]
}

// 分页答题排行榜响应
export interface PaginatedQuizRankingResponse {
  total: number
  page: number
  page_size: number
  data: QuizRankingItem[]
}

// ================ 任务系统类型定义 ================

// 任务类型
export enum TaskType {
  DAILY = 'daily',
  WEEKLY = 'weekly',
  ONCE = 'once',
  TEAM = 'team'
}

// 任务触发方式
export enum TaskTrigger {
  MANUAL = 'manual',
  AUTO = 'auto'
}

// 用户任务状态
export enum UserTaskStatus {
  AVAILABLE = 'AVAILABLE',      // 可领取（未开始）
  IN_PROGRESS = 'IN_PROGRESS',  // 进行中
  COMPLETED = 'COMPLETED',      // 已完成（待领奖）
  REWARDED = 'REWARDED',        // 已领奖
  EXPIRED = 'EXPIRED',          // 已过期

  // 兼容旧状态（将被废弃）
  CLAIMED = 'CLAIMED'           // 已领取（映射到REWARDED）
}

// 任务配置响应
export interface TaskResponse {
  id: number
  task_key: string
  title: string
  description?: string
  icon_url?: string
  task_type: TaskType
  trigger_type: TaskTrigger
  target_type?: string
  target_value: number
  reward_points: number
  reward_experience: number
  bonus_multiplier: number
  min_level_required: number
  max_completions_per_user?: number
  priority: number
  sort_order: number
  is_active: boolean
  is_visible: boolean
  start_time?: string
  end_time?: string
  created_at: string
  updated_at: string
}

// 任务列表响应
export interface TaskListResponse {
  total: number
  page: number
  page_size: number
  data: TaskResponse[]
}

// 用户任务响应
export interface UserTaskResponse {
  id: number
  user_id: number
  task_id: number
  current_value: number
  target_value: number
  status: UserTaskStatus
  reward_points: number
  bonus_points: number
  is_claimed: boolean
  completion_count: number      // 完成次数（用于可重复任务）
  progress_percentage: number
  is_completed: boolean
  started_at: string
  completed_at?: string
  claimed_at?: string
  expires_at?: string
  created_at: string
  updated_at: string
  task_metadata?: string
}

// 用户任务详细信息
export interface UserTaskDetailResponse extends UserTaskResponse {
  task_title?: string
  task_description?: string
  task_icon_url?: string
  task_type?: TaskType
}

// 用户任务列表响应
export interface UserTaskListResponse {
  total: number
  page: number
  page_size: number
  data: UserTaskDetailResponse[]
}

// 任务统计
export interface TaskStatisticsResponse {
  task_id: number
  task_key: string
  task_title: string
  task_type: TaskType
  total_participants: number
  total_completed: number
  completion_rate: number
  total_rewards_distributed: number
  average_completion_time?: number
}

// 用户任务汇总
export interface UserTaskSummary {
  user_id: number
  total_tasks: number
  available_tasks: number       // 可领取任务数
  in_progress_tasks: number
  completed_tasks: number
  rewarded_tasks: number        // 已领奖任务数（替代claimed_tasks）
  expired_tasks: number
  total_points_earned: number
  total_experience_earned: number
}

/**
 * API客户端类
 * 封装所有后端API调用
 */
class ApiClient {
  private instance: AxiosInstance

  constructor() {
    // 创建axios实例
    this.instance = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        // 可以在这里添加认证token等
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.instance.interceptors.response.use(
      (response) => {
        return response.data
      },
      (error: AxiosError) => {
        this.handleError(error)
        return Promise.reject(error)
      }
    )
  }

  /**
   * 统一错误处理
   */
  private handleError(error: AxiosError) {
    let message = '请求失败'

    if (error.response) {
      // 服务器返回错误状态码
      const status = error.response.status
      switch (status) {
        case 400:
          message = '请求参数错误'
          break
        case 401:
          message = '未授权，请先登录'
          break
        case 403:
          message = '禁止访问'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        case 502:
          message = '网关错误'
          break
        case 503:
          message = '服务暂时不可用'
          break
        default:
          message = `请求失败 (${status})`
      }

      // 如果有自定义错误消息，优先使用
      const data = error.response.data as any
      if (data?.message) {
        message = data.message
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      message = '网络连接失败，请检查网络'
    } else {
      // 其他错误
      message = error.message || '未知错误'
    }

    toast.error(message)
    console.error('API Error:', error)
  }

  /**
   * 生成推荐链接
   */
  async generateReferralLink(address: string): Promise<GenerateLinkResponse> {
    return this.instance.post('/referral/generate-link', { address })
  }

  /**
   * 获取用户信息
   */
  async getUserInfo(address: string): Promise<UserInfoResponse> {
    return this.instance.get(`/referral/user/${address}`)
  }

  /**
   * 获取推荐系统配置
   */
  async getReferralConfig(): Promise<ReferralConfigResponse> {
    return this.instance.get('/referral/config')
  }

  /**
   * 绑定推荐关系
   */
  async bindReferrer(refereeAddress: string, referrerAddress: string): Promise<{ success: boolean; message: string }> {
    return this.instance.post('/referral/bind-referrer', {
      referee_address: refereeAddress,
      referrer_address: referrerAddress
    })
  }

  /**
   * 通过邀请码查找推荐人
   */
  async resolveInviteCode(inviteCode: string): Promise<{ success: boolean; invite_code: string; referrer_address: string; referrer_username: string }> {
    return this.instance.get(`/referral/resolve-code/${inviteCode}`)
  }

  /**
   * 通过邀请码绑定推荐关系
   */
  async bindReferrerByCode(refereeAddress: string, inviteCode: string): Promise<{ success: boolean; message: string; referee_address: string; referrer_address: string }> {
    return this.instance.post('/referral/bind-referrer-by-code', {
      referee_address: refereeAddress,
      invite_code: inviteCode
    })
  }

  /**
   * 获取仪表板数据
   */
  async getDashboard(address: string): Promise<DashboardResponse> {
    return this.instance.get(`/dashboard/${address}`)
  }

  /**
   * 获取推荐排行榜
   */
  async getLeaderboard(page = 1, pageSize = 50): Promise<LeaderboardResponse> {
    return this.instance.get('/referral/leaderboard', {
      params: { page, page_size: pageSize }
    })
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.instance.get('/health')
  }

  // ================ 用户管理API ================

  /**
   * 通过钱包地址查询用户
   */
  async getUserByWallet(walletAddress: string): Promise<UserByWalletResponse> {
    return this.instance.get(`/users/by-wallet/${walletAddress}`)
  }

  /**
   * 注册新用户
   */
  async registerUser(data: UserRegisterRequest): Promise<UserResponse> {
    return this.instance.post('/users/register', data)
  }

  /**
   * 获取用户详情
   */
  async getUserDetail(userId: number): Promise<UserDetailResponse> {
    return this.instance.get(`/users/${userId}`)
  }

  /**
   * 更新用户信息
   */
  async updateUser(userId: number, data: UserUpdateRequest): Promise<UserResponse> {
    return this.instance.put(`/users/${userId}`, data)
  }

  // ================ 积分系统API ================

  /**
   * 获取用户积分信息
   */
  async getUserPoints(userId: number): Promise<UserPointsResponse> {
    return this.instance.get(`/points/user/${userId}`)
  }

  /**
   * 获取积分流水记录（分页）
   */
  async getPointTransactions(
    userId: number,
    page = 1,
    pageSize = 20,
    transactionType?: string
  ): Promise<PointsHistoryResponse> {
    return this.instance.get(`/points/transactions/${userId}`, {
      params: {
        transaction_type: transactionType,
        page,
        page_size: pageSize
      }
    })
  }

  /**
   * 获取积分统计
   */
  async getPointsStatistics(userId: number): Promise<PointsStatistics> {
    return this.instance.get(`/points/statistics`)
  }

  // ================ 战队系统API ================

  /**
   * 创建战队
   */
  async createTeam(captainId: number, data: TeamCreateRequest): Promise<TeamResponse> {
    return this.instance.post('/teams/', data, {
      params: { captain_id: captainId }
    })
  }

  /**
   * 获取战队详情
   */
  async getTeam(teamId: number): Promise<TeamResponse> {
    return this.instance.get(`/teams/${teamId}`)
  }

  /**
   * 获取用户所在的战队
   */
  async getUserTeam(userId: number): Promise<TeamResponse | null> {
    return this.instance.get(`/teams/user/${userId}/team`)
  }

  /**
   * 获取战队列表（分页）
   */
  async getTeams(
    page = 1,
    pageSize = 20,
    isPublic?: boolean
  ): Promise<TeamListResponse> {
    return this.instance.get('/teams/', {
      params: {
        page,
        page_size: pageSize,
        is_public: isPublic
      }
    })
  }

  /**
   * 更新战队信息
   */
  async updateTeam(
    teamId: number,
    captainId: number,
    data: TeamUpdateRequest
  ): Promise<TeamResponse> {
    return this.instance.put(`/teams/${teamId}`, data, {
      params: { captain_id: captainId }
    })
  }

  /**
   * 解散战队
   */
  async disbandTeam(teamId: number, captainId: number): Promise<{ message: string; team_id: number }> {
    return this.instance.delete(`/teams/${teamId}`, {
      params: { captain_id: captainId }
    })
  }

  /**
   * 加入战队
   */
  async joinTeam(teamId: number, userId: number): Promise<TeamMemberResponse> {
    return this.instance.post('/teams/join', { team_id: teamId }, {
      params: { user_id: userId }
    })
  }

  /**
   * 审批成员申请
   */
  async approveMember(
    teamId: number,
    userId: number,
    approverId: number,
    approved: boolean
  ): Promise<TeamMemberResponse> {
    return this.instance.post(`/teams/${teamId}/approve`,
      { user_id: userId, approved },
      { params: { approver_id: approverId } }
    )
  }

  /**
   * 离开战队
   */
  async leaveTeam(teamId: number, userId: number): Promise<{ message: string; team_id: number; user_id: number }> {
    return this.instance.post(`/teams/${teamId}/leave`, null, {
      params: { user_id: userId }
    })
  }

  /**
   * 获取战队成员列表
   */
  async getTeamMembers(teamId: number, status?: TeamMemberStatus): Promise<TeamMemberListResponse> {
    return this.instance.get(`/teams/${teamId}/members`, {
      params: { status }
    })
  }

  /**
   * 获取战队排行榜
   */
  async getTeamLeaderboard(page = 1, pageSize = 50): Promise<TeamLeaderboardResponse> {
    return this.instance.get('/teams/leaderboard', {
      params: { page, page_size: pageSize }
    })
  }

  /**
   * 获取战队任务列表
   */
  async getTeamTasks(teamId: number, status?: TeamTaskStatus): Promise<TeamTaskListResponse> {
    return this.instance.get(`/teams/${teamId}/tasks`, {
      params: { status }
    })
  }

  /**
   * 分配战队奖励池
   */
  async distributeTeamRewards(teamId: number, captainId: number): Promise<any> {
    return this.instance.post(`/teams/${teamId}/distribute-rewards`, null, {
      params: { captain_id: captainId }
    })
  }

  // ================ 任务系统API ================

  /**
   * 获取任务列表
   */
  async getTasks(
    page = 1,
    pageSize = 20,
    taskType?: TaskType,
    isActive?: boolean,
    isVisible?: boolean
  ): Promise<TaskListResponse> {
    return this.instance.get('/tasks/', {
      params: {
        page,
        page_size: pageSize,
        task_type: taskType,
        is_active: isActive,
        is_visible: isVisible
      }
    })
  }

  /**
   * 获取任务详情
   */
  async getTask(taskId: number): Promise<TaskResponse> {
    return this.instance.get(`/tasks/${taskId}`)
  }

  /**
   * 领取任务
   */
  async assignTaskToUser(userId: number, taskId: number): Promise<UserTaskResponse> {
    return this.instance.post('/tasks/user-tasks', {
      user_id: userId,
      task_id: taskId
    })
  }

  /**
   * 获取用户的任务列表
   */
  async getUserTasks(
    userId: number,
    page = 1,
    pageSize = 20,
    status?: UserTaskStatus,
    taskType?: TaskType
  ): Promise<UserTaskListResponse> {
    return this.instance.get(`/tasks/user-tasks/user/${userId}`, {
      params: {
        page,
        page_size: pageSize,
        status,
        task_type: taskType
      }
    })
  }

  /**
   * 获取用户的特定任务
   */
  async getUserTask(userId: number, taskId: number): Promise<UserTaskResponse> {
    return this.instance.get(`/tasks/user-tasks/${userId}/task/${taskId}`)
  }

  /**
   * 更新任务进度
   */
  async updateTaskProgress(userTaskId: number, progressDelta: number): Promise<UserTaskResponse> {
    return this.instance.put(`/tasks/user-tasks/${userTaskId}/progress`, {
      progress_delta: progressDelta
    })
  }

  /**
   * 领取任务奖励
   */
  async claimTaskReward(userTaskId: number, userId: number): Promise<any> {
    return this.instance.post(`/tasks/user-tasks/${userTaskId}/claim`, null, {
      params: { user_id: userId }
    })
  }

  /**
   * 获取任务统计
   */
  async getTaskStatistics(taskId: number): Promise<TaskStatisticsResponse> {
    return this.instance.get(`/tasks/${taskId}/statistics`)
  }

  /**
   * 获取用户任务汇总
   */
  async getUserTaskSummary(userId: number): Promise<UserTaskSummary> {
    return this.instance.get(`/tasks/user-tasks/user/${userId}/summary`)
  }

  /**
   * 自动分配任务
   */
  async autoAssignTasks(userId: number): Promise<any> {
    return this.instance.post(`/tasks/user-tasks/auto-assign/${userId}`)
  }

  // ================ Quiz 系统API ================

  /**
   * 获取题目列表（分页）
   */
  async getQuestions(
    page = 1,
    pageSize = 20,
    difficulty?: QuestionDifficulty,
    category?: string,
    isActive?: boolean,
    isFeatured?: boolean
  ): Promise<PaginatedQuestionResponse> {
    return this.instance.get('/quiz/questions', {
      params: {
        page,
        page_size: pageSize,
        difficulty,
        category,
        is_active: isActive,
        is_featured: isFeatured
      }
    })
  }

  /**
   * 获取题目详情（不含答案）
   */
  async getQuestion(questionId: number): Promise<QuestionResponse> {
    return this.instance.get(`/quiz/questions/${questionId}`)
  }

  /**
   * 获取随机题目（排除今天已答过的）
   */
  async getRandomQuestion(
    userId: number,
    difficulty?: QuestionDifficulty,
    category?: string
  ): Promise<QuestionResponse> {
    return this.instance.get('/quiz/random', {
      params: {
        user_id: userId,
        difficulty,
        category
      }
    })
  }

  /**
   * 提交答案
   */
  async submitAnswer(userId: number, answer: AnswerSubmit): Promise<AnswerResult> {
    return this.instance.post('/quiz/submit', answer, {
      params: { user_id: userId }
    })
  }

  /**
   * 获取用户答题记录（分页）
   */
  async getUserAnswers(
    userId: number,
    page = 1,
    pageSize = 20,
    isCorrect?: boolean,
    difficulty?: QuestionDifficulty
  ): Promise<PaginatedUserAnswerResponse> {
    return this.instance.get(`/quiz/user-answers/user/${userId}`, {
      params: {
        page,
        page_size: pageSize,
        is_correct: isCorrect,
        difficulty
      }
    })
  }

  /**
   * 获取用户答题统计
   */
  async getQuizStatistics(userId: number): Promise<QuizStatistics> {
    return this.instance.get(`/quiz/statistics/user/${userId}`)
  }

  /**
   * 获取每日答题会话
   */
  async getDailySession(userId: number): Promise<DailySession> {
    return this.instance.get('/quiz/daily-session', {
      params: { user_id: userId }
    })
  }

  /**
   * 检查每日答题限制
   */
  async checkDailyLimit(userId: number): Promise<DailyLimit> {
    return this.instance.get('/quiz/daily-limit', {
      params: { user_id: userId }
    })
  }

  /**
   * 获取答题排行榜
   */
  async getQuizRanking(
    page = 1,
    pageSize = 50,
    orderBy: 'correct' | 'accuracy' | 'points' | 'streak' = 'correct'
  ): Promise<PaginatedQuizRankingResponse> {
    return this.instance.get('/quiz/ranking', {
      params: {
        page,
        page_size: pageSize,
        order_by: orderBy
      }
    })
  }
}

// 导出单例
export const apiClient = new ApiClient()

/**
 * 推荐相关API
 */
export const referralApi = {
  /**
   * 生成推荐链接
   */
  generateLink: (address: string) => apiClient.generateReferralLink(address),

  /**
   * 获取用户信息
   */
  getUserInfo: (address: string) => apiClient.getUserInfo(address),

  /**
   * 获取配置
   */
  getConfig: () => apiClient.getReferralConfig(),

  /**
   * 绑定推荐关系
   */
  bindReferrer: (refereeAddress: string, referrerAddress: string) =>
    apiClient.bindReferrer(refereeAddress, referrerAddress),

  /**
   * 通过邀请码查找推荐人
   */
  resolveInviteCode: (inviteCode: string) => apiClient.resolveInviteCode(inviteCode),

  /**
   * 通过邀请码绑定推荐关系
   */
  bindReferrerByCode: (refereeAddress: string, inviteCode: string) =>
    apiClient.bindReferrerByCode(refereeAddress, inviteCode)
}

/**
 * 仪表板相关API
 */
export const dashboardApi = {
  /**
   * 获取仪表板数据
   */
  getData: (address: string) => apiClient.getDashboard(address)
}

/**
 * 排行榜相关API
 */
export const leaderboardApi = {
  /**
   * 获取排行榜
   */
  getList: (page?: number, pageSize?: number) => apiClient.getLeaderboard(page, pageSize)
}

/**
 * 用户管理相关API
 */
export const usersApi = {
  /**
   * 通过钱包地址查询用户
   */
  getUserByWallet: (walletAddress: string) => apiClient.getUserByWallet(walletAddress),

  /**
   * 注册新用户
   */
  register: (data: UserRegisterRequest) => apiClient.registerUser(data),

  /**
   * 获取用户详情
   */
  getDetail: (userId: number) => apiClient.getUserDetail(userId),

  /**
   * 更新用户信息
   */
  update: (userId: number, data: UserUpdateRequest) => apiClient.updateUser(userId, data)
}

/**
 * 积分系统相关API
 */
export const pointsApi = {
  /**
   * 获取用户积分信息
   */
  getUserPoints: (userId: number) => apiClient.getUserPoints(userId),

  /**
   * 获取积分流水记录
   */
  getTransactions: (userId: number, page?: number, pageSize?: number, transactionType?: string) =>
    apiClient.getPointTransactions(userId, page, pageSize, transactionType),

  /**
   * 获取积分统计
   */
  getStatistics: (userId: number) => apiClient.getPointsStatistics(userId)
}

/**
 * 战队系统相关API
 */
export const teamsApi = {
  /**
   * 创建战队
   */
  create: (captainId: number, data: TeamCreateRequest) => apiClient.createTeam(captainId, data),

  /**
   * 获取战队详情
   */
  getDetail: (teamId: number) => apiClient.getTeam(teamId),

  /**
   * 获取战队列表
   */
  getList: (page?: number, pageSize?: number, isPublic?: boolean) =>
    apiClient.getTeams(page, pageSize, isPublic),

  /**
   * 获取用户所在的战队
   */
  getUserTeam: (userId: number) => apiClient.getUserTeam(userId),

  /**
   * 更新战队信息
   */
  update: (teamId: number, captainId: number, data: TeamUpdateRequest) =>
    apiClient.updateTeam(teamId, captainId, data),

  /**
   * 解散战队
   */
  disband: (teamId: number, captainId: number) => apiClient.disbandTeam(teamId, captainId),

  /**
   * 加入战队
   */
  join: (teamId: number, userId: number) => apiClient.joinTeam(teamId, userId),

  /**
   * 审批成员
   */
  approveMember: (teamId: number, userId: number, approverId: number, approved: boolean) =>
    apiClient.approveMember(teamId, userId, approverId, approved),

  /**
   * 离开战队
   */
  leave: (teamId: number, userId: number) => apiClient.leaveTeam(teamId, userId),

  /**
   * 获取战队成员
   */
  getMembers: (teamId: number, status?: TeamMemberStatus) => apiClient.getTeamMembers(teamId, status),

  /**
   * 获取战队排行榜
   */
  getLeaderboard: (page?: number, pageSize?: number) => apiClient.getTeamLeaderboard(page, pageSize),

  /**
   * 获取战队任务
   */
  getTasks: (teamId: number, status?: TeamTaskStatus) => apiClient.getTeamTasks(teamId, status),

  /**
   * 分配奖励池
   */
  distributeRewards: (teamId: number, captainId: number) => apiClient.distributeTeamRewards(teamId, captainId)
}

/**
 * 任务系统相关API
 */
export const tasksApi = {
  /**
   * 获取任务列表
   */
  getList: (page?: number, pageSize?: number, taskType?: TaskType, isActive?: boolean, isVisible?: boolean) =>
    apiClient.getTasks(page, pageSize, taskType, isActive, isVisible),

  /**
   * 获取任务详情
   */
  getDetail: (taskId: number) => apiClient.getTask(taskId),

  /**
   * 领取任务
   */
  assignToUser: (userId: number, taskId: number) => apiClient.assignTaskToUser(userId, taskId),

  /**
   * 获取用户任务列表
   */
  getUserTasks: (userId: number, page?: number, pageSize?: number, status?: UserTaskStatus, taskType?: TaskType) =>
    apiClient.getUserTasks(userId, page, pageSize, status, taskType),

  /**
   * 获取用户特定任务
   */
  getUserTask: (userId: number, taskId: number) => apiClient.getUserTask(userId, taskId),

  /**
   * 更新任务进度
   */
  updateProgress: (userTaskId: number, progressDelta: number) =>
    apiClient.updateTaskProgress(userTaskId, progressDelta),

  /**
   * 领取任务奖励
   */
  claimReward: (userTaskId: number, userId: number) => apiClient.claimTaskReward(userTaskId, userId),

  /**
   * 获取任务统计
   */
  getStatistics: (taskId: number) => apiClient.getTaskStatistics(taskId),

  /**
   * 获取用户任务汇总
   */
  getUserSummary: (userId: number) => apiClient.getUserTaskSummary(userId),

  /**
   * 自动分配任务
   */
  autoAssign: (userId: number) => apiClient.autoAssignTasks(userId)
}

/**
 * Quiz 系统相关API
 */
export const quizApi = {
  /**
   * 获取题目列表
   */
  getQuestions: (
    page?: number,
    pageSize?: number,
    difficulty?: QuestionDifficulty,
    category?: string,
    isActive?: boolean,
    isFeatured?: boolean
  ) => apiClient.getQuestions(page, pageSize, difficulty, category, isActive, isFeatured),

  /**
   * 获取题目详情（不含答案）
   */
  getQuestion: (questionId: number) => apiClient.getQuestion(questionId),

  /**
   * 获取随机题目
   */
  getRandomQuestion: (userId: number, difficulty?: QuestionDifficulty, category?: string) =>
    apiClient.getRandomQuestion(userId, difficulty, category),

  /**
   * 提交答案
   */
  submitAnswer: (userId: number, answer: AnswerSubmit) => apiClient.submitAnswer(userId, answer),

  /**
   * 获取用户答题记录
   */
  getUserAnswers: (userId: number, page?: number, pageSize?: number, isCorrect?: boolean, difficulty?: QuestionDifficulty) =>
    apiClient.getUserAnswers(userId, page, pageSize, isCorrect, difficulty),

  /**
   * 获取用户答题统计
   */
  getStatistics: (userId: number) => apiClient.getQuizStatistics(userId),

  /**
   * 获取每日答题会话
   */
  getDailySession: (userId: number) => apiClient.getDailySession(userId),

  /**
   * 检查每日答题限制
   */
  checkDailyLimit: (userId: number) => apiClient.checkDailyLimit(userId),

  /**
   * 获取答题排行榜
   */
  getRanking: (page?: number, pageSize?: number, orderBy?: 'correct' | 'accuracy' | 'points' | 'streak') =>
    apiClient.getQuizRanking(page, pageSize, orderBy)
}

export default apiClient
