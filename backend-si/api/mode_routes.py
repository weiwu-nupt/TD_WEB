#!/usr/bin/env python3
# api/mode_routes.py - 系统模式切换API路由
from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime
from typing import Callable, Optional

from config import SystemMode, current_mode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mode", tags=["Mode"])

# 🔧 虚实融合监控器获取函数
get_virtual_monitor: Optional[Callable] = None

serial_receiver = None

def init_receiver(receiver):
    """初始化接收器引用"""
    global serial_receiver
    serial_receiver = receiver

def init_virtual_monitor(monitor_getter: Callable):
    """
    初始化虚实融合监控器获取函数
    
    Args:
        monitor_getter: 返回 VirtualMonitor 实例的函数
    """
    global get_virtual_monitor
    get_virtual_monitor = monitor_getter
    logger.info("✅ 虚实融合监控器已注入到模式路由")

@router.get("/current")
async def get_current_mode():
    """获取当前系统模式"""
    monitor_status = None
    
    if get_virtual_monitor:
        monitor = get_virtual_monitor()
        if monitor:
            monitor_status = monitor.get_status()
    
    return {
        "success": True,
        "data": {
            "mode": current_mode["mode"],
            "last_switch_time": current_mode["last_switch_time"],
            "receiver_status": serial_receiver.get_status() if serial_receiver else None,
            "virtual_monitor_status": monitor_status
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
        message_queue = serial_receiver.get_message_queue()
        old_count = len(message_queue)
        message_queue.clear()
        logger.info(f"模式切换时清空了 {old_count} 条旧消息")
        
        # 🔧 根据模式启动/停止虚实融合监控器
        if get_virtual_monitor:
            monitor = get_virtual_monitor()
            if monitor:
                if mode == SystemMode.VIRTUAL:
                    # 切换到虚实融合模式 → 启动监控器
                    monitor.start()
                    logger.info("✅ VirtualMonitor 已启动")
                else:
                    # 切换到地面检测模式 → 停止监控器
                    monitor.stop()
                    logger.info("⏹️ VirtualMonitor 已停止")
        
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