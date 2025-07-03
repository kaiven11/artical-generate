#!/usr/bin/env python3
"""
增强版代理管理器
结合原有智能切换系统和新的精确控制功能
"""

import asyncio
import logging
import platform
import subprocess
import winreg
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class EnhancedClashAPI:
    """增强版Clash API管理器"""
    
    def __init__(self, controller_uri: str = "http://127.0.0.1:9090", secret: str = ""):
        self.base_url = controller_uri
        self.headers = {'Content-Type': 'application/json'}
        if secret:
            self.headers['Authorization'] = f'Bearer {secret}'
        self.logger = logging.getLogger(__name__)
    
    async def get_proxies(self) -> Optional[Dict]:
        """获取所有代理和策略组信息"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/proxies", headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('proxies', {})
                    else:
                        self.logger.error(f"❌ Clash API响应错误: HTTP {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"❌ 无法连接到Clash API: {e}")
            return None
    
    async def switch_proxy(self, selector_name: str, proxy_name: str) -> bool:
        """切换指定策略组的代理节点"""
        try:
            url = f"{self.base_url}/proxies/{selector_name}"
            payload = {"name": proxy_name}
            
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.put(url, headers=self.headers, json=payload) as response:
                    if response.status == 204:
                        self.logger.info(f"✅ 成功切换: {selector_name} -> {proxy_name}")
                        return True
                    else:
                        self.logger.error(f"❌ 切换失败: HTTP {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"❌ 切换代理失败: {e}")
            return False
    
    async def get_selector_groups(self) -> Dict[str, Dict]:
        """获取所有Selector策略组"""
        proxies = await self.get_proxies()
        if not proxies:
            return {}
        
        selectors = {}
        for name, data in proxies.items():
            if data.get('type') == 'Selector':
                selectors[name] = {
                    'name': name,
                    'current': data.get('now', ''),
                    'all': data.get('all', []),
                    'type': data.get('type', '')
                }
        
        return selectors
    
    async def get_available_nodes(self, selector_name: str) -> List[str]:
        """获取指定策略组的可用节点"""
        proxies = await self.get_proxies()
        if not proxies or selector_name not in proxies:
            return []
        
        return proxies[selector_name].get('all', [])

class CrossPlatformProxyManager:
    """跨平台系统代理管理器"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7890):
        self.host = host
        self.port = port
        self.os_type = platform.system()
        self.logger = logging.getLogger(__name__)
    
    async def set_system_proxy(self) -> bool:
        """开启系统代理"""
        self.logger.info(f"🌐 为 {self.os_type} 设置系统代理: {self.host}:{self.port}")
        
        try:
            if self.os_type == "Windows":
                return await self._set_windows_proxy()
            elif self.os_type == "Darwin":  # macOS
                return await self._set_macos_proxy()
            elif self.os_type == "Linux":
                return await self._set_linux_proxy()
            else:
                self.logger.error(f"❌ 不支持的操作系统: {self.os_type}")
                return False
        except Exception as e:
            self.logger.error(f"❌ 设置系统代理失败: {e}")
            return False
    
    async def unset_system_proxy(self) -> bool:
        """关闭系统代理"""
        self.logger.info(f"🌐 为 {self.os_type} 关闭系统代理")
        
        try:
            if self.os_type == "Windows":
                return await self._unset_windows_proxy()
            elif self.os_type == "Darwin":
                return await self._unset_macos_proxy()
            elif self.os_type == "Linux":
                return await self._unset_linux_proxy()
            else:
                self.logger.error(f"❌ 不支持的操作系统: {self.os_type}")
                return False
        except Exception as e:
            self.logger.error(f"❌ 关闭系统代理失败: {e}")
            return False
    
    async def _set_windows_proxy(self) -> bool:
        """设置Windows系统代理"""
        try:
            path = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, 'ProxyEnable', 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, 'ProxyServer', 0, winreg.REG_SZ, f'{self.host}:{self.port}')
            winreg.CloseKey(key)
            
            # 通知系统代理设置更改
            import ctypes
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Internet Settings")
            
            self.logger.info("✅ Windows系统代理设置成功")
            return True
        except Exception as e:
            self.logger.error(f"❌ Windows系统代理设置失败: {e}")
            return False
    
    async def _unset_windows_proxy(self) -> bool:
        """关闭Windows系统代理"""
        try:
            path = r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, 'ProxyEnable', 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            
            # 通知系统代理设置更改
            import ctypes
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Internet Settings")
            
            self.logger.info("✅ Windows系统代理关闭成功")
            return True
        except Exception as e:
            self.logger.error(f"❌ Windows系统代理关闭失败: {e}")
            return False
    
    async def _set_macos_proxy(self) -> bool:
        """设置macOS系统代理"""
        try:
            service = await self._get_active_mac_network_service()
            self.logger.info(f"🍎 使用网络服务: {service}")
            
            # 使用asyncio运行subprocess
            await asyncio.create_subprocess_exec(
                'networksetup', '-setwebproxy', service, self.host, str(self.port)
            )
            await asyncio.create_subprocess_exec(
                'networksetup', '-setsecurewebproxy', service, self.host, str(self.port)
            )
            
            self.logger.info("✅ macOS系统代理设置成功")
            return True
        except Exception as e:
            self.logger.error(f"❌ macOS系统代理设置失败: {e}")
            return False
    
    async def _unset_macos_proxy(self) -> bool:
        """关闭macOS系统代理"""
        try:
            service = await self._get_active_mac_network_service()
            
            await asyncio.create_subprocess_exec(
                'networksetup', '-setwebproxystate', service, 'off'
            )
            await asyncio.create_subprocess_exec(
                'networksetup', '-setsecurewebproxystate', service, 'off'
            )
            
            self.logger.info("✅ macOS系统代理关闭成功")
            return True
        except Exception as e:
            self.logger.error(f"❌ macOS系统代理关闭失败: {e}")
            return False
    
    async def _set_linux_proxy(self) -> bool:
        """设置Linux系统代理"""
        try:
            commands = [
                ['gsettings', 'set', 'org.gnome.system.proxy', 'mode', "'manual'"],
                ['gsettings', 'set', 'org.gnome.system.proxy.http', 'host', f"'{self.host}'"],
                ['gsettings', 'set', 'org.gnome.system.proxy.http', 'port', str(self.port)],
                ['gsettings', 'set', 'org.gnome.system.proxy.https', 'host', f"'{self.host}'"],
                ['gsettings', 'set', 'org.gnome.system.proxy.https', 'port', str(self.port)]
            ]
            
            for cmd in commands:
                await asyncio.create_subprocess_exec(*cmd)
            
            self.logger.info("✅ Linux系统代理设置成功")
            return True
        except Exception as e:
            self.logger.error(f"❌ Linux系统代理设置失败: {e}")
            return False
    
    async def _unset_linux_proxy(self) -> bool:
        """关闭Linux系统代理"""
        try:
            await asyncio.create_subprocess_exec(
                'gsettings', 'set', 'org.gnome.system.proxy', 'mode', "'none'"
            )
            self.logger.info("✅ Linux系统代理关闭成功")
            return True
        except Exception as e:
            self.logger.error(f"❌ Linux系统代理关闭失败: {e}")
            return False
    
    async def _get_active_mac_network_service(self) -> str:
        """获取macOS活动网络服务"""
        try:
            # 简化版本，返回常用的网络服务名
            return "Wi-Fi"
        except Exception:
            return "Wi-Fi"

