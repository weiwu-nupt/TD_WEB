#!/usr/bin/env python3
# api/parameter_routes.py - 参数设置API路由
from fastapi import APIRouter, HTTPException
import logging

from models import AllChannelParameters
from config import current_parameters
from response_waiter import ResponseWaiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Parameters"])

# 这个对象会在main.py中注入
udp_sender = None

def init_sender(sender):
    """初始化发送器引用"""
    global udp_sender
    udp_sender = sender

@router.get("/parameters")
async def get_parameters():
    """读取所有通道参数 - 通过FPGA读取"""
    try:
        logger.info("开始读取通道参数...")
        
        # 定义地址映射
        # 上行通道: 0x2000-0x2004
        # 上行干扰: 0x2010-0x2014
        # 下行通道: 0x2020-0x2024
        address_map = {
            "uplink": list(range(0x2000, 0x2005)),
            "uplink_interference": list(range(0x2010, 0x2015)),
            "downlink": list(range(0x2020, 0x2025))
        }
        
        # 存储读取结果
        read_success = 0
        
        for channel, addresses in address_map.items():
            for i, address in enumerate(addresses):
                # 创建等待请求
                request_id = ResponseWaiter.create_request("fpga_read")
                
                # 发送FPGA读取命令
                success, _, _ = udp_sender.send_fpga_operation(
                    operation_type=0,
                    address=address,
                    target_ip="127.0.0.1"
                )
                
                if not success:
                    logger.error(f"发送FPGA读取命令失败: {channel}[{i}]")
                    continue
                
                # 等待FPGA响应
                response = await ResponseWaiter.wait_for_response(request_id, timeout=2)
                
                if response:                 
                    read_success += 1
        
        # 如果成功读取大部分参数
        if read_success >= 9:  # 至少读取60%
            logger.info("通道参数读取成功")
        else:
            logger.warning("读取通道参数超时")
        
    except Exception as e:
        logger.error(f"读取参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parameters")
async def write_parameters(params: AllChannelParameters):
    """写入所有通道参数 - 通过FPGA写入"""
    try:
        logger.info("开始写入通道参数...")
        
        # 编码映射
        def coding_to_value(coding: str) -> int:
            return int(coding.split('/')[1]) - 5
        
        # 构建写入列表
        write_list = []
        
        # 上行通道
        write_list.extend([
            (0x2000, params.uplink.bandwidth),
            (0x2001, coding_to_value(params.uplink.coding)),
            (0x2002, params.uplink.spreading_factor),
            (0x2003, params.uplink.center_frequency),
            (0x2004, int(params.uplink.power * 100))
        ])
        
        # 上行干扰
        write_list.extend([
            (0x2010, params.uplink_interference.bandwidth),
            (0x2011, coding_to_value(params.uplink_interference.coding)),
            (0x2012, params.uplink_interference.spreading_factor),
            (0x2013, params.uplink_interference.center_frequency),
            (0x2014, int(params.uplink_interference.power * 100))
        ])
        
        # 下行通道
        write_list.extend([
            (0x2020, params.downlink.bandwidth),
            (0x2021, coding_to_value(params.downlink.coding)),
            (0x2022, params.downlink.spreading_factor),
            (0x2023, params.downlink.center_frequency),
            (0x2024, int(params.downlink.power * 100))
        ])
        
        # # 写入计数
        # success_count = 0
        
        # 依次写入
        for address, value in write_list:
        #     request_id = ResponseWaiter.create_request("fpga_write")
            
            success, _, _ = udp_sender.send_fpga_operation(
                operation_type=1,
                address=address,
                data=value,
                target_ip="127.0.0.1"
            )
            
        #     if not success:
        #         logger.error(f"发送FPGA写入命令失败: 地址=0x{address:08X}")
        #         continue
            
        #     response = await ResponseWaiter.wait_for_response(request_id, timeout=2)
            
        #     if response:
        #         success_count += 1
        #         logger.info(f"写入参数成功: 地址=0x{address:08X}, 值={value}")
        #     else:
        #         logger.warning(f"写入参数超时: 地址=0x{address:08X}")
        
        # # 如果大部分参数写入成功
        # if success_count >= 9:
        #     # 更新本地缓存
        #     current_parameters["uplink"] = params.uplink.dict()
        #     current_parameters["uplink_interference"] = params.uplink_interference.dict()
        #     current_parameters["downlink"] = params.downlink.dict()
            
        #     logger.info("通道参数写入成功")
            
        #     return {
        #         "success": True,
        #         "data": current_parameters,
        #         "message": f"参数写入成功 ({success_count}/15)"
        #     }
        # else:
        #     return {
        #         "success": False,
        #         "message": f"写入失败，仅成功 {success_count}/15 个参数",
        #         "data": params.dict()
        #     }
        
    except Exception as e:
        logger.error(f"写入参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))