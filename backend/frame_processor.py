#!/usr/bin/env python3
# frame_processor.py - 帧处理逻辑
import struct
import logging
from config import (
    FRAME_TYPE_VIRTUAL_SEND, FRAME_TYPE_VIRTUAL_RECEIVE, 
    FRAME_TYPE_FPGA, FRAME_TYPE_LORA, get_frame_type_name, CONFIG
)

logger = logging.getLogger(__name__)

udp_sender = None

def init_sender(sender):
    """初始化发送器引用"""
    global udp_sender
    udp_sender = sender

def process_virtual_send_frame(parsed_msg: dict, addr: tuple) -> dict:
    """
    信号发送帧 0x00
    直接透传到ARM
    """
    try:
        message_content = parsed_msg.get("message_content", b"")
        
        if len(message_content) < 8:
            raise ValueError("信号发送帧数据长度不足")
        
        # 解析: 发送时间(4) + 信号传播参数(4) + 数据包(N)
        send_time = struct.unpack('>I', message_content[0:4])[0]
        propagation_param = struct.unpack('>I', message_content[4:8])[0]
        data_packet = message_content[8:]
        
        # 🔧 透传到ARM
        if udp_sender:
            # 重新构建完整消息并发送
            from frame_parser import build_message
            full_message = build_message(FRAME_TYPE_VIRTUAL_SEND, message_content)
            
            success = udp_sender.send_raw_data(
                full_message,
                target_ip=CONFIG["arm_ip"],
                target_port=CONFIG["arm_port"]
            )
        
        return {
            "message_type": FRAME_TYPE_VIRTUAL_SEND,
            "virtual_send_info": {
                "send_time": send_time,
                "propagation_param": propagation_param,
                "data_hex": data_packet.hex().upper()
            }
        }
        
    except Exception as e:
        logger.error(f"处理信号发送帧时发生错误: {e}")
        return {
            "message_type": FRAME_TYPE_VIRTUAL_SEND,
            "frame_name": "信号发送帧",
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }

def process_virtual_receive_frame(parsed_msg: dict, addr: tuple) -> dict:
    """
    处理虚实节点信号接收帧 0x01
    直接透传到ARM
    """
    try:
        message_content = parsed_msg.get("message_content", b"")
        
        if len(message_content) < 8:
            raise ValueError("信号接收帧数据长度不足")
        
        # 解析: 接收时间(4) + 接收时间戳(4) + 数据包(N)
        receive_time = struct.unpack('>I', message_content[0:4])[0]
        receive_timestamp = struct.unpack('>I', message_content[4:8])[0]
        data_packet = message_content[8:]
        
        if udp_sender:
            from frame_parser import build_message
            full_message = build_message(FRAME_TYPE_VIRTUAL_RECEIVE, message_content)
            
            success = udp_sender.send_raw_data(
                full_message,
                target_ip=CONFIG["arm_ip"],
                target_port=CONFIG["arm_port"]
            )
        
        return {
            "message_type": FRAME_TYPE_VIRTUAL_RECEIVE,
            "virtual_receive_info": {
                "receive_time": receive_time,
                "receive_timestamp": receive_timestamp,
                "data_hex": data_packet.hex().upper()
            }
        }
        
    except Exception as e:
        logger.error(f"处理虚实节点信号接收帧时发生错误: {e}")
        return {
            "message_type": FRAME_TYPE_VIRTUAL_RECEIVE,
            "frame_name": "虚实节点信号接收帧",
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }

def process_fpga_frame(parsed_msg: dict, addr: tuple) -> dict:
    """
    处理FPGA读写帧 0x05
    
    帧格式：
    - operation_type (1字节): 0=读, 1=写
    - operation_count (1字节): 操作次数
    - 操作数据: [address(4字节) + data(4字节)] * N
    """
    try:
        message_content = parsed_msg.get("message_content", b"")
        
        if len(message_content) < 2:
            raise ValueError("FPGA数据长度不足（至少需要2字节）")
        
        # 🔧 解析操作类型和操作次数
        operation_type = message_content[0]
        operation_count = message_content[1]
        
        # 🔧 解析每个操作
        operations = []
        offset = 2  # 跳过前2个字节
        
        for i in range(operation_count):
            # 检查剩余数据是否足够
            if offset + 8 > len(message_content):
                logger.warning(f"⚠️ FPGA操作#{i+1} 数据不足，跳过")
                break
            
            # 解析地址（4字节大端序）
            address = struct.unpack('>I', message_content[offset:offset+4])[0]
            
            # 解析数据（4字节大端序）
            data = struct.unpack('>I', message_content[offset+4:offset+8])[0]
            
            operations.append({
                "index": i + 1,
                "address": address,
                "value": data
            })
            
            offset += 8  # 下一个操作
        
        # 🔧 构建返回结果（会被加入到消息队列）
        result = {
            "message_type": 0x05,
            "fpga_operation_info": {
                "operation_type_code": operation_type,
                "operation_count": operation_count,
                "operations": operations,
                "total_operations_parsed": len(operations)
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 处理FPGA帧时发生错误: {e}", exc_info=True)
        return {
            "message_type": 0x05,
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }

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
            "message_type": FRAME_TYPE_LORA,
            "frame_name": "LoRa接收帧",
            "lora_receive_info": {
                "frame_count": frame_count,
                "duration_ms": duration,
                "data_content": data_hex
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
        if message_type == FRAME_TYPE_VIRTUAL_SEND:
            return process_virtual_send_frame(parsed_msg, addr)
        elif message_type == FRAME_TYPE_VIRTUAL_RECEIVE:
            return process_virtual_receive_frame(parsed_msg, addr)
        elif message_type == FRAME_TYPE_FPGA:
            return process_fpga_frame(parsed_msg, addr)
        elif message_type == FRAME_TYPE_LORA:
            return process_lora_frame(parsed_msg, addr)
        
    except Exception as e:
        logger.error(f"处理消息类型 0x{message_type:02X} 时发生错误: {e}")