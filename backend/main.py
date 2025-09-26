#!/usr/bin/env python3
# main.py - 简化的UDP接收FastAPI后端
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import socket
import threading
import logging
import time
import json

# 读取配置文件
try:
    with open('../config.json', 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    # 默认配置
    CONFIG = {
        "backend_port": 8000,
        "udp_receive_port": 8002,
        "vue_dev_port": 5555
    }

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 应用
app = FastAPI(title="服务器", version="1.0.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{CONFIG['vue_dev_port']}", f"http://127.0.0.1:{CONFIG['vue_dev_port']}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class UDPConfig(BaseModel):
    receivePort: int

class UDPMessage(BaseModel):
    message: str
    target_ip: str = "127.0.0.1"

# UDP接收器类
class UDPReceiver:
    def __init__(self):
        self.socket = None
        self.thread = None
        self.running = False
        self.current_port = None
        
    def start(self, port: int):
        """启动UDP接收"""
        # 如果已经在运行，先停止
        if self.running:
            self.stop()
            
        try:
            # 创建UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('127.0.0.1', port))
            self.socket.settimeout(1.0)  # 1秒超时
            
            self.running = True
            self.current_port = port
            
            # 启动接收线程
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            
            logger.info(f"UDP接收器已启动，监听端口: {port}")
            return True
            
        except Exception as e:
            logger.error(f"启动UDP接收器失败: {e}")
            self.running = False
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def stop(self):
        """停止UDP接收"""
        if self.running:
            self.running = False
            
            if self.socket:
                self.socket.close()
                self.socket = None
            
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)
            
            logger.info(f"UDP接收器已停止 (端口: {self.current_port})")
            self.current_port = None
    
    def _receive_loop(self):
        """UDP接收循环"""
        while self.running and self.socket:
            try:
                data, addr = self.socket.recvfrom(1024)
                message = data.decode('utf-8', errors='ignore')
                
                # 记录接收到的消息
                logger.info(f"收到UDP消息 [{addr[0]}:{addr[1]}] -> [127.0.0.1:{self.current_port}]: {message}")
                
            except socket.timeout:
                continue  # 超时继续循环
            except Exception as e:
                if self.running:
                    logger.error(f"UDP接收错误: {e}")
                break
    
    def get_status(self):
        """获取接收器状态"""
        return {
            "running": self.running,
            "port": self.current_port,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }

# UDP发送器类（简化版）
class UDPSender:
    @staticmethod
    def send_message(message: str, target_ip: str = "127.0.0.1", target_port: int = None):
        """发送UDP消息"""
        try:
            # 如果没有指定目标端口，使用当前接收端口
            if target_port is None:
                target_port = current_config["receivePort"]
            
            # 创建临时socket发送消息
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                # 绑定到临时端口以获取本地端口号
                sock.bind(('127.0.0.1', 0))
                local_port = sock.getsockname()[1]
                
                sock.sendto(message.encode('utf-8'), (target_ip, target_port))
                logger.info(f"发送UDP消息 [127.0.0.1:{local_port}] -> [{target_ip}:{target_port}]: {message}")
                
                return True, local_port, target_port
        except Exception as e:
            logger.error(f"发送UDP消息失败: {e}")
            return False, None, None

# 全局实例
udp_receiver = UDPReceiver()
udp_sender = UDPSender()

# 存储当前配置
current_config = {
    "receivePort": CONFIG["udp_receive_port"]
}

# API路由
@app.get("/")
async def root():
    return {
        "message": "UDP接收服务运行中", 
        "version": "1.0.0",
        "config": CONFIG
    }

@app.get("/api/udp/config")
async def get_udp_config():
    """获取当前UDP配置"""
    return {
        "success": True,
        "data": current_config,
        "receiver_status": udp_receiver.get_status()
    }

@app.post("/api/udp/config")
async def update_udp_config(config: UDPConfig):
    """更新UDP端口配置"""
    try:
        # 更新全局配置
        current_config["receivePort"] = config.receivePort
        
        # 重启接收器到新端口
        success = udp_receiver.start(config.receivePort)
        
        if success:
            logger.info(f"UDP配置已更新 - 接收端口: {config.receivePort}")
            return {
                "success": True, 
                "message": f"UDP接收端口配置成功: {config.receivePort}",
                "data": current_config
            }
        else:
            raise HTTPException(status_code=500, detail="UDP接收器启动失败")
            
    except Exception as e:
        logger.error(f"更新UDP配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}")

@app.post("/api/udp/send")
async def send_udp_message(msg: UDPMessage):
    """发送UDP消息（测试用）"""
    try:
        success, local_port, target_port = udp_sender.send_message(msg.message, msg.target_ip)
        if success:
            return {
                "success": True, 
                "message": "UDP消息发送成功",
                "details": {
                    "from": f"{msg.target_ip}:{local_port}",
                    "to": f"{msg.target_ip}:{target_port}",
                    "data": msg.message
                }
            }
        else:
            raise HTTPException(status_code=500, detail="UDP消息发送失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/udp/status")
async def get_udp_status():
    """获取UDP服务状态"""
    return {
        "success": True,
        "data": {
            "config": current_config,
            "receiver": udp_receiver.get_status(),
            "system_config": CONFIG
        }
    }

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化UDP接收器"""
    logger.info("正在启动UDP接收服务...")
    logger.info(f"配置信息: {CONFIG}")
    
    # 启动默认接收端口
    udp_receiver.start(current_config["receivePort"])
    
    logger.info("UDP接收服务启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("正在关闭UDP接收服务...")
    udp_receiver.stop()
    logger.info("UDP接收服务已关闭")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=CONFIG["backend_port"], log_level="info")