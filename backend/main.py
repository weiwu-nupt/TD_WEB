#!/usr/bin/env python3
# main.py - 主入口文件
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 配置日志
from utils.logger import setup_logger
logger = setup_logger(__name__)

# 导入配置
from config import CONFIG

# 导入UDP类
from udp_receiver import UDPReceiver
from udp_sender import UDPSender

# 导入API路由
from api import udp_routes, parameter_routes, doppler_routes, lora_routes


# 创建全局实例
udp_receiver = UDPReceiver()
udp_sender = UDPSender()

# 定义 lifespan 事件处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 60)
    logger.info("正在启动地面检测系统后端...")
    logger.info(f"配置信息: {CONFIG}")
    logger.info("=" * 60)
    
    # 启动默认接收端口
    success = udp_receiver.start(CONFIG["local_ip"], CONFIG["udp_receive_port"])

    if success:
        logger.info("✓ UDP接收服务启动成功")
    else:
        logger.error("✗ UDP接收服务启动失败")
    
    logger.info("=" * 60)
    
    yield  # 应用运行中
    
    # 关闭时执行
    logger.info("=" * 60)
    logger.info("正在关闭地面检测系统后端...")
    udp_receiver.stop()
    logger.info("✓ UDP接收服务已关闭")
    logger.info("=" * 60)

# FastAPI应用 - 使用 lifespan 参数
app = FastAPI(
    title="地面检测系统后端", 
    version="2.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{CONFIG['vue_dev_port']}", 
        f"http://127.0.0.1:{CONFIG['vue_dev_port']}"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注入依赖到路由模块
udp_routes.init_udp_objects(udp_receiver, udp_sender)
parameter_routes.init_sender(udp_sender)
doppler_routes.init_sender(udp_sender)
lora_routes.init_sender(udp_sender)

# 注册路由
app.include_router(udp_routes.router)
app.include_router(parameter_routes.router)
app.include_router(doppler_routes.router)
app.include_router(lora_routes.router)

# 根路由
@app.get("/")
async def root():
    return {
        "message": "地面检测系统后端运行中", 
        "version": "2.0.0",
        "config": CONFIG
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=CONFIG["backend_port"], 
        log_level="info"
    )