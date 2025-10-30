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

from starlette.datastructures import Address

# 帧类型常量
FRAME_TYPE_BROADCAST = 0x01    # 广播帧
FRAME_TYPE_TIMESTAMP = 0x02    # 发送时间戳回传帧  
FRAME_TYPE_LINK_STATUS = 0x03  # 链路状态帧
FRAME_TYPE_FPGA = 0x05         # FPGA读写帧
FRAME_TYPE_LORA = 0x07         # LoRa收发帧


# FPGA操作相关模型
class FPGAOperation(BaseModel):
    """FPGA操作模型"""
    operation_type: int  # 0-读, 1-写
    operation_count: int  # 操作数目
    address: int  # 操作地址 (4字节)
    data: Optional[int] = None  # 操作数据 (4字节), 读操作时为None

# LoRa发送模型
class LoRaSendMessage(BaseModel):
    """LoRa发送消息模型"""
    timing_enable: int  # 0-不定时, 1-定时开启
    timing_time: int  # 定时时间 (4字节)
    data_content: str  # 数据内容

def process_broadcast_frame(parsed_msg: dict) -> dict:
    """处理广播帧 0x01"""
    # TODO: 实现广播帧处理逻辑
    processed_data = {
        "frame_name": "广播帧",
        "processing_result": "广播帧处理完成",
        "broadcast_info": {
            "broadcast_id": 1,
            "target_range": "全网",
            "priority": "normal"
        }
    }
    return processed_data

def process_timestamp_frame(parsed_msg: dict) -> dict:
    """处理发送时间戳回传帧 0x02"""
    # TODO: 实现时间戳回传帧处理逻辑
    processed_data = {
        "frame_name": "发送时间戳回传帧",
        "processing_result": "时间戳回传帧处理完成",
        "timestamp_info": {
            "original_timestamp": parsed_msg.get("timestamp1", 0),
            "return_timestamp": parsed_msg.get("timestamp2", 0),
            "delay_ms": abs(parsed_msg.get("timestamp2", 0) - parsed_msg.get("timestamp1", 0))
        }
    }
    return processed_data

def process_link_status_frame(parsed_msg: dict) -> dict:
    """处理链路状态帧 0x03"""
    # TODO: 实现链路状态帧处理逻辑
    processed_data = {
        "frame_name": "链路状态帧",
        "processing_result": "链路状态帧处理完成",
        "link_info": {
            "link_quality": "良好",
            "signal_strength": -60,
            "connection_status": "connected"
        }
    }
    return processed_data

def process_fpga_frame(parsed_msg: dict) -> dict:
    """处理FPGA读写帧 0x05"""
    try:
        payload = bytes.fromhex(parsed_msg.get("payload", ""))
        
        if len(payload) < 2:
            return {
                "frame_name": "FPGA操作帧",
                "processing_result": "数据长度不足",
                "error": "invalid_length"
            }
        
        operation_type = payload[0]  # 0-读, 1-写
        operation_count = payload[1]  # 操作数目
        
        operations = []
        offset = 2
        
        for i in range(operation_count):
            if operation_type == 0:  # 读操作
                if len(payload) < offset + 4:
                    break
                address = struct.unpack('>I', payload[offset:offset+4])[0]
                operations.append({
                    "type": "read",
                    "address": f"0x{address:08X}",
                    "address_decimal": address
                })
                offset += 4
            else:  # 写操作
                if len(payload) < offset + 8:
                    break
                address = struct.unpack('>I', payload[offset:offset+4])[0]
                data = struct.unpack('>I', payload[offset+4:offset+8])[0]
                operations.append({
                    "type": "write",
                    "address": f"0x{address:08X}",
                    "address_decimal": address,
                    "data": f"0x{data:08X}",
                    "data_decimal": data
                })
                offset += 8
        
        operation_name = "读操作" if operation_type == 0 else "写操作"
        
        processed_data = {
            "frame_name": "FPGA操作帧",
            "processing_result": f"FPGA{operation_name}解析完成",
            "fpga_info": {
                "operation_type": operation_type,
                "operation_name": operation_name,
                "operation_count": operation_count,
                "operations": operations,
                "parsed_count": len(operations)
            }
        }
        
        return processed_data
        
    except Exception as e:
        logger.error(f"处理FPGA帧时发生错误: {e}")
        return {
            "frame_name": "FPGA操作帧",
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }

