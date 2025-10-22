const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("RWAReferral", function () {
  let referral;
  let owner, user1, user2, user3, user4;

  beforeEach(async function () {
    // 获取测试账户
    [owner, user1, user2, user3, user4] = await ethers.getSigners();

    // 部署合约
    const RWAReferral = await ethers.getContractFactory("RWAReferral");
    referral = await RWAReferral.deploy();
    await referral.waitForDeployment();
  });

  describe("部署测试", function () {
    it("应该正确设置推荐配置", async function () {
      const config = await referral.getReferralConfig();

      expect(config[0]).to.equal(10000); // decimals
      expect(config[1]).to.equal(2000);  // referralBonus (20%)
      expect(config[2]).to.equal(30 * 24 * 60 * 60); // 30 days
      expect(config[3]).to.equal(7500);  // level1 (75%)
      expect(config[4]).to.equal(2500);  // level2 (25%)
    });

    it("应该正确部署合约", async function () {
      expect(await referral.getAddress()).to.be.properAddress;
    });
  });

  describe("绑定推荐人", function () {
    it("应该成功绑定推荐人", async function () {
      // user2 绑定 user1 为推荐人
      await expect(referral.connect(user2).bindReferrer(user1.address))
        .to.emit(referral, "RegisteredReferrer")
        .withArgs(user2.address, user1.address);

      // 验证推荐关系
      const info = await referral.getUserInfo(user2.address);
      expect(info[0]).to.equal(user1.address); // referrer
    });

    it("不能自己推荐自己", async function () {
      // 使用staticCall获取返回值
      const result = await referral.connect(user1).bindReferrer.staticCall(user1.address);
      expect(result).to.be.false;
    });

    it("不能重复绑定推荐人", async function () {
      // 第一次绑定
      await referral.connect(user2).bindReferrer(user1.address);

      // 尝试再次绑定
      const tx = await referral.connect(user2).bindReferrer(user3.address);
      const receipt = await tx.wait();

      // 应该没有发出 RegisteredReferrer 事件
      const event = receipt.logs.find(
        log => log.fragment && log.fragment.name === "RegisteredReferrer"
      );
      expect(event).to.be.undefined;
    });

    it("不能循环推荐", async function () {
      // user2 推荐 user1
      await referral.connect(user2).bindReferrer(user1.address);

      // user1 不能推荐 user2 (循环)
      const result = await referral.connect(user1).bindReferrer.staticCall(user2.address);
      expect(result).to.be.false;
    });
  });

  describe("一级推荐奖励", function () {
    beforeEach(async function () {
      // 建立推荐关系: user1 ← user2
      await referral.connect(user2).bindReferrer(user1.address);
    });

    it("应该正确分发一级奖励", async function () {
      const amount = ethers.parseEther("100");

      // user2 触发奖励 (v2.0: 不再发送BNB)
      await referral.connect(user2).triggerReward(amount);

      // 检查 user1 的奖励
      const info = await referral.getUserInfo(user1.address);
      const expectedReward = amount * 2000n * 7500n / 10000n / 10000n; // 15%

      expect(info[1]).to.equal(expectedReward);
    });

    it("应该更新推荐人数", async function () {
      const infoBefore = await referral.getUserInfo(user1.address);
      expect(infoBefore[2]).to.equal(1); // referredCount
    });
  });

  describe("二级推荐奖励", function () {
    beforeEach(async function () {
      // 建立推荐关系: user1 ← user2 ← user3
      await referral.connect(user2).bindReferrer(user1.address);
      await referral.connect(user3).bindReferrer(user2.address);
    });

    it("应该正确分发二级奖励", async function () {
      const amount = ethers.parseEther("100");

      // user3 触发奖励 (v2.0: 不再发送BNB)
      await referral.connect(user3).triggerReward(amount);

      // 检查奖励
      const user2Info = await referral.getUserInfo(user2.address);
      const user1Info = await referral.getUserInfo(user1.address);

      // user2 (一级): 15%
      const expectedUser2Reward = amount * 2000n * 7500n / 10000n / 10000n;
      // user1 (二级): 5%
      const expectedUser1Reward = amount * 2000n * 2500n / 10000n / 10000n;

      expect(user2Info[1]).to.equal(expectedUser2Reward);
      expect(user1Info[1]).to.equal(expectedUser1Reward);
    });

    it("应该正确更新推荐人数", async function () {
      const user1Info = await referral.getUserInfo(user1.address);
      const user2Info = await referral.getUserInfo(user2.address);

      expect(user1Info[2]).to.equal(1); // user1 推荐了 user2
      expect(user2Info[2]).to.equal(1); // user2 推荐了 user3
    });
  });

  describe("活跃状态测试", function () {
    beforeEach(async function () {
      await referral.connect(user2).bindReferrer(user1.address);
    });

    it("新用户应该是活跃的", async function () {
      const amount = ethers.parseEther("100");
      await referral.connect(user2).triggerReward(amount);

      expect(await referral.isUserActive(user1.address)).to.be.true;
    });

    it("30天后用户应该变为不活跃", async function () {
      const amount = ethers.parseEther("100");
      await referral.connect(user2).triggerReward(amount);

      // 时间前进 31 天
      await time.increase(31 * 24 * 60 * 60);

      expect(await referral.isUserActive(user1.address)).to.be.false;
    });

    it("不活跃用户不应获得奖励", async function () {
      const amount = ethers.parseEther("100");

      // 第一次触发奖励
      await referral.connect(user2).triggerReward(amount);
      const firstReward = (await referral.getUserInfo(user1.address))[1];

      // 时间前进 31 天
      await time.increase(31 * 24 * 60 * 60);

      // 第二次触发奖励 (user1 已不活跃)
      await referral.connect(user2).triggerReward(amount);
      const secondReward = (await referral.getUserInfo(user1.address))[1];

      // 奖励应该保持不变
      expect(secondReward).to.equal(firstReward);
    });

    it("应该可以更新用户活跃时间", async function () {
      const amount = ethers.parseEther("100");
      await referral.connect(user2).triggerReward(amount);

      // 时间前进 20 天
      await time.increase(20 * 24 * 60 * 60);

      // 更新活跃时间
      await referral.connect(user1).updateUserActivity();

      // 再前进 20 天 (总共 40 天,但距离上次更新只有 20 天)
      await time.increase(20 * 24 * 60 * 60);

      // 用户应该仍然活跃
      expect(await referral.isUserActive(user1.address)).to.be.true;
    });
  });

  describe("批量查询", function () {
    beforeEach(async function () {
      // 建立推荐关系
      await referral.connect(user2).bindReferrer(user1.address);
      await referral.connect(user3).bindReferrer(user1.address);
      await referral.connect(user4).bindReferrer(user2.address);

      // 触发一些奖励
      const amount = ethers.parseEther("100");
      await referral.connect(user2).triggerReward(amount);
      await referral.connect(user3).triggerReward(amount);
    });

    it("应该正确批量查询用户信息", async function () {
      const users = [user1.address, user2.address, user3.address];
      const [referrers, rewards, referredCounts] = await referral.batchGetUserInfo(users);

      expect(referrers.length).to.equal(3);
      expect(rewards.length).to.equal(3);
      expect(referredCounts.length).to.equal(3);

      // user1 推荐了 user2 和 user3
      expect(referredCounts[0]).to.equal(2);

      // user2 推荐了 user4
      expect(referredCounts[1]).to.equal(1);

      // user1 应该有奖励
      expect(rewards[0]).to.be.gt(0);
    });
  });

  describe("边界条件测试", function () {
    it("奖励金额为0应该失败", async function () {
      await referral.connect(user2).bindReferrer(user1.address);

      await expect(
        referral.connect(user2).triggerReward(0)
      ).to.be.revertedWith("Purchase amount must be greater than 0");
    });

    it("应该支持空地址数组的批量查询", async function () {
      const [referrers, rewards, referredCounts] = await referral.batchGetUserInfo([]);

      expect(referrers.length).to.equal(0);
      expect(rewards.length).to.equal(0);
      expect(referredCounts.length).to.equal(0);
    });
  });

  // ==================== v2.0 新功能测试 ====================

  describe("v2.0 事件测试", function () {
    beforeEach(async function () {
      // 建立推荐关系: user1 ← user2 ← user3
      await referral.connect(user2).bindReferrer(user1.address);
      await referral.connect(user3).bindReferrer(user2.address);
    });

    it("应该发出 UserPurchased 事件", async function () {
      const amount = ethers.parseEther("1"); // 1 BNB

      const tx = await referral.connect(user3).triggerReward(amount);
      const receipt = await tx.wait();

      // 找到 UserPurchased 事件
      const event = receipt.logs.find(
        log => log.fragment && log.fragment.name === "UserPurchased"
      );

      expect(event).to.not.be.undefined;
      expect(event.args.user).to.equal(user3.address);
      expect(event.args.amount).to.equal(amount);
      expect(event.args.timestamp).to.be.greaterThan(0);
    });

    it("应该发出 RewardCalculated 事件(一级推荐)", async function () {
      const amount = ethers.parseEther("1"); // 1 BNB

      // 计算预期积分
      // BNB奖励 = 1 BNB * 20% * 75% = 0.15 BNB
      // 积分 = 0.15 BNB * 1000 = 150 积分
      const bnbReward = amount * 2000n * 7500n / 10000n / 10000n; // 0.15 BNB
      const expectedPoints = bnbReward * 1000n / ethers.parseEther("1"); // 150

      const tx = await referral.connect(user3).triggerReward(amount);
      const receipt = await tx.wait();

      // 找到一级推荐的 RewardCalculated 事件
      const events = receipt.logs.filter(
        log => log.fragment && log.fragment.name === "RewardCalculated"
      );

      const l1Event = events.find(e => e.args.level === 1n);
      expect(l1Event).to.not.be.undefined;
      expect(l1Event.args.purchaser).to.equal(user3.address);
      expect(l1Event.args.referrer).to.equal(user2.address);
      expect(l1Event.args.purchaseAmount).to.equal(amount);
      expect(l1Event.args.pointsAmount).to.equal(expectedPoints);
      expect(l1Event.args.level).to.equal(1);
    });

    it("应该发出 RewardCalculated 事件(二级推荐)", async function () {
      const amount = ethers.parseEther("1"); // 1 BNB

      // 二级奖励: 1 BNB * 20% * 25% = 0.05 BNB = 50 积分
      const bnbReward = amount * 2000n * 2500n / 10000n / 10000n;
      const expectedPoints = bnbReward * 1000n / ethers.parseEther("1"); // 50

      const tx = await referral.connect(user3).triggerReward(amount);
      const receipt = await tx.wait();

      // 找到二级推荐的 RewardCalculated 事件
      const events = receipt.logs.filter(
        log => log.fragment && log.fragment.name === "RewardCalculated"
      );

      const l2Event = events.find(e => e.args.level === 2n);
      expect(l2Event).to.not.be.undefined;
      expect(l2Event.args.purchaser).to.equal(user3.address);
      expect(l2Event.args.referrer).to.equal(user1.address);
      expect(l2Event.args.purchaseAmount).to.equal(amount);
      expect(l2Event.args.pointsAmount).to.equal(expectedPoints);
      expect(l2Event.args.level).to.equal(2);
    });

    it("积分计算应该正确", async function () {
      const amount = ethers.parseEther("2"); // 2 BNB

      const tx = await referral.connect(user3).triggerReward(amount);
      const receipt = await tx.wait();

      // 找到所有 RewardCalculated 事件
      const events = receipt.logs.filter(
        log => log.fragment && log.fragment.name === "RewardCalculated"
      );

      expect(events.length).to.equal(2); // 一级和二级

      // 一级: 2 BNB * 15% = 0.3 BNB = 300 积分
      expect(events[0].args.pointsAmount).to.equal(300n);

      // 二级: 2 BNB * 5% = 0.1 BNB = 100 积分
      expect(events[1].args.pointsAmount).to.equal(100n);
    });
  });

  describe("v2.0 getReferralTree 测试", function () {
    it("应该正确返回推荐链", async function () {
      // 建立推荐链: user1 ← user2 ← user3 ← user4
      await referral.connect(user2).bindReferrer(user1.address);
      await referral.connect(user3).bindReferrer(user2.address);
      await referral.connect(user4).bindReferrer(user3.address);

      const tree = await referral.getReferralTree(user4.address);

      expect(tree.length).to.equal(3);
      expect(tree[0]).to.equal(user3.address); // 一级推荐人
      expect(tree[1]).to.equal(user2.address); // 二级推荐人
      expect(tree[2]).to.equal(user1.address); // 三级推荐人
    });

    it("没有推荐人应该返回空数组", async function () {
      const tree = await referral.getReferralTree(user1.address);
      expect(tree.length).to.equal(0);
    });

    it("只有一级推荐人", async function () {
      await referral.connect(user2).bindReferrer(user1.address);

      const tree = await referral.getReferralTree(user2.address);
      expect(tree.length).to.equal(1);
      expect(tree[0]).to.equal(user1.address);
    });
  });

  describe("v2.0 批量查询优化测试", function () {
    beforeEach(async function () {
      // 建立推荐关系
      await referral.connect(user2).bindReferrer(user1.address);
      await referral.connect(user3).bindReferrer(user1.address);

      // 触发奖励
      const amount = ethers.parseEther("1");
      await referral.connect(user2).triggerReward(amount);
    });

    it("应该返回活跃状态信息", async function () {
      const users = [user1.address, user2.address, user3.address];
      const [
        referrers,
        rewards,
        referredCounts,
        lastActiveTimes,
        activeStatuses
      ] = await referral.batchGetUserInfo(users);

      expect(lastActiveTimes.length).to.equal(3);
      expect(activeStatuses.length).to.equal(3);

      // user1 和 user2 应该是活跃的
      expect(activeStatuses[0]).to.be.true; // user1 (获得奖励时被更新)
      expect(activeStatuses[1]).to.be.true; // user2 (触发奖励时被更新)
    });

    it("不活跃用户应该正确标记", async function () {
      // 时间前进 31 天
      await time.increase(31 * 24 * 60 * 60);

      const users = [user1.address, user2.address];
      const [,,, , activeStatuses] = await referral.batchGetUserInfo(users);

      expect(activeStatuses[0]).to.be.false;
      expect(activeStatuses[1]).to.be.false;
    });
  });

  describe("v2.0 无 payable 测试", function () {
    it("triggerReward 不应该接受 BNB", async function () {
      await referral.connect(user2).bindReferrer(user1.address);

      const amount = ethers.parseEther("1");

      // 调用时不发送 BNB（v2.0 不再需要）
      await expect(referral.connect(user2).triggerReward(amount))
        .to.not.be.reverted;
    });

    it("triggerReward 应该返回计算的总积分", async function () {
      // 建立推荐关系: user1 ← user2 ← user3
      await referral.connect(user2).bindReferrer(user1.address);
      await referral.connect(user3).bindReferrer(user2.address);

      const amount = ethers.parseEther("1"); // 1 BNB

      // 总积分 = 150 (一级) + 50 (二级) = 200
      const totalPoints = await referral.connect(user3).triggerReward.staticCall(amount);
      expect(totalPoints).to.equal(200n);
    });
  });
});
