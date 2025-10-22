"""
Web3客户端 - 与智能合约交互
"""
from web3 import Web3
from typing import Optional, Dict, Any
import logging

from app.core.config import settings

# Web3.py v6兼容性：POA中间件导入
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware

logger = logging.getLogger(__name__)

# RWAReferral合约ABI (从编译产物中提取)
REFERRAL_ABI = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "level", "type": "uint256"}
        ],
        "name": "PaidReferral",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "referee", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "referrer", "type": "address"}
        ],
        "name": "RegisteredReferrer",
        "type": "event"
    },
    {
        "inputs": [{"internalType": "address payable", "name": "referrer", "type": "address"}],
        "name": "bindReferrer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "getUserInfo",
        "outputs": [
            {"internalType": "address", "name": "referrer", "type": "address"},
            {"internalType": "uint256", "name": "reward", "type": "uint256"},
            {"internalType": "uint256", "name": "referredCount", "type": "uint256"},
            {"internalType": "uint256", "name": "lastActiveTimestamp", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address[]", "name": "users", "type": "address[]"}],
        "name": "batchGetUserInfo",
        "outputs": [
            {"internalType": "address[]", "name": "referrers", "type": "address[]"},
            {"internalType": "uint256[]", "name": "rewards", "type": "uint256[]"},
            {"internalType": "uint256[]", "name": "referredCounts", "type": "uint256[]"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "isUserActive",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "hasReferrer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getReferralConfig",
        "outputs": [
            {"internalType": "uint256", "name": "decimals", "type": "uint256"},
            {"internalType": "uint256", "name": "referralBonus", "type": "uint256"},
            {"internalType": "uint256", "name": "secondsUntilInactive", "type": "uint256"},
            {"internalType": "uint256", "name": "level1Rate", "type": "uint256"},
            {"internalType": "uint256", "name": "level2Rate", "type": "uint256"}
        ],
        "stateMutability": "pure",
        "type": "function"
    }
]


class Web3Client:
    """Web3客户端类"""

    def __init__(self):
        """初始化Web3连接"""
        self.w3 = Web3(Web3.HTTPProvider(settings.bsc_rpc_url))

        # 为BSC网络添加POA middleware
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # 验证连接
        if not self.w3.is_connected():
            logger.error("❌ 无法连接到BSC网络")
            raise ConnectionError("Failed to connect to BSC network")

        logger.info(f"✅ 已连接到BSC {settings.BSC_NETWORK}")
        logger.info(f"📍 当前区块: {self.w3.eth.block_number}")

        # 初始化合约
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(settings.REFERRAL_CONTRACT_ADDRESS),
            abi=REFERRAL_ABI
        )

    async def get_user_info(self, address: str) -> Dict[str, Any]:
        """
        查询用户信息

        Args:
            address: 用户钱包地址

        Returns:
            用户信息字典
        """
        try:
            checksum_address = Web3.to_checksum_address(address)
            result = self.contract.functions.getUserInfo(checksum_address).call()

            return {
                "referrer": result[0],
                "reward": result[1],
                "referred_count": result[2],
                "last_active_timestamp": result[3]
            }
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            raise

    async def batch_get_user_info(self, addresses: list[str]) -> Dict[str, Any]:
        """
        批量查询用户信息

        Args:
            addresses: 用户钱包地址列表

        Returns:
            批量用户信息
        """
        try:
            checksum_addresses = [Web3.to_checksum_address(addr) for addr in addresses]
            result = self.contract.functions.batchGetUserInfo(checksum_addresses).call()

            return {
                "referrers": result[0],
                "rewards": result[1],
                "referred_counts": result[2]
            }
        except Exception as e:
            logger.error(f"批量获取用户信息失败: {e}")
            raise

    async def has_referrer(self, address: str) -> bool:
        """检查用户是否有推荐人"""
        try:
            checksum_address = Web3.to_checksum_address(address)
            return self.contract.functions.hasReferrer(checksum_address).call()
        except Exception as e:
            logger.error(f"检查推荐人失败: {e}")
            return False

    async def is_user_active(self, address: str) -> bool:
        """检查用户是否活跃"""
        try:
            checksum_address = Web3.to_checksum_address(address)
            return self.contract.functions.isUserActive(checksum_address).call()
        except Exception as e:
            logger.error(f"检查用户活跃状态失败: {e}")
            return False

    async def get_referral_config(self) -> Dict[str, int]:
        """获取推荐配置"""
        try:
            result = self.contract.functions.getReferralConfig().call()
            return {
                "decimals": result[0],
                "referral_bonus": result[1],
                "seconds_until_inactive": result[2],
                "level1_rate": result[3],
                "level2_rate": result[4]
            }
        except Exception as e:
            logger.error(f"获取推荐配置失败: {e}")
            raise

    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict]:
        """获取交易回执"""
        try:
            return self.w3.eth.get_transaction_receipt(tx_hash)
        except Exception as e:
            logger.error(f"获取交易回执失败: {e}")
            return None


# 创建全局Web3客户端实例
web3_client = Web3Client()
