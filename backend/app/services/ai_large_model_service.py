# -*- coding: utf-8 -*-
"""
AI大模型调用服务使用可视化浏览器进行接口调用
"""

import asyncio
import logging
import os
import time
from typing import Any

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    DRISSION_AVAILABLE = True
except ImportError:
    DRISSION_AVAILABLE = False
    ChromiumPage = None
    ChromiumOptions = None


class AILargeModelService:
    """AI大模型服务."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def call_large_model(self, payload: Any) -> str:
        """
        使用可视化浏览器调用AI大模型接口
        
        Args:
            payload: 请求数据
        
        Returns:
            str: 模型返回的结果
        """
        if not DRISSION_AVAILABLE:
            raise RuntimeError("DrissionPage not installed. Please install: pip install DrissionPage")
        
        page = None
        try:
            # 创建浏览器配置
            options = self._create_browser_options()
            
            # 创建浏览器实例
            self.logger.info("🚀 启动Chrome浏览器进行AI大模型调用...")
            page = ChromiumPage(addr_or_opts=options)
            self.logger.info("✅ Chrome浏览器启动成功!")
            
            # 模拟访问大模型接口
            model_service_url = "https://example.com/ai-model"
            self.logger.info(f"🌐 正在访问模型服务: {model_service_url}")
            page.get(model_service_url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 模拟输入接口请求内容
            input_area = page.ele("textarea#input", timeout=5)
            if not input_area:
                raise Exception("❌ 未找到输入区域")
            input_area.clear()
            input_area.input(str(payload)[:5000])
            
            # 模拟点击提交按钮
            submit_button = page.ele("button#submit", timeout=5)
            if not submit_button:
                raise Exception("❌ 未找到提交按钮")
            submit_button.click()
            
            # 等待结果
            self.logger.info("⏳ 等待大模型返回结果...")
            time.sleep(5)
            
            # 获取结果区域文本
            result_area = page.ele("div#result", timeout=5)
            result_text = result_area.text.strip() if result_area else ""
            self.logger.info(f"🎯 获取结果: {result_text[:200]}...")
            
            return result_text
        except Exception as e:
            self.logger.error(f"💥 模型调用失败: {e}")
            raise
        finally:
            if page:
                try:
                    self.logger.info("🔒 关闭浏览器")
                    page.quit()
                except:
                    pass

    def _create_browser_options(self):
        """创建浏览器配置选项"""
        options = ChromiumOptions()
        
        # 指定Chrome浏览器路径
        chrome_path = r"C:\Users\asus\AppData\Local\Chromium\Application\chrome.exe"
        self.logger.info(f"🔧 使用Chrome路径: {chrome_path}")
        options.set_browser_path(chrome_path)
        
        # 用户数据目录
        current_dir = os.getcwd()
        user_data_dir = os.path.join(current_dir, "chro")
        os.makedirs(user_data_dir, exist_ok=True)
        self.logger.info(f"📁 用户数据目录: {user_data_dir}")
        options.set_user_data_path(user_data_dir)
        
        # 指纹参数
        options.set_argument("--fingerprint=1000")
        options.set_argument("--fingerprint-platform=windows")
        options.set_argument("--fingerprint-brand=Chrome")
        options.set_argument("--lang=zh-CN")
        options.set_argument("--timezone=Asia/Shanghai")
        
        # 反检测配置
        options.set_argument("--disable-blink-features=AutomationControlled")
        options.set_argument("--disable-dev-shm-usage")
        options.set_argument("--no-sandbox")
        options.set_argument("--disable-web-security")
        options.set_argument("--disable-features=VizDisplayCompositor")
        
        # 窗口配置 - 强制可视化模式
        options.set_argument("--window-size=1200,800")
        options.set_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # 禁用无头模式
        # options.set_argument("--headless")  # 注释掉确保不使用无头模式
        
        self.logger.info("🔧 浏览器配置: 可视化模式，1200x800窗口")
        return options


# Service instance
_ai_large_model_service = None

def get_ai_large_model_service() -> AILargeModelService:
    """Get AI large model service instance."""
    global _ai_large_model_service
    if _ai_large_model_service is None:
        _ai_large_model_service = AILargeModelService()
    return _ai_large_model_service