def process_lora_frame(parsed_msg: dict) -> dict:
    """处理LoRa收发帧 0x07"""
    try:
        payload = bytes.fromhex(parsed_msg.get("payload", ""))
        direction = parsed_msg.get("direction", "receive")
        
        if direction == "send":
            # LoRa发送帧
            if len(payload) < 5:
                return {
                    "frame_name": "LoRa发送帧",
                    "processing_result": "数据长度不足",
                    "error": "invalid_length"
                }
            
            timing_enable = payload[0]
            timing_time = struct.unpack('>I', payload[1:5])[0]
            data_content = payload[5:].decode('utf-8', errors='ignore') if len(payload) > 5 else ""
            
            processed_data = {
                "frame_name": "LoRa发送帧",
                "processing_result": "LoRa发送帧解析完成",
                "lora_send_info": {
                    "timing_enable": timing_enable,
                    "timing_enabled": timing_enable == 1,
                    "timing_time": timing_time,
                    "timing_time_ms": timing_time,
                    "data_content": data_content,
                    "data_length": len(data_content),
                    "data_hex": payload[5:].hex() if len(payload) > 5 else ""
                }
            }
        else:
            # LoRa接收帧
            if len(payload) < 8:
                return {
                    "frame_name": "LoRa接收帧",
                    "processing_result": "数据长度不足",
                    "error": "invalid_length"
                }
            
            receive_timestamp = struct.unpack('>I', payload[0:4])[0]
            complete_timestamp = struct.unpack('>I', payload[4:8])[0]
            data_content = payload[8:].decode('utf-8', errors='ignore') if len(payload) > 8 else ""
            
            duration = complete_timestamp - receive_timestamp
            
            processed_data = {
                "frame_name": "LoRa接收帧",
                "processing_result": "LoRa接收帧解析完成",
                "lora_receive_info": {
                    "receive_timestamp": receive_timestamp,
                    "complete_timestamp": complete_timestamp,
                    "duration_ms": duration,
                    "data_content": data_content,
                    "data_length": len(data_content),
                    "data_hex": payload[8:].hex() if len(payload) > 8 else ""
                }
            }
        
        return processed_data
        
    except Exception as e:
        logger.error(f"处理LoRa帧时发生错误: {e}")
        return {
            "frame_name": "LoRa收发帧",
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }


def get_frame_type_name(frame_type: int) -> str:
    """获取帧类型名称"""
    frame_names = {
        0x01: "广播帧",
        0x02: "发送时间戳回传帧", 
        0x03: "链路状态帧",
        0x05: "FPGA操作帧",
        0x07: "LoRa收发帧"
    }
    return frame_names.get(frame_type, f"未知帧(0x{frame_type:02X})")

def process_frame_by_type(parsed_msg: dict) -> dict:
    """根据帧类型处理消息"""
    frame_type = parsed_msg.get("frame_type", 0)
    
    try:
        if frame_type == FRAME_TYPE_BROADCAST:
            processing_result = process_broadcast_frame(parsed_msg)
        elif frame_type == FRAME_TYPE_TIMESTAMP:
            processing_result = process_timestamp_frame(parsed_msg)
        elif frame_type == FRAME_TYPE_LINK_STATUS:
            processing_result = process_link_status_frame(parsed_msg)
        elif frame_type == FRAME_TYPE_FPGA:
            processing_result = process_fpga_frame(parsed_msg)
        elif frame_type == FRAME_TYPE_LORA:
            processing_result = process_lora_frame(parsed_msg)
        else:
            processing_result = {
                "frame_name": f"未知帧(0x{frame_type:02X})",
                "processing_result": "未知帧类型，跳过处理",
                "error": "unsupported_frame_type"
            }
        
        return processing_result
        
    except Exception as e:
        logger.error(f"处理帧类型 0x{frame_type:02X} 时发生错误: {e}")
        return {
            "frame_name": get_frame_type_name(frame_type),
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }

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

