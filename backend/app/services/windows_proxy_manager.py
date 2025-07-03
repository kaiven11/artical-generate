#!/usr/bin/env python3
"""
Windows系统代理管理器
通过直接修改Windows注册表来控制系统代理设置
实现真正的IP地址切换
"""

import asyncio
import logging
import winreg
import subprocess
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import aiohttp

@dataclass
class ProxyConfig:
    """代理配置"""
    name: str
    host: str
    port: int
    type: str  # http, socks5
    username: Optional[str] = None
    password: Optional[str] = None
    
    @property
    def url(self) -> str:
        """获取代理URL"""
        if self.username and self.password:
            return f"{self.type}://{self.username}:{self.password}@{self.host}:{self.port}"
        else:
            return f"{self.type}://{self.host}:{self.port}"
    
    @property
    def server_string(self) -> str:
        """获取Windows代理服务器字符串"""
        return f"{self.host}:{self.port}"

class WindowsProxyManager:
    """Windows系统代理管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_proxy = None
        self.proxy_configs = []
        self.last_switch_time = None
        self.switch_count = 0
        
        # 注册表路径
        self.registry_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        
    def add_proxy_config(self, proxy_config: ProxyConfig):
        """添加代理配置"""
        self.proxy_configs.append(proxy_config)
        self.logger.info(f"➕ 添加代理配置: {proxy_config.name} ({proxy_config.host}:{proxy_config.port})")
    
    def load_proxy_configs_from_clash(self, clash_proxies: Dict) -> int:
        """从Clash代理配置中加载代理"""
        loaded_count = 0
        
        for name, proxy_data in clash_proxies.items():
            # 跳过代理组和系统代理
            if proxy_data.get('type') in ['Selector', 'URLTest', 'Fallback', 'LoadBalance']:
                continue
            if name in ['DIRECT', 'REJECT']:
                continue
                
            proxy_type = proxy_data.get('type', '').lower()
            server = proxy_data.get('server', '')
            port = proxy_data.get('port', 0)
            
            if not server or not port:
                continue
            
            # 转换代理类型
            if proxy_type in ['ss', 'shadowsocks']:
                # Shadowsocks通常通过本地客户端提供HTTP代理
                proxy_config = ProxyConfig(
                    name=name,
                    host='127.0.0.1',
                    port=7890,  # Clash默认HTTP端口
                    type='http'
                )
            elif proxy_type in ['http', 'https']:
                proxy_config = ProxyConfig(
                    name=name,
                    host=server,
                    port=port,
                    type='http',
                    username=proxy_data.get('username'),
                    password=proxy_data.get('password')
                )
            elif proxy_type in ['socks5', 'socks']:
                proxy_config = ProxyConfig(
                    name=name,
                    host=server,
                    port=port,
                    type='socks5',
                    username=proxy_data.get('username'),
                    password=proxy_data.get('password')
                )
            else:
                # 其他类型代理通过Clash本地端口
                proxy_config = ProxyConfig(
                    name=name,
                    host='127.0.0.1',
                    port=7890,
                    type='http'
                )
            
            self.add_proxy_config(proxy_config)
            loaded_count += 1
        
        self.logger.info(f"📋 从Clash加载了 {loaded_count} 个代理配置")
        return loaded_count
    
    def get_current_system_proxy(self) -> Optional[Tuple[bool, str]]:
        """获取当前系统代理设置"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path) as key:
                try:
                    proxy_enable = winreg.QueryValueEx(key, "ProxyEnable")[0]
                    if proxy_enable:
                        proxy_server = winreg.QueryValueEx(key, "ProxyServer")[0]
                        return True, proxy_server
                    else:
                        return False, ""
                except FileNotFoundError:
                    return False, ""
        except Exception as e:
            self.logger.error(f"❌ 获取系统代理设置失败: {e}")
            return None
    
    def set_system_proxy(self, proxy_config: Optional[ProxyConfig]) -> bool:
        """设置系统代理"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_WRITE) as key:
                if proxy_config:
                    # 启用代理
                    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                    winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_config.server_string)
                    
                    # 设置代理覆盖（绕过本地地址）
                    bypass_list = "localhost;127.*;10.*;172.16.*;172.17.*;172.18.*;172.19.*;172.20.*;172.21.*;172.22.*;172.23.*;172.24.*;172.25.*;172.26.*;172.27.*;172.28.*;172.29.*;172.30.*;172.31.*;192.168.*;<local>"
                    winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, bypass_list)
                    
                    self.logger.info(f"✅ 系统代理已设置: {proxy_config.server_string}")
                    self.current_proxy = proxy_config
                else:
                    # 禁用代理
                    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                    winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "")
                    
                    self.logger.info("✅ 系统代理已禁用")
                    self.current_proxy = None
                
                # 通知系统代理设置已更改
                self._notify_proxy_change()
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 设置系统代理失败: {e}")
            return False
    
    def _notify_proxy_change(self):
        """通知系统代理设置已更改"""
        try:
            # 使用Windows API通知系统设置更改
            import ctypes
            from ctypes import wintypes
            
            # 定义常量
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            
            # 通知系统Internet设置已更改
            ctypes.windll.user32.SendMessageW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "Internet Settings"
            )
            
            self.logger.debug("📢 已通知系统代理设置更改")
            
        except Exception as e:
            self.logger.debug(f"⚠️ 通知系统代理更改失败: {e}")
    
    async def test_proxy_ip(self, proxy_config: ProxyConfig, timeout: int = 10) -> Optional[str]:
        """测试代理的IP地址"""
        try:
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get(
                    "http://httpbin.org/ip",
                    proxy=proxy_config.url
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        ip = data.get('origin', '').split(',')[0].strip()
                        self.logger.info(f"🌐 代理 {proxy_config.name} IP: {ip}")
                        return ip
                    else:
                        self.logger.warning(f"⚠️ 代理 {proxy_config.name} 测试失败: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.warning(f"⚠️ 代理 {proxy_config.name} 连接失败: {e}")
            return None
    
    async def get_current_ip(self) -> Optional[str]:
        """获取当前系统的出口IP"""
        try:
            timeout_config = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get("http://httpbin.org/ip") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('origin', '').split(',')[0].strip()
                        
        except Exception as e:
            self.logger.error(f"❌ 获取当前IP失败: {e}")
            return None
    
    async def switch_to_different_ip_proxy(self, max_attempts: int = 5) -> bool:
        """切换到具有不同IP的代理"""
        if not self.proxy_configs:
            self.logger.error("❌ 没有可用的代理配置")
            return False
        
        # 获取当前IP
        current_ip = await self.get_current_ip()
        self.logger.info(f"🔍 当前IP: {current_ip}")
        
        # 尝试切换到不同IP的代理
        for attempt in range(max_attempts):
            # 选择下一个代理配置
            if self.current_proxy:
                try:
                    current_index = self.proxy_configs.index(self.current_proxy)
                    next_index = (current_index + 1) % len(self.proxy_configs)
                except ValueError:
                    next_index = 0
            else:
                next_index = 0
            
            next_proxy = self.proxy_configs[next_index]
            
            self.logger.info(f"🔄 尝试切换到代理: {next_proxy.name}")
            
            # 设置系统代理
            if self.set_system_proxy(next_proxy):
                # 等待代理生效
                await asyncio.sleep(3)
                
                # 测试新IP
                new_ip = await self.get_current_ip()
                
                if new_ip and new_ip != current_ip:
                    self.logger.info(f"✅ 成功切换到不同IP: {current_ip} -> {new_ip}")
                    self.last_switch_time = datetime.now()
                    self.switch_count += 1
                    return True
                else:
                    self.logger.warning(f"⚠️ 第{attempt+1}次尝试，IP未改变: {new_ip}")
            else:
                self.logger.error(f"❌ 设置代理失败: {next_proxy.name}")
        
        self.logger.warning(f"⚠️ 经过{max_attempts}次尝试，未能切换到不同IP")
        return False
    
    async def rotate_proxy(self) -> bool:
        """轮换到下一个代理"""
        if not self.proxy_configs:
            self.logger.error("❌ 没有可用的代理配置")
            return False
        
        # 选择下一个代理
        if self.current_proxy:
            try:
                current_index = self.proxy_configs.index(self.current_proxy)
                next_index = (current_index + 1) % len(self.proxy_configs)
            except ValueError:
                next_index = 0
        else:
            next_index = 0
        
        next_proxy = self.proxy_configs[next_index]
        
        self.logger.info(f"🔄 轮换到代理: {next_proxy.name}")
        
        if self.set_system_proxy(next_proxy):
            self.last_switch_time = datetime.now()
            self.switch_count += 1
            return True
        else:
            return False
    
    def disable_system_proxy(self) -> bool:
        """禁用系统代理"""
        return self.set_system_proxy(None)
    
    def get_proxy_stats(self) -> Dict:
        """获取代理统计信息"""
        return {
            'total_proxies': len(self.proxy_configs),
            'current_proxy': self.current_proxy.name if self.current_proxy else None,
            'switch_count': self.switch_count,
            'last_switch_time': self.last_switch_time.isoformat() if self.last_switch_time else None
        }


# 全局Windows代理管理器实例
_windows_proxy_manager = None

def get_windows_proxy_manager() -> WindowsProxyManager:
    """获取Windows代理管理器实例"""
    global _windows_proxy_manager
    if _windows_proxy_manager is None:
        _windows_proxy_manager = WindowsProxyManager()
    return _windows_proxy_manager
