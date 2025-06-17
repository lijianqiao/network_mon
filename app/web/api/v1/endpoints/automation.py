"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: automation.py
@DateTime: 2025-06-17
@Docs: 网络自动化相关API端点
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import NetworkAutomationServiceDep
from app.schemas.base import SuccessResponse
from app.schemas.network import (
    BatchNetworkTaskRequest,
    BatchNetworkTaskResponse,
    DeviceConnectivityRequest,
    DeviceConnectivityResponse,
    DiscoveredDevice,
    NetworkDiscoveryRequest,
    NetworkDiscoveryResponse,
    NetworkTaskRequest,
    NetworkTaskResponse,
    SupportedTaskInfo,
    SupportedTasksResponse,
)

router = APIRouter(prefix="/automation", tags=["网络自动化"])

# ================================ 任务执行 ================================


@router.get("/tasks/supported", response_model=SuccessResponse[SupportedTasksResponse])
async def get_supported_tasks(automation_service: NetworkAutomationServiceDep):
    """获取支持的网络任务列表"""
    try:
        task_names = automation_service.get_supported_tasks()
        # task_categories = automation_service.get_task_categories()

        # 构建任务信息
        task_info_map = {
            "device_version": {
                "description": "获取设备版本信息",
                "category": "device_info",
                "supported_devices": ["h3c", "huawei", "cisco"],
                "required_params": [],
                "optional_params": [],
            },
            "interface_status": {
                "description": "获取接口状态信息",
                "category": "interface",
                "supported_devices": ["h3c", "huawei", "cisco"],
                "required_params": [],
                "optional_params": ["interface_name"],
            },
            "interface_detail": {
                "description": "获取接口详细信息",
                "category": "interface",
                "supported_devices": ["h3c", "huawei", "cisco"],
                "required_params": ["interface_name"],
                "optional_params": [],
            },
            "find_mac": {
                "description": "查找MAC地址",
                "category": "network",
                "supported_devices": ["h3c", "huawei", "cisco"],
                "required_params": ["mac_address"],
                "optional_params": [],
            },
            "arp_table": {
                "description": "获取ARP表",
                "category": "network",
                "supported_devices": ["h3c", "huawei", "cisco"],
                "required_params": [],
                "optional_params": [],
            },
            "ping": {
                "description": "执行Ping测试",
                "category": "connectivity",
                "supported_devices": ["h3c", "huawei", "cisco"],
                "required_params": ["target_ip"],
                "optional_params": ["count", "size"],
            },
        }

        tasks = []
        categories = set()
        for task_name in task_names:
            if task_name in task_info_map:
                info = task_info_map[task_name]
                tasks.append(
                    SupportedTaskInfo(
                        name=task_name,
                        description=info["description"],
                        category=info["category"],
                        supported_devices=info["supported_devices"],
                        required_params=info["required_params"],
                        optional_params=info["optional_params"],
                    )
                )
                categories.add(info["category"])

        response = SupportedTasksResponse(tasks=tasks, total_count=len(tasks), categories=sorted(categories))

        return SuccessResponse(data=response)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取支持任务失败: {str(e)}"
        ) from e


@router.post("/tasks/execute", response_model=SuccessResponse[NetworkTaskResponse])
async def execute_network_task(task_request: NetworkTaskRequest, automation_service: NetworkAutomationServiceDep):
    """执行网络任务"""
    try:
        # 将字符串device_id转换为整数（假设是数据库ID）
        try:
            device_id = int(task_request.device_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"设备ID必须是整数: {task_request.device_id}"
            ) from e

        result = await automation_service.execute_device_task(
            device_id=device_id,
            task_name=task_request.task_name,
            username=task_request.username,
            password=task_request.password,
            **task_request.task_params,
        )

        # 转换时间戳格式
        if isinstance(result.get("timestamp"), str):
            timestamp = datetime.fromisoformat(result["timestamp"])
        else:
            timestamp = result["timestamp"]

        response = NetworkTaskResponse(
            success=result["success"],
            task_id=result["task_id"],
            device_id=str(result["device_id"]),
            task_name=task_request.task_name,
            timestamp=timestamp,
            duration=result.get("duration"),
            result=result.get("result"),
            error=result.get("error"),
        )

        return SuccessResponse(data=response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"执行任务失败: {str(e)}") from e


