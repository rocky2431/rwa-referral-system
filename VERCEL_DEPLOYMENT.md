# Vercel部署指南

## 📋 前置准备

### 1. 注册Vercel账号
访问 [https://vercel.com](https://vercel.com) 注册账号,推荐使用GitHub账号登录。

### 2. 安装Vercel CLI
```bash
npm install -g vercel
```

### 3. 登录Vercel
```bash
vercel login
```

## 🚀 部署步骤

### 方式一: 通过Vercel CLI部署

#### 1. 进入项目目录
```bash
cd /path/to/rwa-referral-system
```

#### 2. 执行部署命令
```bash
vercel
```

首次部署时会提示:
- **Set up and deploy?** → `Y`
- **Which scope?** → 选择你的账号
- **Link to existing project?** → `N` (首次部署)
- **What's your project's name?** → `rwa-referral-system` (或自定义名称)
- **In which directory is your code located?** → `./`
- **Want to override the settings?** → `N`

#### 3. 生产部署
测试通过后,执行生产部署:
```bash
vercel --prod
```

### 方式二: 通过GitHub集成部署 (推荐)

#### 1. 访问Vercel Dashboard
https://vercel.com/dashboard

#### 2. 导入Git仓库
1. 点击 **"Add New"** → **"Project"**
2. 选择 **"Import Git Repository"**
3. 选择 `rocky2431/rwa-referral-system`

#### 3. 配置项目
- **Framework Preset**: 选择 `Other` 或 `Vite`
- **Root Directory**: `./` (保持默认)
- **Build Command**: `cd frontend && npm install && npm run build`
- **Output Directory**: `frontend/dist`

#### 4. 配置环境变量
在 **"Environment Variables"** 区域添加:

```env
# 必需环境变量
VITE_API_BASE_URL=https://your-backend-api.com/api/v1
VITE_CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000
VITE_CHAIN_ID=97

# 可选环境变量
VITE_BSC_NETWORK=testnet
VITE_APP_NAME=RWA Referral System
VITE_WALLETCONNECT_PROJECT_ID=your_walletconnect_project_id
```

#### 5. 部署
点击 **"Deploy"** 开始部署。

## ⚙️ 环境变量配置详解

### 核心变量

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `VITE_API_BASE_URL` | 后端API地址 | `https://api.example.com/api/v1` |
| `VITE_CONTRACT_ADDRESS` | 智能合约地址 | `0x...` |
| `VITE_CHAIN_ID` | 区块链网络ID | `97` (测试网) / `56` (主网) |

### 可选变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `VITE_BSC_NETWORK` | BSC网络类型 | `testnet` |
| `VITE_APP_NAME` | 应用名称 | `RWA Referral System` |
| `VITE_WALLETCONNECT_PROJECT_ID` | WalletConnect项目ID | - |

### 获取WalletConnect Project ID
1. 访问 [https://cloud.walletconnect.com/](https://cloud.walletconnect.com/)
2. 注册并创建新项目
3. 复制 `Project ID`

## 🔧 自定义域名配置

### 1. 在Vercel Dashboard中
- 进入项目设置
- 点击 **"Domains"**
- 添加自定义域名

### 2. 配置DNS记录
在域名服务商处添加CNAME记录:
```
CNAME  @  cname.vercel-dns.com
```

## 📊 部署后验证

### 1. 检查部署状态
```bash
vercel ls
```

### 2. 查看部署日志
```bash
vercel logs [deployment-url]
```

### 3. 访问部署的应用
部署成功后,Vercel会提供访问URL:
- **测试环境**: `https://rwa-referral-system-xxx.vercel.app`
- **生产环境**: `https://rwa-referral-system.vercel.app`

### 4. 功能测试清单
- [ ] 页面正常加载
- [ ] 钱包连接功能
- [ ] API调用正常
- [ ] 路由跳转正常
- [ ] 响应式布局正常

## 🔄 自动部署配置

通过GitHub集成后,Vercel会自动:
- ✅ 监听 `main` 分支的push事件
- ✅ 自动触发生产部署
- ✅ 为PR创建预览部署
- ✅ 在PR中显示部署状态

### 配置自动部署分支
在 Vercel Dashboard → Settings → Git:
- **Production Branch**: `main`
- **Preview Branches**: `All` 或指定分支

## 🐛 常见问题

### 1. 构建失败: "Command not found"
**原因**: Node.js版本不匹配

**解决方案**: 在项目根目录创建 `.nvmrc` 文件:
```
18
```

或在 `package.json` 中指定:
```json
{
  "engines": {
    "node": ">=18.0.0"
  }
}
```

### 2. 部署后API调用失败
**原因**: 环境变量未配置或后端CORS未开放

**解决方案**:
1. 检查 `VITE_API_BASE_URL` 是否正确
2. 确保后端允许Vercel域名的CORS请求

### 3. 路由刷新404
**原因**: SPA路由重写规则未生效

**解决方案**: 确保 `vercel.json` 包含:
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### 4. 构建超时
**原因**: 依赖安装耗时过长

**解决方案**: 优化 `package.json`,移除不必要的依赖

## 📝 维护与更新

### 更新部署
1. 提交代码到GitHub
   ```bash
   git add .
   git commit -m "feat: 更新功能"
   git push origin main
   ```

2. Vercel自动触发部署

### 回滚部署
```bash
vercel rollback [deployment-url]
```

或在Vercel Dashboard中选择历史部署版本进行回滚。

## 🔐 安全建议

1. **环境变量管理**: 敏感信息必须通过Vercel环境变量配置,不要提交到代码仓库
2. **API密钥保护**: 使用环境变量存储API密钥
3. **CORS配置**: 后端仅允许Vercel域名的跨域请求
4. **HTTPS**: Vercel默认启用HTTPS,确保所有API调用也使用HTTPS

## 📚 相关资源

- [Vercel官方文档](https://vercel.com/docs)
- [Vite部署指南](https://vitejs.dev/guide/static-deploy.html#vercel)
- [Vercel CLI文档](https://vercel.com/docs/cli)
- [环境变量配置](https://vercel.com/docs/environment-variables)

---

**部署完成后,请及时更新README.md中的演示地址!** 🎉
