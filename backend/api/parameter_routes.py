#!/usr/bin/env python3
# api/parameter_routes.py - 参数设置API路由
from fastapi import APIRouter, HTTPException
import logging

from models import AllChannelParameters
from config import CONFIG, current_parameters

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

def get_fb(bandwidth: int) -> float:
    """根据带宽获取基带频率f_b"""
    if bandwidth == 125:
        return 1e6
    elif bandwidth == 250:
        return 2e6
    elif bandwidth == 500:
        return 4e6
    return 1e6

def build_uplink_registers(bandwidth: int, sf: int, coding: str, data_length: int):
    """构建上行/上行干扰的两个寄存器值"""
    bw = BANDWIDTH_MAP.get(bandwidth, 0)
    base_sf = sf
    coding_rate = CODING_MAP.get(coding, 0b001)
    
    # reg1 = 0x80853 + (bw << 2)
    reg1 = 0x808D3 + (bw << 2)
    reg2 = ((data_length+1) << 24) + ((coding_rate+1) << 21) + (1 << 20) + (base_sf << 4) + 0x1000D
    
    return reg1, reg2

def build_downlink_register(bandwidth: int, sf: int, coding: str):
    """构建下行通道的寄存器值"""
    bw = BANDWIDTH_MAP.get(bandwidth, 0)
    coding_rate = CODING_MAP.get(coding, 0b001)  
    reg = 0x1D801 + (coding_rate << 8) + (sf << 4) + (bw << 2)
    # reg = 0xD801 + (coding_rate << 8) + (sf << 4) + (bw << 2)
    return reg

def build_interference_registers(interference, bandwidth: int, mode_settings):
    """构建干扰寄存器"""

    mode = mode_settings.mode
    reg0 = 0
    
    # 根据模式设置对应的bit
    if mode == 'receive_only':
        reg0 |= (1 << 0)  # bit 0 = 1: 单收
    elif mode == 'transmit_only':
        reg0 |= (1 << 1)  # bit 1 = 1: 单发
    elif mode == 'transceive':
        reg0 |= (1 << 2)  # bit 2 = 1: 收发
    elif mode == 'carrier':
        reg0 |= (1 << 3)  # bit 3 = 1: 单载波

    if not interference.enabled:
        return (0x0, reg0)
    
    reg0 |= (1 << 4)  # bit 4: 噪声开关 (enabled=True时置1)
    
    # bit 5: 是否为单音
    if interference.type == 'single_tone':
        reg0 |= (1 << 5)
    
    # bit 6: 模式 (0=共通道, 1=独立通道)
    if interference.mode == 'independent':
        reg0 |= (1 << 6)
    
    # 0x2: 0x2000 + 噪声功率
    reg2 = 0x2000 + int(interference.power)
    
    # 0x3: 噪声功率
    reg3 = int(interference.power)
    
    # 0x4: 单音写中心频率，其他写0
    if interference.type == 'single_tone':
        reg4 = int(interference.center_frequency)
    else:
        reg4 = 0
    
    return [(0x0, reg0), (0x2, reg2), (0x3, reg3), (0x4, reg4)]

def build_doppler_registers(doppler, bandwidth: int):
    """构建多普勒寄存器"""
    if doppler.type == 'none':
        # 无多普勒
        return False 
    
    f_b = get_fb(bandwidth)
    
    # 计算频移上限和下限
    freq_max_reg = int((doppler.frequencyMax / f_b) * (2**32))
    freq_min_reg = int((doppler.frequencyMin / f_b) * (2**32))
    
    # 计算变化率
    if doppler.type == 'constant':
        rate_reg = 0  # 恒定多普勒，变化率为0
    elif doppler.type == 'linear':
        rate_reg = int((doppler.rate / f_b/f_b) * (2**40))
    else:
        rate_reg = 0
    
    return [
        (0x30, freq_max_reg & 0xFFFFFFFF),  # 频移上限
        (0x31, freq_min_reg & 0xFFFFFFFF),  # 频移下限
        (0x32, rate_reg & 0xFFFFFFFF)       # 频移变化率
    ]

@router.get("/parameters")
async def get_parameters():
    """读取所有通道参数"""
    try:
        logger.info("读取通道参数...")
        
        # 返回当前缓存的参数
        return {
            "success": True,
            "data": current_parameters
        }
        
    except Exception as e:
        logger.error(f"读取参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parameters")
async def write_parameters(params: AllChannelParameters):
    """写入所有通道参数"""
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
        batch_operations.append((0x0, 0))
        batch_operations.append((0x20, reg1))
        batch_operations.append((0x28, reg2))
        batch_operations.append((0x60, reg1))
        batch_operations.append((0x68, reg2))
        batch_operations.append((0x0, 3))
        
        # 射频频率 (地址: 0xFF)
        if params.uplink.rf_frequency is not None:
            rf_freq = int(params.uplink.rf_frequency)  # kHz
            batch_operations.append((0xFF, rf_freq))

        if params.uplink.attenuation is not None:
            attenuation = int(params.uplink.attenuation) # dB
            batch_operations.append((0xFE, attenuation)) 
        
        # 2. 下行通道 (地址: 0x40)
        reg = build_downlink_register(
            params.downlink.bandwidth,
            params.downlink.spreading_factor,
            params.downlink.coding
        )
        batch_operations.append((0x40, reg))

        # 3. 干扰设置 (地址: 0x0, 0x2, 0x3, 0x4)
        interference_regs = build_interference_registers(
            params.interference,
            params.uplink.bandwidth,
            params.mode
        )
        if interference_regs:
            batch_operations.extend(interference_regs)

        # 4. 多普勒设置 (地址: 0x25, 0x26, 0x27)
        doppler_regs = build_doppler_registers(
            params.doppler,
            params.uplink.bandwidth
        )
        if doppler_regs:
            batch_operations.extend(doppler_regs)
        
        # 使用 send_fpga_operation 批量写入
        success = udp_sender.send_fpga_operation(
            operation_type=1,  # 写操作
            batch_operations=batch_operations,
            target_ip=CONFIG["arm_ip"],
            target_port=CONFIG["arm_port"]
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="FPGA写入失败")
        
        # 更新本地缓存
        current_parameters["uplink"] = params.uplink.dict()
        current_parameters["downlink"] = params.downlink.dict()
        current_parameters["interference"] = params.interference.dict()
        current_parameters["doppler"] = params.doppler.dict()
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