class ChannelParameters(BaseModel):
    """通道参数模型"""
    bandwidth: int  # 带宽(KHz)
    coding: str     # 编码
    spreading_factor: int  # 扩频因子
    center_frequency: int  # 中心频率(MHz)
    power: float    # 功率(W)

class AllChannelParameters(BaseModel):
    """所有通道参数"""
    uplink: ChannelParameters
    uplink_interference: ChannelParameters
    downlink: ChannelParameters

class DopplerSettings(BaseModel):
    """多普勒设置模型"""
    type: str  # 'none', 'constant', 'linear', 'sinusoidal', 'random'
    frequencyMin: int  # 频移下限(Hz)
    frequencyMax: int  # 频移上限(Hz)
    rate: Optional[float] = None  # 变化率(Hz/s) - 用于线性
    period: Optional[float] = None  # 周期(s) - 用于正弦

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
                    # 处理帧数据
                    processing_result = process_frame_by_type(parsed_msg)
                
                    # 添加接收信息和处理结果
                    parsed_msg.update({
                        "source_ip": addr[0],
                        "source_port": addr[1],
                        "dest_port": self.current_port,
                        "receive_time": datetime.now().isoformat(),
                        "direction": "receive",
                        "processing": processing_result  # 添加处理结果
                    })
                
                    # 添加到消息队列
                    message_queue.append(parsed_msg)
                
                    logger.info(f"收到{parsed_msg['frame_type_name']} [{addr[0]}:{addr[1]}] -> [127.0.0.1:{self.current_port}]: "
                               f"帧类型=0x{parsed_msg['frame_type']:02X}, "
                               f"时间戳1={parsed_msg['timestamp1']}ms, "
                               f"时间戳2={parsed_msg['timestamp2']}ms, "
                               f"数据长度={parsed_msg['payload_length']}, "
                               f"处理结果={processing_result['processing_result']}")
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
    def send_message(message: str, target_ip: str = "127.0.0.1", target_port: int = None, frame_type: int = 0x01):
        """发送UDP消息"""
        try:
            if target_port is None:
                target_port = current_config["receivePort"]
    
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
                logger.info(f"发送{get_frame_type_name(frame_type)}UDP消息 [127.0.0.1:{local_port}] -> [{target_ip}:{target_port}]: "
                           f"帧类型=0x{frame_type:02X}, 载荷长度={len(payload)}")
        
                return True, local_port, target_port
        except Exception as e:
            logger.error(f"发送UDP消息失败: {e}")
            return False, None, None

    @staticmethod
    def fpga_operation(operations: FPGAOperation, target_ip: str = "127.0.0.1", target_port: int = None):
        """发送FPGA操作帧"""
        try:         


            full_message = struct.pack('>BHHHH',
                                    FRAME_TYPE_FPGA,
                                    operations.operation_type,
                                    operations.address,
                                    operations.data)
            
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('127.0.0.1', 0))
                local_port = sock.getsockname()[1]
                
                sock.sendto(full_message, (target_ip, target_port))
                
                op_name = "读操作" if operation_type == 0 else "写操作"
                logger.info(f"发送FPGA{op_name}帧 [127.0.0.1:{local_port}] -> [{target_ip}:{target_port}]: "
                           f"操作数={operation_count}, 载荷长度={len(payload)}")
                
                return True, local_port, target_port
                
        except Exception as e:
            logger.error(f"FPGA操作帧失败: {e}")
            return False, None, None

    @staticmethod
    def send_lora_message(timing_enable: int, timing_time: int, data_content: str, 
                         target_ip: str = "127.0.0.1", target_port: int = None):
        """发送LoRa消息帧"""
        try:
            if target_port is None:
                target_port = current_config["receivePort"]
            
            frame_type = FRAME_TYPE_LORA
            
            # 构建payload
            payload = struct.pack('B', timing_enable)
            payload += struct.pack('>I', timing_time)
            payload += data_content.encode('utf-8')
            
            # 构建完整帧
            current_time = time.time()
            seconds = int(current_time) & 0xFFFF
            milliseconds = int((current_time % 1) * 1000) & 0xFFFF
            seconds2 = seconds
            milliseconds2 = (milliseconds + 1) & 0xFFFF
            
            frame_data = struct.pack('>BHHHH',
                                    frame_type,
                                    seconds,
                                    milliseconds,
                                    seconds2,
                                    milliseconds2)
            
            full_message = frame_data + payload
            
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('127.0.0.1', 0))
                local_port = sock.getsockname()[1]
                
                sock.sendto(full_message, (target_ip, target_port))
                
                timing_status = "定时开启" if timing_enable == 1 else "不定时"
                logger.info(f"发送LoRa消息帧 [127.0.0.1:{local_port}] -> [{target_ip}:{target_port}]: "
                           f"{timing_status}, 定时时间={timing_time}ms, 数据长度={len(data_content)}")
                
                return True, local_port, target_port
                
        except Exception as e:
            logger.error(f"发送LoRa消息帧失败: {e}")
            return False, None, None

