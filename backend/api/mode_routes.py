#!/usr/bin/env python3
# api/mode_routes.py - 系统模式切换API路由
from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime

from config import SystemMode, current_mode
from udp_receiver import get_message_queue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mode", tags=["Mode"])

# UDP接收器引用
udp_receiver = None

def init_receiver(receiver):
    """初始化接收器引用"""
    global udp_receiver
    udp_receiver = receiver

@router.get("/current")
async def get_current_mode():
    """获取当前系统模式"""
    return {
        "success": True,
        "data": {
            "mode": current_mode["mode"],
            "last_switch_time": current_mode["last_switch_time"],
            "receiver_status": udp_receiver.get_status() if udp_receiver else None
        }
    }

@router.post("/switch/{mode}")
async def switch_mode(mode: SystemMode):
    """切换系统模式"""
    try:
        old_mode = current_mode["mode"]
        
        if old_mode == mode:
            return {
                "success": True,
                "message": f"已经处于{mode}模式",
                "data": current_mode
            }
        
        logger.info(f"🔄 切换系统模式: {old_mode} → {mode}")
        
        # 清空消息队列
        message_queue = get_message_queue()
        old_count = len(message_queue)
        message_queue.clear()
        logger.info(f"模式切换时清空了 {old_count} 条旧消息")
        
        # 更新模式
        current_mode["mode"] = mode
        current_mode["last_switch_time"] = datetime.now().isoformat()
        
        logger.info(f"✅ 系统模式已切换到: {mode}")
        
        return {
            "success": True,
            "message": f"系统模式已切换到: {mode}",
            "data": current_mode
        }
        
    except Exception as e:
        logger.error(f"切换系统模式失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))