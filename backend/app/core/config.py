"""
应用配置管理
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "RWA Referral System"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # 数据库配置
    DATABASE_URL: str = "postgresql://rocky243@localhost:5432/rwa_referral"

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Web3配置
    BSC_NETWORK: str = "testnet"  # testnet | mainnet
    BSC_TESTNET_RPC_URL: str = "https://data-seed-prebsc-1-s1.binance.org:8545"
    BSC_MAINNET_RPC_URL: str = "https://bsc-dataseed1.binance.org"
    BSC_TESTNET_CHAIN_ID: int = 97
    BSC_MAINNET_CHAIN_ID: int = 56
    REFERRAL_CONTRACT_ADDRESS: str = "0x0000000000000000000000000000000000000000"

    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # JWT配置
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # 推荐系统配置
    LEVEL_1_BONUS_RATE: int = 15  # 一级推荐奖励 15%
    LEVEL_2_BONUS_RATE: int = 5   # 二级推荐奖励 5%
    INACTIVE_DAYS: int = 30       # 不活跃天数

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """解析CORS origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def bsc_rpc_url(self) -> str:
        """获取当前网络的RPC URL"""
        if self.BSC_NETWORK == "mainnet":
            return self.BSC_MAINNET_RPC_URL
        return self.BSC_TESTNET_RPC_URL

    @property
    def bsc_chain_id(self) -> int:
        """获取当前网络的Chain ID"""
        if self.BSC_NETWORK == "mainnet":
            return self.BSC_MAINNET_CHAIN_ID
        return self.BSC_TESTNET_CHAIN_ID

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略.env文件中未定义的字段


# 创建全局settings实例
settings = Settings()
