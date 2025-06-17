"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: configs.py
@DateTime: 2025-06-17
@Docs: 配置模板管理相关API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import ConfigTemplateServiceDep
from app.schemas import (
    ConfigTemplateCreate,
    ConfigTemplateQueryParams,
    ConfigTemplateResponse,
    ConfigTemplateUpdate,
    PaginatedResponse,
    StatusResponse,
    SuccessResponse,
    TemplateRenderRequest,
    TemplateRenderResponse,
)

router = APIRouter(prefix="/configs", tags=["配置管理"])


@router.post("/templates", response_model=SuccessResponse[ConfigTemplateResponse], status_code=status.HTTP_201_CREATED)
async def create_config_template(
    data: ConfigTemplateCreate,
    config_service: ConfigTemplateServiceDep,
) -> SuccessResponse[ConfigTemplateResponse]:
    """创建配置模板"""
    try:
        template = await config_service.create(data.model_dump())
        return SuccessResponse(
            message="配置模板创建成功",
            data=ConfigTemplateResponse.model_validate(template, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建配置模板失败: {str(e)}"
        ) from e


@router.get("/templates", response_model=SuccessResponse[PaginatedResponse[ConfigTemplateResponse]])
async def list_config_templates(
    config_service: ConfigTemplateServiceDep,
    params: ConfigTemplateQueryParams = Depends(),
) -> SuccessResponse[PaginatedResponse[ConfigTemplateResponse]]:
    """获取配置模板列表"""
    try:
        result = await config_service.get_paginated(
            page=params.page,
            page_size=params.page_size,
            user="system",
        )

        templates = [
            ConfigTemplateResponse.model_validate(template, from_attributes=True) for template in result["items"]
        ]

        return SuccessResponse(
            message="获取配置模板列表成功",
            data=PaginatedResponse(
                items=templates,
                pagination=result["pagination"],
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取配置模板列表失败: {str(e)}"
        ) from e


@router.get("/templates/{template_id}", response_model=SuccessResponse[ConfigTemplateResponse])
async def get_config_template(
    template_id: int,
    config_service: ConfigTemplateServiceDep,
) -> SuccessResponse[ConfigTemplateResponse]:
    """获取配置模板详情"""
    template = await config_service.get_by_id(template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置模板不存在")

    return SuccessResponse(
        message="获取配置模板详情成功",
        data=ConfigTemplateResponse.model_validate(template, from_attributes=True),
    )


@router.put("/templates/{template_id}", response_model=SuccessResponse[ConfigTemplateResponse])
async def update_config_template(
    template_id: int,
    data: ConfigTemplateUpdate,
    config_service: ConfigTemplateServiceDep,
) -> SuccessResponse[ConfigTemplateResponse]:
    """更新配置模板"""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有提供更新数据")

        template = await config_service.update(template_id, update_data)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置模板不存在")

        return SuccessResponse(
            message="配置模板更新成功",
            data=ConfigTemplateResponse.model_validate(template, from_attributes=True),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新配置模板失败: {str(e)}"
        ) from e


@router.delete("/templates/{template_id}", response_model=SuccessResponse[StatusResponse])
async def delete_config_template(
    template_id: int,
    config_service: ConfigTemplateServiceDep,
) -> SuccessResponse[StatusResponse]:
    """删除配置模板"""
    try:
        success = await config_service.delete(template_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置模板不存在")

        return SuccessResponse(
            message="配置模板删除成功",
            data=StatusResponse(status="success", message="配置模板删除成功"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除配置模板失败: {str(e)}"
        ) from e


@router.get("/templates/by-type/{template_type}", response_model=SuccessResponse[list[ConfigTemplateResponse]])
async def get_templates_by_type(
    template_type: str,
    config_service: ConfigTemplateServiceDep,
) -> SuccessResponse[list[ConfigTemplateResponse]]:
    """根据类型获取配置模板"""
    try:
        templates = await config_service.get_by_type(template_type)
        template_list = [
            ConfigTemplateResponse.model_validate(template, from_attributes=True) for template in templates
        ]

        return SuccessResponse(
            message=f"获取到 {len(template_list)} 个配置模板",
            data=template_list,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取配置模板失败: {str(e)}"
        ) from e


@router.get("/templates/search", response_model=SuccessResponse[list[ConfigTemplateResponse]])
async def search_config_templates(
    config_service: ConfigTemplateServiceDep,
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
) -> SuccessResponse[list[ConfigTemplateResponse]]:
    """搜索配置模板"""
    try:
        templates = await config_service.search_templates(keyword)
        template_list = [
            ConfigTemplateResponse.model_validate(template, from_attributes=True) for template in templates
        ]

        return SuccessResponse(
            message=f"搜索到 {len(template_list)} 个配置模板",
            data=template_list,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"搜索配置模板失败: {str(e)}"
        ) from e


@router.post("/templates/{template_id}/render", response_model=SuccessResponse[TemplateRenderResponse])
async def render_config_template(
    template_id: int,
    data: TemplateRenderRequest,
    config_service: ConfigTemplateServiceDep,
) -> SuccessResponse[TemplateRenderResponse]:
    """渲染配置模板"""
    try:
        # 获取模板
        template = await config_service.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="配置模板不存在")

        # 简单的模板渲染（实际项目中可以使用Jinja2等模板引擎）
        rendered_content = template.content
        for key, value in data.variables.items():
            rendered_content = rendered_content.replace(f"{{{{{key}}}}}", str(value))
        return SuccessResponse(
            message="模板渲染成功",
            data=TemplateRenderResponse(
                rendered_content=rendered_content,
                variables_used=list(data.variables.keys()),
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"模板渲染失败: {str(e)}") from e
