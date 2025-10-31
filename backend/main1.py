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
import uuid
from typing import Dict, Any
import asyncio
import crcmod

# 帧类型常量
FRAME_TYPE_BROADCAST = 0x01    # 广播帧
FRAME_TYPE_TIMESTAMP = 0x02    # 发送时间戳回传帧  
FRAME_TYPE_LINK_STATUS = 0x03  # 链路状态帧
FRAME_TYPE_FPGA = 0x05         # FPGA读写帧
FRAME_TYPE_LORA = 0x07         # LoRa收发帧

pending_requests: Dict[str, Dict[str, Any]] = {}

# 响应超时时间(秒)
RESPONSE_TIMEOUT = 3

FRAME_SYNC_HEADER = 0x1ACFFC1D

# CRC16-CCITT计算
crc16 = crcmod.predefined.mkCrcFun('crc-ccitt-false')

def calculate_crc16(data: bytes) -> int:
    """计算CRC16校验值"""
    return crc16(data)

def parse_message(data: bytes) -> Optional[dict]:
    """
    解析新格式的消息帧
    格式: 帧同步头(4) + 消息类型(1) + 消息长度(1) + 消息内容(N) + CRC(2)
    最小长度: 4 + 1 + 1 + 0 + 2 = 8字节
    """
    try:
        if len(data) < 8:
            logger.error(f"消息长度不足,需要至少8字节,实际{len(data)}字节")
            return None
        
        # 1. 解析帧同步头(4字节,大端序)
        sync_header = struct.unpack('>I', data[0:4])[0]
        if sync_header != FRAME_SYNC_HEADER:
            logger.error(f"帧同步头错误: 期望0x{FRAME_SYNC_HEADER:08X}, 实际0x{sync_header:08X}")
            return None
        
        # 2. 解析消息类型(1字节)
        message_type = data[4]
        
        # 3. 解析消息长度(1字节)
        message_length = data[5]
        
        # 4. 检查实际数据长度
        expected_total_length = 4 + 1 + 1 + message_length + 2  # 同步头+类型+长度+内容+CRC
        if len(data) < expected_total_length:
            logger.error(f"消息长度不匹配: 期望{expected_total_length}字节, 实际{len(data)}字节")
            return None
        
        # 5. 提取消息内容
        message_content = data[6:6+message_length]
        
        # 6. 提取CRC(2字节,大端序)
        received_crc = struct.unpack('>H', data[6+message_length:6+message_length+2])[0]
        
        # 7. 计算CRC(从消息类型到消息内容结束)
        crc_data = data[4:6+message_length]
        calculated_crc = calculate_crc16(crc_data)
        
        # 8. 校验CRC
        crc_valid = (received_crc == calculated_crc)
        if not crc_valid:
            logger.warning(f"CRC校验失败: 接收0x{received_crc:04X}, 计算0x{calculated_crc:04X}")
        
        return {
            "sync_header": f"0x{sync_header:08X}",
            "message_type": message_type,
            "message_length": message_length,
            "message_content": message_content,
            "received_crc": f"0x{received_crc:04X}",
            "calculated_crc": f"0x{calculated_crc:04X}",
            "crc_valid": crc_valid,
            "raw_data": data.hex()
        }
        
    except Exception as e:
        logger.error(f"解析消息失败: {e}")
        return None

