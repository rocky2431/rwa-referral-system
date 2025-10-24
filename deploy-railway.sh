#!/bin/bash

# Railway自动化部署脚本
# 使用方法: ./deploy-railway.sh

set -e  # 遇到错误立即退出

echo "======================================"
echo "🚂 Railway 后端部署脚本"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查是否已登录Railway
echo "📋 步骤 1/7: 检查Railway登录状态..."
if ! railway whoami &> /dev/null; then
    echo -e "${RED}❌ 未登录Railway${NC}"
    echo "请先运行: railway login"
    exit 1
else
    RAILWAY_USER=$(railway whoami)
    echo -e "${GREEN}✅ 已登录: $RAILWAY_USER${NC}"
fi

echo ""
echo "======================================"
echo "📝 部署配置"
echo "======================================"
echo "项目路径: $(pwd)"
echo "GitHub仓库: rocky2431/rwa-referral-system"
echo "Vercel前端: https://socialtest2-86rmmtqhg-rocky2431s-projects.vercel.app"
echo ""

read -p "是否继续部署? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "部署已取消"
    exit 0
fi

echo ""
echo "======================================"
echo "🎯 重要提示"
echo "======================================"
echo -e "${YELLOW}接下来的步骤需要您在Railway Dashboard中手动完成:${NC}"
echo ""
echo "1. 访问 https://railway.app/new"
echo "2. 选择 'Deploy from GitHub repo'"
echo "3. 选择 'rocky2431/rwa-referral-system'"
echo "4. 等待初始部署完成"
echo "5. 添加 PostgreSQL 数据库"
echo "6. 添加 Redis"
echo "7. 配置环境变量"
echo ""
echo -e "${BLUE}完成以上步骤后,按回车继续...${NC}"
read

echo ""
echo "======================================"
echo "📋 环境变量配置清单"
echo "======================================"
echo ""
echo -e "${YELLOW}请在Railway Dashboard中配置以下环境变量:${NC}"
echo ""

cat << 'EOF'
# 基础配置
DEBUG=False
SECRET_KEY=<生成一个32字符的随机字符串>
API_V1_PREFIX=/api/v1

# 数据库 (Railway自动注入)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (Railway自动注入)
REDIS_URL=${{Redis.REDIS_URL}}

# CORS配置 (⚠️ 重要!)
CORS_ORIGINS=https://socialtest2-86rmmtqhg-rocky2431s-projects.vercel.app,https://socialtest2.vercel.app,http://localhost:5173

# JWT配置
JWT_SECRET_KEY=<生成另一个32字符的随机字符串>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Web3配置
BSC_NETWORK=testnet
BSC_TESTNET_RPC_URL=https://data-seed-prebsc-1-s1.binance.org:8545
REFERRAL_CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000

# 推荐系统配置
LEVEL_1_BONUS_RATE=15
LEVEL_2_BONUS_RATE=5
INACTIVE_DAYS=30
EOF

echo ""
echo "======================================"
echo "🔑 生成随机密钥"
echo "======================================"
echo ""
echo "SECRET_KEY:"
openssl rand -hex 32
echo ""
echo "JWT_SECRET_KEY:"
openssl rand -hex 32
echo ""

echo -e "${BLUE}环境变量配置完成后,按回车继续...${NC}"
read

echo ""
echo "======================================"
echo "⚙️  构建和启动命令配置"
echo "======================================"
echo ""
echo "在Railway服务的 Settings > Deploy 中配置:"
echo ""
echo -e "${GREEN}Build Command:${NC}"
echo "pip install -r backend/requirements.txt"
echo ""
echo -e "${GREEN}Start Command:${NC}"
echo "cd backend && uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
echo ""
echo -e "${GREEN}Root Directory:${NC}"
echo "(留空或设为 /)"
echo ""

echo -e "${BLUE}配置完成后,按回车继续...${NC}"
read

echo ""
echo "======================================"
echo "🔍 获取部署URL"
echo "======================================"
echo ""
echo "请输入Railway提供的部署URL (类似: https://xxx.up.railway.app):"
read -p "URL: " RAILWAY_URL

if [ -z "$RAILWAY_URL" ]; then
    echo -e "${RED}❌ URL不能为空${NC}"
    exit 1
fi

# 去除末尾的斜杠
RAILWAY_URL=$(echo "$RAILWAY_URL" | sed 's:/*$::')

echo ""
echo -e "${GREEN}✅ Railway部署URL: $RAILWAY_URL${NC}"

# 保存到文件供后续使用
echo "$RAILWAY_URL" > .railway-url

echo ""
echo "======================================"
echo "🧪 测试后端API"
echo "======================================"
echo ""
echo "测试健康检查端点..."

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${RAILWAY_URL}/health" || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ 后端API运行正常!${NC}"
    echo ""
    echo "响应内容:"
    curl -s "${RAILWAY_URL}/health" | python3 -m json.tool
else
    echo -e "${RED}⚠️  后端API返回状态码: $HTTP_CODE${NC}"
    echo "请检查Railway部署日志"
    echo ""
    echo "可能的原因:"
    echo "1. 服务还在启动中,请稍等片刻后重试"
    echo "2. 环境变量配置有误"
    echo "3. 数据库连接失败"
fi

echo ""
echo "======================================"
echo "📊 后续步骤"
echo "======================================"
echo ""
echo -e "${YELLOW}步骤 1: 更新Vercel环境变量${NC}"
echo ""
echo "运行以下命令更新Vercel前端的API地址:"
echo ""
echo -e "${GREEN}vercel env rm VITE_API_BASE_URL production${NC}"
echo -e "${GREEN}vercel env add VITE_API_BASE_URL production${NC}"
echo "# 输入: ${RAILWAY_URL}/api/v1"
echo ""
echo -e "${GREEN}vercel --prod${NC}"
echo ""

echo -e "${YELLOW}步骤 2: 初始化数据库${NC}"
echo ""
echo "在Railway Dashboard中:"
echo "1. 点击Python服务 > 右上角'...' > Shell"
echo "2. 运行: cd backend && python -c \"from app.db.init_db import init_database; init_database()\""
echo ""

echo -e "${YELLOW}步骤 3: 测试完整流程${NC}"
echo ""
echo "访问前端: https://socialtest2-86rmmtqhg-rocky2431s-projects.vercel.app"
echo "检查是否能正常连接钱包和调用API"
echo ""

echo "======================================"
echo -e "${GREEN}🎉 部署脚本执行完成!${NC}"
echo "======================================"
echo ""
echo "📝 Railway后端URL已保存到: .railway-url"
echo ""
echo "📚 详细文档: RAILWAY_DEPLOYMENT.md"
echo ""
