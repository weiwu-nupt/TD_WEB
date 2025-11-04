from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import logging
import asyncio
import json

from config import CONFIG
from models import FPGAReadRequest, FPGAWriteRequest, LoRaSendMessage
from response_waiter import ResponseWaiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["LoRa"])

# 这个对象会在main.py中注入
udp_sender = None

def init_sender(sender):
    """初始化发送器引用"""
    global udp_sender
    udp_sender = sender

@router.post("/lora/send")
async def lora_send_message(msg: LoRaSendMessage):
    """LoRa发送消息"""
    try:
        success = udp_sender.send_lora_message(
            timing_enable=msg.timing_enable,
            timing_time=msg.timing_time,
            data_content=msg.data_content,
            target_ip=CONFIG["arm_ip"],
            target_port=CONFIG["arm_port"]
        )
        
        if success:
            return {
                "success": True,
                "message": "LoRa消息发送成功",
                "details": {
                    "frame_count": msg.frame_count
                }
            }
        else:
            raise HTTPException(status_code=500, detail="LoRa消息发送失败")
            
    except Exception as e:
        logger.error(f"LoRa发送失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # SSE 推送 LoRa 接收消息
@router.get("/lora/stream")
async def lora_receive_stream():
    """SSE流式推送LoRa接收消息"""
    
    async def event_generator():
        """生成SSE事件"""
        from udp_receiver import get_message_queue
        
        message_queue = get_message_queue()
        last_checked_count = 0
        
        # 发送初始连接消息
        yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE连接成功'})}\n\n"
        logger.info("SSE客户端已连接")
        
        try:
            while True:
                current_count = len(message_queue)
                
                # 检查是否有新消息
                if current_count > last_checked_count:
                    # 获取新消息
                    new_messages = list(message_queue)[last_checked_count:]
                    
                    for msg in new_messages:
                        # 只推送LoRa接收消息
                        if msg.get("message_type") == 0x07 and "lora_receive_info" in msg:
                            lora_info = msg["lora_receive_info"]
                            
                            event_data = {
                                "type": "lora_receive",
                                "data": {
                                    "receive_time": msg.get("receive_time"),
                                    "frame_count": lora_info.get("frame_count", 0),
                                    "receive_timestamp": lora_info["receive_timestamp"],
                                    "complete_timestamp": lora_info["complete_timestamp"],
                                    "duration_ms": lora_info["duration_ms"],
                                    "data_hex": lora_info["data_hex"],
                                    "data_bytes": lora_info["data_bytes"]
                                }
                            }
                            
                            yield f"data: {json.dumps(event_data)}\n\n"
                            logger.info(f"SSE推送LoRa接收消息: 帧#{lora_info.get('frame_count', 0)}")
                    
                    last_checked_count = current_count
                
                # 每300ms检查一次
                await asyncio.sleep(0.3)
                
        except asyncio.CancelledError:
            logger.info("SSE客户端断开连接")
            raise
        except Exception as e:
            logger.error(f"SSE流错误: {e}")
            raise
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
        }
    )