class ResponseWaiter:
    """响应等待管理器"""
    
    @staticmethod
    def create_request(request_type: str) -> str:
        """创建一个新的请求并返回request_id"""
        request_id = str(uuid.uuid4())
        pending_requests[request_id] = {
            "type": request_type,
            "event": asyncio.Event(),
            "response_data": None,
            "timestamp": time.time()
        }
        logger.info(f"创建请求等待: {request_id} - {request_type}")
        return request_id
    
    @staticmethod
    async def wait_for_response(request_id: str, timeout: float = RESPONSE_TIMEOUT) -> Optional[dict]:
        """等待响应"""
        if request_id not in pending_requests:
            logger.error(f"请求ID不存在: {request_id}")
            return None
        
        request = pending_requests[request_id]
        
        try:
            # 等待响应事件触发或超时
            await asyncio.wait_for(
                asyncio.to_thread(request["event"].wait),
                timeout=timeout
            )
            
            response_data = request["response_data"]
            logger.info(f"收到响应: {request_id}")
            return response_data
            
        except asyncio.TimeoutError:
            logger.warning(f"等待响应超时: {request_id}")
            return None
        finally:
            # 清理请求
            if request_id in pending_requests:
                del pending_requests[request_id]
    
    @staticmethod
    def notify_response(frame_type: int, response_data: dict):
        """通知有响应到达"""
        # 根据帧类型找到对应的等待请求
        for request_id, request in list(pending_requests.items()):
            # 匹配请求类型
            if ResponseWaiter._match_request(request["type"], frame_type, response_data):
                request["response_data"] = response_data
                request["event"].set()
                logger.info(f"匹配到等待的请求: {request_id} - 帧类型: 0x{frame_type:02X}")
                break
    
    @staticmethod
    def _match_request(request_type: str, frame_type: int, response_data: dict) -> bool:
        """匹配请求类型和响应"""
        # FPGA读操作响应
        if request_type == "fpga_read" and frame_type == FRAME_TYPE_FPGA:
            fpga_info = response_data.get("processing", {}).get("fpga_info", {})
            if fpga_info.get("operation_type") == 0:  # 读操作
                return True
        
        # FPGA写操作响应
        elif request_type == "fpga_write" and frame_type == FRAME_TYPE_FPGA:
            fpga_info = response_data.get("processing", {}).get("fpga_info", {})
            if fpga_info.get("operation_type") == 1:  # 写操作
                return True
        
        # LoRa接收响应
        elif request_type == "lora_send" and frame_type == FRAME_TYPE_LORA:
            # LoRa发送后等待接收确认
            return True
        
        return False

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

def process_broadcast_frame(parsed_msg: dict, addr: tuple) -> dict:
    """处理广播帧 0x01"""
    try:
        message_content = parsed_msg.get("message_content", b"")
        
        processed_data = {
            "frame_name": "广播帧",
            "processing_result": "广播帧处理完成",
            "source_ip": addr[0],
            "source_port": addr[1],
            "broadcast_info": {
                "broadcast_id": 1,
                "target_range": "全网",
                "priority": "normal",
                "content_hex": message_content.hex(),
                "content_length": len(message_content)
            }
        }
        return processed_data
    except Exception as e:
        logger.error(f"处理广播帧时发生错误: {e}")
        return {
            "frame_name": "广播帧",
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }

def process_timestamp_frame(parsed_msg: dict, addr: tuple) -> dict:
    """处理发送时间戳回传帧 0x02"""
    try:
        message_content = parsed_msg.get("message_content", b"")
        
        if len(message_content) < 8:
            raise ValueError("时间戳数据长度不足")
        
        # 解析两个时间戳(各4字节,大端序)
        timestamp1 = struct.unpack('>I', message_content[0:4])[0]
        timestamp2 = struct.unpack('>I', message_content[4:8])[0]
        
        processed_data = {
            "frame_name": "发送时间戳回传帧",
            "processing_result": "时间戳回传帧处理完成",
            "source_ip": addr[0],
            "source_port": addr[1],
            "timestamp_info": {
                "timestamp1": timestamp1,
                "timestamp2": timestamp2,
                "delay_ms": abs(timestamp2 - timestamp1)
            }
        }
        return processed_data
    except Exception as e:
        logger.error(f"处理时间戳帧时发生错误: {e}")
        return {
            "frame_name": "发送时间戳回传帧",
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }

def process_link_status_frame(parsed_msg: dict, addr: tuple) -> dict:
    """处理链路状态帧 0x03"""
    try:
        processed_data = {
            "frame_name": "链路状态帧",
            "processing_result": "链路状态帧处理完成",
            "source_ip": addr[0],
            "source_port": addr[1],
            "link_info": {
                "link_quality": "良好",
                "signal_strength": -60,
                "connection_status": "connected"
            }
        }
        return processed_data
    except Exception as e:
        logger.error(f"处理链路状态帧时发生错误: {e}")
        return {
            "frame_name": "链路状态帧",
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }

