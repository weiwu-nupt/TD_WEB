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
from config import CONFIG, SystemMode, current_mode

# 导入UDP类
from udp_receiver import UDPReceiver
from udp_sender import UDPSender

# 🔧 导入虚实融合监控器
from virtual_monitor import VirtualMonitor

# 导入API路由
from api import parameter_routes, lora_routes, mode_routes, virtual_routes


# 创建全局实例
udp_receiver = UDPReceiver()
udp_sender = UDPSender()

# 🔧 创建虚实融合监控器实例
virtual_monitor = None

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
    
    # 🔧 停止虚实融合监控器
    if virtual_monitor:
        virtual_monitor.stop()
        logger.info("✓ VirtualMonitor 已关闭")
    
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
from frame_processor import init_sender as init_frame_processor_sender
# 注入依赖到路由模块
parameter_routes.init_sender(udp_sender)
lora_routes.init_sender(udp_sender)
mode_routes.init_receiver(udp_receiver)  
init_frame_processor_sender(udp_sender)

# 🔧 注入虚实融合监控器到模式路由
mode_routes.init_virtual_monitor(lambda: virtual_monitor)

# 注册路由
app.include_router(parameter_routes.router)
app.include_router(lora_routes.router)
app.include_router(mode_routes.router)  
app.include_router(virtual_routes.router)

# 根路由
@app.get("/")
async def root():
    monitor_status = virtual_monitor.get_status() if virtual_monitor else None

    return {
        "message": "地面检测系统后端运行中", 
        "version": "2.0.0",
        "config": CONFIG,
        "current_mode": current_mode["mode"],
        "virtual_monitor": monitor_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=CONFIG["backend_port"], 
        log_level="info"
    )