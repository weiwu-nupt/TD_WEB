#!/usr/bin/env python3
# api/parameter_routes.py - 参数设置API路由
from fastapi import APIRouter, HTTPException
import logging

from models import AllChannelParameters
from config import CONFIG, current_parameters
from response_waiter import ResponseWaiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Parameters"])

udp_sender = None

def init_sender(sender):
    """初始化发送器引用"""
    global udp_sender
    udp_sender = sender

# 带宽映射
BANDWIDTH_MAP = {
    125: 0,
    250: 1,
    500: 2
}

# 编码映射
CODING_MAP = {
    '4/5': 0b001,
    '4/6': 0b010,
    '4/7': 0b011,
    '4/8': 0b100
}

def build_uplink_registers(bandwidth: int, sf: int, coding: str, data_length: int):
    """构建上行/上行干扰的两个寄存器值"""
    bw = BANDWIDTH_MAP.get(bandwidth, 0)
    base_sf = sf
    coding_rate = CODING_MAP.get(coding, 0b001)
    
    # 第一个寄存器 (0x20/0x60)
    # reg1 = (
    #     (1 << 0) |           # bit 0: 保留
    #     (1 << 1) |           # bit 1: 信号格式(0-传统)
    #     (bw << 2) |          # bit 3:2: 信号带宽
    #     (0 << 4) |           # bit 4: 头模式允许
    #     (1 << 5) |           # bit 5: 低速率
    #     (0 << 6) |           # bit 6: 交织模式
    #     (0 << 7) |           # bit 7: 保留
    #     (0 << 8) |           # bit 15:8: down-chirp数目(1)
    #     (0 << 16)            # bit 31:16: 前导码长度(8)
    # )
    reg1 = 0x80853 + (bw << 2)

    # 第二个寄存器 (0x28/0x68)
    # reg2 = (
    #     (0 << 0) |           # bit 0: 头数据使能
    #     (0 << 1) |           # bit 1: 传统lora
    #     (0 << 2) |           # bit 2: FPGA编码使能
    #     (0 << 3) |           # bit 3: 数据白化使能
    #     (base_sf << 4) |     # bit 7:4: 基础SF
    #     (0 << 8) |           # bit 11:8: 自适应SF
    #     (0 << 12) |          # bit 16:12: 头数据CRC
    #     (0 << 17) |          # bit 19:17: SF使能(000-固定SF)
    #     (1 << 20) |          # bit 20: CRC使能
    #     (coding_rate << 21)  # bit 23:21: 编码速率
    # )

    reg2 = ((data_length+1) << 24) + ((coding_rate+1) << 21) + (1 << 20) + (base_sf << 4) + 0x1000D

    
    return reg1, reg2

def build_downlink_register(bandwidth: int, sf: int, coding: str):
    """构建下行通道的寄存器值"""
    bw = BANDWIDTH_MAP.get(bandwidth, 0)
    coding_rate = 0 if coding == '4/5' else 1  # 下行只有4/5(0)和4/6(1)
    
    # reg = (
    #     (1 << 0) |           # bit 0: 接收使能(固定为1)
    #     (0 << 1) |           # bit 1: 信号格式(0-传统)
    #     (bw << 2) |          # bit 3:2: 信号带宽
    #     (sf << 4) |          # bit 7:4: 扩频因子
    #     (coding_rate << 8) | # bit 9:8: 信号编码
    #     (0 << 10) |          # bit 10: 数据CRC使能
    #     (0 << 11) |          # bit 11: 低速模式
    #     (0 << 12) |          # bit 12: 头模式使能
    #     (0 << 13) |          # bit 13: 连续接收使能
    #     (0 << 14) |          # bit 14: FPGA译码使能
    #     (0 << 15)            # bit 15: 数据白化使能
    # )

    reg = 0xD801+ (coding_rate << 8) +  (sf << 4) + (bw << 2)

    
    return reg

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
                
        
    except Exception as e:
        logger.error(f"读取参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parameters")
async def write_parameters(params: AllChannelParameters):
    """写入所有通道参数 - 通过FPGA写入"""
    try:
        logger.info("开始写入通道参数...")
        # 收集所有写操作
        batch_operations = []
        
        # 1. 上行通道 (地址: 0x20, 0x28)
        reg1, reg2 = build_uplink_registers(
            params.uplink.bandwidth,
            params.uplink.spreading_factor,
            params.uplink.coding,
            params.lora_data_length
        )
        batch_operations.append((0x20, reg1))
        batch_operations.append((0x28, reg2))
        
        # 2. 上行通道(干扰) (地址: 0x60, 0x68)
        reg1, reg2 = build_uplink_registers(
            params.uplink_interference.bandwidth,
            params.uplink_interference.spreading_factor,
            params.uplink_interference.coding,
            params.lora_data_length
        )
        batch_operations.append((0x60, reg1))
        batch_operations.append((0x68, reg2))
        
        # 3. 下行通道 (地址: 0x40)
        reg = build_downlink_register(
            params.downlink.bandwidth,
            params.downlink.spreading_factor,
            params.downlink.coding
        )
        batch_operations.append((0x40, reg))
        
        # 使用 send_fpga_operation 批量写入
        success = udp_sender.send_fpga_operation(
            operation_type=1,  # 写操作
            batch_operations=batch_operations,
            target_ip=CONFIG["arm_ip"],
            target_port =CONFIG["arm_port"]
        )
        if not success:
            raise HTTPException(status_code=500, detail="FPGA写入失败")
        
        # 更新本地缓存
        current_parameters["uplink"] = params.uplink.dict()
        current_parameters["uplink_interference"] = params.uplink_interference.dict()
        current_parameters["downlink"] = params.downlink.dict()
        current_parameters["lora_data_length"] = params.lora_data_length
        
        return {
            "success": True,
            "data": current_parameters,
            "message": "通道参数写入成功",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"写入参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))