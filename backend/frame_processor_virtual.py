#!/usr/bin/env python3
# frame_processor_virtual.py - 虚实融合模式帧处理逻辑
import struct
import logging
from config import (
    FRAME_TYPE_VIRTUAL_SEND, FRAME_TYPE_VIRTUAL_RECEIVE,
    FRAME_TYPE_VIRTUAL_TIMESTAMP, FRAME_TYPE_VIRTUAL_LINK,
    get_frame_type_name, CONFIG
)

logger = logging.getLogger(__name__)

# 全局 UDP 发送器引用
udp_sender = None

def init_sender(sender):
    """初始化发送器引用"""
    global udp_sender
    udp_sender = sender

def process_virtual_send_frame(parsed_msg: dict, addr: tuple) -> dict:
    """
    处理虚实节点信号发送帧 0x00
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
        
        logger.info(f"📤 虚实节点信号发送帧: 发送时间={send_time}, 传播参数={propagation_param}, 数据长度={len(data_packet)}")
        
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
            
            if success:
                logger.info(f"✅ 虚实节点信号发送帧已透传到ARM ({CONFIG['arm_ip']}:{CONFIG['arm_port']})")
            else:
                logger.error("❌ 透传到ARM失败")
        
        return {
            "message_type": FRAME_TYPE_VIRTUAL_SEND,
            "frame_name": "虚实节点信号发送帧",
            "processing_result": "透传到ARM",
            "source_ip": addr[0],
            "source_port": addr[1],
            "virtual_send_info": {
                "send_time": send_time,
                "propagation_param": propagation_param,
                "data_length": len(data_packet),
                "data_hex": data_packet.hex().upper()
            }
        }
        
    except Exception as e:
        logger.error(f"处理虚实节点信号发送帧时发生错误: {e}")
        return {
            "message_type": FRAME_TYPE_VIRTUAL_SEND,
            "frame_name": "虚实节点信号发送帧",
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
        
        logger.info(f"📥 虚实节点信号接收帧: 接收时间={receive_time}, 时间戳={receive_timestamp}, 数据长度={len(data_packet)}")
        
        # 🔧 透传到ARM
        if udp_sender:
            from frame_parser import build_message
            full_message = build_message(FRAME_TYPE_VIRTUAL_RECEIVE, message_content)
            
            success = udp_sender.send_raw_data(
                full_message,
                target_ip=CONFIG["arm_ip"],
                target_port=CONFIG["arm_port"]
            )
            
            if success:
                logger.info(f"✅ 虚实节点信号接收帧已透传到ARM ({CONFIG['arm_ip']}:{CONFIG['arm_port']})")
            else:
                logger.error("❌ 透传到ARM失败")
        
        return {
            "message_type": FRAME_TYPE_VIRTUAL_RECEIVE,
            "frame_name": "虚实节点信号接收帧",
            "processing_result": "透传到ARM",
            "source_ip": addr[0],
            "source_port": addr[1],
            "virtual_receive_info": {
                "receive_time": receive_time,
                "receive_timestamp": receive_timestamp,
                "data_length": len(data_packet),
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

def process_virtual_timestamp_frame(parsed_msg: dict, addr: tuple) -> dict:
    """
    处理虚实节点发送时间戳回传帧 0x02
    广播给所有客户端
    """
    try:
        message_content = parsed_msg.get("message_content", b"")
        
        if len(message_content) < 8:
            raise ValueError("时间戳回传帧数据长度不足")
        
        # 解析: 发送完成时间(4) + 链路时间戳(4) + 数据包(N)
        send_complete_time = struct.unpack('>I', message_content[0:4])[0]
        link_timestamp = struct.unpack('>I', message_content[4:8])[0]
        data_packet = message_content[8:]
        
        logger.info(f"⏱️ 虚实节点时间戳回传帧: 完成时间={send_complete_time}, 链路时间戳={link_timestamp}, 数据长度={len(data_packet)}")
        
        # 🔧 广播（这里通过消息队列，前端SSE会接收）
        return {
            "message_type": FRAME_TYPE_VIRTUAL_TIMESTAMP,
            "frame_name": "虚实节点发送时间戳回传帧",
            "processing_result": "广播",
            "source_ip": addr[0],
            "source_port": addr[1],
            "broadcast": True,  # 🔧 标记为广播消息
            "virtual_timestamp_info": {
                "send_complete_time": send_complete_time,
                "link_timestamp": link_timestamp,
                "data_length": len(data_packet),
                "data_hex": data_packet.hex().upper()
            }
        }
        
    except Exception as e:
        logger.error(f"处理虚实节点时间戳回传帧时发生错误: {e}")
        return {
            "message_type": FRAME_TYPE_VIRTUAL_TIMESTAMP,
            "frame_name": "虚实节点发送时间戳回传帧",
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }

def process_virtual_link_frame(parsed_msg: dict, addr: tuple) -> dict:
    """
    处理虚实节点链路状态帧 0x03
    广播给所有客户端
    """
    try:
        message_content = parsed_msg.get("message_content", b"")
        
        if len(message_content) < 12:
            raise ValueError("链路状态帧数据长度不足")
        
        # 解析: 接收起始时间(4) + 备份(8)
        receive_start_time = struct.unpack('>I', message_content[0:4])[0]
        backup_data = struct.unpack('>Q', message_content[4:12])[0]
        
        logger.info(f"📊 虚实节点链路状态帧: 起始时间={receive_start_time}, 备份数据={backup_data}")
        
        # 🔧 广播
        return {
            "message_type": FRAME_TYPE_VIRTUAL_LINK,
            "frame_name": "虚实节点链路状态帧",
            "processing_result": "广播",
            "source_ip": addr[0],
            "source_port": addr[1],
            "broadcast": True,  # 🔧 标记为广播消息
            "virtual_link_info": {
                "receive_start_time": receive_start_time,
                "backup_data": backup_data
            }
        }
        
    except Exception as e:
        logger.error(f"处理虚实节点链路状态帧时发生错误: {e}")
        return {
            "message_type": FRAME_TYPE_VIRTUAL_LINK,
            "frame_name": "虚实节点链路状态帧",
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }

def process_virtual_frame_by_type(parsed_msg: dict, addr: tuple) -> dict:
    """根据消息类型处理虚实融合模式的消息"""
    message_type = parsed_msg.get("message_type", 0)
    
    try:
        if message_type == FRAME_TYPE_VIRTUAL_SEND:
            return process_virtual_send_frame(parsed_msg, addr)
        elif message_type == FRAME_TYPE_VIRTUAL_RECEIVE:
            return process_virtual_receive_frame(parsed_msg, addr)
        elif message_type == FRAME_TYPE_VIRTUAL_TIMESTAMP:
            return process_virtual_timestamp_frame(parsed_msg, addr)
        elif message_type == FRAME_TYPE_VIRTUAL_LINK:
            return process_virtual_link_frame(parsed_msg, addr)
        else:
            logger.warning(f"未知虚实融合消息类型: 0x{message_type:02X}")
            return {
                "message_type": message_type,
                "frame_name": f"未知帧类型(0x{message_type:02X})",
                "processing_result": "未知消息类型",
                "error": "unknown_type"
            }
        
    except Exception as e:
        logger.error(f"处理虚实融合消息类型 0x{message_type:02X} 时发生错误: {e}")
        return {
            "message_type": message_type,
            "frame_name": "错误帧",
            "processing_result": f"处理失败: {str(e)}",
            "error": "processing_error"
        }