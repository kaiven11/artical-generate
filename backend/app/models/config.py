"""
Configuration models for API providers and system settings.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..core.database import Base


class APIProvider(Base):
    """API provider configuration model."""
    
    __tablename__ = "api_providers"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Provider information
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    provider_type = Column(String(50), nullable=False)  # ai, detection, etc.
    
    # API configuration
    api_key = Column(Text, nullable=False)  # Encrypted API key
    api_url = Column(String(500), nullable=False)
    api_version = Column(String(20))
    
    # Status and settings
    is_enabled = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    weight = Column(Integer, default=1)  # For load balancing
    
    # Rate limiting
    max_requests_per_minute = Column(Integer, default=60)
    max_requests_per_hour = Column(Integer, default=1000)
    max_concurrent_requests = Column(Integer, default=5)
    
    # Cost information
    cost_per_1k_tokens_input = Column(Float, default=0.0)
    cost_per_1k_tokens_output = Column(Float, default=0.0)
    monthly_budget = Column(Float, default=0.0)
    current_usage = Column(Float, default=0.0)
    
    # Performance metrics
    success_rate = Column(Float, default=0.0)
    average_response_time = Column(Float, default=0.0)
    total_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    
    # Additional configuration
    extra_config = Column(JSON)  # Additional provider-specific config
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_used_at = Column(DateTime)
    
    def __repr__(self):
        return f"<APIProvider(id={self.id}, name='{self.name}', type='{self.provider_type}')>"
    
    def update_usage(self, tokens_used: int, cost: float, success: bool, response_time: float):
        """Update usage statistics."""
        self.total_requests += 1
        self.current_usage += cost
        self.last_used_at = datetime.utcnow()
        
        if not success:
            self.failed_requests += 1
        
        # Update success rate
        self.success_rate = ((self.total_requests - self.failed_requests) / self.total_requests) * 100
        
        # Update average response time
        if self.average_response_time == 0:
            self.average_response_time = response_time
        else:
            self.average_response_time = (self.average_response_time + response_time) / 2
        
        self.updated_at = datetime.utcnow()
    
    def is_within_budget(self, estimated_cost: float) -> bool:
        """Check if request is within budget."""
        if self.monthly_budget <= 0:
            return True
        return (self.current_usage + estimated_cost) <= self.monthly_budget
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "provider_type": self.provider_type,
            "api_url": self.api_url,
            "api_version": self.api_version,
            "is_enabled": self.is_enabled,
            "is_default": self.is_default,
            "weight": self.weight,
            "max_requests_per_minute": self.max_requests_per_minute,
            "max_requests_per_hour": self.max_requests_per_hour,
            "max_concurrent_requests": self.max_concurrent_requests,
            "cost_per_1k_tokens_input": self.cost_per_1k_tokens_input,
            "cost_per_1k_tokens_output": self.cost_per_1k_tokens_output,
            "monthly_budget": self.monthly_budget,
            "current_usage": self.current_usage,
            "success_rate": self.success_rate,
            "average_response_time": self.average_response_time,
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "extra_config": self.extra_config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }


class APIModel(Base):
    """API model configuration."""
    
    __tablename__ = "api_models"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Model information
    provider_id = Column(Integer, nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    display_name = Column(String(200), nullable=False)
    model_type = Column(String(50), nullable=False)  # text, image, etc.
    
    # Model parameters
    max_tokens = Column(Integer, default=4096)
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=0.9)
    frequency_penalty = Column(Float, default=0.0)
    presence_penalty = Column(Float, default=0.0)
    timeout_seconds = Column(Integer, default=15)  # 优化：从30秒减少到15秒
    
    # Usage settings
    use_cases = Column(JSON)  # List of use cases
    is_enabled = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "model_name": self.model_name,
            "display_name": self.display_name,
            "model_type": self.model_type,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "timeout_seconds": self.timeout_seconds,
            "use_cases": self.use_cases,
            "is_enabled": self.is_enabled,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SystemConfig(Base):
    """System configuration model."""
    
    __tablename__ = "system_config"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Configuration key-value
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    
    # Configuration metadata
    config_type = Column(String(50), default="string")  # string, int, float, bool, json
    is_encrypted = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)  # System configs cannot be deleted
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def get_typed_value(self):
        """Get value with proper type conversion."""
        if self.config_type == "int":
            return int(self.value)
        elif self.config_type == "float":
            return float(self.value)
        elif self.config_type == "bool":
            return self.value.lower() in ("true", "1", "yes", "on")
        elif self.config_type == "json":
            import json
            return json.loads(self.value)
        else:
            return self.value
    
    def set_typed_value(self, value):
        """Set value with type conversion."""
        if self.config_type == "json":
            import json
            self.value = json.dumps(value)
        else:
            self.value = str(value)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "key": self.key,
            "value": self.get_typed_value(),
            "description": self.description,
            "config_type": self.config_type,
            "is_encrypted": self.is_encrypted,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
