#!/usr/bin/env python3
"""
智能代理切换器
结合Clash API控制和Windows系统代理管理
实现真正有效的IP地址切换
"""

import asyncio
import logging
import winreg
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import aiohttp

from .proxy_manager import get_proxy_manager
from .windows_proxy_manager import get_windows_proxy_manager, ProxyConfig

class SmartProxySwitcher:
    """智能代理切换器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.clash_manager = None
        self.windows_manager = None
        self.current_strategy = "clash"  # clash, windows, hybrid
        self.switch_count = 0
        self.last_switch_time = None
        self.ip_history = []  # 记录IP历史
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 初始化Clash管理器
        try:
            self.clash_manager = await get_proxy_manager()
            await self.clash_manager.__aenter__()
            self.logger.info("✅ Clash管理器初始化成功")
        except Exception as e:
            self.logger.warning(f"⚠️ Clash管理器初始化失败: {e}")
        
        # 初始化Windows管理器
        try:
            self.windows_manager = get_windows_proxy_manager()
            self.logger.info("✅ Windows管理器初始化成功")
        except Exception as e:
            self.logger.warning(f"⚠️ Windows管理器初始化失败: {e}")
        
        # 选择最佳策略
        await self._select_best_strategy()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.clash_manager:
            await self.clash_manager.__aexit__(exc_type, exc_val, exc_tb)
    
    async def _select_best_strategy(self):
        """选择最佳代理切换策略"""
        try:
            # 测试当前IP
            current_ip = await self._get_current_ip()
            self.logger.info(f"🔍 当前IP: {current_ip}")
            
            if current_ip:
                self.ip_history.append({
                    'ip': current_ip,
                    'timestamp': datetime.now(),
                    'method': 'initial'
                })
            
            # 检查Clash是否可用
            clash_available = self.clash_manager is not None
            
            # 检查Windows代理管理是否可用
            windows_available = self.windows_manager is not None
            
            if clash_available and windows_available:
                self.current_strategy = "hybrid"
                self.logger.info("🎯 选择混合策略：优先使用Clash API，必要时切换系统代理")
            elif clash_available:
                self.current_strategy = "clash"
                self.logger.info("🎯 选择Clash策略：使用Clash API控制")
            elif windows_available:
                self.current_strategy = "windows"
                self.logger.info("🎯 选择Windows策略：直接控制系统代理")
            else:
                self.logger.error("❌ 没有可用的代理管理方式")
                
        except Exception as e:
            self.logger.error(f"❌ 选择代理策略失败: {e}")
            self.current_strategy = "clash"  # 默认使用Clash
    
    async def _get_current_ip(self) -> Optional[str]:
        """获取当前IP地址"""
        try:
            timeout_config = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get("http://httpbin.org/ip") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('origin', '').split(',')[0].strip()
                        
        except Exception as e:
            self.logger.debug(f"获取当前IP失败: {e}")
            return None
    
    async def _test_ip_change_with_clash(self, max_attempts: int = 3) -> Tuple[bool, Optional[str]]:
        """测试Clash代理切换是否能改变IP"""
        if not self.clash_manager:
            return False, None
        
        try:
            # 获取当前IP
            current_ip = await self._get_current_ip()
            
            # 尝试Clash代理切换
            for attempt in range(max_attempts):
                self.logger.info(f"🔄 Clash切换尝试 {attempt + 1}/{max_attempts}")
                
                # 使用Clash智能切换
                new_proxy = await self.clash_manager.rotate_to_different_ip_proxy("GLOBAL", max_attempts=2)
                
                if new_proxy:
                    # 等待切换生效
                    await asyncio.sleep(3)
                    
                    # 检查新IP
                    new_ip = await self._get_current_ip()
                    
                    if new_ip and new_ip != current_ip:
                        self.logger.info(f"✅ Clash切换成功: {current_ip} -> {new_ip}")
                        return True, new_ip
                    else:
                        self.logger.warning(f"⚠️ Clash切换后IP未改变: {new_ip}")
                        current_ip = new_ip  # 更新当前IP用于下次比较
                else:
                    self.logger.warning(f"⚠️ Clash代理切换失败")
            
            return False, current_ip
            
        except Exception as e:
            self.logger.error(f"❌ 测试Clash IP切换失败: {e}")
            return False, None
    
    async def _force_system_proxy_change(self) -> Tuple[bool, Optional[str]]:
        """强制改变系统代理设置"""
        if not self.windows_manager:
            return False, None
        
        try:
            # 获取当前IP
            current_ip = await self._get_current_ip()
            
            # 临时禁用系统代理
            self.logger.info("🔄 临时禁用系统代理...")
            self.windows_manager.disable_system_proxy()
            await asyncio.sleep(2)
            
            # 获取直连IP
            direct_ip = await self._get_current_ip()
            self.logger.info(f"🌐 直连IP: {direct_ip}")
            
            # 重新启用系统代理
            self.logger.info("🔄 重新启用系统代理...")
            current_proxy_info = self.windows_manager.get_current_system_proxy()
            if current_proxy_info and current_proxy_info[0]:
                # 恢复原来的代理设置
                proxy_server = current_proxy_info[1]
                host, port = proxy_server.split(':')
                proxy_config = ProxyConfig("恢复代理", host, int(port), "http")
                self.windows_manager.set_system_proxy(proxy_config)
            
            await asyncio.sleep(3)
            
            # 获取恢复后的IP
            restored_ip = await self._get_current_ip()
            
            if direct_ip and restored_ip and direct_ip != restored_ip:
                self.logger.info(f"✅ 系统代理切换成功: {direct_ip} -> {restored_ip}")
                return True, restored_ip
            else:
                self.logger.warning("⚠️ 系统代理切换未产生IP变化")
                return False, restored_ip
                
        except Exception as e:
            self.logger.error(f"❌ 强制系统代理切换失败: {e}")
            return False, None
    
    async def smart_switch_proxy(self, max_attempts: int = 5) -> bool:
        """智能代理切换 - 核心方法"""
        self.logger.info("🧠 开始智能代理切换...")
        
        try:
            # 记录切换前状态
            initial_ip = await self._get_current_ip()
            self.logger.info(f"🔍 切换前IP: {initial_ip}")
            
            success = False
            final_ip = initial_ip
            
            # 策略1: 尝试Clash智能切换
            if self.current_strategy in ["clash", "hybrid"] and self.clash_manager:
                self.logger.info("1️⃣ 尝试Clash智能切换...")
                success, final_ip = await self._test_ip_change_with_clash(max_attempts=3)
                
                if success:
                    self.logger.info("✅ Clash智能切换成功")
                else:
                    self.logger.warning("⚠️ Clash智能切换未能改变IP")
            
            # 策略2: 如果Clash切换无效，尝试系统代理强制切换
            if not success and self.current_strategy in ["hybrid", "windows"] and self.windows_manager:
                self.logger.info("2️⃣ 尝试系统代理强制切换...")
                success, final_ip = await self._force_system_proxy_change()
                
                if success:
                    self.logger.info("✅ 系统代理强制切换成功")
                else:
                    self.logger.warning("⚠️ 系统代理强制切换未能改变IP")
            
            # 策略3: 如果仍然无效，尝试多次Clash轮换
            if not success and self.clash_manager:
                self.logger.info("3️⃣ 尝试多次Clash轮换...")
                for attempt in range(3):
                    new_proxy = await self.clash_manager.rotate_proxy("GLOBAL")
                    if new_proxy:
                        await asyncio.sleep(2)
                        current_ip = await self._get_current_ip()
                        if current_ip and current_ip != initial_ip:
                            success = True
                            final_ip = current_ip
                            self.logger.info(f"✅ 多次轮换成功: {initial_ip} -> {final_ip}")
                            break
            
            # 记录切换结果
            if success:
                self.switch_count += 1
                self.last_switch_time = datetime.now()
                
                self.ip_history.append({
                    'ip': final_ip,
                    'timestamp': datetime.now(),
                    'method': 'smart_switch',
                    'success': True
                })
                
                self.logger.info(f"🎉 智能代理切换成功: {initial_ip} -> {final_ip}")
                self.logger.info(f"📊 总切换次数: {self.switch_count}")
                
                return True
            else:
                self.logger.warning("⚠️ 智能代理切换未能改变IP地址")
                self.logger.info("💡 但代理切换仍可能有其他效果（会话隔离、时间延迟等）")
                
                # 即使IP未改变，也记录切换尝试
                self.switch_count += 1
                self.last_switch_time = datetime.now()
                
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 智能代理切换失败: {e}")
            return False
    
    def should_switch_proxy(self, failure_count: int = 0) -> bool:
        """判断是否应该切换代理"""
        # 验证码失败次数达到阈值
        if failure_count >= 2:
            return True
        
        # 距离上次切换时间过长
        if self.last_switch_time:
            time_since_last = datetime.now() - self.last_switch_time
            if time_since_last.total_seconds() > 1800:  # 30分钟
                return True
        
        return False
    
    def get_switch_stats(self) -> Dict:
        """获取切换统计信息"""
        unique_ips = set(record['ip'] for record in self.ip_history if record['ip'])
        
        return {
            'strategy': self.current_strategy,
            'total_switches': self.switch_count,
            'unique_ips': len(unique_ips),
            'ip_history_count': len(self.ip_history),
            'last_switch_time': self.last_switch_time.isoformat() if self.last_switch_time else None,
            'clash_available': self.clash_manager is not None,
            'windows_available': self.windows_manager is not None
        }
    
    def get_ip_history(self, limit: int = 10) -> List[Dict]:
        """获取IP历史记录"""
        return self.ip_history[-limit:] if self.ip_history else []


# 全局智能代理切换器实例
_smart_proxy_switcher = None

async def get_smart_proxy_switcher() -> SmartProxySwitcher:
    """获取智能代理切换器实例"""
    global _smart_proxy_switcher
    if _smart_proxy_switcher is None:
        _smart_proxy_switcher = SmartProxySwitcher()
    return _smart_proxy_switcher
