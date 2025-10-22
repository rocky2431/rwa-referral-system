#!/bin/bash

# Vercel CLI 部署脚本
# 使用方法: ./deploy-vercel.sh

set -e  # 遇到错误立即退出

echo "======================================"
echo "🚀 RWA推荐系统 - Vercel部署脚本"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否已登录Vercel
echo "📋 步骤 1/5: 检查Vercel登录状态..."
if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  未登录Vercel,需要先登录${NC}"
    echo "请执行以下命令完成登录:"
    echo ""
    echo -e "${GREEN}vercel login${NC}"
    echo ""
    echo "登录完成后,重新运行此脚本"
    exit 1
else
    VERCEL_USER=$(vercel whoami)
    echo -e "${GREEN}✅ 已登录: $VERCEL_USER${NC}"
fi

echo ""
echo "📋 步骤 2/5: 确认项目信息..."
echo "项目路径: $(pwd)"
echo "GitHub仓库: rocky2431/rwa-referral-system"
echo ""

# 询问是否继续
read -p "是否继续部署? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "部署已取消"
    exit 0
fi

echo ""
echo "📋 步骤 3/5: 配置环境变量..."
echo ""
echo "请输入以下环境变量 (直接回车使用默认值):"
echo ""

# API基础URL
read -p "VITE_API_BASE_URL (默认: http://localhost:8000/api/v1): " API_URL
API_URL=${API_URL:-http://localhost:8000/api/v1}

# 合约地址
read -p "VITE_CONTRACT_ADDRESS (默认: 0x0000000000000000000000000000000000000000): " CONTRACT_ADDR
CONTRACT_ADDR=${CONTRACT_ADDR:-0x0000000000000000000000000000000000000000}

# 链ID
read -p "VITE_CHAIN_ID (默认: 97): " CHAIN_ID
CHAIN_ID=${CHAIN_ID:-97}

echo ""
echo "环境变量确认:"
echo "  VITE_API_BASE_URL: $API_URL"
echo "  VITE_CONTRACT_ADDRESS: $CONTRACT_ADDR"
echo "  VITE_CHAIN_ID: $CHAIN_ID"
echo ""

read -p "确认无误? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "部署已取消"
    exit 0
fi

echo ""
echo "📋 步骤 4/5: 执行Vercel部署..."
echo ""

# 部署到预览环境
vercel \
  --build-env VITE_API_BASE_URL="$API_URL" \
  --build-env VITE_CONTRACT_ADDRESS="$CONTRACT_ADDR" \
  --build-env VITE_CHAIN_ID="$CHAIN_ID" \
  --yes

PREVIEW_URL=$(vercel ls --limit 1 | grep -o 'https://[^ ]*' | head -n 1)

echo ""
echo -e "${GREEN}✅ 预览环境部署成功!${NC}"
echo "预览URL: $PREVIEW_URL"
echo ""

# 询问是否部署到生产环境
read -p "是否部署到生产环境? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📋 步骤 5/5: 部署到生产环境..."
    echo ""

    vercel --prod \
      --build-env VITE_API_BASE_URL="$API_URL" \
      --build-env VITE_CONTRACT_ADDRESS="$CONTRACT_ADDR" \
      --build-env VITE_CHAIN_ID="$CHAIN_ID" \
      --yes

    echo ""
    echo -e "${GREEN}✅ 生产环境部署成功!${NC}"
    echo ""

    # 获取生产URL
    PROD_URL=$(vercel ls --prod --limit 1 | grep -o 'https://[^ ]*' | head -n 1)
    echo "生产URL: $PROD_URL"
else
    echo "已跳过生产环境部署"
fi

echo ""
echo "======================================"
echo -e "${GREEN}🎉 部署完成!${NC}"
echo "======================================"
echo ""
echo "📝 后续步骤:"
echo "1. 访问部署的URL测试功能"
echo "2. 在Vercel Dashboard配置自定义域名"
echo "3. 更新README.md中的演示地址"
echo ""
echo "📚 详细文档: VERCEL_DEPLOYMENT.md"
echo ""
