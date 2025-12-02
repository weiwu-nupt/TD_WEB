#!/usr/bin/env python3
# api/virtual_routes.py - 虚实融合系统专用API路由
from fastapi import APIRouter, HTTPException
import logging
from models import NodeSettings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/virtual", tags=["Virtual"])

def init_sender(sender):
    """初始化发送器引用"""
    global udp_sender
    udp_sender = sender

@router.post("/node-settings")
async def send_node_settings(settings: NodeSettings):
    """发送节点配置到目标设备"""
    try:
        logger.info("📤 准备发送节点配置...")
        
        if not udp_sender:
            raise HTTPException(status_code=500, detail="UDP发送器未初始化")
        
        # 转换为字典
        settings_dict = settings.dict()
        
        # 发送节点配置
        success = udp_sender.send_node_operation(settings_dict)
        
        if not success:
            raise HTTPException(status_code=500, detail="节点配置发送失败")
        
        return {
            "success": True,
            "message": "节点配置发送成功",
            "data": settings_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 发送节点配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))