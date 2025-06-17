"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: devices.py
@DateTime: 2025-06-17
@Docs: 设备管理相关API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import (
    AreaServiceDep,
    BrandServiceDep,
    DeviceGroupServiceDep,
    DeviceModelServiceDep,
    DeviceServiceDep,
)
from app.schemas import (
    AreaCreate,
    AreaQueryParams,
    AreaResponse,
    AreaUpdate,
    BrandCreate,
    BrandQueryParams,
    BrandResponse,
    BrandUpdate,
    DeviceCreate,
    DeviceGroupCreate,
    DeviceGroupQueryParams,
    DeviceGroupResponse,
    DeviceGroupUpdate,
    DeviceModelCreate,
    DeviceModelQueryParams,
    DeviceModelResponse,
    DeviceModelUpdate,
    DeviceQueryParams,
    DeviceResponse,
    DeviceStatusUpdate,
    DeviceUpdate,
    PaginatedResponse,
    StatusResponse,
    SuccessResponse,
)

router = APIRouter(prefix="/devices", tags=["设备管理"])

# ================================ 品牌管理 ================================


@router.post("/brands", response_model=SuccessResponse[BrandResponse], status_code=status.HTTP_201_CREATED)
async def create_brand(
    data: BrandCreate,
    brand_service: BrandServiceDep,
) -> SuccessResponse[BrandResponse]:
    """创建设备品牌"""
    try:
        brand = await brand_service.create(data.model_dump())
        return SuccessResponse(
            message="品牌创建成功",
            data=BrandResponse.model_validate(brand, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建品牌失败: {str(e)}") from e


@router.get("/brands", response_model=SuccessResponse[PaginatedResponse[BrandResponse]])
async def list_brands(
    brand_service: BrandServiceDep,
    params: BrandQueryParams = Depends(),
) -> SuccessResponse[PaginatedResponse[BrandResponse]]:
    """获取品牌列表"""
    try:
        result = await brand_service.get_paginated(
            page=params.page,
            page_size=params.page_size,
        )

        brands = [BrandResponse.model_validate(brand, from_attributes=True) for brand in result["items"]]

        return SuccessResponse(
            message="获取品牌列表成功",
            data=PaginatedResponse(
                items=brands,
                pagination=result["pagination"],
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取品牌列表失败: {str(e)}"
        ) from e


@router.get("/brands/{brand_id}", response_model=SuccessResponse[BrandResponse])
async def get_brand(
    brand_id: int,
    brand_service: BrandServiceDep,
) -> SuccessResponse[BrandResponse]:
    """获取品牌详情"""
    brand = await brand_service.get_by_id(brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="品牌不存在")

    return SuccessResponse(
        message="获取品牌详情成功",
        data=BrandResponse.model_validate(brand, from_attributes=True),
    )


@router.put("/brands/{brand_id}", response_model=SuccessResponse[BrandResponse])
async def update_brand(
    brand_id: int,
    data: BrandUpdate,
    brand_service: BrandServiceDep,
) -> SuccessResponse[BrandResponse]:
    """更新品牌信息"""
    try:
        # 过滤掉None值
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有提供更新数据")

        brand = await brand_service.update(brand_id, update_data)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="品牌不存在")

        return SuccessResponse(
            message="品牌更新成功",
            data=BrandResponse.model_validate(brand, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新品牌失败: {str(e)}") from e


@router.delete("/brands/{brand_id}", response_model=SuccessResponse[StatusResponse])
async def delete_brand(
    brand_id: int,
    brand_service: BrandServiceDep,
) -> SuccessResponse[StatusResponse]:
    """删除品牌"""
    try:
        success = await brand_service.delete(brand_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="品牌不存在")
        return SuccessResponse(
            message="品牌删除成功",
            data=StatusResponse(status="success", message="品牌删除成功"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除品牌失败: {str(e)}") from e


# ================================ 设备型号管理 ================================


@router.post("/models", response_model=SuccessResponse[DeviceModelResponse], status_code=status.HTTP_201_CREATED)
async def create_device_model(
    data: DeviceModelCreate,
    device_model_service: DeviceModelServiceDep,
) -> SuccessResponse[DeviceModelResponse]:
    """创建设备型号"""
    try:
        model = await device_model_service.create(data.model_dump())
        return SuccessResponse(
            message="设备型号创建成功",
            data=DeviceModelResponse.model_validate(model, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建设备型号失败: {str(e)}"
        ) from e


@router.get("/models", response_model=SuccessResponse[PaginatedResponse[DeviceModelResponse]])
async def list_device_models(
    device_model_service: DeviceModelServiceDep,
    params: DeviceModelQueryParams = Depends(),
) -> SuccessResponse[PaginatedResponse[DeviceModelResponse]]:
    """获取设备型号列表"""
    try:
        result = await device_model_service.get_paginated(
            page=params.page,
            page_size=params.page_size,
        )

        models = [DeviceModelResponse.model_validate(model, from_attributes=True) for model in result["items"]]

        return SuccessResponse(
            message="获取设备型号列表成功",
            data=PaginatedResponse(
                items=models,
                pagination=result["pagination"],
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取设备型号列表失败: {str(e)}"
        ) from e


@router.get("/models/{model_id}", response_model=SuccessResponse[DeviceModelResponse])
async def get_device_model(
    model_id: int,
    device_model_service: DeviceModelServiceDep,
) -> SuccessResponse[DeviceModelResponse]:
    """获取设备型号详情"""
    model = await device_model_service.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备型号不存在")

    return SuccessResponse(
        message="获取设备型号详情成功",
        data=DeviceModelResponse.model_validate(model, from_attributes=True),
    )


@router.put("/models/{model_id}", response_model=SuccessResponse[DeviceModelResponse])
async def update_device_model(
    model_id: int,
    data: DeviceModelUpdate,
    device_model_service: DeviceModelServiceDep,
) -> SuccessResponse[DeviceModelResponse]:
    """更新设备型号信息"""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有提供更新数据")

        model = await device_model_service.update(model_id, update_data)
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备型号不存在")

        return SuccessResponse(
            message="设备型号更新成功",
            data=DeviceModelResponse.model_validate(model, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新设备型号失败: {str(e)}"
        ) from e


@router.delete("/models/{model_id}", response_model=SuccessResponse[StatusResponse])
async def delete_device_model(
    model_id: int,
    device_model_service: DeviceModelServiceDep,
) -> SuccessResponse[StatusResponse]:
    """删除设备型号"""
    try:
        success = await device_model_service.delete(model_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备型号不存在")

        return SuccessResponse(
            message="设备型号删除成功",
            data=StatusResponse(status="success", message="设备型号删除成功"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除设备型号失败: {str(e)}"
        ) from e


# ================================ 区域管理 ================================


@router.post("/areas", response_model=SuccessResponse[AreaResponse], status_code=status.HTTP_201_CREATED)
async def create_area(
    data: AreaCreate,
    area_service: AreaServiceDep,
) -> SuccessResponse[AreaResponse]:
    """创建区域"""
    try:
        area = await area_service.create(data.model_dump())
        return SuccessResponse(
            message="区域创建成功",
            data=AreaResponse.model_validate(area, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建区域失败: {str(e)}") from e


@router.get("/areas", response_model=SuccessResponse[PaginatedResponse[AreaResponse]])
async def list_areas(
    area_service: AreaServiceDep,
    params: AreaQueryParams = Depends(),
) -> SuccessResponse[PaginatedResponse[AreaResponse]]:
    """获取区域列表"""
    try:
        result = await area_service.get_paginated(
            page=params.page,
            page_size=params.page_size,
        )

        areas = [AreaResponse.model_validate(area, from_attributes=True) for area in result["items"]]

        return SuccessResponse(
            message="获取区域列表成功",
            data=PaginatedResponse(
                items=areas,
                pagination=result["pagination"],
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取区域列表失败: {str(e)}"
        ) from e


@router.get("/areas/{area_id}", response_model=SuccessResponse[AreaResponse])
async def get_area(
    area_id: int,
    area_service: AreaServiceDep,
) -> SuccessResponse[AreaResponse]:
    """获取区域详情"""
    area = await area_service.get_by_id(area_id)
    if not area:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="区域不存在")

    return SuccessResponse(
        message="获取区域详情成功",
        data=AreaResponse.model_validate(area, from_attributes=True),
    )


@router.put("/areas/{area_id}", response_model=SuccessResponse[AreaResponse])
async def update_area(
    area_id: int,
    data: AreaUpdate,
    area_service: AreaServiceDep,
) -> SuccessResponse[AreaResponse]:
    """更新区域信息"""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有提供更新数据")

        area = await area_service.update(area_id, update_data)
        if not area:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="区域不存在")

        return SuccessResponse(
            message="区域更新成功",
            data=AreaResponse.model_validate(area, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新区域失败: {str(e)}") from e


@router.delete("/areas/{area_id}", response_model=SuccessResponse[StatusResponse])
async def delete_area(
    area_id: int,
    area_service: AreaServiceDep,
) -> SuccessResponse[StatusResponse]:
    """删除区域"""
    try:
        success = await area_service.delete(area_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="区域不存在")

        return SuccessResponse(
            message="区域删除成功",
            data=StatusResponse(status="success", message="区域删除成功"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除区域失败: {str(e)}") from e


# ================================ 设备分组管理 ================================


@router.post("/groups", response_model=SuccessResponse[DeviceGroupResponse], status_code=status.HTTP_201_CREATED)
async def create_device_group(
    data: DeviceGroupCreate,
    device_group_service: DeviceGroupServiceDep,
) -> SuccessResponse[DeviceGroupResponse]:
    """创建设备分组"""
    try:
        group = await device_group_service.create(data.model_dump())
        return SuccessResponse(
            message="设备分组创建成功",
            data=DeviceGroupResponse.model_validate(group, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建设备分组失败: {str(e)}"
        ) from e


@router.get("/groups", response_model=SuccessResponse[PaginatedResponse[DeviceGroupResponse]])
async def list_device_groups(
    device_group_service: DeviceGroupServiceDep,
    params: DeviceGroupQueryParams = Depends(),
) -> SuccessResponse[PaginatedResponse[DeviceGroupResponse]]:
    """获取设备分组列表"""
    try:
        result = await device_group_service.get_paginated(
            page=params.page,
            page_size=params.page_size,
        )

        groups = [DeviceGroupResponse.model_validate(group, from_attributes=True) for group in result["items"]]

        return SuccessResponse(
            message="获取设备分组列表成功",
            data=PaginatedResponse(
                items=groups,
                pagination=result["pagination"],
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取设备分组列表失败: {str(e)}"
        ) from e


@router.get("/groups/{group_id}", response_model=SuccessResponse[DeviceGroupResponse])
async def get_device_group(
    group_id: int,
    device_group_service: DeviceGroupServiceDep,
) -> SuccessResponse[DeviceGroupResponse]:
    """获取设备分组详情"""
    group = await device_group_service.get_by_id(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备分组不存在")

    return SuccessResponse(
        message="获取设备分组详情成功",
        data=DeviceGroupResponse.model_validate(group, from_attributes=True),
    )


@router.put("/groups/{group_id}", response_model=SuccessResponse[DeviceGroupResponse])
async def update_device_group(
    group_id: int,
    data: DeviceGroupUpdate,
    device_group_service: DeviceGroupServiceDep,
) -> SuccessResponse[DeviceGroupResponse]:
    """更新设备分组信息"""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有提供更新数据")

        group = await device_group_service.update(group_id, update_data)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备分组不存在")

        return SuccessResponse(
            message="设备分组更新成功",
            data=DeviceGroupResponse.model_validate(group, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新设备分组失败: {str(e)}"
        ) from e


@router.delete("/groups/{group_id}", response_model=SuccessResponse[StatusResponse])
async def delete_device_group(
    group_id: int,
    device_group_service: DeviceGroupServiceDep,
) -> SuccessResponse[StatusResponse]:
    """删除设备分组"""
    try:
        success = await device_group_service.delete(group_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备分组不存在")

        return SuccessResponse(
            message="设备分组删除成功",
            data=StatusResponse(status="success", message="设备分组删除成功"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除设备分组失败: {str(e)}"
        ) from e


# ================================ 设备管理 ================================


@router.post("", response_model=SuccessResponse[DeviceResponse], status_code=status.HTTP_201_CREATED)
async def create_device(
    data: DeviceCreate,
    device_service: DeviceServiceDep,
) -> SuccessResponse[DeviceResponse]:
    """创建设备"""
    try:
        device_data = data.model_dump()
        # 将IP地址转换为字符串
        if "management_ip" in device_data:
            device_data["management_ip"] = str(device_data["management_ip"])

        device = await device_service.create(device_data)
        return SuccessResponse(
            message="设备创建成功",
            data=DeviceResponse.model_validate(device, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建设备失败: {str(e)}") from e


@router.get("", response_model=SuccessResponse[PaginatedResponse[DeviceResponse]])
async def list_devices(
    device_service: DeviceServiceDep,
    params: DeviceQueryParams = Depends(),
) -> SuccessResponse[PaginatedResponse[DeviceResponse]]:
    """获取设备列表"""
    try:
        result = await device_service.get_paginated(
            page=params.page,
            page_size=params.page_size,
        )

        devices = [DeviceResponse.model_validate(device, from_attributes=True) for device in result["items"]]

        return SuccessResponse(
            message="获取设备列表成功",
            data=PaginatedResponse(
                items=devices,
                pagination=result["pagination"],
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取设备列表失败: {str(e)}"
        ) from e


@router.get("/{device_id}", response_model=SuccessResponse[DeviceResponse])
async def get_device(
    device_id: int,
    device_service: DeviceServiceDep,
) -> SuccessResponse[DeviceResponse]:
    """获取设备详情"""
    device = await device_service.get_by_id(device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")

    return SuccessResponse(
        message="获取设备详情成功",
        data=DeviceResponse.model_validate(device, from_attributes=True),
    )


@router.put("/{device_id}", response_model=SuccessResponse[DeviceResponse])
async def update_device(
    device_id: int,
    data: DeviceUpdate,
    device_service: DeviceServiceDep,
) -> SuccessResponse[DeviceResponse]:
    """更新设备信息"""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有提供更新数据")

        # 将IP地址转换为字符串
        if "management_ip" in update_data:
            update_data["management_ip"] = str(update_data["management_ip"])

        device = await device_service.update(device_id, update_data)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")

        return SuccessResponse(
            message="设备更新成功",
            data=DeviceResponse.model_validate(device, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新设备失败: {str(e)}") from e


@router.delete("/{device_id}", response_model=SuccessResponse[StatusResponse])
async def delete_device(
    device_id: int,
    device_service: DeviceServiceDep,
) -> SuccessResponse[StatusResponse]:
    """删除设备"""
    try:
        success = await device_service.delete(device_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")

        return SuccessResponse(
            message="设备删除成功",
            data=StatusResponse(status="success", message="设备删除成功"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除设备失败: {str(e)}") from e


@router.patch("/{device_id}/status", response_model=SuccessResponse[DeviceResponse])
async def update_device_status(
    device_id: int,
    data: DeviceStatusUpdate,
    device_service: DeviceServiceDep,
) -> SuccessResponse[DeviceResponse]:
    """更新设备状态"""
    try:
        device = await device_service.update_device_status(device_id, data.status.value)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")

        return SuccessResponse(
            message="设备状态更新成功",
            data=DeviceResponse.model_validate(device, from_attributes=True),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新设备状态失败: {str(e)}"
        ) from e


@router.get("/by-ip/{management_ip}", response_model=SuccessResponse[DeviceResponse])
async def get_device_by_ip(
    management_ip: str,
    device_service: DeviceServiceDep,
) -> SuccessResponse[DeviceResponse]:
    """根据IP地址获取设备"""
    try:
        device = await device_service.get_by_ip(management_ip)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")

        return SuccessResponse(
            message="获取设备信息成功",
            data=DeviceResponse.model_validate(device, from_attributes=True),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取设备失败: {str(e)}") from e


@router.get("/search", response_model=SuccessResponse[list[DeviceResponse]])
async def search_devices(
    device_service: DeviceServiceDep,
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
) -> SuccessResponse[list[DeviceResponse]]:
    """搜索设备"""
    try:
        devices = await device_service.search_devices(keyword)
        device_list = [DeviceResponse.model_validate(device, from_attributes=True) for device in devices]

        return SuccessResponse(
            message=f"搜索到 {len(device_list)} 个设备",
            data=device_list,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"搜索设备失败: {str(e)}") from e


@router.get("/statistics", response_model=SuccessResponse[dict])
async def get_device_statistics(
    device_service: DeviceServiceDep,
) -> SuccessResponse[dict]:
    """获取设备统计信息"""
    try:
        statistics = await device_service.get_device_statistics()
        return SuccessResponse(
            message="获取设备统计信息成功",
            data=statistics,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取设备统计失败: {str(e)}"
        ) from e