# 全局实例
udp_receiver = UDPReceiver()
udp_sender = UDPSender()

# 存储当前配置
current_config = {
    "receivePort": CONFIG["udp_receive_port"]
}

# 存储所有通道参数
current_parameters = {
    "uplink": {
        "bandwidth": 100000,
        "coding": "4/5",
        "spreading_factor": 9,
        "center_frequency": 10000,
        "power": 1.0
    },
    "uplink_interference": {
        "bandwidth": 100000,
        "coding": "4/6",
        "spreading_factor": 8,
        "center_frequency": 10200,
        "power": 0.5
    },
    "downlink": {
        "bandwidth": 100000,
        "coding": "4/7",
        "spreading_factor": 10,
        "center_frequency": 12000,
        "power": 2.0
    }
}

# 存储多普勒设置
current_doppler_settings = {
    "type": "none",
    "frequencyMin": -1000,
    "frequencyMax": 1000,
    "rate": 10.0,
    "period": 1.0
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

@app.get("/api/udp/frame-stats")
async def get_frame_stats():
    """获取帧类型统计"""
    try:
        stats = {
            "total_frames": len(message_queue),
            "frame_types": {},
            "recent_activity": []
        }
        
        # 统计帧类型
        for msg in message_queue:
            frame_type = msg.get("frame_type", 0)
            frame_name = msg.get("frame_type_name", "未知")
            
            if frame_name not in stats["frame_types"]:
                stats["frame_types"][frame_name] = {
                    "count": 0,
                    "type_code": f"0x{frame_type:02X}",
                    "last_seen": None
                }
            
            stats["frame_types"][frame_name]["count"] += 1
            stats["frame_types"][frame_name]["last_seen"] = msg.get("receive_time")
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取帧统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parameters")
async def get_parameters():
    """读取所有通道参数"""
    try:
        logger.info("读取通道参数")
        return {
            "success": True,
            "data": current_parameters,
            "message": "参数读取成功"
        }
    except Exception as e:
        logger.error(f"读取参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parameters")
async def write_parameters(params: AllChannelParameters):
    """写入所有通道参数"""
    try:
        # 更新全局参数
        current_parameters["uplink"] = params.uplink.dict()
        current_parameters["uplink_interference"] = params.uplink_interference.dict()
        current_parameters["downlink"] = params.downlink.dict()
        
        logger.info(f"写入通道参数成功: {current_parameters}")
        
        # TODO: 这里可以添加实际的硬件配置逻辑
        # 例如: configure_hardware(current_parameters)
        
        return {
            "success": True,
            "data": current_parameters,
            "message": "参数写入成功"
        }
    except Exception as e:
        logger.error(f"写入参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/doppler")
async def get_doppler_settings():
    """读取多普勒设置"""
    try:
        logger.info("读取多普勒设置")
        return {
            "success": True,
            "data": current_doppler_settings,
            "message": "多普勒设置读取成功"
        }
    except Exception as e:
        logger.error(f"读取多普勒设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/doppler")
async def write_doppler_settings(settings: DopplerSettings):
    """写入多普勒设置"""
    try:
        # 更新全局设置
        current_doppler_settings["type"] = settings.type
        current_doppler_settings["frequencyMin"] = settings.frequencyMin
        current_doppler_settings["frequencyMax"] = settings.frequencyMax
        
        if settings.rate is not None:
            current_doppler_settings["rate"] = settings.rate
        if settings.period is not None:
            current_doppler_settings["period"] = settings.period
        
        logger.info(f"写入多普勒设置成功: {current_doppler_settings}")
        
        # TODO: 这里可以添加实际的硬件配置逻辑
        # 例如: configure_doppler(current_doppler_settings)
        
        return {
            "success": True,
            "data": current_doppler_settings,
            "message": "多普勒设置写入成功"
        }
    except Exception as e:
        logger.error(f"写入多普勒设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fpga/read")
async def fpga_read_operation(operations: FPGAOperation):
    """FPGA读操作"""
    try:
        operations.operation_type = 0
        operations.address = 0
        operations.data = 0

        success, local_port, target_port = udp_sender.send_fpga_operation(
            operations.operations,
            target_ip="127.0.0.1"
        )
        
        if success:
            return {
                "success": True,
                "message": "FPGA读操作发送成功",
                "details": {
                    "operation_type": "read",
                    "operation_count": len(operations.operations),
                    "from": f"127.0.0.1:{local_port}",
                    "to": f"127.0.0.1:{target_port}"
                }
            }
        else:
            raise HTTPException(status_code=500, detail="FPGA读操作发送失败")
            
    except Exception as e:
        logger.error(f"FPGA读操作失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fpga/write")
async def fpga_write_operation(operations: FPGAOperation):
    """FPGA写操作"""
    try:
        operations.operation_type = 0
        operations.address = 0
        operations.data = 0

        success, local_port, target_port = udp_sender.send_fpga_operation(
            operations.operations,
            target_ip="127.0.0.1"
        )
        
        if success:
            return {
                "success": True,
                "message": "FPGA写操作发送成功",
                "details": {
                    "operation_type": "write",
                    "operation_count": len(operations.operations),
                    "from": f"127.0.0.1:{local_port}",
                    "to": f"127.0.0.1:{target_port}"
                }
            }
        else:
            raise HTTPException(status_code=500, detail="FPGA写操作发送失败")
            
    except Exception as e:
        logger.error(f"FPGA写操作失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lora/send")
async def lora_send_message(msg: LoRaSendMessage):
    """LoRa发送消息"""
    try:
        success, local_port, target_port = udp_sender.send_lora_message(
            timing_enable=msg.timing_enable,
            timing_time=msg.timing_time,
            data_content=msg.data_content,
            target_ip="127.0.0.1"
        )
        
        if success:
            return {
                "success": True,
                "message": "LoRa消息发送成功",
                "details": {
                    "timing_enable": msg.timing_enable,
                    "timing_time": msg.timing_time,
                    "data_length": len(msg.data_content),
                    "from": f"127.0.0.1:{local_port}",
                    "to": f"127.0.0.1:{target_port}"
                }
            }
        else:
            raise HTTPException(status_code=500, detail="LoRa消息发送失败")
            
    except Exception as e:
        logger.error(f"LoRa发送失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=CONFIG["backend_port"], log_level="info")