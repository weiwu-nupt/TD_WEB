#!/usr/bin/env python3
# udp_receiver.py - UDP接收器类
import socket
import threading
import logging
from datetime import datetime
from collections import deque

from frame_parser import parse_message
from frame_processor import process_frame_by_type
from response_waiter import ResponseWaiter

logger = logging.getLogger(__name__)

# 消息队列
message_queue = deque(maxlen=4096)

class UDPReceiver:
    """UDP接收器类"""
    
    def __init__(self):
        self.socket = None
        self.thread = None
        self.running = False
        self.current_port = None
        
    def start(self, local_ip: str, port: int):
        """启动UDP接收"""
        # 如果已经在运行，先停止
        if self.running:
            self.stop()
            
        try:
            # 创建UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((local_ip, port))
            self.socket.settimeout(1.0)  # 1秒超时
            
            self.running = True
            self.current_port = port
            
            # 启动接收线程
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            
            logger.info(f"UDP接收器已启动，监听端口: {port}")
            return True
            
        except Exception as e:
            logger.error(f"启动UDP接收器失败: {e}")
            self.running = False
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def stop(self):
        """停止UDP接收"""
        if self.running:
            self.running = False
            
            if self.socket:
                self.socket.close()
                self.socket = None
            
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2)
            
            logger.info(f"UDP接收器已停止 (端口: {self.current_port})")
            self.current_port = None
    
    def _receive_loop(self):
        """UDP接收循环"""
        while self.running and self.socket:
            try:
                data, addr = self.socket.recvfrom(1024)
                
                # 解析消息
                parsed_msg = parse_message(data)
                
                if parsed_msg is None:
                    logger.error(f"消息解析失败")
                    continue
                
                # 处理消息
                result = process_frame_by_type(parsed_msg, addr)
                
                # # 合并解析信息和处理结果
                # result["message_type"] = parsed_msg["message_type"]
                # result["message_length"] = parsed_msg["message_length"]
                
                # # 添加接收信息
                # result["dest_port"] = self.current_port
                # result["receive_time"] = datetime.now().isoformat()
                # result["direction"] = "receive"
                
                # 添加到消息队列
                if result["message_type"] == 0x07:
                    message_queue.append(result)
                
                # 通知等待的请求
                # ResponseWaiter.notify_response(result["message_type"], result)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"UDP接收错误: {e}")
                break
    
    def get_status(self):
        """获取接收器状态"""
        return {
            "running": self.running,
            "port": self.current_port,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }

# 导出消息队列供其他模块使用
def get_message_queue():
    """获取消息队列"""
    return message_queue