#!/usr/bin/env python3
# virtual_monitor.py - 虚实融合模式寄存器监控
import threading
import time
import struct
import logging
from typing import Optional
from collections import deque

from config import (
    CONFIG, 
    SystemMode, 
    current_mode,
    FRAME_TYPE_VIRTUAL_TIMESTAMP,
    FRAME_TYPE_VIRTUAL_LINK
)
from frame_parser import build_message
from udp_receiver import get_message_queue

logger = logging.getLogger(__name__)

class VirtualMonitor:
    """
    虚实融合模式监控器
    
    定时读取寄存器状态：
    - 0x26[11:8] 数据处理状态 > 0 → 发送虚实节点信号发送时间戳回传帧
    - 0x46[19:16] 接收状态 > 1 → 发送虚实节点链路状态帧
    """
    
    def __init__(self, udp_sender=None):
        self.udp_sender = udp_sender
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.poll_interval = 1  
        
        # 状态跟踪（防止重复发送）
        self.last_0x26_status = 0
        self.last_0x46_status = 0

        # 寄存器值缓存
        self.reg_0x25 = 0  # 链路时间戳（发送）
        self.reg_0x26 = 0  # 数据处理状态
        self.reg_0x45 = 0  # 链路时间戳（接收）
        self.reg_0x46 = 0  # 接收状态
        
        logger.info("✅ VirtualMonitor 初始化完成")
    
    def start(self):
        """启动监控"""
        if self.running:
            logger.warning("⚠️ VirtualMonitor 已经在运行中")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
        logger.info(f"✅ VirtualMonitor 已启动 (轮询间隔: {self.poll_interval}s)")
        return True
    
    def stop(self):
        """停止监控"""
        if not self.running:
            return
        
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        
        logger.info("⏹️ VirtualMonitor 已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        logger.info("🔄 VirtualMonitor 监控循环开始")
        
        while self.running:
            try:
                # 只在虚实融合模式下监控
                if current_mode["mode"] != SystemMode.VIRTUAL:
                    time.sleep(self.poll_interval)
                    continue
                
                 # 🔧 步骤1: 发送读寄存器请求
                self._send_read_registers_request()
                
                # 🔧 步骤2: 短暂等待响应
                time.sleep(0.5)  # 等待100ms让响应到达
                
                # 🔧 步骤3: 从消息队列读取响应
                self._process_register_responses()
                
                # 🔧 步骤4: 检查条件并发送帧
                self._check_and_send_frames()
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"❌ VirtualMonitor 监控循环异常: {e}", exc_info=True)
                time.sleep(1)  # 出错后等待1秒再继续
        
        logger.info("⏹️ VirtualMonitor 监控循环结束")
    
    def _send_read_registers_request(self):
        """
        发送读取寄存器请求
        
        批量读取：0x25, 0x26, 0x45, 0x46
        """
        if not self.udp_sender:
            logger.error("❌ UDP发送器未初始化")
            return
        
        try:
            # 🔧 批量读操作：[地址, 数据(读时为0)]
            batch_operations = [
                (0x25, 0),  # 链路时间戳（发送）
                (0x26, 0),  # 数据处理状态
                (0x45, 0),  # 链路时间戳（接收）
                (0x46, 0),  # 接收状态
            ]
            
            # 使用 send_fpga_operation 发送批量读请求
            success = self.udp_sender.send_fpga_operation(
                operation_type=0,  # 0 = 读操作
                batch_operations=batch_operations,
                target_ip=CONFIG["arm_ip"],
                target_port=CONFIG["arm_port"]
            )
            
            if success:
                logger.debug("📤 已发送读寄存器请求: 0x25, 0x26, 0x45, 0x46")
            else:
                logger.error("❌ 发送读寄存器请求失败")
                
        except Exception as e:
            logger.error(f"❌ 发送读寄存器请求异常: {e}")
    