def process_fpga_frame(parsed_msg: dict, addr: tuple) -> dict:
    """处理FPGA读写帧 0x05"""
    try:
        message_content = parsed_msg.get("message_content", b"")
        
        if len(message_content) < 6:
            raise ValueError("FPGA数据长度不足")
        
        # 解析: operation_type(1) + operation_count(1) + address(4) + [data(4)]
        operation_type = message_content[0]  # 0-读, 1-写
        operation_count = message_content[1]
        address = struct.unpack('>I', message_content[2:6])[0]
        
        operation_info = {
            "operation_type": operation_type,
            "operation_name": "读操作" if operation_type == 0 else "写操作",
            "operation_count": operation_count,
            "address": f"0x{address:08X}",
            "address_decimal": address
        }
        
        # 如果是写操作,解析数据
        if operation_type == 1 and len(message_content) >= 10:
            write_data = struct.unpack('>I', message_content[6:10])[0]
            operation_info["data"] = f"0x{write_data:08X}"
            operation_info["data_decimal"] = write_data
        # 如果是读操作的响应(包含读取的数据)
        elif operation_type == 0 and len(message_content) >= 10:
            read_data = struct.unpack('>I', message_content[6:10])[0]
            operation_info["data"] = f"0x{read_data:08X}"
            operation_info["data_decimal"] = read_data
        
        processed_data = {
            "frame_name": "FPGA操作帧",
            "processing_result": f"FPGA{operation_info['operation_name']}处理完成",
            "source_ip": addr[0],
            "source_port": addr[1],
            "fpga_info": operation_info
        }
        
        return processed_data
        
    except Exception as e:
        logger.error(f"处理FPGA帧时发生错误: {e}")
        return {
            "frame_name": "FPGA操作帧",
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }

