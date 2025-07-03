"""
Platform manager for handling adapter registration and management.
"""

import logging
from typing import Dict, List, Optional, Type, Any
from datetime import datetime
import importlib
import inspect

from ..adapters.base import (
    BaseAdapter, BaseSourceAdapter, BaseAIAdapter, 
    BaseDetectionAdapter, BasePublishAdapter,
    AdapterInfo, PlatformInfo, AdapterType
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Plugin registry for managing adapter plugins."""
    
    def __init__(self):
        self.plugins: Dict[str, Dict[str, Any]] = {}
    
    async def install(self, plugin_path: str) -> bool:
        """Install a plugin from path."""
        try:
            # TODO: Implement plugin installation logic
            logger.info(f"Installing plugin from {plugin_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to install plugin: {e}")
            return False
    
    async def uninstall(self, plugin_name: str) -> bool:
        """Uninstall a plugin."""
        try:
            if plugin_name in self.plugins:
                del self.plugins[plugin_name]
                logger.info(f"Uninstalled plugin: {plugin_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to uninstall plugin: {e}")
            return False


class PlatformManager:
    """Platform manager for adapter registration and management."""
    
    def __init__(self):
        """Initialize platform manager."""
        self.adapters = {
            AdapterType.SOURCE: {},      # Source platform adapters
            AdapterType.AI: {},          # AI service adapters
            AdapterType.PUBLISH: {},     # Publishing platform adapters
            AdapterType.DETECTION: {}    # Detection service adapters
        }
        self.plugin_registry = PluginRegistry()
        self._adapter_configs: Dict[str, Dict[str, Any]] = {}
    
    async def register_adapter(self, adapter_type: AdapterType, name: str, 
                             adapter: BaseAdapter) -> bool:
        """
        Register a platform adapter.
        
        Args:
            adapter_type: Type of adapter
            name: Adapter name
            adapter: Adapter instance
            
        Returns:
            bool: True if registration successful
        """
        try:
            if adapter_type not in self.adapters:
                raise ValueError(f"Unknown adapter type: {adapter_type}")
            
            # Validate adapter interface
            if not self._validate_adapter(adapter_type, adapter):
                raise TypeError(f"Adapter must implement {adapter_type} interface")
            
            # Initialize adapter
            await adapter.initialize()
            
            # Register adapter
            self.adapters[adapter_type][name] = adapter
            
            # Save adapter configuration
            await self._save_adapter_config(adapter_type, name, adapter.get_config())
            
            logger.info(f"Registered {adapter_type} adapter: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register adapter {name}: {e}")
            return False
    
    async def unregister_adapter(self, adapter_type: AdapterType, name: str) -> bool:
        """
        Unregister a platform adapter.
        
        Args:
            adapter_type: Type of adapter
            name: Adapter name
            
        Returns:
            bool: True if unregistration successful
        """
        try:
            if adapter_type in self.adapters and name in self.adapters[adapter_type]:
                del self.adapters[adapter_type][name]
                logger.info(f"Unregistered {adapter_type} adapter: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister adapter {name}: {e}")
            return False
    
    async def get_adapter(self, adapter_type: AdapterType, name: str) -> Optional[BaseAdapter]:
        """
        Get a platform adapter.
        
        Args:
            adapter_type: Type of adapter
            name: Adapter name
            
        Returns:
            BaseAdapter: Adapter instance or None if not found
        """
        try:
            if adapter_type not in self.adapters:
                raise ValueError(f"Unknown adapter type: {adapter_type}")
            
            if name not in self.adapters[adapter_type]:
                # Try to dynamically load adapter
                await self._load_adapter(adapter_type, name)
            
            return self.adapters[adapter_type].get(name)
            
        except Exception as e:
            logger.error(f"Failed to get adapter {name}: {e}")
            return None
    
    async def list_adapters(self, adapter_type: Optional[AdapterType] = None) -> Dict[str, List[AdapterInfo]]:
        """
        List all adapters.
        
        Args:
            adapter_type: Optional adapter type filter
            
        Returns:
            Dict mapping adapter types to adapter info lists
        """
        try:
            if adapter_type:
                return {adapter_type.value: self._get_adapter_info(adapter_type)}
            
            return {
                adapter_type.value: self._get_adapter_info(adapter_type)
                for adapter_type in self.adapters.keys()
            }
            
        except Exception as e:
            logger.error(f"Failed to list adapters: {e}")
            return {}
    
    async def test_adapter(self, adapter_type: AdapterType, name: str) -> bool:
        """
        Test adapter connection.
        
        Args:
            adapter_type: Type of adapter
            name: Adapter name
            
        Returns:
            bool: True if connection test successful
        """
        try:
            adapter = await self.get_adapter(adapter_type, name)
            if adapter:
                return await adapter.test_connection()
            return False
        except Exception as e:
            logger.error(f"Failed to test adapter {name}: {e}")
            return False
    
    async def update_adapter_config(self, adapter_type: AdapterType, name: str, 
                                  config: Dict[str, Any]) -> bool:
        """
        Update adapter configuration.
        
        Args:
            adapter_type: Type of adapter
            name: Adapter name
            config: New configuration
            
        Returns:
            bool: True if update successful
        """
        try:
            adapter = await self.get_adapter(adapter_type, name)
            if adapter:
                adapter.update_config(config)
                await self._save_adapter_config(adapter_type, name, config)
                logger.info(f"Updated config for {adapter_type} adapter: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update adapter config {name}: {e}")
            return False
    
    async def install_plugin(self, plugin_path: str) -> bool:
        """
        Install a plugin.
        
        Args:
            plugin_path: Path to plugin
            
        Returns:
            bool: True if installation successful
        """
        return await self.plugin_registry.install(plugin_path)
    
    async def uninstall_plugin(self, plugin_name: str) -> bool:
        """
        Uninstall a plugin.
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            bool: True if uninstallation successful
        """
        return await self.plugin_registry.uninstall(plugin_name)
    
    def _validate_adapter(self, adapter_type: AdapterType, adapter: BaseAdapter) -> bool:
        """Validate adapter implements required interface."""
        base_classes = {
            AdapterType.SOURCE: BaseSourceAdapter,
            AdapterType.AI: BaseAIAdapter,
            AdapterType.DETECTION: BaseDetectionAdapter,
            AdapterType.PUBLISH: BasePublishAdapter
        }
        
        base_class = base_classes.get(adapter_type)
        if base_class:
            return isinstance(adapter, base_class)
        return isinstance(adapter, BaseAdapter)
    
    def _get_adapter_info(self, adapter_type: AdapterType) -> List[AdapterInfo]:
        """Get adapter information for given type."""
        adapter_infos = []
        
        for name, adapter in self.adapters[adapter_type].items():
            try:
                platform_info = adapter.get_platform_info()
                config = adapter.get_config()
                
                adapter_info = AdapterInfo(
                    name=name,
                    display_name=platform_info.display_name,
                    version=platform_info.version or "1.0.0",
                    is_enabled=True,  # TODO: Get from config
                    is_installed=True,
                    platform_info=platform_info,
                    config=config,
                    last_used=None  # TODO: Get from usage tracking
                )
                adapter_infos.append(adapter_info)
                
            except Exception as e:
                logger.error(f"Failed to get info for adapter {name}: {e}")
        
        return adapter_infos
    
    async def _load_adapter(self, adapter_type: AdapterType, name: str):
        """Dynamically load adapter."""
        try:
            # TODO: Implement dynamic adapter loading
            logger.info(f"Attempting to load {adapter_type} adapter: {name}")
        except Exception as e:
            logger.error(f"Failed to load adapter {name}: {e}")
    
    async def _save_adapter_config(self, adapter_type: AdapterType, name: str, 
                                 config: Dict[str, Any]):
        """Save adapter configuration."""
        try:
            key = f"{adapter_type.value}_{name}"
            self._adapter_configs[key] = config
            # TODO: Persist to database or file
            logger.debug(f"Saved config for {key}")
        except Exception as e:
            logger.error(f"Failed to save adapter config: {e}")


# Global platform manager instance
platform_manager = PlatformManager()


def get_platform_manager() -> PlatformManager:
    """Get platform manager instance."""
    return platform_manager