def _process_register_responses(self):
    """
    从消息队列中处理寄存器读取响应
    
    查找所有 FPGA 操作帧 (0x05) 的响应，处理完后从队列移除
    """
    try:
        message_queue = get_message_queue()
    
        if not message_queue:
            return
        
        # 🔧 收集需要移除的消息索引
        messages_to_remove = []
        
        # 🔧 遍历队列，查找并处理所有 0x05 消息
        for idx, msg in enumerate(list(message_queue)):
            # 只处理 FPGA 操作帧响应
            if msg.get("message_type") != 0x05:
                continue
        
            # 获取 FPGA 操作信息
            fpga_info = msg.get("fpga_operation_info")
            if not fpga_info:
                continue
    
            if fpga_info.get("operation_type_code") != 0:  
                continue
        
            # 提取寄存器数据
            operations = fpga_info.get("operations", [])
        
            for op in operations:
                address = op.get("address")
                value = op.get("value")
            
                if address is None or value is None:
                    continue
            
                # 🔧 更新寄存器缓存
                if address == 0x25:
                    self.reg_0x25 = value
                elif address == 0x26:
                    self.reg_0x26 = value
                elif address == 0x45:
                    self.reg_0x45 = value
                elif address == 0x46:
                    self.reg_0x46 = value
            
            # 🔧 标记为待移除
            messages_to_remove.append(idx)
        
        # 🔧 从队列中移除已处理的 0x05 消息（倒序移除以保持索引正确）
        for idx in reversed(messages_to_remove):
            try:
                message_queue.pop(idx)
            except IndexError:
                logger.warning(f"⚠️ 无法移除索引 {idx}，队列长度: {len(message_queue)}")
        
    except Exception as e:
        logger.error(f"❌ 处理寄存器响应异常: {e}", exc_info=True)
    
    def _check_and_send_frames(self):
        """
        检查寄存器条件并发送相应的帧
        """
        # 🔧 检查 0x26[11:8] 数据处理状态
        data_process_status = (self.reg_0x26 >> 8) & 0x0F
        
        if data_process_status > 0:
            # 状态变化才发送（防止重复）
            if data_process_status != self.last_0x26_status:
                self._send_timestamp_frame()
                self.last_0x26_status = 1
        else:
            self.last_0x26_status = 0
        
        # 🔧 检查 0x46[19:16] 接收状态
        receive_status = (self.reg_0x46 >> 16) & 0x0F
        
        if receive_status > 1:
            # 状态变化才发送（防止重复）
            if receive_status != self.last_0x46_status:
                self._send_link_status_frame()
                self.last_0x46_status = 1
        else:
            self.last_0x46_status = 0
    
    def _send_timestamp_frame(self):
        """
        发送虚实节点信号发送时间戳回传帧 (0x02)
        
        帧格式：
        - 帧类型: 0x02 (1字节)
        - 发送完成时间: 系统时间 (4字节)
        - 链路时间戳: 0x25寄存器值 (4字节)
        - 数据包: 8字节全0
        """
        if not self.udp_sender:
            return
        
        try:
            # 🔧 发送完成时间 = 当前系统时间（秒级时间戳）
            send_complete_time = int(time.time())
            
            # 🔧 链路时间戳 = 0x25 寄存器值
            link_timestamp = self.reg_0x25 & 0xFFFFFFFF
            
            # 🔧 数据包 = 8字节全0
            data_packet = 0
            
            # 构建帧内容
            frame_content = struct.pack(
                '>IIQ',  # 大端序: 4字节 + 4字节 + 8字节
                send_complete_time,  # 发送完成时间
                link_timestamp,      # 链路时间戳（0x25）
                data_packet          # 数据包（8字节0）
            )
            
            # 构建完整消息
            full_message = build_message(FRAME_TYPE_VIRTUAL_TIMESTAMP, frame_content)
            
            # 发送到ARM
            success = self.udp_sender.send_raw_data(
                full_message,
                target_ip=CONFIG["arm_ip"],
                target_port=CONFIG["arm_port"]
            )
                
        except Exception as e:
            logger.error(f"❌ 构建时间戳回传帧失败: {e}")
    
    def _send_link_status_frame(self):
        """
        发送虚实节点链路状态帧 (0x03)
        
        帧格式：
        - 帧类型: 0x03 (1字节)
        - 接收起始时间: 系统时间 (4字节)
        - 链路时间戳: 0x45寄存器值 (4字节)
        - 备份: 8字节全0
        """
        if not self.udp_sender:
            return
        
        try:
            # 🔧 接收起始时间 = 当前系统时间（秒级时间戳）
            receive_start_time = int(time.time())
            
            # 🔧 链路时间戳 = 0x45 寄存器值
            link_timestamp = self.reg_0x45 & 0xFFFFFFFF
            
            # 🔧 备份数据 = 8字节全0
            backup_data = 0
            
            # 构建帧内容
            frame_content = struct.pack(
                '>IIQ',  # 大端序: 4字节 + 4字节 + 8字节
                receive_start_time,  # 接收起始时间
                link_timestamp,      # 链路时间戳（0x45）
                backup_data          # 备份（8字节0）
            )
            
            # 构建完整消息
            full_message = build_message(FRAME_TYPE_VIRTUAL_LINK, frame_content)
            
            # 发送到ARM
            success = self.udp_sender.send_raw_data(
                full_message,
                target_ip=CONFIG["arm_ip"],
                target_port=CONFIG["arm_port"]
            )
                
        except Exception as e:
            logger.error(f"❌ 构建链路状态帧失败: {e}")
    
    def get_status(self) -> dict:
        """获取监控器状态"""
        return {
            "running": self.running,
            "poll_interval": self.poll_interval,
            "thread_alive": self.thread.is_alive() if self.thread else False,
            "last_0x26_status": self.last_0x26_status,
            "last_0x46_status": self.last_0x46_status,
            "registers": {
                "0x25": f"0x{self.reg_0x25:08X}",
                "0x26": f"0x{self.reg_0x26:08X}",
                "0x45": f"0x{self.reg_0x45:08X}",
                "0x46": f"0x{self.reg_0x46:08X}"
            },
            "current_mode": current_mode["mode"]
        }