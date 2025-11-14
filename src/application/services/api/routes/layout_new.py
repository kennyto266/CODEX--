"""
Layout API Routes
布局配置API端点
提供完整的CRUD操作
"""

from typing import List, Optional, Dict, Any
import uuid

import structlog
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Query,
    Path,
    status,
)
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from src.api.dependencies.database import get_db
from src.database.repositories.layout_repository import LayoutRepository
from src.database.models.layout import LayoutConfigModel, LayoutComponentModel

logger = structlog.get_logger("api.layout")
router = APIRouter()

