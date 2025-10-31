#!/usr/bin/env python3
# response_waiter.py - 响应等待管理器
import uuid
import time
import asyncio
import threading
import logging
from typing import Dict, Any, Optional
from config import FRAME_TYPE_FPGA, FRAME_TYPE_LORA, RESPONSE_TIMEOUT

logger = logging.getLogger(__name__)

# 等待响应的请求字典
pending_requests: Dict[str, Dict[str, Any]] = {}

class ResponseWaiter:
    """响应等待管理器"""
    
    @staticmethod
    def create_request(request_type: int) -> str:
        """创建一个新的请求并返回request_id"""
        request_id = str(uuid.uuid4())
        # 使用 asyncio.Event 而不是 threading.Event
        pending_requests[request_id] = {
            "type": request_type,
            "event": asyncio.Event(),
            "response_data": None,
            "timestamp": time.time()
        }
        logger.info(f"创建请求等待: {request_id} - {request_type}")
        return request_id
    
    @staticmethod
    async def wait_for_response(request_id: str, timeout: float = RESPONSE_TIMEOUT) -> Optional[dict]:
        """等待响应"""
        if request_id not in pending_requests:
            logger.error(f"请求ID不存在: {request_id}")
            return None
        
        request = pending_requests[request_id]
        
        try:
            # 直接等待 asyncio.Event,不使用 to_thread
            await asyncio.wait_for(
                request["event"].wait(),
                timeout=timeout
            )
            
            response_data = request["response_data"]
            logger.info(f"收到响应: {request_id}")
            return response_data
            
        except asyncio.TimeoutError:
            logger.warning(f"等待响应超时: {request_id}")
            return None
        finally:
            # 清理请求
            if request_id in pending_requests:
                del pending_requests[request_id]
    
    @staticmethod
    def notify_response(frame_type: int):
        """通知有响应到达"""
        for request_id, request in list(pending_requests.items()):
            if ResponseWaiter._match_request(request["type"], frame_type):
                request["event"].set()
                logger.info(f"匹配到等待的请求: {request_id} - 帧类型: 0x{frame_type:02X}")
                break
    
    @staticmethod
    def _match_request(request_type: str, frame_type: int) -> bool:
        """匹配请求类型和响应"""
        # FPGA读操作响应
        if request_type == "fpga_read" and frame_type == FRAME_TYPE_FPGA:
                return True
        
        # FPGA写操作响应
        elif request_type == "fpga_write" and frame_type == FRAME_TYPE_FPGA:
                return True
        
        # LoRa接收响应
        elif request_type == "lora_send" and frame_type == FRAME_TYPE_LORA:
            return True
        
        return False