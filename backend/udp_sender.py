#!/usr/bin/env python3
# udp_sender.py - UDP发送器类
import socket
import struct
import logging

from config import (
    CONFIG, get_frame_type_name,
    FRAME_TYPE_FPGA, FRAME_TYPE_LORA
)
from frame_parser import build_message

logger = logging.getLogger(__name__)

class UDPSender:
    """UDP发送器类"""
    
    @staticmethod
    def send_message(message: str, target_ip: str = "127.0.0.1", 
                    target_port: int = None, frame_type: int = 0x01):
        """发送UDP消息"""
        try:
            if target_port is None:
                target_port = current_config["receivePort"]
            
            # 构建消息内容
            message_content = message.encode('utf-8')
            
            # 构建完整消息
            full_message = build_message(frame_type, message_content)
            
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
                target_port = CONFIG["arm_port"]
            
            # 构建消息内容: operation_type(1) + operation_count(1) + address(4) + [data(4)]
            operation_count = 1
            message_content = struct.pack('BB', operation_type, operation_count)
            message_content += struct.pack('>I', address)
            
            if operation_type == 1:  # 写操作
                if data is None:
                    raise ValueError("写操作必须提供数据")
            else:
                data = 0
            message_content += struct.pack('>I', data)
    
            # 构建完整消息
            full_message = build_message(FRAME_TYPE_FPGA, message_content)
            
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('127.0.0.1', 0))
                local_port = sock.getsockname()[1]
                
                sock.sendto(full_message, (target_ip, target_port))
                
                op_name = "读操作" if operation_type == 0 else "写操作"
                logger.info(f"发送FPGA{op_name} [127.0.0.1:{local_port}] -> [{target_ip}:{target_port}]: "
                           f"地址=0x{address:08X}")
                
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
            full_message = build_message(FRAME_TYPE_LORA, message_content)
            
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