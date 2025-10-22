"""
FastAPI主应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.api.api import api_router
from app.utils import redis_client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="RWA Launchpad社交裂变引流系统API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """根路径 - 健康检查"""
    return {
        "status": "running",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: 实际检查数据库连接
        "blockchain": "connected"  # TODO: 实际检查区块链连接
    }


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"🚀 {settings.APP_NAME} starting...")
    logger.info(f"📝 API文档: http://localhost:8000/docs")
    logger.info(f"🔗 BSC网络: {settings.BSC_NETWORK}")
    logger.info(f"📍 合约地址: {settings.REFERRAL_CONTRACT_ADDRESS}")

    # 初始化Redis连接
    try:
        await redis_client.connect()
        logger.info("✅ Redis连接初始化成功")
    except Exception as e:
        logger.warning(f"⚠️  Redis连接初始化失败（将在无缓存模式下运行）: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info(f"👋 {settings.APP_NAME} shutting down...")

    # 关闭Redis连接
    try:
        await redis_client.disconnect()
    except Exception as e:
        logger.warning(f"⚠️  Redis断开连接时出错: {e}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
