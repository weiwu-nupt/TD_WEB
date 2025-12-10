import serial
import struct
import logging
import threading
from typing import List, Tuple, Optional
from collections import deque
from frame_parser import build_message, parse_message
from frame_processor import process_frame_by_type
from config import FRAME_SYNC_HEADER, SystemMode, current_mode

logger = logging.getLogger(__name__)

# 消息队列
message_queue = deque(maxlen=4096)
queue_lock = threading.Lock()

class SerialCommunicator:
    """
    串口通信类 
    """
    
    def __init__(self, port: str = "COM1", baudrate: int = 115200):
        """
        初始化串口通信
        
        Args:
            port: 串口设备名称 (Linux: /dev/ttyUSB0, Windows: COM1)
            baudrate: 波特率 (默认115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.send_lock = threading.Lock()
        self.receive_thread = None
        self.running = False
        self._connect()
    
    def _connect(self):
        """连接串口"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,
                write_timeout=1.0
            )
            logger.info(f"✅ 串口已连接: {self.port} @ {self.baudrate} baud")
        except Exception as e:
            logger.error(f"❌ 串口连接失败: {e}")
            self.serial = None
    
    def start_receiving(self):
        """启动接收线程"""
        if self.running:
            logger.warning("⚠️ 串口接收器已在运行")
            return False
        
        if not self.is_connected():
            logger.error("❌ 串口未连接，无法启动接收")
            return False
        
        message_queue.clear()
        
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        logger.info("✅ 串口接收线程已启动")
        return True
    
    def stop(self):
        """停止串口通信"""
        if self.running:
            self.running = False
            
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=2)
            
            if self.serial and self.serial.is_open:
                self.serial.close()
            
            message_queue.clear()
            logger.info("⏹️ 串口通信已停止")
    
    def is_connected(self) -> bool:
        """检查串口是否连接"""
        return self.serial is not None and self.serial.is_open
    
    def _find_sync_header(self, buffer: bytearray) -> int:
        """在缓冲区中查找帧同步头"""
        sync_bytes = struct.pack('>I', FRAME_SYNC_HEADER)
        
        for i in range(len(buffer) - 3):
            if buffer[i:i+4] == sync_bytes:
                return i
        return -1
    
    def _receive_loop(self):
        """串口接收循环"""
        buffer = bytearray()
        
        while self.running and self.serial and self.serial.is_open:
            try:
                # 读取可用数据
                if self.serial.in_waiting > 0:
                    data = self.serial.read(self.serial.in_waiting)
                    buffer.extend(data)
                
                # 查找帧同步头
                sync_pos = self._find_sync_header(buffer)
                
                if sync_pos == -1:
                    if len(buffer) > 3:
                        buffer = buffer[-3:]
                    continue
                
                # 丢弃同步头之前的数据
                if sync_pos > 0:
                    logger.warning(f"⚠️ 丢弃 {sync_pos} 字节无效数据")
                    buffer = buffer[sync_pos:]
                
                # 检查是否有完整的消息头
                if len(buffer) < 8:
                    continue
                
                # 读取消息长度
                message_length = buffer[5]
                expected_total = 4 + 1 + 1 + message_length + 2
                
                # 等待完整消息
                if len(buffer) < expected_total:
                    continue
                
                # 提取完整消息
                message_data = bytes(buffer[:expected_total])
                buffer = buffer[expected_total:]
                
                # 解析消息
                parsed_msg = parse_message(message_data)
                
                if parsed_msg is None:
                    logger.error("❌ 串口消息解析失败")
                    continue
                
                # 处理消息
                msg_type = parsed_msg.get("message_type", 0)
                result = process_frame_by_type(parsed_msg, ('serial', 0))
                
                with queue_lock:
                    # 根据模式决定是否加入队列
                    if current_mode["mode"] == SystemMode.GROUND:
                        # 地面检测模式：只添加LoRa接收消息
                        if msg_type == 0x07:
                            message_queue.append(result)
                    else:
                        # 虚实融合模式：添加相关消息
                        if msg_type in [0x00, 0x01, 0x05]:
                            message_queue.append(result)
                
                logger.debug(f"📥 收到消息类型: 0x{msg_type:02X}")
            
            except serial.SerialException as e:
                if self.running:
                    logger.error(f"❌ 串口接收错误: {e}")
                break
            except Exception as e:
                if self.running:
                    logger.error(f"❌ 串口接收异常: {e}", exc_info=True)
    
    # ========== 发送方法==========
    
    def send_fpga_operation(
        self,
        operation_type: int,
        address: Optional[int] = None,
        data: Optional[int] = None,
        batch_operations: Optional[List[Tuple[int, int]]] = None
    ) -> bool:
        """发送FPGA操作消息（0x05）"""
        if not self.is_connected():
            logger.error("❌ 串口未连接")
            return False
        
        try:
            with self.send_lock:
                if batch_operations:
                    operation_count = len(batch_operations)
                    message_content = struct.pack('BB', operation_type, operation_count)
                    
                    for addr, val in batch_operations:
                        message_content += struct.pack('>I', addr)
                        message_content += struct.pack('>I', val)
                else:
                    if address is None:
                        raise ValueError("单次操作需要提供address参数")
                    
                    if operation_type == 0:
                        message_content = struct.pack('BB', operation_type, 1)
                        message_content += struct.pack('>I', address)
                    elif operation_type == 1:
                        if data is None:
                            data = 0
                        message_content = struct.pack('BB', operation_type, 1)
                        message_content += struct.pack('>I', address)
                        message_content += struct.pack('>I', data)
                
                full_message = build_message(0x05, message_content)
                
                bytes_written = self.serial.write(full_message)
                self.serial.flush()
                
                logger.debug(f"📤 发送FPGA操作: {bytes_written}字节")
                return bytes_written == len(full_message)
        
        except Exception as e:
            logger.error(f"❌ FPGA操作发送失败: {e}")
            return False
    
    def send_lora_message(
        self,
        timing_enable: int,
        timing_time: int,
        data_content: str,
        frame_count: int = 0
    ) -> bool:
        """发送LoRa消息（0x06）"""
        if not self.is_connected():
            logger.error("❌ 串口未连接")
            return False
        
        try:
            with self.send_lock:
                # 解析实际数据
                actual_data_bytes = bytes.fromhex(data_content)
                
                # 构建 data = frame_count(1) + 实际数据
                data_with_count = struct.pack('B', frame_count) + actual_data_bytes
                
                # timing_enable(1) + timing_time(4) + data
                message_content = struct.pack('B', timing_enable)
                message_content += struct.pack('>I', timing_time)
                message_content += data_with_count
                
                # 构建完整消息
                full_message = build_message(0x06, message_content)
                
                bytes_written = self.serial.write(full_message)
                self.serial.flush()
                
                logger.info(f"📤 发送LoRa消息: 帧#{frame_count}, {bytes_written}字节")
                return bytes_written == len(full_message)
        
        except Exception as e:
            logger.error(f"❌ LoRa消息发送失败: {e}")
            return False
    
    def send_node_operation(self, node_settings: dict) -> bool:
        """发送节点配置消息（0x08）"""
        if not self.is_connected():
            logger.error("❌ 串口未连接")
            return False
        
        try:
            with self.send_lock:
                # 节点模式映射
                mode_map = {'standalone': 0, 'network': 1, 'virtual': 2}
                node_mode = mode_map.get(node_settings.get('nodeMode', 'virtual'), 2)
                
                # 节点属性映射
                type_map = {'normal': 0, 'mother': 1}
                node_type = type_map.get(node_settings.get('nodeType', 'normal'), 0)
                
                # 编码映射
                coding_map = {'4/5': 1, '4/6': 2, '4/7': 3, '4/8': 4}
                
                # 构建消息内容
                message_content = struct.pack('B', node_settings.get('nodeId', 1))
                message_content += struct.pack('B', node_mode)
                message_content += struct.pack('B', node_settings.get('totalNodes', 1))
                message_content += struct.pack('B', node_type)
                message_content += struct.pack('>I', node_settings.get('frequency', 900000))
                message_content += struct.pack('B', node_settings.get('attenuation', 10))
                
                # 前向链路参数
                forward = node_settings.get('forward', {})
                message_content += struct.pack('>I', forward.get('bandwidth', 125))
                message_content += struct.pack('B', forward.get('spreadingFactor', 7))
                forward_coding = coding_map.get(forward.get('coding', '4/5'), 1)
                message_content += struct.pack('B', forward_coding)
                
                # 反向链路参数
                backward = node_settings.get('backward', {})
                message_content += struct.pack('>I', backward.get('bandwidth', 125))
                message_content += struct.pack('B', backward.get('spreadingFactor', 7))
                backward_coding = coding_map.get(backward.get('coding', '4/5'), 1)
                message_content += struct.pack('B', backward_coding)
                message_content += struct.pack('B', backward.get('spreadingFactor2', 7))
                
                # 构建完整消息
                full_message = build_message(0x08, message_content)
                
                bytes_written = self.serial.write(full_message)
                self.serial.flush()
                
                logger.info(f"📤 发送节点配置: {bytes_written}字节")
                return bytes_written == len(full_message)
        
        except Exception as e:
            logger.error(f"❌ 节点配置发送失败: {e}")
            return False
    
    def get_status(self):
        """获取串口状态"""
        return {
            "connected": self.is_connected(),
            "port": self.port,
            "baudrate": self.baudrate,
            "receiving": self.running,
            "thread_alive": self.receive_thread.is_alive() if self.receive_thread else False
        }


# 导出消息队列供其他模块使用
def get_message_queue():
    """获取消息队列"""
    return message_queue

def get_queue_lock():
    """获取队列锁"""
    return queue_lock
