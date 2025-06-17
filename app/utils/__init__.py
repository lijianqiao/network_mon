"""
-*- coding: utf-8 -*-
 @Author: li
 @ProjectName: network
 @Email: lijianqiao2906@live.com
 @FileName: __init__.py.py
 @DateTime: 2025/3/11 上午9:53
 @Docs: 实用程序模块
"""

from .log_decorators import LogConfig, LogConfigs, system_log
from .logger import log_function_calls, logger

__all__ = [
    "logger",
    "log_function_calls",
    "system_log",
    "LogConfig",
    "LogConfigs",
]
