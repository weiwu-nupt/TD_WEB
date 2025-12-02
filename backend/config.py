#!/usr/bin/env python3
# config.py - 配置管理
import json
import logging
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

# 🔧 新增：系统模式枚举
class SystemMode(str, Enum):
    GROUND = "ground"  # 地面检测模式
    VIRTUAL = "virtual"  # 虚实融合模式

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

# 🔧 新增：当前系统模式
current_mode = {
    "mode": SystemMode.GROUND,  # 默认地面检测模式
    "last_switch_time": None
}

current_config = {
    "receivePort": CONFIG["udp_receive_port"]
}

# 帧类型常量
FRAME_TYPE_VIRTUAL_SEND = 0x00       # 虚实节点信号发送帧
FRAME_TYPE_VIRTUAL_RECEIVE = 0x01    # 虚实节点信号接收帧
FRAME_TYPE_VIRTUAL_TIMESTAMP = 0x02  # 虚实节点发送时间戳回传帧
FRAME_TYPE_VIRTUAL_LINK = 0x03       # 虚实节点链路状态帧
FRAME_TYPE_FPGA = 0x05           # FPGA读写帧
FRAME_TYPE_LORA = 0x07           # LoRa收发帧
FRAME_TYPE_NODE_SETTINGS = 0x08 # 节点参数设置帧



# 帧同步头常量
FRAME_SYNC_HEADER = 0x1ACFFC1D

# 响应超时时间(秒)
RESPONSE_TIMEOUT = 10

# 存储所有通道参数
current_parameters = {
    "uplink": {
        "bandwidth": 125,
        "coding": "4/5",
        "spreading_factor": 10,
        "rf_frequency": 470000,  # 🔧 新增：默认470MHz = 470000kHz
        "attenuation": 10
    },
    "downlink": {
        "bandwidth": 125,
        "coding": "4/5",
        "spreading_factor": 10
    },
    "interference": {
        "enabled": False,
        "mode": "shared",
        "type": "single_tone",
        "center_frequency": 0,
        "power": 0,
        "spreading_factor": 7
    },
    "doppler": {
        "type": "none",
        "frequencyMin": -10000,
        "frequencyMax": 10000,
        "rate": 1000
    },
    "lora_data_length": 0
}

def get_frame_type_name(frame_type: int) -> str:
    """获取帧类型名称"""
    if current_mode["mode"] == SystemMode.GROUND:
        # 地面检测模式
        frame_names = {
            FRAME_TYPE_BROADCAST: "广播帧",
            FRAME_TYPE_TIMESTAMP: "发送时间戳回传帧", 
            FRAME_TYPE_LINK_STATUS: "链路状态帧",
            FRAME_TYPE_FPGA: "FPGA操作帧",
            FRAME_TYPE_LORA: "LoRa收发帧"
        }
    else:
        # 虚实融合模式
        frame_names = {
            FRAME_TYPE_VIRTUAL_SEND: "虚实节点信号发送帧",
            FRAME_TYPE_VIRTUAL_RECEIVE: "虚实节点信号接收帧",
            FRAME_TYPE_VIRTUAL_TIMESTAMP: "虚实节点发送时间戳回传帧",
            FRAME_TYPE_VIRTUAL_LINK: "虚实节点链路状态帧"
        }
    return frame_names.get(frame_type, f"未知帧(0x{frame_type:02X})")