class EnhancedProxyManager:
    """增强版代理管理器 - 结合智能切换和精确控制"""
    
    def __init__(self, clash_uri: str = "http://127.0.0.1:9090", clash_secret: str = ""):
        self.clash_api = EnhancedClashAPI(clash_uri, clash_secret)
        self.system_proxy = CrossPlatformProxyManager()
        self.logger = logging.getLogger(__name__)
        self.switch_history = []
        self.last_switch_time = None
    
    async def get_current_status(self) -> Dict:
        """获取当前代理状态"""
        selectors = await self.clash_api.get_selector_groups()
        
        status = {
            'clash_available': len(selectors) > 0,
            'selector_groups': selectors,
            'switch_count': len(self.switch_history),
            'last_switch': self.last_switch_time.isoformat() if self.last_switch_time else None
        }
        
        return status
    
    async def switch_to_specific_node(self, selector_name: str, node_name: str) -> bool:
        """切换到指定的代理节点"""
        self.logger.info(f"🎯 精确切换: {selector_name} -> {node_name}")
        
        # 获取当前IP
        ip_before = await self._get_current_ip()
        
        # 执行切换
        success = await self.clash_api.switch_proxy(selector_name, node_name)
        
        if success:
            # 等待切换生效
            await asyncio.sleep(3)
            
            # 获取切换后IP
            ip_after = await self._get_current_ip()
            
            # 记录切换历史
            self.switch_history.append({
                'timestamp': datetime.now(),
                'selector': selector_name,
                'node': node_name,
                'ip_before': ip_before,
                'ip_after': ip_after,
                'ip_changed': ip_before != ip_after if ip_before and ip_after else False
            })
            
            self.last_switch_time = datetime.now()
            
            self.logger.info(f"✅ 精确切换成功: {ip_before} -> {ip_after}")
            return True
        else:
            self.logger.error("❌ 精确切换失败")
            return False
    
    async def smart_switch_with_ip_change(self, selector_name: str = "PROXY", max_attempts: int = 5) -> bool:
        """智能切换 - 尝试找到不同IP的节点"""
        self.logger.info(f"🧠 智能切换: 寻找不同IP的节点")
        
        # 获取当前IP和节点
        current_ip = await self._get_current_ip()
        available_nodes = await self.clash_api.get_available_nodes(selector_name)
        
        if not available_nodes:
            self.logger.error(f"❌ 策略组 {selector_name} 没有可用节点")
            return False
        
        self.logger.info(f"🔍 当前IP: {current_ip}")
        self.logger.info(f"📋 可用节点: {len(available_nodes)} 个")
        
        # 尝试切换到不同的节点
        for attempt in range(min(max_attempts, len(available_nodes))):
            # 选择下一个节点
            node_index = attempt % len(available_nodes)
            target_node = available_nodes[node_index]
            
            self.logger.info(f"🔄 尝试 {attempt + 1}/{max_attempts}: {target_node}")
            
            # 切换节点
            if await self.clash_api.switch_proxy(selector_name, target_node):
                await asyncio.sleep(3)
                
                # 检查新IP
                new_ip = await self._get_current_ip()
                
                if new_ip and new_ip != current_ip:
                    self.logger.info(f"🎉 找到不同IP: {current_ip} -> {new_ip}")
                    
                    # 记录成功的切换
                    self.switch_history.append({
                        'timestamp': datetime.now(),
                        'selector': selector_name,
                        'node': target_node,
                        'ip_before': current_ip,
                        'ip_after': new_ip,
                        'ip_changed': True,
                        'attempts': attempt + 1
                    })
                    
                    self.last_switch_time = datetime.now()
                    return True
                else:
                    self.logger.warning(f"⚠️ IP未改变: {new_ip}")
            else:
                self.logger.warning(f"⚠️ 切换到 {target_node} 失败")
        
        self.logger.warning(f"⚠️ 经过 {max_attempts} 次尝试，未找到不同IP的节点")
        return False
    
    async def force_system_proxy_cycle(self) -> bool:
        """强制系统代理循环 - 禁用再启用"""
        self.logger.info("🔄 执行强制系统代理循环")
        
        # 获取切换前IP
        ip_before = await self._get_current_ip()
        
        # 禁用系统代理
        await self.system_proxy.unset_system_proxy()
        await asyncio.sleep(2)
        
        # 获取直连IP
        direct_ip = await self._get_current_ip()
        
        # 重新启用系统代理
        await self.system_proxy.set_system_proxy()
        await asyncio.sleep(3)
        
        # 获取恢复后IP
        ip_after = await self._get_current_ip()
        
        self.logger.info(f"🔄 代理循环: {ip_before} -> {direct_ip} -> {ip_after}")
        
        # 记录循环操作
        self.switch_history.append({
            'timestamp': datetime.now(),
            'type': 'system_proxy_cycle',
            'ip_before': ip_before,
            'direct_ip': direct_ip,
            'ip_after': ip_after,
            'effective': ip_before != ip_after if ip_before and ip_after else False
        })
        
        return ip_before != ip_after if ip_before and ip_after else False
    
    async def _get_current_ip(self) -> Optional[str]:
        """获取当前IP地址"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get("http://httpbin.org/ip") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('origin', '').split(',')[0].strip()
        except Exception as e:
            self.logger.debug(f"获取IP失败: {e}")
            return None
    
    def get_switch_statistics(self) -> Dict:
        """获取切换统计信息"""
        if not self.switch_history:
            return {'total_switches': 0, 'ip_changes': 0, 'success_rate': 0}
        
        ip_changes = len([h for h in self.switch_history if h.get('ip_changed', False)])
        success_rate = (ip_changes / len(self.switch_history)) * 100
        
        return {
            'total_switches': len(self.switch_history),
            'ip_changes': ip_changes,
            'success_rate': success_rate,
            'last_switch': self.last_switch_time.isoformat() if self.last_switch_time else None
        }


# 全局实例
_enhanced_proxy_manager = None

async def get_enhanced_proxy_manager() -> EnhancedProxyManager:
    """获取增强版代理管理器实例"""
    global _enhanced_proxy_manager
    if _enhanced_proxy_manager is None:
        _enhanced_proxy_manager = EnhancedProxyManager()
    return _enhanced_proxy_manager
