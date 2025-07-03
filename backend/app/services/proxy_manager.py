"""
代理管理服务
集成Clash API，实现自动代理切换功能，解决朱雀检测验证码失败问题
"""

import asyncio
import aiohttp
import logging
import random
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ProxyInfo:
    """代理信息"""
    name: str
    type: str  # http, socks5, etc.
    server: str
    port: int
    delay: Optional[int] = None
    alive: bool = True
    last_used: Optional[datetime] = None


@dataclass
class ProxyGroup:
    """代理组信息"""
    name: str
    type: str  # select, url-test, fallback, etc.
    now: str  # 当前选中的代理
    all: List[str]  # 所有可用代理


class ClashProxyManager:
    """Clash代理管理器"""
    
    def __init__(self, clash_api_url: str = "http://127.0.0.1:9090"):
        self.clash_api_url = clash_api_url.rstrip('/')
        self.logger = logging.getLogger(__name__)
        self.session = None
        self.current_proxy = None
        self.proxy_rotation_count = 0
        self.last_switch_time = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def get_proxies(self) -> Dict[str, ProxyInfo]:
        """获取所有代理信息"""
        try:
            url = f"{self.clash_api_url}/proxies"

            # 确保session已初始化
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=10)
                )

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    proxies = {}
                    
                    for name, proxy_data in data.get('proxies', {}).items():
                        # 跳过代理组，只获取实际代理节点
                        if proxy_data.get('type') in ['Selector', 'URLTest', 'Fallback', 'LoadBalance']:
                            continue
                            
                        proxies[name] = ProxyInfo(
                            name=name,
                            type=proxy_data.get('type', 'unknown'),
                            server=proxy_data.get('server', ''),
                            port=proxy_data.get('port', 0),
                            delay=proxy_data.get('history', [{}])[-1].get('delay') if proxy_data.get('history') else None,
                            alive=len(proxy_data.get('history', [])) > 0
                        )
                    
                    self.logger.info(f"📡 获取到 {len(proxies)} 个代理节点")
                    return proxies
                else:
                    self.logger.error(f"❌ 获取代理失败: HTTP {response.status}")
                    return {}
                    
        except Exception as e:
            self.logger.error(f"❌ 获取代理信息失败: {e}")
            return {}
    
    async def get_proxy_groups(self) -> Dict[str, ProxyGroup]:
        """获取代理组信息"""
        try:
            url = f"{self.clash_api_url}/proxies"

            # 确保session已初始化
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=10)
                )

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    groups = {}
                    
                    for name, group_data in data.get('proxies', {}).items():
                        # 只获取代理组
                        if group_data.get('type') in ['Selector', 'URLTest', 'Fallback', 'LoadBalance']:
                            groups[name] = ProxyGroup(
                                name=name,
                                type=group_data.get('type', 'unknown'),
                                now=group_data.get('now', ''),
                                all=group_data.get('all', [])
                            )
                    
                    self.logger.info(f"📊 获取到 {len(groups)} 个代理组")
                    return groups
                else:
                    self.logger.error(f"❌ 获取代理组失败: HTTP {response.status}")
                    return {}
                    
        except Exception as e:
            self.logger.error(f"❌ 获取代理组信息失败: {e}")
            return {}
    
    async def switch_proxy(self, group_name: str, proxy_name: str) -> bool:
        """切换指定代理组的代理"""
        try:
            url = f"{self.clash_api_url}/proxies/{group_name}"
            data = {"name": proxy_name}
            
            async with self.session.put(url, json=data) as response:
                if response.status == 204:
                    self.logger.info(f"✅ 成功切换代理: {group_name} -> {proxy_name}")
                    self.current_proxy = proxy_name
                    self.proxy_rotation_count += 1
                    self.last_switch_time = datetime.now()
                    return True
                else:
                    self.logger.error(f"❌ 切换代理失败: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ 切换代理失败: {e}")
            return False
    
    async def get_best_proxy(self, group_name: str = "GLOBAL") -> Optional[str]:
        """获取最佳代理（延迟最低且可用）"""
        try:
            groups = await self.get_proxy_groups()
            if group_name not in groups:
                self.logger.warning(f"⚠️ 代理组 {group_name} 不存在")
                return None
            
            group = groups[group_name]
            proxies = await self.get_proxies()
            
            # 过滤出该组中可用的代理，并按延迟排序
            available_proxies = []
            for proxy_name in group.all:
                if proxy_name in proxies and proxies[proxy_name].alive:
                    proxy = proxies[proxy_name]
                    if proxy.delay is not None:
                        available_proxies.append((proxy_name, proxy.delay))
            
            if not available_proxies:
                self.logger.warning(f"⚠️ 代理组 {group_name} 中没有可用代理")
                return None
            
            # 按延迟排序，选择最快的
            available_proxies.sort(key=lambda x: x[1])
            best_proxy = available_proxies[0][0]
            
            self.logger.info(f"🎯 最佳代理: {best_proxy} (延迟: {available_proxies[0][1]}ms)")
            return best_proxy
            
        except Exception as e:
            self.logger.error(f"❌ 获取最佳代理失败: {e}")
            return None
    
    async def rotate_proxy(self, group_name: str = "GLOBAL") -> Optional[str]:
        """轮换代理（选择下一个可用代理）"""
        try:
            groups = await self.get_proxy_groups()
            if group_name not in groups:
                self.logger.warning(f"⚠️ 代理组 {group_name} 不存在")
                return None

            group = groups[group_name]
            current_proxy = group.now

            # 获取可用代理列表
            proxies = await self.get_proxies()
            available_proxies = [
                name for name in group.all
                if name in proxies and proxies[name].alive
            ]

            if len(available_proxies) <= 1:
                self.logger.warning(f"⚠️ 代理组 {group_name} 中可用代理不足，无法轮换")
                return current_proxy

            # 找到当前代理的索引
            try:
                current_index = available_proxies.index(current_proxy)
                # 选择下一个代理
                next_index = (current_index + 1) % len(available_proxies)
                next_proxy = available_proxies[next_index]
            except ValueError:
                # 当前代理不在可用列表中，随机选择一个
                next_proxy = random.choice(available_proxies)

            # 切换到新代理
            if await self.switch_proxy(group_name, next_proxy):
                self.logger.info(f"🔄 代理轮换成功: {current_proxy} -> {next_proxy}")
                return next_proxy
            else:
                return None

        except Exception as e:
            self.logger.error(f"❌ 代理轮换失败: {e}")
            return None

    async def rotate_to_different_ip_proxy(self, group_name: str = "GLOBAL", max_attempts: int = 5) -> Optional[str]:
        """轮换到具有不同IP地址的代理"""
        try:
            import aiohttp

            # 获取当前IP
            current_ip = await self._get_current_proxy_ip()
            self.logger.info(f"🔍 当前代理IP: {current_ip}")

            groups = await self.get_proxy_groups()
            if group_name not in groups:
                self.logger.warning(f"⚠️ 代理组 {group_name} 不存在")
                return None

            group = groups[group_name]
            current_proxy = group.now

            # 获取可用代理列表，排除系统代理
            proxies = await self.get_proxies()
            available_proxies = [
                name for name in group.all
                if name in proxies and proxies[name].alive and
                name not in ['DIRECT', 'REJECT'] and
                not any(keyword in name.lower() for keyword in ['剩余', '距离', '套餐', '流量'])
            ]

            if len(available_proxies) <= 1:
                self.logger.warning(f"⚠️ 代理组 {group_name} 中可用代理不足")
                return current_proxy

            # 尝试多次切换，直到找到不同IP的代理
            for attempt in range(max_attempts):
                # 轮换到下一个代理
                next_proxy = await self.rotate_proxy(group_name)
                if not next_proxy or next_proxy == current_proxy:
                    continue

                # 等待代理切换生效
                await asyncio.sleep(2)

                # 检查新代理的IP
                new_ip = await self._get_current_proxy_ip()

                if new_ip and new_ip != current_ip:
                    self.logger.info(f"✅ 成功切换到不同IP: {current_ip} -> {new_ip}")
                    return next_proxy
                else:
                    self.logger.warning(f"⚠️ 第{attempt+1}次尝试，IP未改变: {new_ip}")
                    current_proxy = next_proxy

            self.logger.warning(f"⚠️ 经过{max_attempts}次尝试，未能找到不同IP的代理")
            return None

        except Exception as e:
            self.logger.error(f"❌ 切换到不同IP代理失败: {e}")
            return None

    async def _get_current_proxy_ip(self) -> Optional[str]:
        """获取当前代理的IP地址"""
        try:
            proxy_url = self.get_proxy_url()
            if not proxy_url:
                return None

            timeout_config = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get(
                    "http://httpbin.org/ip",
                    proxy=proxy_url
                ) as response:
                    if response.status == 200:
                        import json
                        data = await response.json()
                        return data.get('origin', '').split(',')[0].strip()

            return None

        except Exception as e:
            self.logger.debug(f"获取代理IP失败: {e}")
            return None
    
    async def test_proxy_connectivity(self, proxy_name: str) -> bool:
        """测试代理连通性"""
        try:
            # 这里可以实现具体的代理测试逻辑
            # 暂时返回True，实际应该测试代理是否可用
            self.logger.info(f"🔍 测试代理连通性: {proxy_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 测试代理连通性失败: {e}")
            return False
    
    def get_proxy_url(self, proxy_name: str = None) -> Optional[str]:
        """获取代理URL，用于配置浏览器"""
        if not proxy_name:
            proxy_name = self.current_proxy
            
        if not proxy_name:
            return None
        
        # 这里需要根据实际的代理配置返回代理URL
        # 格式通常为: http://host:port 或 socks5://host:port
        # 由于Clash的代理配置比较复杂，这里返回一个通用的本地代理地址
        return "http://127.0.0.1:7890"  # Clash默认HTTP代理端口
    
    def should_rotate_proxy(self, failure_count: int = 0) -> bool:
        """判断是否应该轮换代理"""
        # 如果检测失败次数超过阈值，或者距离上次切换时间过长
        if failure_count >= 3:
            return True
        
        if self.last_switch_time:
            time_since_last_switch = datetime.now() - self.last_switch_time
            if time_since_last_switch > timedelta(minutes=30):  # 30分钟自动轮换
                return True
        
        return False

    async def setup_load_balance_group(self, group_name: str = "🔄 自动轮换", strategy: str = "round-robin") -> bool:
        """设置负载均衡代理组（提供配置建议）"""
        try:
            # 获取所有可用的真实代理节点
            proxies = await self.get_proxies()

            # 过滤出真实代理节点
            real_proxies = []
            exclude_keywords = [
                "DIRECT", "REJECT", "剩余", "流量", "距离", "重置", "套餐", "到期",
                "GB", "MB", "天", "小时", "分钟", "秒"
            ]

            for proxy_name, proxy_info in proxies.items():
                # 检查是否要排除
                should_exclude = False
                for keyword in exclude_keywords:
                    if keyword in proxy_name:
                        should_exclude = True
                        break

                # 检查是否是真实代理节点
                if not should_exclude and proxy_info.alive:
                    if any(indicator in proxy_name for indicator in ["🇯🇵", "🇸🇬", "🇺🇸", "🇭🇰", "AWS", "服务器", "节点"]):
                        real_proxies.append(proxy_name)

            if len(real_proxies) < 2:
                self.logger.warning(f"⚠️ 可用代理节点不足，无法创建负载均衡组")
                return False

            self.logger.info(f"📋 发现 {len(real_proxies)} 个真实代理节点，准备创建负载均衡组")

            # 注意：Clash API 不支持动态创建代理组
            # 这个功能需要在配置文件中预先定义
            self.logger.info(f"💡 请在Clash配置文件中添加负载均衡组:")
            self.logger.info(f"   proxy-groups:")
            self.logger.info(f"     - name: \"{group_name}\"")
            self.logger.info(f"       type: load-balance")
            self.logger.info(f"       strategy: {strategy}")
            self.logger.info(f"       proxies:")
            for proxy in real_proxies[:10]:  # 只显示前10个
                self.logger.info(f"         - \"{proxy}\"")

            return True

        except Exception as e:
            self.logger.error(f"❌ 设置负载均衡组失败: {e}")
            return False

    async def switch_to_load_balance(self, group_name: str = "🔄 自动轮换") -> bool:
        """切换到负载均衡代理组"""
        try:
            # 检查负载均衡组是否存在
            groups = await self.get_proxy_groups()
            if group_name not in groups:
                self.logger.warning(f"⚠️ 负载均衡组 '{group_name}' 不存在")
                return False

            group = groups[group_name]
            if group.type.lower() != 'loadbalance':
                self.logger.warning(f"⚠️ 代理组 '{group_name}' 不是负载均衡类型")
                return False

            # 切换GLOBAL组到负载均衡组
            success = await self.switch_proxy("GLOBAL", group_name)
            if success:
                self.logger.info(f"✅ 已切换到负载均衡组: {group_name}")
                self.logger.info(f"🔄 现在每次请求将自动轮换代理节点")
                return True
            else:
                self.logger.error(f"❌ 切换到负载均衡组失败")
                return False

        except Exception as e:
            self.logger.error(f"❌ 切换到负载均衡组失败: {e}")
            return False

    async def check_load_balance_status(self) -> Dict[str, Any]:
        """检查负载均衡状态"""
        try:
            groups = await self.get_proxy_groups()

            # 查找负载均衡组
            load_balance_groups = []
            for name, group in groups.items():
                if group.type.lower() == 'loadbalance':
                    load_balance_groups.append({
                        'name': name,
                        'current': group.now,
                        'proxies': group.all,
                        'proxy_count': len(group.all)
                    })

            # 检查当前是否使用负载均衡
            current_using_lb = False
            current_lb_group = None

            if "GLOBAL" in groups:
                global_current = groups["GLOBAL"].now
                for lb_group in load_balance_groups:
                    if lb_group['name'] == global_current:
                        current_using_lb = True
                        current_lb_group = lb_group
                        break

            return {
                'load_balance_groups': load_balance_groups,
                'current_using_load_balance': current_using_lb,
                'current_lb_group': current_lb_group,
                'total_lb_groups': len(load_balance_groups)
            }

        except Exception as e:
            self.logger.error(f"❌ 检查负载均衡状态失败: {e}")
            return {
                'load_balance_groups': [],
                'current_using_load_balance': False,
                'current_lb_group': None,
                'total_lb_groups': 0
            }


