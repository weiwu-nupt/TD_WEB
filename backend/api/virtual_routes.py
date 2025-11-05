#!/usr/bin/env python3
# api/virtual_routes.py - 虚实融合系统专用API路由
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
from datetime import datetime

from udp_receiver import get_message_queue
from config import SystemMode, current_mode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/virtual", tags=["Virtual"])

async def virtual_event_stream():
    """
    虚实融合事件流（SSE）
    
    推送 0x00 (信号发送) 和 0x01 (信号接收) 帧
    """
    logger.info("✅ 虚实融合SSE客户端已连接")
    
    # 发送初始连接消息
    yield f"data: {json.dumps({'type': 'connected', 'message': '虚实融合SSE已连接', 'timestamp': datetime.now().isoformat()})}\n\n"
    
    last_processed_count = 0
    
    try:
        while True:
            # 只在虚实融合模式下推送
            if current_mode["mode"] != SystemMode.VIRTUAL:
                await asyncio.sleep(1)
                continue
            
            message_queue = get_message_queue()
            
            # 🔧 遍历队列，查找并处理 0x00 和 0x01 消息
            messages_to_remove = []
            
            for idx, msg in enumerate(list(message_queue)):
                msg_type = msg.get("message_type")
                
                # 只处理 0x00 (发送) 和 0x01 (接收)
                if msg_type in [0x00, 0x01]:
                    # 准备推送的事件数据
                    event_data = {
                        "type": "virtual_event",
                        "data": msg
                    }
                    
                    yield f"data: {json.dumps(event_data)}\n\n"
                    logger.info(f"📤 推送虚实融合事件: 类型=0x{msg_type:02X}")
                    
                    # 🔧 标记为待移除
                    messages_to_remove.append(idx)
            
            # 🔧 从队列中移除已推送的消息（倒序移除以保持索引正确）
            for idx in reversed(messages_to_remove):
                try:
                    message_queue.pop(idx)
                except IndexError:
                    logger.warning(f"⚠️ 无法移除索引 {idx}，队列长度: {len(message_queue)}")
            
                await asyncio.sleep(0.5)  # 每500ms检查一次
            
    except asyncio.CancelledError:
        logger.info("⏹️ 虚实融合SSE连接已关闭")
        raise

@router.get("/stream")
async def virtual_stream():
    """
    虚实融合事件流端点
    
    返回 Server-Sent Events (SSE) 流
    """
    return StreamingResponse(
        virtual_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/status")
async def get_virtual_status():
    """获取虚实融合系统状态"""
    from main import virtual_monitor
    
    monitor_status = virtual_monitor.get_status() if virtual_monitor else None
    
    return {
        "success": True,
        "data": {
            "current_mode": current_mode["mode"],
            "monitor_status": monitor_status
        }
    }