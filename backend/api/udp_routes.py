#!/usr/bin/env python3
# api/udp_routes.py - UDP相关API路由
from fastapi import APIRouter, HTTPException
import logging
from  models import UDPConfig, UDPMessage
from config import CONFIG, current_config
from udp_receiver import get_message_queue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/udp", tags=["UDP"])

# 这些对象会在main.py中注入
udp_receiver = None
udp_sender = None

def init_udp_objects(receiver, sender):
    """初始化UDP对象引用"""
    global udp_receiver, udp_sender
    udp_receiver = receiver
    udp_sender = sender

@router.get("/config")
async def get_udp_config():
    """获取当前UDP配置"""
    return {
        "success": True,
        "data": current_config,
        "receiver_status": udp_receiver.get_status()
    }

@router.post("/config")
async def update_udp_config(config: UDPConfig):
    """更新UDP端口配置"""
    try:
        # 更新全局配置
        CONFIG["udp_receive_port"] = config.receivePort
        
        # 重启接收器到新端口
        success = udp_receiver.start(config.receivePort)
        
        if success:
            logger.info(f"UDP配置已更新 - 接收端口: {config.receivePort}")
            return {
                "success": True, 
                "message": f"UDP接收端口配置成功: {config.receivePort}",
                "data": CONFIG["udp_receive_port"]
            }
        else:
            raise HTTPException(status_code=500, detail="UDP接收器启动失败")
            
    except Exception as e:
        logger.error(f"更新UDP配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}")

@router.post("/send")
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

@router.get("/status")
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

@router.get("/messages")
async def get_messages(limit: int = 50):
    """获取最近的消息"""
    try:
        message_queue = get_message_queue()
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

@router.delete("/messages")
async def clear_messages():
    """清空消息队列"""
    try:
        message_queue = get_message_queue()
        message_queue.clear()
        return {
            "success": True,
            "message": "消息队列已清空"
        }
    except Exception as e:
        logger.error(f"清空消息队列失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/frame-stats")
async def get_frame_stats():
    """获取帧类型统计"""
    try:
        message_queue = get_message_queue()
        stats = {
            "total_frames": len(message_queue),
            "frame_types": {},
            "recent_activity": []
        }
        
        # 统计帧类型
        for msg in message_queue:
            frame_type = msg.get("message_type", 0)
            frame_name = msg.get("frame_name", "未知")
            
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