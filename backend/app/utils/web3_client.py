"""
Web3客户端工具类
提供区块链连接、合约交互等功能
"""

import json
import os
from pathlib import Path
from typing import Optional

from web3 import Web3
from web3.contract import Contract
from loguru import logger

# Web3.py v6兼容性：POA中间件导入
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    # 兼容旧版本
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware


class Web3Client:
    """Web3客户端单例类"""

    _instance: Optional['Web3Client'] = None

    def __init__(
        self,
        rpc_url: str,
        chain_id: int,
        contract_address: str,
        contract_abi_path: Optional[str] = None
    ):
        """
        初始化Web3客户端

        Args:
            rpc_url: 区块链RPC节点URL
            chain_id: 链ID (97=BSC测试网, 56=BSC主网)
            contract_address: RWAReferral合约地址
            contract_abi_path: 合约ABI文件路径（可选）
        """
        self.rpc_url = rpc_url
        self.chain_id = chain_id
        self.contract_address = Web3.to_checksum_address(contract_address)

        # 初始化Web3实例
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        # 添加PoA中间件（BSC需要）
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # 验证连接
        if not self.w3.is_connected():
            raise ConnectionError(f"无法连接到区块链节点: {rpc_url}")

        logger.info(f"✅ 成功连接到区块链节点: {rpc_url}")
        logger.info(f"📊 链ID: {chain_id}, 当前区块: {self.w3.eth.block_number}")

        # 加载合约ABI
        if contract_abi_path is None:
            contract_abi_path = Path(__file__).parent / "RWAReferral_ABI.json"

        with open(contract_abi_path, 'r') as f:
            self.contract_abi = json.load(f)

        # 创建合约实例
        self.contract: Contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )

        logger.info(f"📝 RWAReferral合约地址: {self.contract_address}")

    @classmethod
    def get_instance(
        cls,
        rpc_url: Optional[str] = None,
        chain_id: Optional[int] = None,
        contract_address: Optional[str] = None,
        contract_abi_path: Optional[str] = None
    ) -> 'Web3Client':
        """
        获取Web3Client单例实例

        Args:
            rpc_url: 区块链RPC节点URL
            chain_id: 链ID
            contract_address: 合约地址
            contract_abi_path: 合约ABI路径

        Returns:
            Web3Client实例
        """
        if cls._instance is None:
            if not all([rpc_url, chain_id, contract_address]):
                raise ValueError("首次调用必须提供所有参数")

            cls._instance = cls(
                rpc_url=rpc_url,
                chain_id=chain_id,
                contract_address=contract_address,
                contract_abi_path=contract_abi_path
            )

        return cls._instance

    def get_latest_block(self) -> int:
        """获取最新区块号"""
        return self.w3.eth.block_number

    def get_transaction_receipt(self, tx_hash: str):
        """获取交易回执"""
        return self.w3.eth.get_transaction_receipt(tx_hash)

    def get_logs(
        self,
        event_name: str,
        from_block: int,
        to_block: int | str = 'latest'
    ) -> list:
        """
        获取指定事件的日志

        Args:
            event_name: 事件名称 (如 "RewardCalculated")
            from_block: 起始区块
            to_block: 结束区块 (默认'latest')

        Returns:
            事件日志列表
        """
        event = getattr(self.contract.events, event_name)

        logs = event.get_logs(
            fromBlock=from_block,
            toBlock=to_block
        )

        return logs

    def decode_event(self, log):
        """
        解码事件日志

        Args:
            log: 原始日志对象

        Returns:
            解码后的事件数据
        """
        # Web3.py已经自动解码，直接返回args
        return {
            'event_name': log.event,
            'block_number': log.blockNumber,
            'transaction_hash': log.transactionHash.hex(),
            'log_index': log.logIndex,
            'args': dict(log.args)
        }

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.w3.is_connected()

    def get_contract_function(self, function_name: str):
        """
        获取合约函数

        Args:
            function_name: 函数名称

        Returns:
            合约函数对象
        """
        return getattr(self.contract.functions, function_name)
