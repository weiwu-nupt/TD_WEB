#!/usr/bin/env python3
# api/fpga_lora_routes.py - FPGA和LoRa测试API路由
from fastapi import APIRouter, HTTPException
import logging

from models import FPGAReadRequest, FPGAWriteRequest, LoRaSendMessage
from response_waiter import ResponseWaiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["FPGA & LoRa"])

# 这个对象会在main.py中注入
udp_sender = None

def init_sender(sender):
    """初始化发送器引用"""
    global udp_sender
    udp_sender = sender

@router.post("/fpga/read")
async def fpga_read_single(request: FPGAReadRequest):
    """FPGA单条读操作"""
    try:
        request_id = ResponseWaiter.create_request("fpga_read")
        
        success, local_port, target_port = udp_sender.send_fpga_operation(
            operation_type=0,
            address=request.address,
            target_ip="127.0.0.1"
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="FPGA读操作发送失败")
        
        response = await ResponseWaiter.wait_for_response(request_id, timeout=5)
        
        if response:
            return {
                "success": True,
                "message": "FPGA读操作成功",
                "data": response.get("fpga_info", {})
            }
        else:
            raise HTTPException(status_code=408, detail="等待响应超时")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FPGA读操作失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fpga/write")
async def fpga_write_single(request: FPGAWriteRequest):
    """FPGA单条写操作"""
    try:
        request_id = ResponseWaiter.create_request("fpga_write")
        
        success, local_port, target_port = udp_sender.send_fpga_operation(
            operation_type=1,
            address=request.address,
            data=request.data,
            target_ip="127.0.0.1"
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="FPGA写操作发送失败")
        
        response = await ResponseWaiter.wait_for_response(request_id, timeout=5)
        
        if response:
            return {
                "success": True,
                "message": "FPGA写操作成功",
                "data": response.get("fpga_info", {})
            }
        else:
            raise HTTPException(status_code=408, detail="等待响应超时")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FPGA写操作失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lora/send")
async def lora_send_message(msg: LoRaSendMessage):
    """LoRa发送消息"""
    try:
        success, local_port, target_port = udp_sender.send_lora_message(
            timing_enable=msg.timing_enable,
            timing_time=msg.timing_time,
            data_content=msg.data_content,
            target_ip="127.0.0.1"
        )
        
        if success:
            return {
                "success": True,
                "message": "LoRa消息发送成功",
                "details": {
                    "timing_enable": msg.timing_enable,
                    "timing_time": msg.timing_time,
                    "data_length": len(msg.data_content),
                    "from": f"127.0.0.1:{local_port}",
                    "to": f"127.0.0.1:{target_port}"
                }
            }
        else:
            raise HTTPException(status_code=500, detail="LoRa消息发送失败")
            
    except Exception as e:
        logger.error(f"LoRa发送失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))