# 全局代理管理器实例
_proxy_manager = None

class HybridProxyManager:
    """混合代理管理器 - 结合Clash和Windows系统代理"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.clash_manager = None
        self.windows_manager = None
        self.use_windows_proxy = False  # 是否使用Windows系统代理切换

    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 初始化Clash管理器
        self.clash_manager = ClashProxyManager()
        await self.clash_manager.__aenter__()

        # 初始化Windows管理器
        try:
            from .windows_proxy_manager import get_windows_proxy_manager
            self.windows_manager = get_windows_proxy_manager()

            # 从Clash加载代理配置到Windows管理器
            clash_proxies = await self.clash_manager.get_proxies()
            if clash_proxies:
                proxy_data = {}
                for name, proxy_info in clash_proxies.items():
                    proxy_data[name] = {
                        'type': proxy_info.type,
                        'server': proxy_info.server,
                        'port': proxy_info.port
                    }

                loaded_count = self.windows_manager.load_proxy_configs_from_clash(proxy_data)
                if loaded_count > 0:
                    self.use_windows_proxy = True
                    self.logger.info(f"✅ Windows代理管理器已启用，加载了 {loaded_count} 个代理")
                else:
                    self.logger.warning("⚠️ 未能从Clash加载代理配置，使用Clash模式")

        except Exception as e:
            self.logger.warning(f"⚠️ Windows代理管理器初始化失败: {e}")
            self.use_windows_proxy = False

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.clash_manager:
            await self.clash_manager.__aexit__(exc_type, exc_val, exc_tb)

    async def rotate_to_different_ip_proxy(self, group_name: str = "GLOBAL", max_attempts: int = 5) -> Optional[str]:
        """轮换到具有不同IP地址的代理"""
        if self.use_windows_proxy and self.windows_manager:
            self.logger.info("🔄 使用Windows系统代理切换...")
            success = await self.windows_manager.switch_to_different_ip_proxy(max_attempts)
            if success:
                current_proxy = self.windows_manager.current_proxy
                return current_proxy.name if current_proxy else "Windows-Proxy"
            else:
                self.logger.warning("⚠️ Windows代理切换失败，回退到Clash模式")
                return await self.clash_manager.rotate_to_different_ip_proxy(group_name, max_attempts)
        else:
            self.logger.info("🔄 使用Clash代理切换...")
            return await self.clash_manager.rotate_to_different_ip_proxy(group_name, max_attempts)

    async def rotate_proxy(self, group_name: str = "GLOBAL") -> Optional[str]:
        """轮换代理"""
        if self.use_windows_proxy and self.windows_manager:
            success = await self.windows_manager.rotate_proxy()
            if success:
                current_proxy = self.windows_manager.current_proxy
                return current_proxy.name if current_proxy else "Windows-Proxy"
            else:
                return await self.clash_manager.rotate_proxy(group_name)
        else:
            return await self.clash_manager.rotate_proxy(group_name)

    def should_rotate_proxy(self, failure_count: int = 0) -> bool:
        """判断是否应该轮换代理"""
        if self.clash_manager:
            return self.clash_manager.should_rotate_proxy(failure_count)
        return failure_count >= 2

    def get_proxy_url(self, proxy_name: str = None) -> Optional[str]:
        """获取代理URL"""
        if self.use_windows_proxy and self.windows_manager and self.windows_manager.current_proxy:
            return self.windows_manager.current_proxy.url
        elif self.clash_manager:
            return self.clash_manager.get_proxy_url(proxy_name)
        return None

    async def get_current_ip(self) -> Optional[str]:
        """获取当前IP地址"""
        if self.use_windows_proxy and self.windows_manager:
            return await self.windows_manager.get_current_ip()
        elif self.clash_manager:
            return await self.clash_manager._get_current_proxy_ip()
        return None

    def get_proxy_stats(self) -> Dict:
        """获取代理统计信息"""
        stats = {
            'mode': 'Windows' if self.use_windows_proxy else 'Clash',
            'clash_available': self.clash_manager is not None,
            'windows_available': self.windows_manager is not None
        }

        if self.use_windows_proxy and self.windows_manager:
            stats.update(self.windows_manager.get_proxy_stats())

        return stats


async def get_proxy_manager() -> HybridProxyManager:
    """获取混合代理管理器实例"""
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = HybridProxyManager()
    return _proxy_manager

async def check_system_proxy_status() -> bool:
    """检查系统代理是否已启用"""
    try:
        import winreg

        # 检查Windows系统代理设置
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as key:
            try:
                proxy_enable = winreg.QueryValueEx(key, "ProxyEnable")[0]
                if proxy_enable:
                    proxy_server = winreg.QueryValueEx(key, "ProxyServer")[0]
                    print(f"🌐 系统代理已启用: {proxy_server}")
                    return "127.0.0.1:7890" in proxy_server
                else:
                    print("⚠️ 系统代理未启用")
                    return False
            except FileNotFoundError:
                print("⚠️ 未找到代理设置")
                return False

    except Exception as e:
        print(f"❌ 检查系统代理状态失败: {e}")
        return False


# 全局代理管理器实例
_proxy_manager = None


async def get_proxy_manager() -> ClashProxyManager:
    """获取代理管理器实例"""
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ClashProxyManager()
    return _proxy_manager
