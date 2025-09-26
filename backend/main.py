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
import struct
from datetime import datetime
from collections import deque
import asyncio
from typing import Optional

# 添加消息队列
message_queue = deque(maxlen=4096)

def parse_message_frame(data: bytes) -> Optional[dict]:
    """解析消息帧"""
    try:
        if len(data) < 9:  # 最小长度：1+4+4 = 9字节
            return None
        
        # 解析帧头
        frame_type = data[0]
        
        # 解析接收时间戳（秒+毫秒）
        timestamp_bytes = data[1:9]
        seconds = struct.unpack('>H', timestamp_bytes[0:2])[0]  # 大端序，2字节
        milliseconds = struct.unpack('>H', timestamp_bytes[2:4])[0]  # 大端序，2字节
        
        # 第二个时间戳
        seconds2 = struct.unpack('>H', timestamp_bytes[4:6])[0]
        milliseconds2 = struct.unpack('>H', timestamp_bytes[6:8])[0]
        
        # 数据包内容
        payload = data[9:] if len(data) > 9 else b''
        
        # 计算完整时间戳（转换为毫秒）
        timestamp_ms = seconds * 1000 + milliseconds
        timestamp_ms2 = seconds2 * 1000 + milliseconds2
        
        return {
            "frame_type": frame_type,
            "timestamp1": timestamp_ms,
            "timestamp2": timestamp_ms2,
            "payload": payload.hex() if payload else "",
            "payload_length": len(payload),
            "raw_data": data.hex()
        }
    except Exception as e:
        logger.error(f"解析消息帧失败: {e}")
        return None

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
            
            # 解析消息帧
            parsed_msg = parse_message_frame(data)
            
            if parsed_msg:
                # 添加接收信息
                parsed_msg.update({
                    "source_ip": addr[0],
                    "source_port": addr[1],
                    "dest_port": self.current_port,
                    "receive_time": datetime.now().isoformat(),
                    "direction": "receive"
                })
                
                # 添加到消息队列
                message_queue.append(parsed_msg)
                
                logger.info(f"收到结构化消息 [{addr[0]}:{addr[1]}] -> [127.0.0.1:{self.current_port}]: "
                           f"帧类型={parsed_msg['frame_type']}, "
                           f"时间戳1={parsed_msg['timestamp1']}ms, "
                           f"时间戳2={parsed_msg['timestamp2']}ms, "
                           f"数据长度={parsed_msg['payload_length']}")
            else:
                # 原始消息处理（兼容性）
                message = data.decode('utf-8', errors='ignore')
                logger.info(f"收到UDP消息 [{addr[0]}:{addr[1]}] -> [127.0.0.1:{self.current_port}]: {message}")
                
        except socket.timeout:
            continue
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

# UDP发送器
class UDPSender:

    @staticmethod
    def send_message(message: str, target_ip: str = "127.0.0.1", target_port: int = None):
        """发送UDP消息"""
        try:
            if target_port is None:
                target_port = current_config["receivePort"]
        
            # 创建标准帧格式的测试消息
            frame_type = 0x01  # 测试帧类型
        
            # 当前时间戳（秒+毫秒）
            import time
            current_time = time.time()
            seconds = int(current_time) & 0xFFFF  # 取低16位
            milliseconds = int((current_time % 1) * 1000) & 0xFFFF
        
            # 第二个时间戳（稍微延后1ms）
            seconds2 = seconds
            milliseconds2 = (milliseconds + 1) & 0xFFFF
        
            # 构建帧数据
            frame_data = struct.pack('>BHHHH', 
                                    frame_type,      # 帧类型 1字节
                                    seconds,         # 时间戳1秒 2字节
                                    milliseconds,    # 时间戳1毫秒 2字节
                                    seconds2,        # 时间戳2秒 2字节
                                    milliseconds2)   # 时间戳2毫秒 2字节
        
            # 添加消息内容作为payload
            payload = message.encode('utf-8')
            full_message = frame_data + payload
        
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('127.0.0.1', 0))
                local_port = sock.getsockname()[1]
            
                sock.sendto(full_message, (target_ip, target_port))
                logger.info(f"发送标准帧UDP消息 [127.0.0.1:{local_port}] -> [{target_ip}:{target_port}]: "
                           f"帧类型={frame_type}, 载荷长度={len(payload)}")
            
                return True, local_port, target_port
        except Exception as e:
            logger.error(f"发送UDP消息失败: {e}")
            return False, None, None

    def get_status(self):
        """获取接收器状态"""
        return {
            "running": self.running,
            "port": self.current_port,
            "thread_alive": self.thread.is_alive() if self.thread else False
    }

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

@app.get("/api/udp/messages")
async def get_messages(limit: int = 50):
    """获取最近的消息"""
    try:
        # 获取最新的消息
        recent_messages = list(message_queue)[-limit:] if message_queue else []
        
        return {
            "success": True,
            "data": {
                "messages": recent_messages,
                "total_count": len(message_queue),
                "queue_size": len(recent_messages)
            }
        }
    except Exception as e:
        logger.error(f"获取消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/udp/messages")
async def clear_messages():
    """清空消息队列"""
    try:
        message_queue.clear()
        return {
            "success": True,
            "message": "消息队列已清空"
        }
    except Exception as e:
        logger.error(f"清空消息队列失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=CONFIG["backend_port"], log_level="info")