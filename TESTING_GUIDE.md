# 前端测试指南

**测试地址**: http://localhost:5173
**后端API**: http://localhost:8000/docs
**智能合约**: 0xEdA477776C59f0F78A2874945d659aDF27E46EA7 (BSC Testnet)

---

## 🔧 测试前准备

### 1. 安装MetaMask
- Chrome扩展商店搜索"MetaMask"
- 安装并创建/导入钱包

### 2. 配置BSC测试网
在MetaMask中添加BSC测试网：
- **网络名称**: BSC Testnet
- **RPC URL**: https://data-seed-prebsc-1-s1.binance.org:8545/
- **Chain ID**: 97
- **货币符号**: BNB
- **区块浏览器**: https://testnet.bscscan.com

### 3. 获取测试BNB
访问BSC测试网水龙头获取测试币：
- https://testnet.bnbchain.org/faucet-smart
- 或搜索"BSC testnet faucet"

---

## ✅ 测试清单

### 测试1: 首页加载
- [ ] 打开 http://localhost:5173
- [ ] 验证页面正常显示
- [ ] 检查导航菜单是否完整
- [ ] 查看统计数据卡片（总用户数、总奖励等）

**预期结果**: ✅ 页面正常加载，无Console错误

---

### 测试2: 钱包连接
- [ ] 点击右上角"连接钱包"按钮
- [ ] MetaMask弹窗出现
- [ ] 选择账户并确认连接
- [ ] 检查按钮文本变为钱包地址（0x...）

**预期结果**: ✅ 钱包成功连接，显示地址简写

---

### 测试3: Dashboard页面
- [ ] 点击导航栏"仪表板"
- [ ] 验证页面加载Dashboard数据
- [ ] 检查显示内容：
  - [ ] 总积分数值
  - [ ] 推荐人数
  - [ ] 最后活跃时间
  - [ ] 推荐人地址

**预期结果**:
- ✅ 如果已注册：显示用户数据
- ✅ 如果未注册：显示默认值（0积分，0推荐）

**API调用**:
```bash
curl http://localhost:8000/api/v1/dashboard/{你的钱包地址}
```

---

### 测试4: 用户注册（如果未注册）
- [ ] 打开浏览器Console（F12）
- [ ] 在Console中执行：
```javascript
fetch('http://localhost:8000/api/v1/users/register', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    wallet_address: '你的钱包地址（小写）',
    username: '测试用户'
  })
}).then(r => r.json()).then(console.log)
```
- [ ] 刷新Dashboard页面，查看数据更新

**预期结果**: ✅ 用户创建成功，Dashboard显示用户数据

---

### 测试5: 我的积分页面
- [ ] 点击导航栏"我的积分"
- [ ] 验证积分信息显示
- [ ] 检查积分来源分类（推荐、任务、答题等）

**预期结果**: ✅ 显示积分详情（初始为0）

---

### 测试6: 智能合约交互
- [ ] 在Dashboard页面查看推荐链接（如果显示）
- [ ] 测试合约读取功能：
```javascript
// 在Console中执行
const contract = new ethers.Contract(
  '0xEdA477776C59f0F78A2874945d659aDF27E46EA7',
  ['function getUserInfo(address) view returns (address, uint256, uint256, uint256)'],
  new ethers.providers.Web3Provider(window.ethereum)
);

contract.getUserInfo('你的钱包地址').then(console.log);
```

**预期结果**: ✅ 返回用户信息数组

---

### 测试7: 推荐关系绑定
- [ ] 准备另一个测试钱包地址
- [ ] 在Console执行绑定：
```javascript
const signer = new ethers.providers.Web3Provider(window.ethereum).getSigner();
const contract = new ethers.Contract(
  '0xEdA477776C59f0F78A2874945d659aDF27E46EA7',
  ['function bindReferrer(address) external returns (bool)'],
  signer
);

// 绑定推荐人（替换为实际地址）
contract.bindReferrer('推荐人钱包地址').then(tx => tx.wait()).then(console.log);
```

**预期结果**: ✅ 交易成功，推荐关系建立

---

### 测试8: 查看合约信息
- [ ] 访问 https://testnet.bscscan.com/address/0xEdA477776C59f0F78A2874945d659aDF27E46EA7
- [ ] 查看合约详情
- [ ] 检查Read Contract功能
- [ ] 调用getReferralConfig查看配置

**预期结果**: ✅ 合约已验证，可读取配置参数

---

## 🐛 常见问题

### 问题1: MetaMask未安装
**解决**: 安装MetaMask扩展

### 问题2: 网络错误
**解决**: 确保切换到BSC测试网（Chain ID: 97）

### 问题3: Console显示错误
**检查**:
1. 后端服务是否运行（http://localhost:8000/docs）
2. 前端服务是否运行（http://localhost:5173）
3. Network标签查看API调用状态

### 问题4: 合约调用失败
**原因**: 可能智能合约未正确部署或配置
**检查**:
- 前端.env中的VITE_CONTRACT_ADDRESS是否正确
- BSC测试网RPC是否可访问
- 钱包是否有测试BNB（用于Gas费）

---

## 📊 测试数据记录

### 基础信息
- **测试时间**: ___________
- **测试钱包**: ___________
- **浏览器**: Chrome / Firefox / Safari
- **网络**: BSC Testnet

### 功能测试结果

| 功能 | 状态 | 备注 |
|------|------|------|
| 首页加载 | ⬜ 通过 ⬜ 失败 | |
| 钱包连接 | ⬜ 通过 ⬜ 失败 | |
| Dashboard | ⬜ 通过 ⬜ 失败 | |
| 用户注册 | ⬜ 通过 ⬜ 失败 | |
| 积分查询 | ⬜ 通过 ⬜ 失败 | |
| 合约读取 | ⬜ 通过 ⬜ 失败 | |
| 推荐绑定 | ⬜ 通过 ⬜ 失败 | |

---

## 🔍 调试工具

### Chrome DevTools
- **F12**: 打开开发者工具
- **Console**: 查看日志和错误
- **Network**: 查看API请求
- **Application > Local Storage**: 查看前端存储

### API测试
使用Postman或curl测试后端API：
```bash
# 查看API文档
open http://localhost:8000/docs

# 测试Dashboard API
curl http://localhost:8000/api/v1/dashboard/0x你的钱包地址

# 测试用户注册
curl -X POST http://localhost:8000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"wallet_address":"0x你的钱包地址","username":"测试用户"}'
```

---

## ✅ 完整测试通过标准

- [ ] 所有页面正常加载，无Console错误
- [ ] 钱包连接成功
- [ ] Dashboard显示正确数据
- [ ] 用户可以注册
- [ ] 积分查询正常
- [ ] 智能合约可以调用
- [ ] 推荐关系可以建立

---

**测试完成后，请将结果反馈！** 🎉
