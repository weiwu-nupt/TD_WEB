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

class ChannelParameters(BaseModel):
    """单个通道参数"""
    bandwidth: int  # 125, 250, 500
    spreading_factor: int  # 6-12
    coding: str  # '4/5', '4/6', '4/7', '4/8'
    rf_frequency: Optional[int] = None  # 🔧 新增：射频频率 (kHz)，仅上行通道需要
    attenuation: Optional[int] = None  # 🔧 新增：衰减 (dB)，仅上行通道需要，范围1-70

class InterferenceSettings(BaseModel):
    """干扰设置"""
    enabled: bool = False
    mode: str = 'shared'  # 'shared' 或 'independent'
    type: str = 'single_tone'  # 'single_tone', 'low_noise', 'channel_noise'
    center_frequency: float = 0
    power: float = 0
    spreading_factor: int = 7

class DopplerSettings(BaseModel):
    """多普勒设置"""
    type: str = 'none'  # 'none', 'constant', 'linear'
    frequencyMin: float = -1000
    frequencyMax: float = 1000
    rate: float = 10


class ModeSettings(BaseModel):
    mode: str = 'transceive'  # 'receive_only', 'transmit_only', 'transceive', 'carrier'

class AllChannelParameters(BaseModel):
    """所有通道参数"""
    lora_data_length: int
    uplink: ChannelParameters
    downlink: ChannelParameters
    interference: InterferenceSettings
    doppler: DopplerSettings
    mode: ModeSettings

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
    frame_count: int 

class NodeSettings(BaseModel):
    """虚实融合节点配置"""
    nodeId: int  # 节点ID (1字节, 0-255)
    nodeMode: str  # 节点模式: 'standalone', 'network', 'virtual'
    totalNodes: int  # 组网总节点数 (1字节, 1-255)
    nodeType: str  # 节点属性: 'mother', 'normal'
    frequency: int  # 工作频率 (kHz) (4字节)
    attenuation: int  # 通道衰减 (dB) (1字节, 1-70)
    
    class ForwardLink(BaseModel):
        bandwidth: int  # 带宽 (kHz) (4字节)
        spreadingFactor: int  # 扩频因子 (1字节, 6-12)
        coding: str  # 编码 (1字节): '4/5', '4/6', '4/7', '4/8'
    
    class BackwardLink(BaseModel):
        bandwidth: int  # 带宽 (kHz) (4字节)
        spreadingFactor: int  # 扩频因子 (1字节, 6-12)
        coding: str  # 编码 (1字节): '4/5', '4/6', '4/7', '4/8'
        spreadingFactor2: int  # 扩频因子2 (1字节, 6-12)
    
    class Target(BaseModel):
        ip: str  # 目标IP
        port: int  # 目标端口
    
    forward: ForwardLink
    backward: BackwardLink
    target: Target