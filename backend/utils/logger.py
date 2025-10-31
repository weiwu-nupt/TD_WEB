#!/usr/bin/env python3
# utils/logger.py - 日志配置
import logging
import sys
from pathlib import Path

def setup_logger(name: str = None, level: int = logging.INFO):
    """配置日志系统"""
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 创建文件handler
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / 'app.log', encoding='utf-8')
    file_handler.setLevel(level)
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加handler
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger