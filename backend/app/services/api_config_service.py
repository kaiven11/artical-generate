"""
API configuration service for managing providers and models.
"""

import logging
import asyncio
import time
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from cryptography.fernet import Fernet
import httpx

from ..models.config import APIProvider, APIModel, SystemConfig
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class APIConfigService:
    """Service for managing API configurations."""
    
    def __init__(self, db: Session):
        self.db = db
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for API keys."""
        try:
            # Try to get existing key from system config
            config = self.db.query(SystemConfig).filter(
                SystemConfig.key == "api_encryption_key"
            ).first()
            
            if config:
                return config.value.encode()
            else:
                # Create new key
                key = Fernet.generate_key()
                new_config = SystemConfig(
                    key="api_encryption_key",
                    value=key.decode(),
                    description="Encryption key for API keys",
                    config_type="string",
                    is_encrypted=False,
                    is_system=True
                )
                self.db.add(new_config)
                self.db.commit()
                return key
        except Exception as e:
            logger.error(f"Failed to get/create encryption key: {e}")
            # Fallback to a default key (not recommended for production)
            return Fernet.generate_key()
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key."""
        try:
            return self._cipher.encrypt(api_key.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {e}")
            return api_key  # Fallback to plain text (not recommended)
    
    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key."""
        try:
            return self._cipher.decrypt(encrypted_key.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            return encrypted_key  # Fallback to assuming it's plain text
    
    async def get_providers(
        self, 
        provider_type: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[APIProvider]:
        """Get API providers with optional filtering."""
        try:
            query = self.db.query(APIProvider)
            
            if provider_type:
                query = query.filter(APIProvider.provider_type == provider_type)
            
            if enabled_only:
                query = query.filter(APIProvider.is_enabled == True)
            
            providers = query.order_by(APIProvider.display_name).all()
            
            # Decrypt API keys for response (but mask them)
            result = []
            for provider in providers:
                # Create a dict representation with masked API key
                provider_dict = {
                    'id': provider.id,
                    'name': provider.name,
                    'display_name': provider.display_name,
                    'description': provider.description,
                    'provider_type': provider.provider_type,
                    'api_url': provider.api_url,
                    'api_version': provider.api_version,
                    'is_enabled': provider.is_enabled,
                    'is_default': provider.is_default,
                    'weight': provider.weight,
                    'max_requests_per_minute': provider.max_requests_per_minute,
                    'max_requests_per_hour': provider.max_requests_per_hour,
                    'max_concurrent_requests': provider.max_concurrent_requests,
                    'cost_per_1k_tokens_input': provider.cost_per_1k_tokens_input,
                    'cost_per_1k_tokens_output': provider.cost_per_1k_tokens_output,
                    'monthly_budget': provider.monthly_budget,
                    'current_usage': provider.current_usage,
                    'success_rate': provider.success_rate,
                    'average_response_time': provider.average_response_time,
                    'total_requests': provider.total_requests,
                    'failed_requests': provider.failed_requests,
                    'extra_config': provider.extra_config,
                    'api_key': "***" + provider.api_key[-4:] if len(provider.api_key) > 4 else "***",
                    'created_at': provider.created_at.isoformat() if provider.created_at else '',
                    'updated_at': provider.updated_at.isoformat() if provider.updated_at else ''
                }
                result.append(provider_dict)

            return result
        except Exception as e:
            logger.error(f"Failed to get providers: {e}")
            raise
    
    async def get_provider(self, provider_id: int) -> Optional[APIProvider]:
        """Get a specific provider by ID."""
        try:
            provider = self.db.query(APIProvider).filter(
                APIProvider.id == provider_id
            ).first()
            
            if provider:
                # Create a dict representation with masked API key
                return {
                    'id': provider.id,
                    'name': provider.name,
                    'display_name': provider.display_name,
                    'description': provider.description,
                    'provider_type': provider.provider_type,
                    'api_url': provider.api_url,
                    'api_version': provider.api_version,
                    'is_enabled': provider.is_enabled,
                    'is_default': provider.is_default,
                    'weight': provider.weight,
                    'max_requests_per_minute': provider.max_requests_per_minute,
                    'max_requests_per_hour': provider.max_requests_per_hour,
                    'max_concurrent_requests': provider.max_concurrent_requests,
                    'cost_per_1k_tokens_input': provider.cost_per_1k_tokens_input,
                    'cost_per_1k_tokens_output': provider.cost_per_1k_tokens_output,
                    'monthly_budget': provider.monthly_budget,
                    'current_usage': provider.current_usage,
                    'success_rate': provider.success_rate,
                    'average_response_time': provider.average_response_time,
                    'total_requests': provider.total_requests,
                    'failed_requests': provider.failed_requests,
                    'extra_config': provider.extra_config,
                    'api_key': "***" + provider.api_key[-4:] if len(provider.api_key) > 4 else "***",
                    'created_at': provider.created_at.isoformat() if provider.created_at else '',
                    'updated_at': provider.updated_at.isoformat() if provider.updated_at else ''
                }

            return None
        except Exception as e:
            logger.error(f"Failed to get provider {provider_id}: {e}")
            raise
    
    async def create_provider(self, provider_data: Dict[str, Any]) -> APIProvider:
        """Create a new API provider."""
        try:
            # Check if provider name already exists
            existing = self.db.query(APIProvider).filter(
                APIProvider.name == provider_data["name"]
            ).first()
            
            if existing:
                raise ValueError(f"Provider with name '{provider_data['name']}' already exists")
            
            # Encrypt API key
            provider_data["api_key"] = self._encrypt_api_key(provider_data["api_key"])
            
            # Handle default provider logic
            if provider_data.get("is_default", False):
                # Unset other default providers of the same type
                self.db.query(APIProvider).filter(
                    and_(
                        APIProvider.provider_type == provider_data["provider_type"],
                        APIProvider.is_default == True
                    )
                ).update({"is_default": False})
            
            # Create new provider
            provider = APIProvider(**provider_data)
            self.db.add(provider)
            self.db.commit()
            self.db.refresh(provider)

            # Create a dict representation with masked API key
            return {
                'id': provider.id,
                'name': provider.name,
                'display_name': provider.display_name,
                'description': provider.description,
                'provider_type': provider.provider_type,
                'api_url': provider.api_url,
                'api_version': provider.api_version,
                'is_enabled': provider.is_enabled,
                'is_default': provider.is_default,
                'weight': provider.weight,
                'max_requests_per_minute': provider.max_requests_per_minute,
                'max_requests_per_hour': provider.max_requests_per_hour,
                'max_concurrent_requests': provider.max_concurrent_requests,
                'cost_per_1k_tokens_input': provider.cost_per_1k_tokens_input,
                'cost_per_1k_tokens_output': provider.cost_per_1k_tokens_output,
                'monthly_budget': provider.monthly_budget,
                'current_usage': provider.current_usage,
                'success_rate': provider.success_rate,
                'average_response_time': provider.average_response_time,
                'total_requests': provider.total_requests,
                'failed_requests': provider.failed_requests,
                'extra_config': provider.extra_config,
                'api_key': "***" + provider.api_key[-4:] if len(provider.api_key) > 4 else "***",
                'created_at': provider.created_at.isoformat() if provider.created_at else '',
                'updated_at': provider.updated_at.isoformat() if provider.updated_at else ''
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create provider: {e}")
            raise
    
    async def update_provider(
        self, 
        provider_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[APIProvider]:
        """Update an existing API provider."""
        try:
            provider = self.db.query(APIProvider).filter(
                APIProvider.id == provider_id
            ).first()
            
            if not provider:
                return None
            
            # Encrypt API key if provided
            if "api_key" in update_data:
                update_data["api_key"] = self._encrypt_api_key(update_data["api_key"])
            
            # Handle default provider logic
            if update_data.get("is_default", False):
                # Unset other default providers of the same type
                self.db.query(APIProvider).filter(
                    and_(
                        APIProvider.provider_type == provider.provider_type,
                        APIProvider.is_default == True,
                        APIProvider.id != provider_id
                    )
                ).update({"is_default": False})
            
            # Update provider
            for key, value in update_data.items():
                setattr(provider, key, value)
            
            self.db.commit()
            self.db.refresh(provider)

            # Create a dict representation with masked API key
            return {
                'id': provider.id,
                'name': provider.name,
                'display_name': provider.display_name,
                'description': provider.description,
                'provider_type': provider.provider_type,
                'api_url': provider.api_url,
                'api_version': provider.api_version,
                'is_enabled': provider.is_enabled,
                'is_default': provider.is_default,
                'weight': provider.weight,
                'max_requests_per_minute': provider.max_requests_per_minute,
                'max_requests_per_hour': provider.max_requests_per_hour,
                'max_concurrent_requests': provider.max_concurrent_requests,
                'cost_per_1k_tokens_input': provider.cost_per_1k_tokens_input,
                'cost_per_1k_tokens_output': provider.cost_per_1k_tokens_output,
                'monthly_budget': provider.monthly_budget,
                'current_usage': provider.current_usage,
                'success_rate': provider.success_rate,
                'average_response_time': provider.average_response_time,
                'total_requests': provider.total_requests,
                'failed_requests': provider.failed_requests,
                'extra_config': provider.extra_config,
                'api_key': "***" + provider.api_key[-4:] if len(provider.api_key) > 4 else "***",
                'created_at': provider.created_at.isoformat() if provider.created_at else '',
                'updated_at': provider.updated_at.isoformat() if provider.updated_at else ''
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update provider {provider_id}: {e}")
            raise
    
    async def delete_provider(self, provider_id: int) -> bool:
        """Delete an API provider."""
        try:
            provider = self.db.query(APIProvider).filter(
                APIProvider.id == provider_id
            ).first()
            
            if not provider:
                return False
            
            # Delete associated models first
            self.db.query(APIModel).filter(
                APIModel.provider_id == provider_id
            ).delete()
            
            # Delete provider
            self.db.delete(provider)
            self.db.commit()
            
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete provider {provider_id}: {e}")
            raise
    
    async def test_provider_connection(self, provider_id: int) -> Dict[str, Any]:
        """Test connection to an API provider."""
        try:
            provider = self.db.query(APIProvider).filter(
                APIProvider.id == provider_id
            ).first()
            
            if not provider:
                return {
                    "success": False,
                    "message": "Provider not found",
                    "error_details": "Provider does not exist"
                }
            
            # Decrypt API key for testing
            api_key = self._decrypt_api_key(provider.api_key)
            
            # Test connection based on provider type
            start_time = time.time()
            
            if provider.provider_type == "ai":
                result = await self._test_ai_provider(provider, api_key)
            elif provider.provider_type == "detection":
                result = await self._test_detection_provider(provider, api_key)
            else:
                result = await self._test_generic_provider(provider, api_key)
            
            response_time = time.time() - start_time
            result["response_time"] = round(response_time * 1000, 2)  # Convert to ms
            
            # Update provider statistics (only if columns exist)
            try:
                if hasattr(provider, 'success_rate') and result["success"]:
                    provider.success_rate = min(100.0, getattr(provider, 'success_rate', 0) + 1.0)
                if hasattr(provider, 'average_response_time') and result["success"]:
                    current_avg = getattr(provider, 'average_response_time', 0)
                    provider.average_response_time = current_avg * 0.9 + response_time * 0.1
                if hasattr(provider, 'failed_requests') and not result["success"]:
                    provider.failed_requests = getattr(provider, 'failed_requests', 0) + 1
                if hasattr(provider, 'total_requests'):
                    provider.total_requests = getattr(provider, 'total_requests', 0) + 1

                self.db.commit()
            except Exception as stats_error:
                logger.warning(f"Failed to update provider statistics: {stats_error}")
                # Don't fail the test if statistics update fails
            
            return result
        except Exception as e:
            logger.error(f"Failed to test provider {provider_id}: {e}")
            return {
                "success": False,
                "message": "Connection test failed",
                "error_details": str(e)
            }
    
    async def _test_ai_provider(self, provider: APIProvider, api_key: str) -> Dict[str, Any]:
        """Test AI provider connection."""
        try:
            logger.info(f"Testing AI provider {provider.name} with URL: {provider.api_url}")
            logger.info(f"API key (first 10 chars): {api_key[:10]}...")

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Test connection with a simple chat completion request
            async with httpx.AsyncClient(timeout=30.0) as client:
                # For local API services, use chat/completions endpoint
                if "localhost" in provider.api_url or "127.0.0.1" in provider.api_url:
                    # Local API service - use chat completions with available model
                    response = await client.post(
                        provider.api_url,
                        headers=headers,
                        json={
                            "model": "Claude-4-Sonnet",
                            "messages": [{"role": "user", "content": "Hello"}],
                            "max_tokens": 10,
                            "temperature": 0.7
                        }
                    )
                elif "openai" in provider.name.lower():
                    # OpenAI API - try models endpoint first
                    try:
                        response = await client.get(
                            f"{provider.api_url.replace('/chat/completions', '')}/models",
                            headers=headers
                        )
                    except:
                        # Fallback to chat completions
                        response = await client.post(
                            provider.api_url,
                            headers=headers,
                            json={
                                "model": "gpt-3.5-turbo",
                                "messages": [{"role": "user", "content": "Hello"}],
                                "max_tokens": 10
                            }
                        )
                elif "anthropic" in provider.name.lower() or "claude" in provider.name.lower():
                    # Check if it's a local Claude-compatible API or official Anthropic API
                    if "/chat/completions" in provider.api_url:
                        # Local Claude-compatible API using OpenAI format
                        # Try to extract model name from display_name or use common names
                        model_name = "claude-sonnet-4-20250514"  # Default for this type of service
                        if hasattr(provider, 'display_name') and provider.display_name:
                            # Extract model name from display_name like "claude-sonnet-4 (claude-sonnet-4-20250514)"
                            import re
                            match = re.search(r'\((.*?)\)', provider.display_name)
                            if match:
                                model_name = match.group(1)

                        response = await client.post(
                            provider.api_url,
                            headers=headers,
                            json={
                                "model": model_name,
                                "messages": [{"role": "user", "content": "Hello"}],
                                "max_tokens": 10,
                                "temperature": 0.7
                            }
                        )
                    else:
                        # Official Anthropic Claude API - use messages endpoint
                        response = await client.post(
                            f"{provider.api_url.replace('/chat/completions', '')}/messages",
                            headers=headers,
                            json={
                                "model": "claude-3-haiku-20240307",
                                "max_tokens": 10,
                                "messages": [{"role": "user", "content": "Hello"}]
                            }
                        )
                else:
                    # Generic test - try chat completions
                    response = await client.post(
                        provider.api_url,
                        headers=headers,
                        json={
                            "model": "gpt-3.5-turbo",
                            "messages": [{"role": "user", "content": "Hello"}],
                            "max_tokens": 10
                        }
                    )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        model_list = []

                        # Handle different response formats
                        if "data" in data and isinstance(data["data"], list):
                            # OpenAI models list format
                            model_list = [model.get("id", "unknown") for model in data["data"]]
                        elif "choices" in data:
                            # Chat completion response - extract model from usage or response
                            model_list = [data.get("model", "unknown")]
                        elif "model" in data:
                            # Direct model response
                            model_list = [data["model"]]

                        return {
                            "success": True,
                            "message": "Connection successful",
                            "model_list": model_list[:10] if model_list else ["Available"]
                        }
                    except Exception as json_error:
                        # Response is 200 but not JSON - still consider it successful
                        return {
                            "success": True,
                            "message": "Connection successful (non-JSON response)",
                            "model_list": ["Available"]
                        }
                else:
                    error_text = response.text[:200] if response.text else "No error details"
                    return {
                        "success": False,
                        "message": f"HTTP {response.status_code}: {error_text}",
                        "error_details": response.text
                    }
        except Exception as e:
            return {
                "success": False,
                "message": "Connection failed",
                "error_details": str(e)
            }
    
    async def _test_detection_provider(self, provider: APIProvider, api_key: str) -> Dict[str, Any]:
        """Test detection provider connection."""
        # Placeholder for detection provider testing
        return {
            "success": True,
            "message": "Detection provider test not implemented yet"
        }
    
    async def _test_generic_provider(self, provider: APIProvider, api_key: str) -> Dict[str, Any]:
        """Test generic provider connection."""
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(provider.api_url, headers=headers)
                
                if response.status_code < 400:
                    return {
                        "success": True,
                        "message": "Connection successful"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"HTTP {response.status_code}",
                        "error_details": response.text
                    }
        except Exception as e:
            return {
                "success": False,
                "message": "Connection failed",
                "error_details": str(e)
            }
    
    # Model management methods
    async def get_provider_models(
        self, 
        provider_id: int, 
        enabled_only: bool = False
    ) -> List[APIModel]:
        """Get models for a specific provider."""
        try:
            query = self.db.query(APIModel).filter(
                APIModel.provider_id == provider_id
            )
            
            if enabled_only:
                query = query.filter(APIModel.is_enabled == True)
            
            return query.order_by(APIModel.display_name).all()
        except Exception as e:
            logger.error(f"Failed to get models for provider {provider_id}: {e}")
            raise
    
    async def create_model(self, model_data: Dict[str, Any]) -> APIModel:
        """Create a new API model."""
        try:
            # Verify provider exists
            provider = self.db.query(APIProvider).filter(
                APIProvider.id == model_data["provider_id"]
            ).first()
            
            if not provider:
                raise ValueError("Provider not found")
            
            # Create model
            model = APIModel(**model_data)
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)
            
            return model
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create model: {e}")
            raise
    
    async def update_model(
        self, 
        model_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[APIModel]:
        """Update an existing API model."""
        try:
            model = self.db.query(APIModel).filter(
                APIModel.id == model_id
            ).first()
            
            if not model:
                return None
            
            # Update model
            for key, value in update_data.items():
                setattr(model, key, value)
            
            self.db.commit()
            self.db.refresh(model)
            
            return model
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update model {model_id}: {e}")
            raise
    
    async def delete_model(self, model_id: int) -> bool:
        """Delete an API model."""
        try:
            model = self.db.query(APIModel).filter(
                APIModel.id == model_id
            ).first()
            
            if not model:
                return False
            
            self.db.delete(model)
            self.db.commit()
            
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete model {model_id}: {e}")
            raise
