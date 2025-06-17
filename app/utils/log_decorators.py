"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: log_decorators.py
@DateTime: 2025-06-17
@Docs: 系统日志装饰器，用于记录操作日志和系统日志到数据库
"""

import asyncio
import inspect
import json
import traceback
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar

from app.models.data_enum import ActionEnum, LogLevelEnum, OperationResultEnum, ResourceTypeEnum
from app.utils.logger import logger

# 使用类型变量支持泛型
F = TypeVar("F", bound=Callable[..., Any])


class LogConfig:
    """日志配置类"""

    def __init__(
        self,
        log_operation: bool = True,
        log_system: bool = True,
        operation_type: str | None = None,
        resource_type: str | None = None,
        log_args: bool = False,
        log_result: bool = False,
        exclude_args: list[str] | None = None,
        mask_sensitive: list[str] | None = None,
    ):
        self.log_operation = log_operation  # 是否记录操作日志
        self.log_system = log_system  # 是否记录系统日志
        self.operation_type = operation_type  # 操作类型
        self.resource_type = resource_type  # 资源类型
        self.log_args = log_args  # 是否记录参数
        self.log_result = log_result  # 是否记录返回值
        self.exclude_args = exclude_args or []  # 排除的参数
        self.mask_sensitive = mask_sensitive or ["password", "token", "secret", "key"]  # 敏感信息掩码


def _mask_sensitive_data(data: Any, sensitive_keys: list[str]) -> Any:
    """掩码敏感信息"""
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                masked[key] = "***MASKED***"
            else:
                masked[key] = _mask_sensitive_data(value, sensitive_keys)
        return masked
    elif isinstance(data, list) or isinstance(data, tuple):
        return [_mask_sensitive_data(item, sensitive_keys) for item in data]
    else:
        return data


def _prepare_log_data(args: tuple, kwargs: dict, result: Any = None, config: LogConfig | None = None) -> dict[str, Any]:
    """准备日志数据"""
    if config is None:
        config = LogConfig()

    log_data = {}

    # 处理参数
    if config.log_args and args:
        # 过滤排除的参数
        filtered_args = []
        for i, arg in enumerate(args):
            if f"arg_{i}" not in config.exclude_args:
                filtered_args.append(arg)

        if filtered_args:
            log_data["args"] = _mask_sensitive_data(filtered_args, config.mask_sensitive)

    if config.log_args and kwargs:
        # 过滤排除的参数
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in config.exclude_args}

        if filtered_kwargs:
            log_data["kwargs"] = _mask_sensitive_data(filtered_kwargs, config.mask_sensitive)

    # 处理返回值
    if config.log_result and result is not None:
        # 限制返回值大小
        result_str = str(result)
        if len(result_str) > 1000:
            result_str = result_str[:1000] + "...[truncated]"
        log_data["result"] = result_str

    return log_data


async def _log_operation(
    user: str,
    action: str,
    resource_type: str,
    resource_name: str,
    result: OperationResultEnum,
    execution_time: float,
    ip_address: str | None = None,
    error_message: str | None = None,
    details: dict | None = None,
) -> None:
    """记录操作日志到数据库"""
    try:
        # 动态导入避免循环导入
        from app.repositories import get_operation_log_dao

        operation_log_dao = get_operation_log_dao()

        await operation_log_dao.create(
            user=user,
            action=action,  # 这里action应该是枚举值字符串
            resource_type=resource_type,  # 这里resource_type应该是枚举值字符串
            resource_id=None,  # 可以后续扩展为从参数中提取
            resource_name=resource_name,
            result=result,  # 这里result应该是枚举实例
            execution_time=execution_time,
            ip_address=ip_address or "127.0.0.1",
            error_message=error_message,
            details=json.dumps(details, ensure_ascii=False) if details else None,
        )
    except Exception:
        # 数据库记录失败时不应该影响主业务流程
        # 静默失败，只依赖文件日志
        pass


async def _log_system(
    level: LogLevelEnum,
    message: str,
    module: str,
    logger_name: str,
    exception_info: str | None = None,
    extra_data: dict | None = None,
) -> None:
    """记录系统日志到数据库"""
    try:
        # 尝试动态导入并创建日志记录
        from app.repositories import get_system_log_dao

        system_log_dao = get_system_log_dao()

        await system_log_dao.create(
            level=level,  # 这里level应该是枚举实例
            message=message,
            module=module,
            logger_name=logger_name,
            exception_info=exception_info,
            extra_data=json.dumps(extra_data, ensure_ascii=False) if extra_data else None,
        )
    except Exception:
        # 数据库记录失败时不应该影响主业务流程
        # 这种情况通常发生在：
        # 1. 数据库未初始化
        # 2. 数据库连接失败
        # 3. 其他数据库相关错误
        # 静默失败，只依赖文件日志
        pass


def system_log(config: LogConfig | None = None) -> Callable[[F], F]:
    """系统日志装饰器

    用于记录函数调用的操作日志和系统日志

    Args:
        config: 日志配置

    Usage:
        @system_log()
        async def create_device(self, device_data: dict, user: str) -> Device:
            pass

        @system_log(LogConfig(
            operation_type="CREATE",
            resource_type="DEVICE",
            log_args=True,
            log_result=True,
            exclude_args=["password"],
        ))
        async def login(self, username: str, password: str) -> User:
            pass
    """
    if config is None:
        config = LogConfig()

    def decorator(func: F) -> F:
        func_name = func.__name__
        module_name = func.__module__

        # 自动推断操作类型和资源类型
        operation_type = config.operation_type or _infer_operation_type(func_name)
        resource_type = config.resource_type or _infer_resource_type(func_name, module_name)

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = datetime.now()
                execution_time = 0.0
                result = None
                error_message = None
                operation_result = OperationResultEnum.SUCCESS

                # 提取用户信息
                user = _extract_user_info(args, kwargs)
                resource_name = _extract_resource_name(args, kwargs)

                try:
                    # 记录开始
                    if config.log_system:
                        log_data = _prepare_log_data(args, kwargs, config=config)
                        await _log_system(
                            LogLevelEnum.INFO,
                            f"Function {func_name} started",
                            module_name,
                            func_name,
                            extra_data=log_data,
                        )
                        logger.info(f"函数 {func_name} 已开始", extra=log_data)

                    # 执行函数
                    result = await func(*args, **kwargs)

                    # 计算执行时间
                    execution_time = (datetime.now() - start_time).total_seconds()

                    # 记录成功
                    if config.log_system:
                        log_data = _prepare_log_data(args, kwargs, result, config)
                        await _log_system(
                            LogLevelEnum.INFO,
                            f"函数 {func_name} 成功完成",
                            module_name,
                            func_name,
                            extra_data=log_data,
                        )
                        logger.info(f"函数 {func_name} 完成", extra=log_data)

                    return result

                except Exception as e:
                    # 计算执行时间
                    execution_time = (datetime.now() - start_time).total_seconds()
                    operation_result = OperationResultEnum.FAILED
                    error_message = str(e)
                    exception_info = traceback.format_exc()

                    # 记录错误
                    if config.log_system:
                        log_data = _prepare_log_data(args, kwargs, config=config)
                        log_data["error"] = error_message
                        await _log_system(
                            LogLevelEnum.ERROR,
                            f"函数 {func_name} 失败: {error_message}",
                            module_name,
                            func_name,
                            exception_info=exception_info,
                            extra_data=log_data,
                        )
                        logger.error(f"函数 {func_name} 失败", extra=log_data)

                    raise

                finally:
                    # 记录操作日志
                    if config.log_operation and user:
                        details = _prepare_log_data(args, kwargs, result, config)
                        await _log_operation(
                            user=user,
                            action=operation_type,
                            resource_type=resource_type,
                            resource_name=resource_name,
                            result=operation_result,
                            execution_time=execution_time,
                            error_message=error_message,
                            details=details,
                        )

            return async_wrapper  # type: ignore
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = datetime.now()
                execution_time = 0.0
                result = None
                error_message = None
                operation_result = OperationResultEnum.SUCCESS

                # 提取用户信息
                user = _extract_user_info(args, kwargs)
                resource_name = _extract_resource_name(args, kwargs)

                try:
                    # 记录开始
                    if config.log_system:
                        log_data = _prepare_log_data(args, kwargs, config=config)
                        logger.info(f"函数 {func_name} 已开始", extra=log_data)

                    # 执行函数
                    result = func(*args, **kwargs)

                    # 计算执行时间
                    execution_time = (datetime.now() - start_time).total_seconds()

                    # 记录成功
                    if config.log_system:
                        log_data = _prepare_log_data(args, kwargs, result, config)
                        logger.info(f"函数 {func_name} 完成", extra=log_data)

                    return result

                except Exception as e:
                    # 计算执行时间
                    execution_time = (datetime.now() - start_time).total_seconds()
                    operation_result = OperationResultEnum.FAILED
                    error_message = str(e)

                    # 记录错误
                    if config.log_system:
                        log_data = _prepare_log_data(args, kwargs, config=config)
                        log_data["error"] = error_message
                        logger.error(f"函数 {func_name} 失败", extra=log_data)

                    raise

                finally:
                    # 同步函数中的操作日志需要在后台任务中处理
                    if config.log_operation and user:
                        details = _prepare_log_data(args, kwargs, result, config)
                        # 创建后台任务记录操作日志
                        asyncio.create_task(
                            _log_operation(
                                user=user,
                                action=operation_type,
                                resource_type=resource_type,
                                resource_name=resource_name,
                                result=operation_result,
                                execution_time=execution_time,
                                error_message=error_message,
                                details=details,
                            )
                        )

            return sync_wrapper  # type: ignore

    return decorator


def _infer_operation_type(func_name: str) -> str:
    """从函数名推断操作类型"""
    func_name_lower = func_name.lower()

    if any(prefix in func_name_lower for prefix in ["create", "add", "insert", "new"]):
        return ActionEnum.CREATE.value
    elif any(prefix in func_name_lower for prefix in ["update", "modify", "edit", "change"]):
        return ActionEnum.UPDATE.value
    elif any(prefix in func_name_lower for prefix in ["delete", "remove", "del"]):
        return ActionEnum.DELETE.value
    elif any(prefix in func_name_lower for prefix in ["get", "find", "list", "search", "query", "select"]):
        return ActionEnum.READ.value
    elif any(prefix in func_name_lower for prefix in ["login", "auth", "signin"]):
        return ActionEnum.LOGIN.value
    elif any(prefix in func_name_lower for prefix in ["logout", "signout"]):
        return ActionEnum.LOGOUT.value
    elif any(prefix in func_name_lower for prefix in ["execute", "run", "exec"]):
        return ActionEnum.EXECUTE.value
    elif any(prefix in func_name_lower for prefix in ["connect"]):
        return ActionEnum.CONNECT.value
    elif any(prefix in func_name_lower for prefix in ["disconnect"]):
        return ActionEnum.DISCONNECT.value
    elif any(prefix in func_name_lower for prefix in ["backup"]):
        return ActionEnum.BACKUP.value
    elif any(prefix in func_name_lower for prefix in ["restore"]):
        return ActionEnum.RESTORE.value
    elif any(prefix in func_name_lower for prefix in ["restart", "reboot"]):
        return ActionEnum.RESTART.value
    elif any(prefix in func_name_lower for prefix in ["shutdown", "stop"]):
        return ActionEnum.SHUTDOWN.value
    else:
        return ActionEnum.EXECUTE.value  # 默认为执行操作


def _infer_resource_type(func_name: str, module_name: str) -> str:
    """从函数名和模块名推断资源类型"""
    # 先从模块名推断
    module_parts = module_name.split(".")
    for part in module_parts:
        if "device" in part.lower():
            return ResourceTypeEnum.DEVICE.value
        elif "user" in part.lower():
            return ResourceTypeEnum.USER.value
        elif "config" in part.lower() or "template" in part.lower():
            return ResourceTypeEnum.TEMPLATE.value
        elif "monitor" in part.lower():
            return ResourceTypeEnum.MONITOR.value
        elif "alert" in part.lower():
            return ResourceTypeEnum.ALERT.value
        elif "log" in part.lower():
            return ResourceTypeEnum.SYSTEM.value

    # 从函数名推断
    func_name_lower = func_name.lower()
    if "device" in func_name_lower:
        return ResourceTypeEnum.DEVICE.value
    elif "user" in func_name_lower:
        return ResourceTypeEnum.USER.value
    elif "config" in func_name_lower or "template" in func_name_lower:
        return ResourceTypeEnum.TEMPLATE.value
    elif "monitor" in func_name_lower:
        return ResourceTypeEnum.MONITOR.value
    elif "alert" in func_name_lower:
        return ResourceTypeEnum.ALERT.value
    elif "area" in func_name_lower:
        return ResourceTypeEnum.AREA.value
    elif "brand" in func_name_lower:
        return ResourceTypeEnum.BRAND.value
    elif "model" in func_name_lower:
        return ResourceTypeEnum.DEVICE_MODEL.value
    elif "group" in func_name_lower:
        return ResourceTypeEnum.DEVICE_GROUP.value
    else:
        return ResourceTypeEnum.SYSTEM.value


def _extract_user_info(args: tuple, kwargs: dict) -> str:
    """从参数中提取用户信息"""
    # 先从kwargs中查找
    for key in ["user", "user_id", "username", "current_user", "operator"]:
        if key in kwargs:
            value = kwargs[key]
            return str(value) if value is not None else "system"

    # 从args中查找（通常是第一个参数是self，第二个可能是用户）
    if len(args) >= 2:
        # 检查第二个参数是否像用户信息
        user_candidate = args[1]
        if isinstance(user_candidate, str) and user_candidate:
            return user_candidate

    return "system"


def _extract_resource_name(args: tuple, kwargs: dict) -> str:
    """从参数中提取资源名称"""
    # 从kwargs中查找
    for key in ["name", "resource_name", "hostname", "title", "id"]:
        if key in kwargs:
            value = kwargs[key]
            return str(value) if value is not None else "unknown"

    # 从args中查找ID或名称
    for arg in args[1:]:  # 跳过self
        if isinstance(arg, str | int) and arg:
            return str(arg)
        elif isinstance(arg, dict):
            for key in ["name", "hostname", "title", "id"]:
                if key in arg:
                    return str(arg[key])

    return "unknown"


# 预定义的常用配置
class LogConfigs:
    """预定义的日志配置"""

    # 完整记录（开发和调试用）
    FULL = LogConfig(
        log_operation=True,
        log_system=True,
        log_args=True,
        log_result=True,
    )

    # 只记录操作日志
    OPERATION_ONLY = LogConfig(
        log_operation=True,
        log_system=False,
    )

    # 只记录系统日志
    SYSTEM_ONLY = LogConfig(
        log_operation=False,
        log_system=True,
    )

    # 安全配置（不记录敏感参数）
    SECURE = LogConfig(
        log_operation=True,
        log_system=True,
        log_args=False,
        log_result=False,
    )  # 用户认证相关
    AUTH = LogConfig(
        log_operation=True,
        log_system=True,
        operation_type=ActionEnum.LOGIN.value,
        resource_type=ResourceTypeEnum.USER.value,
        log_args=False,  # 不记录密码等敏感信息
        log_result=False,
        mask_sensitive=["password", "token", "secret", "key", "credential"],
    )
