# 🚀 Vercel CLI 快速部署指南

## 方式一: 使用自动化脚本 (推荐)

### 1. 登录Vercel (首次需要)
```bash
vercel login
```
这会打开浏览器,请在浏览器中完成登录。

### 2. 运行部署脚本
```bash
cd /Users/rocky243/Desktop/paimon.dex/socialtest2
./deploy-vercel.sh
```

脚本会自动:
- ✅ 检查登录状态
- ✅ 引导您配置环境变量
- ✅ 部署到预览环境
- ✅ 询问是否部署到生产环境

---

## 方式二: 手动命令行部署

### 步骤 1: 登录Vercel
```bash
vercel login
```

### 步骤 2: 首次部署(预览环境)
```bash
cd /Users/rocky243/Desktop/paimon.dex/socialtest2

vercel \
  --build-env VITE_API_BASE_URL=http://localhost:8000/api/v1 \
  --build-env VITE_CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000 \
  --build-env VITE_CHAIN_ID=97 \
  --yes
```

首次部署时的提示选择:
- **Set up and deploy?** → `Y`
- **Which scope?** → 选择你的账号
- **Link to existing project?** → `N` (首次部署)
- **What's your project's name?** → `rwa-referral-system`
- **In which directory is your code located?** → `./` (直接回车)

### 步骤 3: 部署到生产环境
预览环境测试通过后:
```bash
vercel --prod \
  --build-env VITE_API_BASE_URL=http://localhost:8000/api/v1 \
  --build-env VITE_CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000 \
  --build-env VITE_CHAIN_ID=97 \
  --yes
```

---

## 环境变量说明

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `VITE_API_BASE_URL` | 后端API地址 | `http://localhost:8000/api/v1` 或实际后端地址 |
| `VITE_CONTRACT_ADDRESS` | 智能合约地址 | `0x...` (部署后填入实际地址) |
| `VITE_CHAIN_ID` | 区块链网络ID | `97` (BSC测试网) 或 `56` (BSC主网) |

**注意**:
- 如果您有实际的后端API地址,请替换 `VITE_API_BASE_URL` 的值
- 智能合约部署后,请更新 `VITE_CONTRACT_ADDRESS`

---

## 部署后管理

### 查看已部署的项目
```bash
vercel ls
```

### 查看部署日志
```bash
vercel logs
```

### 添加/更新环境变量
```bash
vercel env add VITE_API_BASE_URL production
vercel env add VITE_CONTRACT_ADDRESS production
vercel env add VITE_CHAIN_ID production
```

### 重新部署(使用最新代码)
```bash
git pull origin main
vercel --prod
```

### 回滚部署
```bash
vercel rollback
```

---

## 常见问题

### Q1: 登录时浏览器未自动打开
**解决**: 复制终端显示的URL,手动在浏览器中打开。

### Q2: 构建失败
**检查**:
1. 确保在项目根目录执行命令
2. 查看构建日志: `vercel logs`
3. 检查 `vercel.json` 配置是否正确

### Q3: 部署后页面空白
**可能原因**:
1. 环境变量未配置
2. API地址不可访问
3. 路由配置问题

**解决**:
- 检查浏览器控制台错误
- 确认环境变量已正确设置
- 检查 `vercel.json` 中的 rewrites 配置

### Q4: 如何更新环境变量后重新部署
```bash
# 方法1: 在Dashboard中更新后触发重新部署
vercel --prod

# 方法2: 通过CLI更新并部署
vercel env rm VITE_API_BASE_URL production
vercel env add VITE_API_BASE_URL production
vercel --prod
```

---

## 部署检查清单

部署完成后,请检查:

- [ ] 网站可以正常访问
- [ ] 钱包连接功能正常
- [ ] API调用成功(检查浏览器Network)
- [ ] 页面路由跳转正常
- [ ] 响应式布局在移动端正常

---

## 获取帮助

- 详细文档: `VERCEL_DEPLOYMENT.md`
- Vercel CLI文档: https://vercel.com/docs/cli
- 项目问题: https://github.com/rocky2431/rwa-referral-system/issues

---

**部署成功后,别忘了更新README.md中的演示地址!** 🎉
