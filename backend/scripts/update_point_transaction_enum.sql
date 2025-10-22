-- 更新 point_transaction_type 枚举类型
-- 添加新的积分交易类型：REGISTER_REWARD, REFERRAL_REWARD, TASK_REWARD

-- 方法1：直接添加新值到枚举（PostgreSQL 9.1+）
ALTER TYPE point_transaction_type ADD VALUE IF NOT EXISTS 'register_reward';
ALTER TYPE point_transaction_type ADD VALUE IF NOT EXISTS 'referral_reward';
ALTER TYPE point_transaction_type ADD VALUE IF NOT EXISTS 'task_reward';

-- 查看更新后的枚举值
SELECT enumlabel FROM pg_enum WHERE enumtypid = 'point_transaction_type'::regtype ORDER BY enumsortorder;
