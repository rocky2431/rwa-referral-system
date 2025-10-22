// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title RWAReferral
 * @dev RWA Launchpad推荐奖励合约
 *
 * 基于ThunderCore Referral逻辑，重写为Solidity 0.8.19版本
 *
 * 奖励机制:
 * - 总奖励率: 20%
 * - 一级推荐: 15% (总奖励的75%)
 * - 二级推荐: 5% (总奖励的25%)
 *
 * 活跃规则:
 * - 用户30天未活跃将不再获得奖励
 */
contract RWAReferral {
    // ==================== 结构体 ====================

    struct Account {
        address payable referrer;      // 推荐人地址
        uint256 reward;                // 累计获得的奖励
        uint256 referredCount;         // 推荐人数
        uint256 lastActiveTimestamp;   // 最后活跃时间
    }

    // ==================== 状态变量 ====================

    /// @notice 基础单位 (用于百分比计算)
    uint256 public constant DECIMALS = 10000;

    /// @notice 总推荐奖励率 (20%)
    uint256 public constant REFERRAL_BONUS = 2000;

    /// @notice 用户不活跃时间阈值 (30天)
    uint256 public constant SECONDS_UNTIL_INACTIVE = 30 days;

    /// @notice 一级推荐奖励占比 (75% = 15%)
    uint256 public constant LEVEL_1_RATE = 7500;

    /// @notice 二级推荐奖励占比 (25% = 5%)
    uint256 public constant LEVEL_2_RATE = 2500;

    /// @notice 最大推荐层级
    uint256 public constant MAX_LEVEL = 2;

    /// @notice BNB 到积分兑换率 (1 BNB = 1000 积分, 以wei计算)
    /// @dev 1 BNB = 10^18 wei = 1000 积分, 所以 1 wei = 1000 / 10^18 积分
    uint256 public constant POINTS_PER_BNB = 1000;

    /// @notice 所有账户信息
    mapping(address => Account) public accounts;

    /// @notice 合约所有者
    address public owner;

    // ==================== 事件 ====================

    /// @notice 推荐人绑定成功事件
    event RegisteredReferrer(address indexed referee, address indexed referrer);

    /// @notice 推荐人绑定失败事件
    event RegisteredReferrerFailed(address indexed referee, address indexed referrer, string reason);

    /// @notice 奖励计算完成事件 (v2.0 - 用于链下积分发放)
    /// @param purchaser 购买者地址
    /// @param referrer 获得奖励的推荐人地址
    /// @param purchaseAmount 购买金额 (BNB wei)
    /// @param pointsAmount 计算出的积分数量
    /// @param level 推荐层级 (1=一级, 2=二级)
    /// @param timestamp 事件时间戳
    event RewardCalculated(
        address indexed purchaser,
        address indexed referrer,
        uint256 purchaseAmount,
        uint256 pointsAmount,
        uint256 level,
        uint256 timestamp
    );

    /// @notice 用户购买事件 (触发奖励计算)
    /// @param user 购买者地址
    /// @param amount 购买金额 (BNB wei)
    /// @param timestamp 购买时间戳
    event UserPurchased(
        address indexed user,
        uint256 amount,
        uint256 timestamp
    );

    /// @notice 用户活跃时间更新事件
    event UpdatedUserLastActiveTime(address indexed user, uint256 timestamp);

    /// @notice 用户活跃状态变更事件
    /// @param user 用户地址
    /// @param isActive 是否活跃
    /// @param timestamp 时间戳
    event UserActivityStatusChanged(
        address indexed user,
        bool isActive,
        uint256 timestamp
    );

    // ==================== 修饰器 ====================

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this");
        _;
    }

    // ==================== 构造函数 ====================

    constructor() {
        owner = msg.sender;
    }

    // ==================== 外部函数 ====================

    /**
     * @notice 绑定推荐人
     * @param referrer 推荐人地址
     * @return 是否绑定成功
     */
    function bindReferrer(address payable referrer) external returns (bool) {
        // 验证推荐人地址
        if (referrer == address(0)) {
            emit RegisteredReferrerFailed(msg.sender, referrer, "Invalid referrer address");
            return false;
        }

        // 不能自己推荐自己
        if (msg.sender == referrer) {
            emit RegisteredReferrerFailed(msg.sender, referrer, "Cannot refer yourself");
            return false;
        }

        // 已经有推荐人了
        if (accounts[msg.sender].referrer != address(0)) {
            emit RegisteredReferrerFailed(msg.sender, referrer, "Already has referrer");
            return false;
        }

        // 检查是否会形成循环推荐
        if (_wouldCreateCycle(msg.sender, referrer)) {
            emit RegisteredReferrerFailed(msg.sender, referrer, "Would create referral cycle");
            return false;
        }

        // 绑定推荐关系
        accounts[msg.sender].referrer = referrer;
        accounts[referrer].referredCount++;

        // 更新活跃时间
        _updateActiveTimestamp(msg.sender);
        _updateActiveTimestamp(referrer);

        emit RegisteredReferrer(msg.sender, referrer);

        return true;
    }

    /**
     * @notice 触发推荐奖励计算 (v2.0 - 仅发出事件，由后端监听并发放积分)
     * @param purchaseAmount 购买金额 (BNB wei)
     * @return totalPointsCalculated 总共计算的积分数量
     */
    function triggerReward(uint256 purchaseAmount) external returns (uint256) {
        require(purchaseAmount > 0, "Purchase amount must be greater than 0");

        // 发出购买事件
        emit UserPurchased(msg.sender, purchaseAmount, block.timestamp);

        uint256 totalPointsCalculated = 0;
        address current = accounts[msg.sender].referrer;
        uint256[] memory rates = _getLevelRates();

        // 遍历推荐人链,计算奖励积分
        for (uint256 i = 0; i < MAX_LEVEL && current != address(0); i++) {
            // 检查推荐人是否活跃
            if (_isActive(current)) {
                // 计算BNB奖励金额
                uint256 bnbReward = (purchaseAmount * REFERRAL_BONUS * rates[i]) / (DECIMALS * DECIMALS);

                if (bnbReward > 0) {
                    // 计算积分数量: (bnbReward in wei * POINTS_PER_BNB) / 1 ether
                    uint256 pointsAmount = (bnbReward * POINTS_PER_BNB) / 1 ether;

                    // 更新累计奖励 (保留统计，单位仍为wei)
                    accounts[current].reward += bnbReward;
                    totalPointsCalculated += pointsAmount;

                    // 发出奖励计算事件 (后端监听此事件发放积分)
                    emit RewardCalculated(
                        msg.sender,
                        current,
                        purchaseAmount,
                        pointsAmount,
                        i + 1,
                        block.timestamp
                    );
                }
            }

            // 移动到下一级推荐人
            current = accounts[current].referrer;
        }

        // 更新用户活跃时间
        _updateActiveTimestamp(msg.sender);

        return totalPointsCalculated;
    }

    /**
     * @notice 查询用户完整信息
     * @param user 用户地址
     * @return referrer 推荐人地址
     * @return reward 累计获得的奖励
     * @return referredCount 推荐人数
     * @return lastActiveTimestamp 最后活跃时间
     */
    function getUserInfo(address user)
        external
        view
        returns (
            address referrer,
            uint256 reward,
            uint256 referredCount,
            uint256 lastActiveTimestamp
        )
    {
        Account memory account = accounts[user];
        return (
            account.referrer,
            account.reward,
            account.referredCount,
            account.lastActiveTimestamp
        );
    }

    /**
     * @notice 批量查询用户信息 (优化版 - v2.0)
     * @param users 用户地址数组
     * @return referrers 推荐人地址数组
     * @return rewards 累计奖励数组
     * @return referredCounts 推荐人数数组
     * @return lastActiveTimes 最后活跃时间数组
     * @return activeStatuses 活跃状态数组
     */
    function batchGetUserInfo(address[] calldata users)
        external
        view
        returns (
            address[] memory referrers,
            uint256[] memory rewards,
            uint256[] memory referredCounts,
            uint256[] memory lastActiveTimes,
            bool[] memory activeStatuses
        )
    {
        uint256 length = users.length;
        referrers = new address[](length);
        rewards = new uint256[](length);
        referredCounts = new uint256[](length);
        lastActiveTimes = new uint256[](length);
        activeStatuses = new bool[](length);

        for (uint256 i = 0; i < length; i++) {
            Account memory account = accounts[users[i]];
            referrers[i] = account.referrer;
            rewards[i] = account.reward;
            referredCounts[i] = account.referredCount;
            lastActiveTimes[i] = account.lastActiveTimestamp;
            activeStatuses[i] = _isActive(users[i]);
        }

        return (referrers, rewards, referredCounts, lastActiveTimes, activeStatuses);
    }

    /**
     * @notice 检查用户是否活跃
     */
    function isUserActive(address user) external view returns (bool) {
        return _isActive(user);
    }

    /**
     * @notice 更新用户活跃时间
     */
    function updateUserActivity() external {
        _updateActiveTimestamp(msg.sender);
    }

    /**
     * @notice 获取推荐配置信息
     */
    function getReferralConfig()
        external
        pure
        returns (
            uint256 decimals,
            uint256 referralBonus,
            uint256 secondsUntilInactive,
            uint256 level1Rate,
            uint256 level2Rate
        )
    {
        return (
            DECIMALS,
            REFERRAL_BONUS,
            SECONDS_UNTIL_INACTIVE,
            LEVEL_1_RATE,
            LEVEL_2_RATE
        );
    }

    /**
     * @notice 检查是否有推荐人
     */
    function hasReferrer(address user) external view returns (bool) {
        return accounts[user].referrer != address(0);
    }

    /**
     * @notice 获取用户的推荐链 (向上追溯到根节点)
     * @param user 用户地址
     * @return referralTree 推荐链地址数组 [直接推荐人, 二级推荐人, ...]
     * @dev 最多追溯10层，避免gas消耗过高
     */
    function getReferralTree(address user) external view returns (address[] memory) {
        address[] memory tree = new address[](10);
        uint256 count = 0;
        address current = accounts[user].referrer;

        // 向上追溯推荐链
        while (current != address(0) && count < 10) {
            tree[count] = current;
            count++;
            current = accounts[current].referrer;
        }

        // 创建实际长度的数组
        address[] memory result = new address[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = tree[i];
        }

        return result;
    }

    /**
     * @notice 获取用户的下级推荐人列表 (需要遍历所有用户，gas消耗高，仅供查询)
     * @dev 此函数仅用于链下查询，不建议在链上调用
     * @param referrer 推荐人地址
     * @param startIndex 起始索引
     * @param limit 返回数量限制
     * @return referees 下级推荐人地址数组
     * @return hasMore 是否还有更多数据
     */
    function getDirectReferees(
        address referrer,
        uint256 startIndex,
        uint256 limit
    ) external view returns (address[] memory referees, bool hasMore) {
        // 注意：此函数需要遍历mapping，实际应由后端索引事件实现
        // 这里仅作为接口定义，实现留空
        referees = new address[](0);
        hasMore = false;
        return (referees, hasMore);
    }

    // ==================== 内部函数 ====================

    /**
     * @dev 检查是否会形成循环推荐
     */
    function _wouldCreateCycle(address user, address referrer) internal view returns (bool) {
        address current = referrer;
        for (uint256 i = 0; i < 10 && current != address(0); i++) {
            if (current == user) {
                return true;
            }
            current = accounts[current].referrer;
        }
        return false;
    }

    /**
     * @dev 检查用户是否活跃
     */
    function _isActive(address user) internal view returns (bool) {
        uint256 lastActive = accounts[user].lastActiveTimestamp;
        if (lastActive == 0) {
            return false;
        }
        return (block.timestamp - lastActive) < SECONDS_UNTIL_INACTIVE;
    }

    /**
     * @dev 更新用户活跃时间
     */
    function _updateActiveTimestamp(address user) internal {
        accounts[user].lastActiveTimestamp = block.timestamp;
        emit UpdatedUserLastActiveTime(user, block.timestamp);
    }

    /**
     * @dev 获取各级推荐奖励比例
     */
    function _getLevelRates() internal pure returns (uint256[] memory) {
        uint256[] memory rates = new uint256[](MAX_LEVEL);
        rates[0] = LEVEL_1_RATE; // 一级 75%
        rates[1] = LEVEL_2_RATE; // 二级 25%
        return rates;
    }

    // ==================== 紧急函数 ====================

    /**
     * @notice 提取合约余额 (仅所有者)
     */
    function withdraw() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    /**
     * @notice 接收BNB
     */
    receive() external payable {}
}
