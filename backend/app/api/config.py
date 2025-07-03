"""
API configuration management endpoints.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.config import APIProvider, APIModel, SystemConfig
from ..services.api_config_service import APIConfigService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])

# Pydantic models for API requests/responses
class APIProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    provider_type: str = Field(..., pattern="^(ai|detection|publish)$")
    api_key: str = Field(..., min_length=1)
    api_url: str = Field(..., min_length=1, max_length=500)
    api_version: Optional[str] = None
    is_enabled: bool = True
    is_default: bool = False
    weight: int = Field(default=1, ge=1, le=100)
    max_requests_per_minute: int = Field(default=60, ge=1, le=10000)
    max_requests_per_hour: int = Field(default=1000, ge=1, le=100000)
    max_concurrent_requests: int = Field(default=5, ge=1, le=100)
    cost_per_1k_tokens_input: float = Field(default=0.0, ge=0.0)
    cost_per_1k_tokens_output: float = Field(default=0.0, ge=0.0)
    monthly_budget: float = Field(default=0.0, ge=0.0)
    extra_config: Optional[Dict[str, Any]] = None

class APIProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    api_version: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None
    weight: Optional[int] = None
    max_requests_per_minute: Optional[int] = None
    max_requests_per_hour: Optional[int] = None
    max_concurrent_requests: Optional[int] = None
    cost_per_1k_tokens_input: Optional[float] = None
    cost_per_1k_tokens_output: Optional[float] = None
    monthly_budget: Optional[float] = None
    extra_config: Optional[Dict[str, Any]] = None

class APIProviderResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    provider_type: str
    api_url: str
    api_version: Optional[str]
    is_enabled: bool
    is_default: bool
    weight: int
    max_requests_per_minute: int
    max_requests_per_hour: int
    max_concurrent_requests: int
    cost_per_1k_tokens_input: float
    cost_per_1k_tokens_output: float
    monthly_budget: float
    current_usage: float
    success_rate: float
    average_response_time: float
    total_requests: int
    failed_requests: int
    extra_config: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to handle datetime serialization."""
        data = {
            'id': obj.id,
            'name': obj.name,
            'display_name': obj.display_name,
            'description': obj.description,
            'provider_type': obj.provider_type,
            'api_url': obj.api_url,
            'api_version': obj.api_version,
            'is_enabled': obj.is_enabled,
            'is_default': obj.is_default,
            'weight': obj.weight,
            'max_requests_per_minute': obj.max_requests_per_minute,
            'max_requests_per_hour': obj.max_requests_per_hour,
            'max_concurrent_requests': obj.max_concurrent_requests,
            'cost_per_1k_tokens_input': obj.cost_per_1k_tokens_input,
            'cost_per_1k_tokens_output': obj.cost_per_1k_tokens_output,
            'monthly_budget': obj.monthly_budget,
            'current_usage': obj.current_usage,
            'success_rate': obj.success_rate,
            'average_response_time': obj.average_response_time,
            'total_requests': obj.total_requests,
            'failed_requests': obj.failed_requests,
            'extra_config': obj.extra_config,
            'created_at': obj.created_at.isoformat() if obj.created_at else '',
            'updated_at': obj.updated_at.isoformat() if obj.updated_at else ''
        }
        return cls(**data)

class APIModelCreate(BaseModel):
    provider_id: int
    model_name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    model_type: str = Field(default="text", pattern="^(text|image|audio|video)$")
    max_tokens: int = Field(default=4096, ge=1, le=1000000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    timeout_seconds: int = Field(default=15, ge=1, le=300)  # 优化：从30秒减少到15秒
    use_cases: Optional[List[str]] = None
    is_enabled: bool = True

class APIModelResponse(BaseModel):
    id: int
    provider_id: int
    model_name: str
    display_name: str
    model_type: str
    max_tokens: int
    temperature: float
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    timeout_seconds: int
    use_cases: Optional[List[str]]
    is_enabled: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    response_time: Optional[float] = None
    model_list: Optional[List[str]] = None
    error_details: Optional[str] = None

# API Provider endpoints
@router.get("/providers", response_model=List[APIProviderResponse])
async def get_providers(
    provider_type: Optional[str] = None,
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all API providers."""
    try:
        service = APIConfigService(db)
        providers = await service.get_providers(
            provider_type=provider_type,
            enabled_only=enabled_only
        )
        return providers
    except Exception as e:
        logger.error(f"Failed to get providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/providers", response_model=APIProviderResponse)
async def create_provider(
    provider: APIProviderCreate,
    db: Session = Depends(get_db)
):
    """Create a new API provider."""
    try:
        service = APIConfigService(db)
        new_provider = await service.create_provider(provider.model_dump())
        return new_provider
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers/{provider_id}", response_model=APIProviderResponse)
async def get_provider(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific API provider."""
    try:
        service = APIConfigService(db)
        provider = await service.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/providers/{provider_id}", response_model=APIProviderResponse)
async def update_provider(
    provider_id: int,
    provider_update: APIProviderUpdate,
    db: Session = Depends(get_db)
):
    """Update an API provider."""
    try:
        service = APIConfigService(db)
        updated_provider = await service.update_provider(
            provider_id, 
            provider_update.model_dump(exclude_unset=True)
        )
        if not updated_provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        return updated_provider
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """Delete an API provider."""
    try:
        service = APIConfigService(db)
        success = await service.delete_provider(provider_id)
        if not success:
            raise HTTPException(status_code=404, detail="Provider not found")
        return {"message": "Provider deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/providers/{provider_id}/test", response_model=ConnectionTestResponse)
async def test_provider_connection(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """Test connection to an API provider."""
    try:
        logger.info(f"Testing connection for provider {provider_id}")
        service = APIConfigService(db)
        result = await service.test_provider_connection(provider_id)
        logger.info(f"Test result for provider {provider_id}: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API Model endpoints
@router.get("/providers/{provider_id}/models", response_model=List[APIModelResponse])
async def get_provider_models(
    provider_id: int,
    enabled_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get models for a specific provider."""
    try:
        service = APIConfigService(db)
        models = await service.get_provider_models(provider_id, enabled_only)
        return models
    except Exception as e:
        logger.error(f"Failed to get models for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models", response_model=APIModelResponse)
async def create_model(
    model: APIModelCreate,
    db: Session = Depends(get_db)
):
    """Create a new API model."""
    try:
        service = APIConfigService(db)
        new_model = await service.create_model(model.model_dump())
        return new_model
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/models/{model_id}", response_model=APIModelResponse)
async def update_model(
    model_id: int,
    model_update: dict,
    db: Session = Depends(get_db)
):
    """Update an API model."""
    try:
        service = APIConfigService(db)
        updated_model = await service.update_model(model_id, model_update)
        if not updated_model:
            raise HTTPException(status_code=404, detail="Model not found")
        return updated_model
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/models/{model_id}")
async def delete_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Delete an API model."""
    try:
        service = APIConfigService(db)
        success = await service.delete_model(model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model not found")
        return {"message": "Model deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
