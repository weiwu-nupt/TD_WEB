#!/usr/bin/env python3
# models.py - Pydantic数据模型
from pydantic import BaseModel
from typing import Optional

# UDP配置模型
class UDPConfig(BaseModel):
    """UDP配置模型"""
    receivePort: int

class UDPMessage(BaseModel):
    """UDP消息模型"""
    message: str
    target_ip: str = "127.0.0.1"

# 通道参数模型
class ChannelParameters(BaseModel):
    """通道参数模型"""
    bandwidth: int              # 带宽(125/250/500 kHz)
    coding: str                 # 编码(4/5, 4/6, 4/7, 4/8)
    spreading_factor: int       # 扩频因子(6-12)

class WriteParametersRequest(BaseModel):
    """写入参数请求"""
    uplink: ChannelParameters
    uplink_interference: ChannelParameters
    downlink: ChannelParameters
    lora_data_length: int  # LoRa数据长度(字节)

class AllChannelParameters(BaseModel):
    """所有通道参数"""
    uplink: ChannelParameters
    uplink_interference: ChannelParameters
    downlink: ChannelParameters

# 多普勒设置模型
class DopplerSettings(BaseModel):
    """多普勒设置模型"""
    type: str                        # 'none', 'constant', 'linear', 'sinusoidal', 'random'
    frequencyMin: int                # 频移下限(Hz)
    frequencyMax: int                # 频移上限(Hz)
    rate: Optional[float] = None     # 变化率(Hz/s) - 用于线性
    period: Optional[float] = None   # 周期(s) - 用于正弦

# FPGA操作模型
class FPGAReadRequest(BaseModel):
    """FPGA读请求"""
    address: int  # 操作地址

class FPGAWriteRequest(BaseModel):
    """FPGA写请求"""
    address: int  # 操作地址
    data: int     # 写入数据

# LoRa发送模型
class LoRaSendMessage(BaseModel):
    """LoRa发送消息模型"""
    timing_enable: int   # 0-不定时, 1-定时开启
    timing_time: int     # 定时时间 (4字节)
    data_content: str    # 数据内容