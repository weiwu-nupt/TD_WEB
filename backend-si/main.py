from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 配置日志
from utils.logger import setup_logger
logger = setup_logger(__name__)

# 导入配置
from config import CONFIG, SystemMode, current_mode

from serial_communicator import SerialCommunicator

# 导入API路由
from api import parameter_routes, lora_routes, mode_routes, virtual_routes
from frame_processor import init_sender as init_frame_processor_sender # 导入放在这里

# 🔧 创建全局串口通信器实例
serial_comm = None

# 定义 lifespan 事件处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global serial_comm
    
    logger.info("=" * 60)
    logger.info("正在启动地面检测系统后端...")
    logger.info(f"配置信息: {CONFIG}")
    logger.info("=" * 60)
    
    # 🔧 启动串口通信（替代UDP）
    try:
        #"Linux": "/dev/ttyUSB0"  "Windows": "COM1","COM2..."
        serial_comm = SerialCommunicator(
            port=CONFIG["serial_port"],
            baudrate=CONFIG["serial_baudrate"]
        )
        
        if serial_comm.is_connected():
            serial_comm.start_receiving()
            logger.info("✓ 串口通信已启动（发送+接收）")
            
            # ==========================================
            # 关键修改：在这里注入依赖！确保 serial_comm 已实例化
            # ==========================================
            parameter_routes.init_sender(serial_comm)
            lora_routes.init_sender(serial_comm)
            virtual_routes.init_sender(serial_comm)
            mode_routes.init_receiver(serial_comm) 
            init_frame_processor_sender(serial_comm)
            logger.info("✓ 路由依赖注入完成")
            
        else:
            logger.error("✗ 串口连接失败")
    
    except Exception as e:
        logger.error(f"✗ 串口初始化失败: {e}")
    
    logger.info("=" * 60)
    
    yield  # 应用运行中
    
    # 🔧 停止串口通信
    if serial_comm:
        serial_comm.stop()
        logger.info("✓ 串口通信已关闭")
    
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

# --- 删除或注释掉原来在这里的 init_sender 调用 ---
# parameter_routes.init_sender(serial_comm)  <-- 这里删掉
# lora_routes.init_sender(serial_comm)       <-- 这里删掉
# virtual_routes.init_sender(serial_comm)    <-- 这里删掉
# mode_routes.init_receiver(serial_comm)     <-- 这里删掉
# init_frame_processor_sender(serial_comm)   <-- 这里删掉

# 注册路由
app.include_router(parameter_routes.router)
app.include_router(lora_routes.router)
app.include_router(mode_routes.router)  
app.include_router(virtual_routes.router)

# 根路由
@app.get("/")
async def root():
    return {
        "message": "地面检测系统后端运行中", 
        "version": "2.0.0",
        "config": CONFIG,
        "current_mode": current_mode["mode"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=CONFIG["backend_port"], 
        log_level="info"
    )