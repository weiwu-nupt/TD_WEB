import socket
import struct
import logging
from typing import Tuple, Optional, List
from config import (
    CONFIG, get_frame_type_name,
    FRAME_TYPE_FPGA, FRAME_TYPE_LORA
)
from frame_parser import build_message

logger = logging.getLogger(__name__)

class UDPSender:
    """UDP发送器类"""

    @staticmethod
    def send_fpga_operation(
        operation_type: int,
        address: Optional[int] = None,
        data: Optional[int] = None,
        target_ip: str = "127.0.0.1",
        target_port: int = 9100,
        batch_operations: Optional[List[Tuple[int, int]]] = None
    ) ->bool:
        """
        发送FPGA操作消息
        
        Args:
            operation_type: 操作类型 (0=读, 1=写)
            address: 单个操作的地址 (单次读写时使用)
            data: 单个操作的数据 (写操作时使用)
            target_ip: 目标IP
            target_port: 目标端口
            batch_operations: 批量操作列表 [(address, data), ...]
        """
        try:
            if batch_operations:
                # 批量写入模式
                operation_count = len(batch_operations)
                
                # 消息内容: operation_type(1) + operation_count(1) + [address(4) + data(4)] * N
                message_content = struct.pack('BB', operation_type, operation_count)
                
                for addr, val in batch_operations:
                    # 大端序: 高位字节在前,低位字节在后
                    message_content += struct.pack('>I', addr)  # 地址(4字节)
                    message_content += struct.pack('>I', val)   # 数据(4字节)
                
            else:
                # 单次读写模式
                if address is None:
                    raise ValueError("单次操作需要提供address参数")
                
                if operation_type == 0:
                    # 读操作: operation_type(1) + operation_count(1) + address(4)
                    message_content = struct.pack('BB', operation_type, 1)  # 读, 1个地址
                    message_content += struct.pack('>I', address)
                    
                elif operation_type == 1:
                    # 写操作: operation_type(1) + operation_count(1) + address(4) + data(4)
                    if data is None:
                        raise ValueError("写操作需要提供data参数")
                    else:
                        data =0
                    
                    message_content = struct.pack('BB', operation_type, 1)  # 写, 1个操作
                    message_content += struct.pack('>I', address)
                    message_content += struct.pack('>I', data)
                    
            
            # 构建完整消息
            full_message = build_message(FRAME_TYPE_FPGA, message_content)
            
            # 发送UDP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('0.0.0.0', 8002))
                sock.sendto(full_message, (target_ip, target_port))
            
            return True
            
        except Exception as e:
            logger.error(f"FPGA操作发送失败: {e}")
            return False

    @staticmethod
    def send_lora_message(
        timing_enable: int,
        timing_time: int,
        data_content: str,
        frame_count: int = 0,
        target_ip: str = "127.0.0.1",
        target_port: int = 9100
    ) -> bool:
        """发送LoRa消息帧"""
        try:
            # 解析实际数据
            actual_data_bytes = bytes.fromhex(data_content)
        
            # 构建 data = frame_count(1) + 实际数据
            data_with_count = struct.pack('B', frame_count) + actual_data_bytes

            # timing_enable(1) + timing_time(4) + data_length(2) + data
            message_content = struct.pack('B', timing_enable)       # 定时使能(1字节)
            message_content += struct.pack('>I', timing_time)       # 定时时间(4字节,大端序)
            message_content += data_with_count                      # data = frame_count + 实际数据

            # 构建完整消息
            full_message = build_message(FRAME_TYPE_LORA, message_content)
            
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('0.0.0.0', 8002))
                sock.sendto(full_message, (target_ip, target_port))
                
            return True
                
        except Exception as e:
            logger.error(f"发送LoRa消息失败: {e}")
            return False

    @staticmethod
    def send_raw_data(self, data: bytes, target_ip: str, target_port: int) -> bool:
        """
        🔧 新增：发送原始字节数据（用于透传）
        """
        try:
            self.socket.sendto(data, (target_ip, target_port))
            logger.info(f"✅ 原始数据已发送到 {target_ip}:{target_port}, 长度: {len(data)}字节")
            return True
        except Exception as e:
            logger.error(f"❌ 发送原始数据失败: {e}")
            return False