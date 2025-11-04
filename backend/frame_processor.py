#!/usr/bin/env python3
# frame_processor.py - 帧处理逻辑
import struct
import logging
from config import (
    FRAME_TYPE_BROADCAST, FRAME_TYPE_TIMESTAMP, FRAME_TYPE_LINK_STATUS,
    FRAME_TYPE_FPGA, FRAME_TYPE_LORA, get_frame_type_name
)

logger = logging.getLogger(__name__)

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
        operation_type = message_content[0]
        operation_count = message_content[1]
        address = struct.unpack('>I', message_content[2:6])[0]

        # if address == 0x123:

        
        # operation_info = {
        #     "operation_type": operation_type,
        #     "operation_name": "读操作" if operation_type == 0 else "写操作",
        #     "operation_count": operation_count,
        #     "address": f"0x{address:08X}",
        #     "address_decimal": address
        # }
        
        # # 如果是写操作或读操作响应,解析数据
        # if len(message_content) >= 10:
        #     data_value = struct.unpack('>I', message_content[6:10])[0]
        #     operation_info["data"] = f"0x{data_value:08X}"
        #     operation_info["data_decimal"] = data_value
        
        # processed_data = {
        #     "frame_name": "FPGA操作帧",
        #     "processing_result": f"FPGA{operation_info['operation_name']}处理完成",
        #     "source_ip": addr[0],
        #     "source_port": addr[1],
        #     "fpga_info": operation_info
        # }
        return True
        
    except Exception as e:
        logger.error(f"处理FPGA帧时发生错误: {e}")

def process_lora_frame(parsed_msg: dict, addr: tuple) -> dict:
    """处理LoRa收发帧 0x07"""
    try:
        message_content = parsed_msg.get("message_content", b"")
        
        if len(message_content) < 9:
            raise ValueError("LoRa数据长度不足")
        
        # receive_timestamp(4) + complete_timestamp(4) + frame_count(1) + data(n)
            
        receive_timestamp = struct.unpack('>I', message_content[0:4])[0]
        complete_timestamp = struct.unpack('>I', message_content[4:8])[0]
        frame_count = message_content[8]  # 帧计数
        data_bytes = message_content[9:]
        data_hex = data_bytes.hex().upper()
            
        duration = complete_timestamp - receive_timestamp
            
        processed_data = {
            "frame_name": "LoRa接收帧",
            "lora_receive_info": {
                "frame_count": frame_count,
                "duration_ms": duration,
                "data_content": data_hex,
                "content_length": len(data_bytes)
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
        
    except Exception as e:
        logger.error(f"处理消息类型 0x{message_type:02X} 时发生错误: {e}")