#!/usr/bin/env python3
# config.py - 配置管理
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 读取配置文件
def load_config():
    """加载配置文件"""
    config_file = Path(__file__).parent.parent / 'config.json'
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("配置文件未找到,使用默认配置")
        return {
            "local_ip": "192.168.1.116",
            "backend_port": 8000,
            "udp_receive_port": 8002,
            "vue_dev_port": 5555,
            "arm_ip": "192.168.1.10",
            "arm_port":8003
        }

# 全局配置
CONFIG = load_config()

current_config = {
    "receivePort": CONFIG["udp_receive_port"]
}

# 帧类型常量
FRAME_TYPE_BROADCAST = 0x01      # 广播帧
FRAME_TYPE_TIMESTAMP = 0x02      # 发送时间戳回传帧  
FRAME_TYPE_LINK_STATUS = 0x03    # 链路状态帧
FRAME_TYPE_FPGA = 0x05           # FPGA读写帧
FRAME_TYPE_LORA = 0x07           # LoRa收发帧

# 帧同步头常量
FRAME_SYNC_HEADER = 0x1ACFFC1D

# 响应超时时间(秒)
RESPONSE_TIMEOUT = 10

# 存储所有通道参数
current_parameters = {
    "uplink": {
        "bandwidth": 100000,
        "coding": "4/5",
        "spreading_factor": 9,
        "center_frequency": 10000,
        "power": 1.0
    },
    "downlink": {
        "bandwidth": 100000,
        "coding": "4/7",
        "spreading_factor": 10,
        "center_frequency": 12000,
        "power": 2.0
    }
}

# 存储多普勒设置
current_doppler_settings = {
    "type": "none",
    "frequencyMin": -1000,
    "frequencyMax": 1000,
    "rate": 10.0,
    "period": 1.0
}

def get_frame_type_name(frame_type: int) -> str:
    """获取帧类型名称"""
    frame_names = {
        FRAME_TYPE_BROADCAST: "广播帧",
        FRAME_TYPE_TIMESTAMP: "发送时间戳回传帧", 
        FRAME_TYPE_LINK_STATUS: "链路状态帧",
        FRAME_TYPE_FPGA: "FPGA操作帧",
        FRAME_TYPE_LORA: "LoRa收发帧"
    }
    return frame_names.get(frame_type, f"未知帧(0x{frame_type:02X})")