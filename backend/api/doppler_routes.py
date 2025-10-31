#!/usr/bin/env python3
# api/doppler_routes.py - 多普勒设置API路由
from fastapi import APIRouter, HTTPException
import logging

from models import DopplerSettings
from config import current_doppler_settings
from response_waiter import ResponseWaiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Doppler"])

# 这个对象会在main.py中注入
udp_sender = None

def init_sender(sender):
    """初始化发送器引用"""
    global udp_sender
    udp_sender = sender

@router.get("/doppler")
async def get_doppler_settings():
    """读取多普勒设置 - 通过FPGA读取"""
    try:
        logger.info("开始读取多普勒设置...")
        
        # 定义多普勒参数地址
        doppler_addresses = {
            "type": 0x1000,
            "frequencyMin": 0x1001,
            "frequencyMax": 0x1002,
            "rate": 0x1003,
            "period": 0x1004
        }
        
        # 存储读取结果
        read_results = {}
        
        # 依次读取每个参数
        for param_name, address in doppler_addresses.items():
            # 创建等待请求
            request_id = ResponseWaiter.create_request("fpga_read")
            
            # 发送FPGA读取命令
            success, local_port, target_port = udp_sender.send_fpga_operation(
                operation_type=0,  # 读操作
                address=address,
                target_ip="127.0.0.1"
            )
            
            if not success:
                logger.error(f"发送FPGA读取命令失败: {param_name}")
                continue
            
            # 等待FPGA响应
            response = await ResponseWaiter.wait_for_response(request_id, timeout=2)
            
            if response:
                fpga_info = response.get("fpga_info", {})
                read_results[param_name] = fpga_info.get("data_decimal", 0)
                logger.info(f"读取参数 {param_name} 成功: {read_results[param_name]}")
            else:
                logger.warning(f"读取参数 {param_name} 超时")
        
        # 如果成功读取到数据,更新设置
        if len(read_results) >= 3:  # 至少读取到3个参数
            doppler_type_map = {0: "none", 1: "constant", 2: "linear", 3: "sinusoidal", 4: "random"}
            
            current_doppler_settings["type"] = doppler_type_map.get(
                read_results.get("type", 0), "none"
            )
            current_doppler_settings["frequencyMin"] = read_results.get("frequencyMin", -1000)
            current_doppler_settings["frequencyMax"] = read_results.get("frequencyMax", 1000)
            current_doppler_settings["rate"] = read_results.get("rate", 1000) / 100.0
            current_doppler_settings["period"] = read_results.get("period", 100) / 100.0
            
            logger.info(f"多普勒设置读取成功: {current_doppler_settings}")
            
            return {
                "success": True,
                "data": current_doppler_settings,
                "message": "多普勒设置读取成功",
                "from_cache": False
            }
        else:
            logger.warning("读取参数不完整，返回缓存值")
            return {
                "success": True,
                "data": current_doppler_settings,
                "message": "读取不完整，返回缓存值",
                "from_cache": True
            }
        
    except Exception as e:
        logger.error(f"读取多普勒设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/doppler")
async def write_doppler_settings(settings: DopplerSettings):
    """写入多普勒设置 - 通过FPGA写入"""
    try:
        logger.info(f"开始写入多普勒设置: {settings.dict()}")
        
        # 类型映射
        type_map = {"none": 0, "constant": 1, "linear": 2, "sinusoidal": 3, "random": 4}
        type_value = type_map.get(settings.type, 0)
        
        # 定义要写入的参数
        write_params = {
            0x1000: type_value,
            0x1001: settings.frequencyMin,
            0x1002: settings.frequencyMax,
            0x1003: int((settings.rate or 10) * 100),
            0x1004: int((settings.period or 1) * 100)
        }
        
        # 写入计数
        success_count = 0
        
        # 依次写入每个参数
        for address, value in write_params.items():
            # 创建等待请求
            # request_id = ResponseWaiter.create_request("fpga_write")
            
            # 发送FPGA写入命令
            success, local_port, target_port = udp_sender.send_fpga_operation(
                operation_type=1,  # 写操作
                address=address,
                data=value,
                target_ip="127.0.0.1"
            )
            
            if not success:
                logger.error(f"发送FPGA写入命令失败: 地址=0x{address:08X}")
                continue
            
            # 等待FPGA响应确认
            # response = await ResponseWaiter.wait_for_response(request_id, timeout=2)
            
            # if response:
            #     success_count += 1
            #     logger.info(f"写入参数成功: 地址=0x{address:08X}, 值={value}")
            # else:
            #     logger.warning(f"写入参数超时: 地址=0x{address:08X}")
        
        # 如果大部分参数写入成功
        # if success_count >= 3:
        #     # 更新本地缓存
        #     current_doppler_settings.update(settings.dict())
            
        #     logger.info("多普勒设置写入成功")
            
        #     return {
        #         "success": True,
        #         "data": current_doppler_settings,
        #         "message": f"多普勒设置写入成功 ({success_count}/5)",
        #     }
        # else:
        #     return {
        #         "success": False,
        #         "message": f"写入失败，仅成功 {success_count}/5 个参数",
        #         "data": settings.dict()
        #     }
        
    except Exception as e:
        logger.error(f"写入多普勒设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))