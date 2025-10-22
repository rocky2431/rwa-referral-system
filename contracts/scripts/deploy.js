const hre = require("hardhat");

async function main() {
  console.log("🚀 开始部署 RWAReferral 合约...\n");

  // 获取部署者账户
  const [deployer] = await hre.ethers.getSigners();
  console.log("📝 部署账户:", deployer.address);

  // 查询账户余额
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("💰 账户余额:", hre.ethers.formatEther(balance), "BNB\n");

  // 部署合约
  console.log("⏳ 正在部署合约...");
  const RWAReferral = await hre.ethers.getContractFactory("RWAReferral");
  const referral = await RWAReferral.deploy();

  await referral.waitForDeployment();

  const address = await referral.getAddress();
  console.log("✅ 合约部署成功!");
  console.log("📍 合约地址:", address);

  // 获取配置信息
  const config = await referral.getReferralConfig();
  const pointsPerBNB = await referral.POINTS_PER_BNB();

  console.log("\n⚙️  推荐配置 (v2.0):");
  console.log("   - 基础单位:", config[0].toString());
  console.log("   - 总奖励率:", (Number(config[1]) / 100).toFixed(2) + "%");
  console.log("   - 不活跃阈值:", (Number(config[2]) / 86400).toFixed(0), "天");
  console.log("   - 一级奖励:", (Number(config[1]) * Number(config[3]) / 100 / 10000).toFixed(2) + "%");
  console.log("   - 二级奖励:", (Number(config[1]) * Number(config[4]) / 100 / 10000).toFixed(2) + "%");
  console.log("   - 积分兑换率:", pointsPerBNB.toString(), "积分/BNB");

  console.log("\n💰 积分奖励示例 (1 BNB购买):");
  console.log("   - 一级推荐人获得:", (15n * pointsPerBNB / 100n).toString(), "积分");
  console.log("   - 二级推荐人获得:", (5n * pointsPerBNB / 100n).toString(), "积分");

  console.log("\n📋 下一步操作:");
  console.log("1. 将合约地址更新到 .env 文件:");
  console.log(`   REFERRAL_CONTRACT_ADDRESS=${address}`);
  console.log("\n2. 在 BscScan 上验证合约:");
  console.log(`   npx hardhat verify --network ${hre.network.name} ${address}`);
  console.log("\n3. 查看合约:");
  if (hre.network.name === "bscTestnet") {
    console.log(`   https://testnet.bscscan.com/address/${address}`);
  } else if (hre.network.name === "bscMainnet") {
    console.log(`   https://bscscan.com/address/${address}`);
  }

  // 保存部署信息到文件
  const fs = require("fs");
  const deploymentInfo = {
    version: "v2.0",
    network: hre.network.name,
    contractAddress: address,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    blockNumber: await hre.ethers.provider.getBlockNumber(),
    config: {
      decimals: config[0].toString(),
      referralBonus: config[1].toString(),
      secondsUntilInactive: config[2].toString(),
      level1Rate: config[3].toString(),
      level2Rate: config[4].toString(),
      pointsPerBNB: pointsPerBNB.toString()
    },
    features: {
      eventDriven: true,
      pointsSystem: true,
      description: "v2.0: 事件驱动积分发放系统"
    }
  };

  const deploymentsDir = "../deployments";
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir);
  }

  fs.writeFileSync(
    `${deploymentsDir}/${hre.network.name}.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );

  console.log(`\n💾 部署信息已保存到: deployments/${hre.network.name}.json`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ 部署失败:", error);
    process.exit(1);
  });
