"""
統一API響應格式模型
"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class PaginationInfo(BaseModel):
    """分頁信息"""
    total: int = Field(..., description="總記錄數")
    page: int = Field(..., description="當前頁碼")
    size: int = Field(..., description="每頁數量")
    pages: int = Field(..., description="總頁數")
    has_next: bool = Field(..., description="是否有下一頁")
    has_prev: bool = Field(..., description="是否有上一頁")
    next_page: Optional[int] = Field(None, description="下一頁頁碼")
    prev_page: Optional[int] = Field(None, description="上一頁頁碼")


class APIResponse(BaseModel):
    """
    統一API響應格式

    所有API端點都應該返回這個格式
    """

    success: bool = Field(default=True, description="請求是否成功")
    data: Optional[Any] = Field(default=None, description="響應數據")
    error: Optional[str] = Field(default=None, description="錯誤信息")
    message: Optional[str] = Field(default=None, description="提示信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="時間戳")

    @classmethod
    def success(cls, data: Any = None, message: str = None) -> "APIResponse":
        """創建成功響應"""
        return cls(success=True, data=data, message=message)

    @classmethod
    def error(cls, error: str, message: str = None) -> "APIResponse":
        """創建錯誤響應"""
        return cls(success=False, error=error, message=message)

    @classmethod
    def paginated(
        cls,
        data: List[Any],
        pagination: PaginationInfo,
        filters: Optional[Dict] = None
    ) -> "APIResponse":
        """創建分頁響應"""
        return cls(
            success=True,
            data={
                "items": data,
                "pagination": pagination.dict(),
                "filters": filters or {}
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return self.dict(by_alias=True)


class APIResponseWithMeta(BaseModel):
    """
    帶元數據的API響應
    """

    success: bool = True
    data: Any
    meta: Dict[str, Any] = Field(default_factory=dict)
    links: Optional[Dict[str, str]] = Field(default=None, description="相關鏈接")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== 便捷函數 ====================

def create_success_response(data: Any = None, message: str = None) -> APIResponse:
    """創建成功響應"""
    return APIResponse.success(data=data, message=message)


def create_error_response(error: str, message: str = None) -> APIResponse:
    """創建錯誤響應"""
    return APIResponse.error(error=error, message=message)


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    size: int,
    filters: Optional[Dict] = None
) -> APIResponse:
    """創建分頁響應"""
    pagination = PaginationInfo(
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if total > 0 else 0,
        has_next=page * size < total,
        has_prev=page > 1,
        next_page=page + 1 if page * size < total else None,
        prev_page=page - 1 if page > 1 else None
    )
    return APIResponse.paginated(items, pagination, filters)


def create_list_response(
    items: List[Any],
    total: Optional[int] = None,
    message: str = None
) -> APIResponse:
    """創建列表響應"""
    if total is None:
        total = len(items)
    return APIResponse.success(data={"items": items, "total": total}, message=message)


def create_detail_response(
    item: Any,
    message: str = None
) -> APIResponse:
    """創建詳情響應"""
    return APIResponse.success(data=item, message=message)


def create_created_response(
    item: Any,
    message: str = "創建成功"
) -> APIResponse:
    """創建創建成功響應"""
    return APIResponse.success(data=item, message=message)


def create_updated_response(
    item: Any,
    message: str = "更新成功"
) -> APIResponse:
    """創建更新成功響應"""
    return APIResponse.success(data=item, message=message)


def create_deleted_response(message: str = "刪除成功") -> APIResponse:
    """創建刪除成功響應"""
    return APIResponse.success(data=None, message=message)


# ==================== 響應模板 ====================

class ResponseTemplates:
    """API響應模板"""

    # 成功響應模板
    SUCCESS = "請求處理成功"

    # 錯誤響應模板
    ERROR_INVALID_PARAM = "無效的參數"
    ERROR_NOT_FOUND = "資源不存在"
    ERROR_UNAUTHORIZED = "未授權訪問"
    ERROR_FORBIDDEN = "禁止訪問"
    ERROR_INTERNAL = "內部服務器錯誤"
    ERROR_DATABASE = "數據庫操作失敗"
    ERROR_CACHE = "緩存操作失敗"

    # 提示信息模板
    MSG_CREATED = "創建成功"
    MSG_UPDATED = "更新成功"
    MSG_DELETED = "刪除成功"
    MSG_FOUND = "查詢成功"
    MSG_LISTED = "列表查詢成功"


# ==================== 響應輔助類 ====================

class ResponseHelper:
    """響應輔助類"""

    @staticmethod
    def handle_exception(e: Exception, logger=None) -> APIResponse:
        """統一異常處理"""
        error_msg = str(e)
        if logger:
            logger.error(f"API異常: {error_msg}", exc_info=True)

        # 根據異常類型返回不同的錯誤信息
        if isinstance(e, ValueError):
            return create_error_response(ResponseTemplates.ERROR_INVALID_PARAM, error_msg)
        elif isinstance(e, PermissionError):
            return create_error_response(ResponseTemplates.ERROR_FORBIDDEN, error_msg)
        elif isinstance(e, FileNotFoundError):
            return create_error_response(ResponseTemplates.ERROR_NOT_FOUND, error_msg)
        else:
            return create_error_response(ResponseTemplates.ERROR_INTERNAL, error_msg)

    @staticmethod
    def validate_pagination_params(page: int, size: int, max_size: int = 100) -> tuple:
        """驗證分頁參數"""
        if page < 1:
            page = 1
        if size < 1:
            size = 50
        if size > max_size:
            size = max_size
        return page, size

    @staticmethod
    def validate_sort_params(sort_by: str, sort_order: str, allowed_fields: List[str]) -> tuple:
        """驗證排序參數"""
        if sort_by not in allowed_fields:
            sort_by = allowed_fields[0] if allowed_fields else None

        sort_order = sort_order.lower()
        if sort_order not in ["asc", "desc"]:
            sort_order = "desc"

        return sort_by, sort_order