@router.post("/tasks/batch", response_model=SuccessResponse[BatchNetworkTaskResponse])
async def execute_batch_network_task(
    batch_request: BatchNetworkTaskRequest, automation_service: NetworkAutomationServiceDep
):
    """批量执行网络任务"""
    try:
        batch_id = str(uuid.uuid4())

        # 将字符串device_ids转换为整数列表
        try:
            device_ids = [int(device_id) for device_id in batch_request.device_ids]
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"设备ID必须是整数: {str(e)}") from e

        # 执行批量任务
        batch_result = await automation_service.execute_batch_task(
            device_ids=device_ids,
            task_name=batch_request.task_name,
            username=batch_request.username,
            password=batch_request.password,
            **batch_request.task_params,
        )

        # 转换结果格式
        tasks = []
        for result in batch_result["results"]:
            if isinstance(result.get("timestamp"), str):
                timestamp = datetime.fromisoformat(result["timestamp"])
            else:
                timestamp = result["timestamp"]

            tasks.append(
                NetworkTaskResponse(
                    success=result["success"],
                    task_id=result["task_id"],
                    device_id=str(result["device_id"]),
                    task_name=batch_request.task_name,
                    timestamp=timestamp,
                    duration=result.get("duration"),
                    result=result.get("result"),
                    error=result.get("error"),
                )
            )

        response = BatchNetworkTaskResponse(
            batch_id=batch_id,
            total_count=batch_result["total_count"],
            success_count=batch_result["success_count"],
            failed_count=batch_result["failed_count"],
            pending_count=0,
            tasks=tasks,
        )

        return SuccessResponse(data=response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"批量执行任务失败: {str(e)}"
        ) from e


# ================================ 连通性测试 ================================


@router.post("/connectivity/test", response_model=SuccessResponse[DeviceConnectivityResponse])
async def test_device_connectivity(
    connectivity_request: DeviceConnectivityRequest, automation_service: NetworkAutomationServiceDep
):
    """测试设备连通性"""
    try:
        # 将字符串device_id转换为整数
        try:
            device_id = int(connectivity_request.device_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"设备ID必须是整数: {connectivity_request.device_id}"
            ) from e

        result = await automation_service.test_device_connectivity(
            device_id=device_id,
            username=connectivity_request.username,
            password=connectivity_request.password,
            timeout=connectivity_request.timeout,
        )

        response = DeviceConnectivityResponse(
            device_id=str(result["device_id"]),
            device_ip=result["device_ip"],
            success=result["success"],
            response_time=result.get("response_time"),
            error=result.get("error"),
            timestamp=datetime.fromisoformat(result["timestamp"]),
        )

        return SuccessResponse(data=response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"连通性测试失败: {str(e)}"
        ) from e


# ================================ 网络发现 ================================


@router.post("/discovery/scan", response_model=SuccessResponse[NetworkDiscoveryResponse])
async def scan_network(discovery_request: NetworkDiscoveryRequest, automation_service: NetworkAutomationServiceDep):
    """扫描网络发现设备"""
    try:
        result = await automation_service.discover_network_devices(
            network_range=discovery_request.network_range,
            device_types=discovery_request.device_types,
            username=discovery_request.username,
            password=discovery_request.password,
            timeout=discovery_request.timeout,
        )

        # 转换发现的设备格式
        discovered_devices = []
        for device_data in result["discovered_devices"]:
            discovered_devices.append(
                DiscoveredDevice(
                    ip=device_data["ip"],
                    hostname=device_data.get("hostname"),
                    device_type=device_data.get("device_type"),
                    vendor=device_data.get("vendor"),
                    model=device_data.get("model"),
                    version=device_data.get("version"),
                    response_time=device_data["response_time"],
                )
            )

        response = NetworkDiscoveryResponse(
            discovery_id=result["discovery_id"],
            network_range=result["network_range"],
            total_hosts=result["total_hosts"],
            scanned_hosts=result["scanned_hosts"],
            discovered_devices=discovered_devices,
            start_time=datetime.fromisoformat(result["start_time"]),
            end_time=datetime.fromisoformat(result["end_time"]) if result.get("end_time") else None,
            duration=result.get("duration"),
        )

        return SuccessResponse(data=response)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"网络发现失败: {str(e)}") from e


# ================================ 统计信息 ================================


@router.get("/statistics", response_model=SuccessResponse[dict])
async def get_automation_statistics(automation_service: NetworkAutomationServiceDep):
    """获取自动化统计信息"""
    try:
        statistics = await automation_service.get_automation_statistics()
        return SuccessResponse(data=statistics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取统计信息失败: {str(e)}"
        ) from e