def process_lora_frame(parsed_msg: dict, addr: tuple) -> dict:
    """处理LoRa收发帧 0x07"""
    try:
        message_content = parsed_msg.get("message_content", b"")
        
        if len(message_content) < 1:
            raise ValueError("LoRa数据长度不足")
        
        # 判断是发送帧还是接收帧
        # 发送帧: timing_enable(1) + timing_time(4) + data(n)
        # 接收帧: receive_timestamp(4) + complete_timestamp(4) + data(n)
        
        # 简单判断: 如果第一个字节<=1且长度>=5,认为是发送帧
        if len(message_content) >= 5 and message_content[0] <= 1:
            # LoRa发送帧
            timing_enable = message_content[0]
            timing_time = struct.unpack('>I', message_content[1:5])[0]
            data_content = message_content[5:].decode('utf-8', errors='ignore')
            
            processed_data = {
                "frame_name": "LoRa发送帧",
                "processing_result": "LoRa发送帧处理完成",
                "source_ip": addr[0],
                "source_port": addr[1],
                "lora_send_info": {
                    "timing_enable": timing_enable,
                    "timing_enabled": timing_enable == 1,
                    "timing_time": timing_time,
                    "timing_time_ms": timing_time,
                    "data_content": data_content,
                    "content_length": len(data_content),
                    "data_hex": message_content[5:].hex()
                }
            }
        else:
            # LoRa接收帧
            if len(message_content) < 8:
                raise ValueError("LoRa接收帧数据长度不足")
            
            receive_timestamp = struct.unpack('>I', message_content[0:4])[0]
            complete_timestamp = struct.unpack('>I', message_content[4:8])[0]
            data_content = message_content[8:].decode('utf-8', errors='ignore')
            
            duration = complete_timestamp - receive_timestamp
            
            processed_data = {
                "frame_name": "LoRa接收帧",
                "processing_result": "LoRa接收帧处理完成",
                "source_ip": addr[0],
                "source_port": addr[1],
                "lora_receive_info": {
                    "receive_timestamp": receive_timestamp,
                    "complete_timestamp": complete_timestamp,
                    "duration_ms": duration,
                    "data_content": data_content,
                    "content_length": len(data_content),
                    "data_hex": message_content[8:].hex()
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

def process_frame_by_type(parsed_msg: dict, addr: tuple) -> dict:
    """根据消息类型处理消息"""
    message_type = parsed_msg.get("message_type", 0)
    
    # 先检查CRC
    if not parsed_msg.get("crc_valid", False):
        logger.warning(f"CRC校验失败,但继续处理: 消息类型=0x{message_type:02X}")
    
    try:
        if message_type == FRAME_TYPE_BROADCAST:
            return process_broadcast_frame(parsed_msg, addr)
        elif message_type == FRAME_TYPE_TIMESTAMP:
            return process_timestamp_frame(parsed_msg, addr)
        elif message_type == FRAME_TYPE_LINK_STATUS:
            return process_link_status_frame(parsed_msg, addr)
        elif message_type == FRAME_TYPE_FPGA:
            return process_fpga_frame(parsed_msg, addr)
        elif message_type == FRAME_TYPE_LORA:
            return process_lora_frame(parsed_msg, addr)
        else:
            return {
                "frame_name": f"未知帧(0x{message_type:02X})",
                "processing_result": "未知消息类型，跳过处理",
                "source_ip": addr[0],
                "source_port": addr[1],
                "error": "unsupported_frame_type"
            }
        
    except Exception as e:
        logger.error(f"处理消息类型 0x{message_type:02X} 时发生错误: {e}")
        return {
            "frame_name": get_frame_type_name(message_type),
            "processing_result": f"处理失败: {str(e)}",
            "source_ip": addr[0],
            "source_port": addr[1],
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

# def parse_message_frame(data: bytes) -> Optional[dict]:
#     """解析消息帧"""
#     try:
#         if len(data) < 9:  # 最小长度：1+4+4 = 9字节
#             return None
        
#         # 解析帧头
#         frame_type = data[0]
        
#         # 解析接收时间戳（秒+毫秒）
#         timestamp_bytes = data[1:9]
#         seconds = struct.unpack('>H', timestamp_bytes[0:2])[0]  # 大端序，2字节
#         milliseconds = struct.unpack('>H', timestamp_bytes[2:4])[0]  # 大端序，2字节
        
#         # 第二个时间戳
#         seconds2 = struct.unpack('>H', timestamp_bytes[4:6])[0]
#         milliseconds2 = struct.unpack('>H', timestamp_bytes[6:8])[0]
        
#         # 数据包内容
#         payload = data[9:] if len(data) > 9 else b''
        
#         # 计算完整时间戳（转换为毫秒）
#         timestamp_ms = seconds * 1000 + milliseconds
#         timestamp_ms2 = seconds2 * 1000 + milliseconds2
        
#         return {
#             "frame_type": frame_type,
#             "timestamp1": timestamp_ms,
#             "timestamp2": timestamp_ms2,
#             "payload": payload.hex() if payload else "",
#             "payload_length": len(payload),
#             "raw_data": data.hex()
#         }
#     except Exception as e:
#         logger.error(f"解析消息帧失败: {e}")
#         return None

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
                
                # 解析消息
                parsed_msg = parse_message(data)
                
                if parsed_msg is None:
                    logger.error(f"消息解析失败: {data.hex()}")
                    continue
                
                # 处理消息
                result = process_frame_by_type(parsed_msg, addr)
                
                # 合并解析信息和处理结果
                result["message_type"] = parsed_msg["message_type"]
                result["message_length"] = parsed_msg["message_length"]
                result["crc_valid"] = parsed_msg["crc_valid"]
                result["sync_header"] = parsed_msg["sync_header"]
                result["raw_data"] = parsed_msg["raw_data"]
                
                # 添加接收信息
                result["dest_port"] = self.current_port
                result["receive_time"] = datetime.now().isoformat()
                result["direction"] = "receive"
                
                # 添加到消息队列
                message_queue.append(result)
                
                # 通知等待的请求
                ResponseWaiter.notify_response(result["message_type"], result)
                
                crc_status = "✓" if parsed_msg["crc_valid"] else "✗"
                logger.info(f"收到{result['frame_name']} [{addr[0]}:{addr[1]}] -> [127.0.0.1:{self.current_port}]: "
                           f"类型=0x{result['message_type']:02X}, "
                           f"长度={result['message_length']}, "
                           f"CRC={crc_status}, "
                           f"处理={result['processing_result']}")
                
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

    # @staticmethod
    # def send_message(message: str, target_ip: str = "127.0.0.1", target_port: int = None, frame_type: int = 0x01):
    #     """发送UDP消息"""
    #     try:
    #         if target_port is None:
    #             target_port = current_config["receivePort"]
    
    #         # 当前时间戳（秒+毫秒）
    #         import time
    #         current_time = time.time()
    #         seconds = int(current_time) & 0xFFFF  # 取低16位
    #         milliseconds = int((current_time % 1) * 1000) & 0xFFFF
    
    #         # 第二个时间戳（稍微延后1ms）
    #         seconds2 = seconds
    #         milliseconds2 = (milliseconds + 1) & 0xFFFF
    
    #         # 构建帧数据
    #         frame_data = struct.pack('>BHHHH', 
    #                                 frame_type,      # 帧类型 1字节
    #                                 seconds,         # 时间戳1秒 2字节
    #                                 milliseconds,    # 时间戳1毫秒 2字节
    #                                 seconds2,        # 时间戳2秒 2字节
    #                                 milliseconds2)   # 时间戳2毫秒 2字节
    
    #         # 添加消息内容作为payload
    #         payload = message.encode('utf-8')
    #         full_message = frame_data + payload
    
    #         with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    #             sock.bind(('127.0.0.1', 0))
    #             local_port = sock.getsockname()[1]
        
    #             sock.sendto(full_message, (target_ip, target_port))
    #             logger.info(f"发送{get_frame_type_name(frame_type)}UDP消息 [127.0.0.1:{local_port}] -> [{target_ip}:{target_port}]: "
    #                        f"帧类型=0x{frame_type:02X}, 载荷长度={len(payload)}")
        
    #             return True, local_port, target_port
    #     except Exception as e:
    #         logger.error(f"发送UDP消息失败: {e}")
    #         return False, None, None

    @staticmethod
    def build_message(message_type: int, message_content: bytes) -> bytes:
        """
        构建新格式的消息
        格式: 帧同步头(4) + 消息类型(1) + 消息长度(1) + 消息内容(N) + CRC(2)
        """
        # 1. 帧同步头
        sync_header = struct.pack('>I', FRAME_SYNC_HEADER)
        
        # 2. 消息类型
        msg_type = struct.pack('B', message_type)
        
        # 3. 消息长度
        msg_length = struct.pack('B', len(message_content))
        
        # 4. 计算CRC(从消息类型到消息内容)
        crc_data = msg_type + msg_length + message_content
        crc_value = calculate_crc16(crc_data)
        crc_bytes = struct.pack('>H', crc_value)
        
        # 5. 组装完整消息
        full_message = sync_header + msg_type + msg_length + message_content + crc_bytes
        
        return full_message

    @staticmethod
    def send_message(message: str, target_ip: str = "127.0.0.1", target_port: int = None, frame_type: int = 0x01):
        """发送UDP消息"""
        try:
            if target_port is None:
                target_port = current_config["receivePort"]
            
            # 构建消息内容
            message_content = message.encode('utf-8')
            
            # 构建完整消息
            full_message = UDPSender.build_message(frame_type, message_content)
            
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('127.0.0.1', 0))
                local_port = sock.getsockname()[1]
                
                sock.sendto(full_message, (target_ip, target_port))
                logger.info(f"发送{get_frame_type_name(frame_type)} [127.0.0.1:{local_port}] -> [{target_ip}:{target_port}]: "
                           f"类型=0x{frame_type:02X}, 长度={len(message_content)}")
                
                return True, local_port, target_port
        except Exception as e:
            logger.error(f"发送UDP消息失败: {e}")
            return False, None, None

    @staticmethod
    def send_fpga_operation(operation_type: int, address: int, data: int = None, 
                          target_ip: str = "127.0.0.1", target_port: int = None):
        """发送单条FPGA操作"""
        try:
            if target_port is None:
                target_port = current_config["receivePort"]
            
            # 构建消息内容: operation_type(1) + operation_count(1) + address(4) + [data(4)]
            operation_count = 1
            message_content = struct.pack('BB', operation_type, operation_count)
            message_content += struct.pack('>I', address)
            
            if operation_type == 1:  # 写操作
                if data is None:
                    raise ValueError("写操作必须提供数据")
                message_content += struct.pack('>I', data)
            
            # 构建完整消息
            full_message = UDPSender.build_message(FRAME_TYPE_FPGA, message_content)
            
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('127.0.0.1', 0))
                local_port = sock.getsockname()[1]
                
                sock.sendto(full_message, (target_ip, target_port))
                
                op_name = "读操作" if operation_type == 0 else "写操作"
                logger.info(f"发送FPGA{op_name} [127.0.0.1:{local_port}] -> [{target_ip}:{target_port}]: "
                           f"地址=0x{address:08X}" + 
                           (f", 数据=0x{data:08X}" if data is not None else ""))
                
                return True, local_port, target_port
                
        except Exception as e:
            logger.error(f"发送FPGA操作失败: {e}")
            return False, None, None

    @staticmethod
    def send_lora_message(timing_enable: int, timing_time: int, data_content: str, 
                         target_ip: str = "127.0.0.1", target_port: int = None):
        """发送LoRa消息帧"""
        try:
            if target_port is None:
                target_port = current_config["receivePort"]
            
            # 构建消息内容: timing_enable(1) + timing_time(4) + data_content(n)
            message_content = struct.pack('B', timing_enable)
            message_content += struct.pack('>I', timing_time)
            message_content += data_content.encode('utf-8')
            
            # 构建完整消息
            full_message = UDPSender.build_message(FRAME_TYPE_LORA, message_content)
            
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('127.0.0.1', 0))
                local_port = sock.getsockname()[1]
                
                sock.sendto(full_message, (target_ip, target_port))
                
                timing_status = "定时开启" if timing_enable == 1 else "不定时"
                logger.info(f"发送LoRa消息 [127.0.0.1:{local_port}] -> [{target_ip}:{target_port}]: "
                           f"{timing_status}, 定时={timing_time}ms, 数据长度={len(data_content)}")
                
                return True, local_port, target_port
                
        except Exception as e:
            logger.error(f"发送LoRa消息失败: {e}")
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
    """读取所有通道参数 - 通过FPGA读取"""
    try:
        logger.info("开始读取通道参数...")
        
        # 创建等待请求
        request_id = ResponseWaiter.create_request("fpga_read")
        
        # 构造FPGA读操作 - 假设每个通道5个参数，地址从0x2000开始
        # 上行通道: 0x2000-0x2004
        # 上行干扰: 0x2010-0x2014
        # 下行通道: 0x2020-0x2024
        operations = []
        
        # 上行通道
        for i in range(5):
            operations.append(FPGAOperation(operation_type=0, operation_count=1, address=0x2000 + i))
        
        # 上行干扰通道
        for i in range(5):
            operations.append(FPGAOperation(operation_type=0, operation_count=1, address=0x2010 + i))
        
        # 下行通道
        for i in range(5):
            operations.append(FPGAOperation(operation_type=0, operation_count=1, address=0x2020 + i))
        
        # 发送FPGA读取命令
        success, local_port, target_port = udp_sender.send_fpga_operation(
            operations,
            target_ip="127.0.0.1"
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="发送FPGA读取命令失败")
        
        # 等待FPGA响应
        response = await ResponseWaiter.wait_for_response(request_id, timeout=5)
        
        if response is None:
            logger.warning("等待FPGA响应超时，返回当前缓存值")
            return {
                "success": True,
                "data": current_parameters,
                "message": "读取超时，返回缓存值",
                "from_cache": True
            }
        
        # 解析FPGA响应数据
        fpga_info = response.get("processing", {}).get("fpga_info", {})
        operations_result = fpga_info.get("operations", [])
        
        if len(operations_result) >= 15:
            # 解析上行通道 (0-4)
            current_parameters["uplink"]["bandwidth"] = operations_result[0].get("data_decimal", 100000)
            current_parameters["uplink"]["coding"] = f"4/{5 + operations_result[1].get('data_decimal', 0)}"
            current_parameters["uplink"]["spreading_factor"] = operations_result[2].get("data_decimal", 9)
            current_parameters["uplink"]["center_frequency"] = operations_result[3].get("data_decimal", 10000)
            current_parameters["uplink"]["power"] = operations_result[4].get("data_decimal", 100) / 100.0
            
            # 解析上行干扰通道 (5-9)
            current_parameters["uplink_interference"]["bandwidth"] = operations_result[5].get("data_decimal", 100000)
            current_parameters["uplink_interference"]["coding"] = f"4/{5 + operations_result[6].get('data_decimal', 1)}"
            current_parameters["uplink_interference"]["spreading_factor"] = operations_result[7].get("data_decimal", 8)
            current_parameters["uplink_interference"]["center_frequency"] = operations_result[8].get("data_decimal", 10200)
            current_parameters["uplink_interference"]["power"] = operations_result[9].get("data_decimal", 50) / 100.0
            
            # 解析下行通道 (10-14)
            current_parameters["downlink"]["bandwidth"] = operations_result[10].get("data_decimal", 100000)
            current_parameters["downlink"]["coding"] = f"4/{5 + operations_result[11].get('data_decimal', 2)}"
            current_parameters["downlink"]["spreading_factor"] = operations_result[12].get("data_decimal", 10)
            current_parameters["downlink"]["center_frequency"] = operations_result[13].get("data_decimal", 12000)
            current_parameters["downlink"]["power"] = operations_result[14].get("data_decimal", 200) / 100.0
        
        logger.info(f"通道参数读取成功")
        
        return {
            "success": True,
            "data": current_parameters,
            "message": "参数读取成功",
            "from_cache": False,
            "fpga_response": fpga_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"读取参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parameters")
