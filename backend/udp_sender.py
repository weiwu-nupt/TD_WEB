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
    def send_raw_data(data: bytes, target_ip: str, target_port: int) -> bool:
        """
        🔧 新增：发送原始字节数据（用于透传）
        """
        try:
            socket.sendto(data, (target_ip, target_port))
            return True
        except Exception as e:
            logger.error(f"❌ 发送原始数据失败: {e}")
            return False

    @staticmethod
    def send_node_operation(
        node_settings: dict,
        target_ip: str = "127.0.0.1",
        target_port: int = 9100
    ) -> bool:
        """
        发送节点配置消息 (0x08)
    
        消息格式:
        - 帧同步头: 0x1ACFFC1D (4字节)
        - 消息类型: 0x08 (1字节)
        - 消息长度: (1字节)
        - 节点ID: (1字节)
        - 节点模式: (1字节) 0=单机, 1=组网, 2=虚实融合
        - 组网总节点数: (1字节)
        - 节点属性: (1字节) 0=普通, 1=母星
        - 工作频率: (4字节, 大端序, kHz)
        - 通道衰减: (1字节, dB)
        - 前向链路带宽: (4字节, 大端序, kHz)
        - 前向扩频因子: (1字节)
        - 前向编码: (1字节) 1=4/5, 2=4/6, 3=4/7, 4=4/8
        - 反向链路带宽: (4字节, 大端序, kHz)
        - 反向扩频因子: (1字节)
        - 反向编码: (1字节) 1=4/5, 2=4/6, 3=4/7, 4=4/8
        - 反向扩频因子2: (1字节)
        - CRC: (2字节)
        """
        try:
            # 节点模式映射
            mode_map = {'standalone': 0, 'network': 1, 'virtual': 2}
            node_mode = mode_map.get(node_settings.get('nodeMode', 'virtual'), 2)
        
            # 节点属性映射
            type_map = {'normal': 0, 'mother': 1}
            node_type = type_map.get(node_settings.get('nodeType', 'normal'), 0)
        
            # 编码映射
            coding_map = {'4/5': 1, '4/6': 2, '4/7': 3, '4/8': 4}
        
            # 构建消息内容
            message_content = struct.pack('B', node_settings.get('nodeId', 1))  # 节点ID
            message_content += struct.pack('B', node_mode)  # 节点模式
            message_content += struct.pack('B', node_settings.get('totalNodes', 1))  # 组网总节点数
            message_content += struct.pack('B', node_type)  # 节点属性
            message_content += struct.pack('>I', node_settings.get('frequency', 900000))  # 工作频率 (4字节大端序)
            message_content += struct.pack('B', node_settings.get('attenuation', 10))  # 通道衰减
        
            # 前向链路参数
            forward = node_settings.get('forward', {})
            message_content += struct.pack('>I', forward.get('bandwidth', 125))  # 带宽
            message_content += struct.pack('B', forward.get('spreadingFactor', 7))  # 扩频因子
            forward_coding = coding_map.get(forward.get('coding', '4/5'), 1)
            message_content += struct.pack('B', forward_coding)  # 编码
        
            # 反向链路参数
            backward = node_settings.get('backward', {})
            message_content += struct.pack('>I', backward.get('bandwidth', 125))  # 带宽
            message_content += struct.pack('B', backward.get('spreadingFactor', 7))  # 扩频因子
            backward_coding = coding_map.get(backward.get('coding', '4/5'), 1)
            message_content += struct.pack('B', backward_coding)  # 编码
            message_content += struct.pack('B', backward.get('spreadingFactor2', 7))  # 扩频因子2
        
            # 构建完整消息 (消息类型 0x08)
            full_message = build_message(0x08, message_content)
        
            # 获取目标配置
            target = node_settings.get('target', {})
            target_ip = target.get('ip', target_ip)
            target_port = target.get('port', target_port)
        
            # 发送UDP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(full_message, (target_ip, target_port))
        
            logger.info(f"✅ 节点配置已发送到 {target_ip}:{target_port}")
            return True
        
        except Exception as e:
            logger.error(f"❌ 发送节点配置失败: {e}")
            return False