async def write_parameters(params: AllChannelParameters):
    """写入所有通道参数 - 通过FPGA写入"""
    try:
        logger.info(f"开始写入通道参数...")
        
        # 创建等待请求
        request_id = ResponseWaiter.create_request("fpga_write")
        
        # 构造FPGA写操作
        operations = []
        
        # 编码映射: "4/5" -> 0, "4/6" -> 1, "4/7" -> 2, "4/8" -> 3
        def coding_to_value(coding: str) -> int:
            return int(coding.split('/')[1]) - 5
        
        # 上行通道
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2000, 
                                       data=params.uplink.bandwidth))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2001, 
                                       data=coding_to_value(params.uplink.coding)))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2002, 
                                       data=params.uplink.spreading_factor))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2003, 
                                       data=params.uplink.center_frequency))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2004, 
                                       data=int(params.uplink.power * 100)))
        
        # 上行干扰通道
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2010, 
                                       data=params.uplink_interference.bandwidth))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2011, 
                                       data=coding_to_value(params.uplink_interference.coding)))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2012, 
                                       data=params.uplink_interference.spreading_factor))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2013, 
                                       data=params.uplink_interference.center_frequency))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2014, 
                                       data=int(params.uplink_interference.power * 100)))
        
        # 下行通道
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2020, 
                                       data=params.downlink.bandwidth))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2021, 
                                       data=coding_to_value(params.downlink.coding)))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2022, 
                                       data=params.downlink.spreading_factor))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2023, 
                                       data=params.downlink.center_frequency))
        operations.append(FPGAOperation(operation_type=1, operation_count=1, address=0x2024, 
                                       data=int(params.downlink.power * 100)))
        
        # 发送FPGA写入命令
        success, local_port, target_port = udp_sender.send_fpga_operation(
            operations,
            target_ip="127.0.0.1"
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="发送FPGA写入命令失败")
        
        # 等待FPGA响应确认
        response = await ResponseWaiter.wait_for_response(request_id, timeout=5)
        
        if response is None:
            logger.warning("等待FPGA写入确认超时")
            return {
                "success": False,
                "message": "写入超时，未收到确认",
                "data": params.dict()
            }
        
        # 写入成功，更新本地缓存
        current_parameters["uplink"] = params.uplink.dict()
        current_parameters["uplink_interference"] = params.uplink_interference.dict()
        current_parameters["downlink"] = params.downlink.dict()
        
        logger.info("通道参数写入成功")
        
        return {
            "success": True,
            "data": current_parameters,
            "message": "参数写入成功",
            "fpga_response": response.get("processing", {}).get("fpga_info", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"写入参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/doppler")
async def get_doppler_settings():
    """读取多普勒设置 - 通过FPGA读取"""
    try:
        logger.info("开始读取多普勒设置...")
        
        # 创建等待请求
        request_id = ResponseWaiter.create_request("fpga_read")
        
        # 构造FPGA读操作 - 假设多普勒设置存储在地址0x1000-0x1004
        operations = [
            FPGAOperation(operation_type=0, operation_count=1, address=0x1000),  # 类型
            FPGAOperation(operation_type=0, operation_count=1, address=0x1001),  # 频移下限
            FPGAOperation(operation_type=0, operation_count=1, address=0x1002),  # 频移上限
            FPGAOperation(operation_type=0, operation_count=1, address=0x1003),  # 变化率
            FPGAOperation(operation_type=0, operation_count=1, address=0x1004),  # 周期
        ]
        
        # 发送FPGA读取命令
        success, local_port, target_port = udp_sender.send_fpga_operation(
            operations,
            target_ip="127.0.0.1"
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="发送FPGA读取命令失败")
        
        # 等待FPGA响应
        response = await ResponseWaiter.wait_for_response(request_id, timeout=5)
        
        if response is None:
            logger.warning("等待FPGA响应超时，返回当前缓存值")
            return {
                "success": True,
                "data": current_doppler_settings,
                "message": "读取超时，返回缓存值",
                "from_cache": True
            }
        
        # 解析FPGA响应数据
        fpga_info = response.get("processing", {}).get("fpga_info", {})
        operations_result = fpga_info.get("operations", [])
        
        if len(operations_result) >= 5:
            # 更新多普勒设置
            # 注意：这里需要根据实际的FPGA数据格式进行解析
            # 假设返回的operations中包含读取的数据
            doppler_type_map = {0: "none", 1: "constant", 2: "linear", 3: "sinusoidal", 4: "random"}
            
            current_doppler_settings["type"] = doppler_type_map.get(
                operations_result[0].get("data_decimal", 0), "none"
            )
            current_doppler_settings["frequencyMin"] = operations_result[1].get("data_decimal", -1000)
            current_doppler_settings["frequencyMax"] = operations_result[2].get("data_decimal", 1000)
            current_doppler_settings["rate"] = operations_result[3].get("data_decimal", 10) / 100.0
            current_doppler_settings["period"] = operations_result[4].get("data_decimal", 100) / 100.0
        
        logger.info(f"多普勒设置读取成功: {current_doppler_settings}")
        
        return {
            "success": True,
            "data": current_doppler_settings,
            "message": "多普勒设置读取成功",
            "from_cache": False,
            "fpga_response": fpga_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"读取多普勒设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/doppler")
async def write_doppler_settings(settings: DopplerSettings):
    """写入多普勒设置 - 通过FPGA写入"""
    try:
        logger.info(f"开始写入多普勒设置: {settings.dict()}")
        
        # 创建等待请求
        request_id = ResponseWaiter.create_request("fpga_write")
        
        # 类型映射
        type_map = {"none": 0, "constant": 1, "linear": 2, "sinusoidal": 3, "random": 4}
        type_value = type_map.get(settings.type, 0)
        
        # 构造FPGA写操作
        operations = [
            FPGAOperation(operation_type=1, operation_count=1, address=0x1000, data=type_value),
            FPGAOperation(operation_type=1, operation_count=1, address=0x1001, data=settings.frequencyMin),
            FPGAOperation(operation_type=1, operation_count=1, address=0x1002, data=settings.frequencyMax),
            FPGAOperation(operation_type=1, operation_count=1, address=0x1003, 
                         data=int((settings.rate or 10) * 100)),  # 转换为整数
            FPGAOperation(operation_type=1, operation_count=1, address=0x1004, 
                         data=int((settings.period or 1) * 100)),  # 转换为整数
        ]
        
        # 发送FPGA写入命令
        success, local_port, target_port = udp_sender.send_fpga_operation(
            operations,
            target_ip="127.0.0.1"
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="发送FPGA写入命令失败")
        
        # 等待FPGA响应确认
        response = await ResponseWaiter.wait_for_response(request_id, timeout=5)
        
        if response is None:
            logger.warning("等待FPGA写入确认超时")
            return {
                "success": False,
                "message": "写入超时，未收到确认",
                "data": settings.dict()
            }
        
        # 写入成功，更新本地缓存
        current_doppler_settings.update(settings.dict())
        
        logger.info("多普勒设置写入成功")
        
        return {
            "success": True,
            "data": current_doppler_settings,
            "message": "多普勒设置写入成功",
            "fpga_response": response.get("processing", {}).get("fpga_info", {})
        }
        
    except HTTPException:
        raise
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