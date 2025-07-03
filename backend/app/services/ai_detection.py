"""
AI detection service using Zhuque (朱雀) detection website.
"""

import asyncio
import logging
import re
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    DRISSION_AVAILABLE = True
except ImportError:
    DRISSION_AVAILABLE = False
    ChromiumPage = None
    ChromiumOptions = None

from ..core.performance_config import get_performance_config
from .proxy_manager import get_proxy_manager


@dataclass
class AIDetectionResult:
    """AI detection result."""
    ai_probability: float  # AI浓度百分比 (0-100)
    confidence: float = 0.8  # 检测置信度 (0-1)
    detector: str = "zhuque"  # 检测器名称
    status: str = "success"  # 检测状态
    is_passed: bool = False  # 是否通过检测 (AI浓度 < 25%)
    detection_details: Optional[Dict[str, Any]] = None
    detection_time: Optional[datetime] = None
    success: bool = True
    error: Optional[str] = None


class ZhuqueAIDetector:
    """朱雀AI检测服务."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.detection_url = "https://matrix.tencent.com/ai-detect/ai_gen_txt?utm_source=ai-bot.cn"
        self.threshold = 25.0  # AI浓度阈值

        # 使用性能配置
        self.perf_config = get_performance_config()
        ai_config = self.perf_config.get_ai_detection_config()

        self.timeout = ai_config["timeout"]  # 超时时间（秒）
        self.max_wait_time = ai_config["max_wait_time"]  # 最大等待时间
        self.check_interval = ai_config["check_interval"]  # 检查间隔

        self.current_fingerprint = 1000  # 当前指纹值
        self.current_profile_dir = "chro"  # 当前用户数据目录
        self.max_daily_detections = 20  # 每个指纹的最大检测次数
        self.detection_count = 0  # 当前指纹的检测次数

        # 代理管理
        self.proxy_manager = None
        self.current_proxy_url = None
        self.verification_failure_count = 0  # 验证码失败次数

    def _switch_fingerprint_and_profile(self):
        """当检测失败时，切换指纹和用户数据目录（指纹+1）"""

        # 保存旧配置
        old_fingerprint = self.current_fingerprint
        old_profile_dir = self.current_profile_dir

        # 指纹参数直接加1
        new_fingerprint = self.current_fingerprint + 1

        # 生成新的用户数据目录
        new_profile_dir = f"chro_{new_fingerprint}"

        self.current_fingerprint = new_fingerprint
        self.current_profile_dir = new_profile_dir
        self.detection_count = 0  # 重置检测次数

        self.logger.info("🔄 检测失败，正在切换指纹配置...")
        self.logger.info(f"🔧 指纹切换: {old_fingerprint} -> {new_fingerprint} (+1)")
        self.logger.info(f"📁 用户数据目录切换: {old_profile_dir} -> {new_profile_dir}")
        self.logger.info(f"🔢 检测次数重置: {self.detection_count}/{self.max_daily_detections}")

    def _check_daily_limit_exceeded(self, page_content: str) -> bool:
        """检查是否遇到了每日检测次数限制"""
        limit_indicators = [
            "今日次数已用完",
            "今日检测次数已达上限",
            "daily limit exceeded",
            "检测次数已用完",
            "次数用完"
        ]

        return any(indicator in page_content for indicator in limit_indicators)

    def _check_verification_failure(self, page_content: str) -> bool:
        """检查是否遇到验证码失败"""
        verification_indicators = [
            "验证码失败",
            "验证失败",
            "verification failed",
            "captcha failed",
            "请重新验证",
            "验证码错误",
            "人机验证失败"
        ]

        return any(indicator in page_content for indicator in verification_indicators)

    async def _init_proxy_manager(self):
        """初始化代理管理器"""
        if self.proxy_manager is None:
            try:
                self.proxy_manager = await get_proxy_manager()
                await self.proxy_manager.__aenter__()
                self.logger.info("🌐 代理管理器初始化成功")
            except Exception as e:
                self.logger.warning(f"⚠️ 代理管理器初始化失败: {e}")
                self.proxy_manager = None

    async def _init_smart_proxy_switcher(self):
        """初始化智能代理切换器"""
        if not hasattr(self, 'smart_proxy_switcher') or self.smart_proxy_switcher is None:
            try:
                from .smart_proxy_switcher import get_smart_proxy_switcher
                self.smart_proxy_switcher = await get_smart_proxy_switcher()
                await self.smart_proxy_switcher.__aenter__()
                self.logger.info("🧠 智能代理切换器初始化成功")
            except Exception as e:
                self.logger.warning(f"⚠️ 智能代理切换器初始化失败: {e}")
                self.smart_proxy_switcher = None

    async def _switch_proxy_if_needed(self) -> bool:
        """根据需要切换代理"""
        try:
            # 优先使用智能代理切换器
            await self._init_smart_proxy_switcher()

            if self.smart_proxy_switcher and self.smart_proxy_switcher.should_switch_proxy(self.verification_failure_count):
                self.logger.info("🧠 使用智能代理切换器...")

                # 执行智能代理切换
                switch_success = await self.smart_proxy_switcher.smart_switch_proxy(max_attempts=5)

                if switch_success:
                    self.verification_failure_count = 0  # 重置失败计数
                    self.logger.info("✅ 智能代理切换成功")

                    # 获取切换统计信息
                    stats = self.smart_proxy_switcher.get_switch_stats()
                    self.logger.info(f"📊 切换统计: 策略={stats['strategy']}, 总次数={stats['total_switches']}, 唯一IP={stats['unique_ips']}")

                    return True
                else:
                    self.logger.warning("⚠️ 智能代理切换未能改变IP，但仍可能有效果")
                    self.verification_failure_count = 0  # 重置失败计数
                    return True

            # 回退到传统代理管理器
            await self._init_proxy_manager()

            if not self.proxy_manager:
                self.logger.warning("⚠️ 代理管理器不可用，无法切换代理")
                return False

            # 检查是否需要切换代理
            if self.proxy_manager.should_rotate_proxy(self.verification_failure_count):
                self.logger.info("🔄 使用传统代理切换...")

                # 使用智能代理切换，确保IP地址不同
                new_proxy = await self.proxy_manager.rotate_to_different_ip_proxy("GLOBAL", max_attempts=3)
                if new_proxy:
                    self.current_proxy_url = self.proxy_manager.get_proxy_url(new_proxy)
                    self.verification_failure_count = 0  # 重置失败计数
                    self.logger.info(f"✅ 传统代理切换成功: {new_proxy}")
                    self.logger.info(f"🌐 新代理URL: {self.current_proxy_url}")
                    return True
                else:
                    self.logger.warning("⚠️ 传统代理切换失败，尝试普通轮换...")
                    # 如果智能切换失败，尝试普通轮换
                    fallback_proxy = await self.proxy_manager.rotate_proxy("GLOBAL")
                    if fallback_proxy:
                        self.current_proxy_url = self.proxy_manager.get_proxy_url(fallback_proxy)
                        self.verification_failure_count = 0
                        self.logger.info(f"✅ 普通代理切换成功: {fallback_proxy}")
                        return True
                    else:
                        self.logger.error("❌ 所有代理切换方式都失败")
                        return False

            return True

        except Exception as e:
            self.logger.error(f"❌ 代理切换过程中出现错误: {e}")
            return False

    async def detect_ai_content(self, content: str) -> AIDetectionResult:
        """
        检测文本内容的AI浓度.

        Args:
            content: 要检测的文本内容

        Returns:
            AIDetectionResult: 检测结果
        """
        self.logger.info("Starting AI content detection using Zhuque service")

        max_retries = 3  # 最大重试次数（用于切换指纹）

        for retry_count in range(max_retries):
            try:
                # 初始化代理管理器（如果需要）
                await self._init_proxy_manager()

                # 检查是否需要切换代理
                await self._switch_proxy_if_needed()

                # 使用DrissionPage进行网页自动化操作
                result = await self._detect_with_drissionpage(content)

                # 如果检测成功，增加计数并重置失败计数
                if result.success:
                    self.detection_count += 1
                    self.verification_failure_count = 0  # 重置验证失败计数
                    self.logger.info(f"📊 当前指纹检测次数: {self.detection_count}/{self.max_daily_detections}")

                return result

            except Exception as e:
                error_msg = str(e)

                # 检查是否是次数限制错误
                if any(indicator in error_msg for indicator in ["今日次数已用完", "检测次数已用完", "daily limit"]):
                    self.logger.warning(f"⚠️ 检测失败: {error_msg}")
                    if retry_count < max_retries - 1:
                        self.logger.info("🔄 正在切换指纹并重试...")
                        self._switch_fingerprint_and_profile()
                        continue

                # 检查是否是验证码失败错误
                elif any(indicator in error_msg for indicator in ["验证码失败", "验证失败", "已切换代理"]):
                    self.logger.warning(f"⚠️ 验证码失败: {error_msg}")
                    if retry_count < max_retries - 1:
                        self.logger.info("🔄 代理已切换，重试检测...")
                        continue

                # 其他检测失败
                elif "检测失败" in error_msg:
                    self.logger.warning(f"⚠️ 检测失败: {error_msg}")
                    if retry_count < max_retries - 1:
                        self.logger.info("🔄 正在切换指纹并重试...")
                        self._switch_fingerprint_and_profile()
                        continue

                self.logger.error(f"AI detection failed (attempt {retry_count + 1}/{max_retries}): {e}")

                # 如果不是最后一次重试，也尝试切换指纹
                if retry_count < max_retries - 1:
                    self.logger.info("🔄 尝试切换指纹重试...")
                    self._switch_fingerprint_and_profile()
                    continue

                # 如果是最后一次重试，返回失败结果
                return AIDetectionResult(
                    ai_probability=100.0,  # 检测失败时假设为100%AI内容
                    is_passed=False,
                    detection_details={"error": str(e)},
                    detection_time=datetime.now(),
                    success=False,
                    error=str(e)
                )
    
    async def _detect_with_drissionpage(self, content: str) -> AIDetectionResult:
        """使用DrissionPage进行AI检测."""
        if not DRISSION_AVAILABLE:
            raise RuntimeError("DrissionPage not installed. Please install: pip install DrissionPage")

        page = None
        try:
            import os
            import tempfile

            # 使用当前的指纹和用户数据目录
            fingerprint = self.current_fingerprint
            current_dir = os.getcwd()
            user_data_dir = os.path.join(current_dir, self.current_profile_dir)

            # 确保目录存在
            try:
                os.makedirs(user_data_dir, exist_ok=True)
                self.logger.info(f"🔧 创建用户数据目录: {user_data_dir}")
            except Exception as e:
                self.logger.warning(f"无法创建用户数据目录: {e}")
                # 如果创建失败，使用临时目录
                user_data_dir = os.path.join(tempfile.gettempdir(), f"chrome_profile_{fingerprint}")
                os.makedirs(user_data_dir, exist_ok=True)

            # 配置ChromiumOptions
            options = ChromiumOptions()

            # 指定Chrome浏览器路径（指纹浏览器）
            chrome_path = r"C:\Users\asus\AppData\Local\Chromium\Application\chrome.exe"
            self.logger.info(f"🔧 使用指纹浏览器路径: {chrome_path}")
            options.set_browser_path(chrome_path)

            # 设置用户数据目录
            self.logger.info(f"🔧 使用user-data-dir: {user_data_dir}")
            options.set_user_data_path(user_data_dir)

            # 设置指纹参数（使用动态指纹值）
            options.set_argument(f"--fingerprint={fingerprint}")
            options.set_argument("--fingerprint-platform=windows")
            options.set_argument("--fingerprint-brand=Chrome")
            options.set_argument("--lang=zh-CN")
            options.set_argument("--timezone=Asia/Shanghai")

            # 配置代理（如果可用）
            if self.current_proxy_url:
                options.set_argument(f"--proxy-server={self.current_proxy_url}")
                self.logger.info(f"🌐 使用代理: {self.current_proxy_url}")
            else:
                self.logger.info("🌐 未配置代理，使用直连")

            # 反检测配置
            options.set_argument("--disable-blink-features=AutomationControlled")
            options.set_argument("--disable-dev-shm-usage")
            options.set_argument("--no-sandbox")
            options.set_argument("--disable-web-security")
            options.set_argument("--disable-features=VizDisplayCompositor")
            options.set_argument("--disable-extensions")
            options.set_argument("--disable-plugins")
            options.set_argument("--disable-default-apps")
            options.set_argument("--disable-sync")

            # 窗口配置 - 强制可视化模式，确保用户能看到朱雀检测过程
            options.set_argument("--window-size=1400,900")    # 更大的窗口
            options.set_argument("--window-position=100,100") # 设置窗口位置，与内容提取器错开
            options.set_argument("--start-maximized")         # 启动时最大化
            options.set_argument("--disable-web-security")    # 禁用web安全限制
            options.set_argument("--disable-features=VizDisplayCompositor")
            options.set_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

            # 强制禁用无头模式 - 确保朱雀检测过程可见
            # 绝对不使用无头模式
            options.set_argument("--disable-headless")
            options.set_argument("--no-headless")

            # 确保窗口在前台显示
            options.set_argument("--force-device-scale-factor=1")
            options.set_argument("--high-dpi-support=1")
            
            # 显示配置的参数
            self.logger.info(f"🔧 浏览器配置:")
            self.logger.info(f"   - Chrome路径: {chrome_path}")
            self.logger.info(f"   - 指纹参数: --fingerprint={fingerprint}")
            self.logger.info(f"   - 用户数据目录: {user_data_dir}")
            self.logger.info(f"   - 检测次数: {self.detection_count}/{self.max_daily_detections}")
            self.logger.info(f"   - 窗口模式: 可视化（非无头模式）")
            self.logger.info(f"   - 窗口大小: 1200x800")

            # 创建ChromiumPage实例
            self.logger.info("🚀 正在启动Chrome浏览器...")
            self.logger.info("📺 朱雀检测浏览器将以可视化模式运行，您可以看到整个检测过程")
            self.logger.info("🔥 朱雀检测浏览器窗口即将弹出，请注意观察！")

            page = ChromiumPage(addr_or_opts=options)

            # 确保窗口激活并置于前台
            try:
                page.set.window.max()  # 最大化窗口
                page.set.window.to_front()  # 置于前台
            except:
                pass

            self.logger.info("✅ Chrome浏览器启动成功!")
            self.logger.info("🔍 浏览器窗口已打开，正在访问朱雀检测网站...")
            self.logger.info("👁️ 请查看弹出的朱雀检测浏览器窗口！")

            # 执行反检测脚本
            page.run_js("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # 给用户时间观察浏览器窗口 - 使用性能配置
            ai_config = self.perf_config.get_ai_detection_config()
            startup_wait = ai_config["browser_startup_wait"]
            self.logger.info(f"⏳ 等待{startup_wait}秒，让您观察朱雀检测浏览器窗口...")
            import time
            time.sleep(startup_wait)

            # 导航到检测页面
            self.logger.info(f"🌐 正在访问朱雀检测页面: {self.detection_url}")
            self.logger.info("👀 请观察浏览器窗口中朱雀检测页面的加载过程...")
            page.get(self.detection_url)

            # 等待页面完全加载，给用户时间观察 - 使用性能配置
            page_load_wait = ai_config["page_load_wait"]
            self.logger.info("⏳ 等待朱雀检测页面加载完成...")
            page.wait.load_start()
            time.sleep(page_load_wait)

            # 调试：打印页面信息
            self.logger.info(f"🔍 页面标题: {page.title}")
            self.logger.info(f"🔍 当前URL: {page.url}")

            # 查找所有textarea元素进行调试
            self.logger.info("🔍 查找页面上的所有textarea元素...")
            all_textareas = page.eles('tag:textarea')
            self.logger.info(f"🔍 找到 {len(all_textareas)} 个textarea元素")

            for i, ta in enumerate(all_textareas):
                try:
                    placeholder = ta.attr('placeholder') or ''
                    id_attr = ta.attr('id') or ''
                    class_attr = ta.attr('class') or ''
                    self.logger.info(f"🔍 textarea {i+1}: id='{id_attr}', class='{class_attr}', placeholder='{placeholder}'")
                except Exception as e:
                    self.logger.info(f"🔍 textarea {i+1}: 无法获取属性 - {e}")

            # 查找文本输入区域 - 使用更简单的选择器
            text_area_selectors = [
                'textarea',  # 最简单的选择器
                'tag:textarea',  # DrissionPage语法
            ]

            text_area = None
            for selector in text_area_selectors:
                try:
                    self.logger.info(f"🔍 尝试选择器: {selector}")
                    text_area = page.ele(selector, timeout=ai_config["element_find_timeout"])
                    if text_area:
                        self.logger.info(f"✅ 找到文本输入区域，使用选择器: {selector}")
                        break
                except Exception as e:
                    self.logger.info(f"❌ 选择器 '{selector}' 失败: {e}")
                    continue

            if not text_area:
                self.logger.error("❌ 未找到文本输入区域")
                # 尝试获取页面源码进行调试
                try:
                    page_source = page.html
                    if 'textarea' in page_source.lower():
                        self.logger.info("🔍 页面源码中包含textarea标签")
                    else:
                        self.logger.info("🔍 页面源码中不包含textarea标签")
                except:
                    pass

                return AIDetectionResult(
                    ai_probability=0.0,
                    is_passed=False,
                    detection_details={"error": "未找到文本输入区域"},
                    detection_time=datetime.now(),
                    success=False,
                    error="未找到文本输入区域"
                )

            # 输入要检测的内容
            self.logger.info("📝 正在输入检测内容...")
            text_area.clear()
            time.sleep(ai_config["input_wait"])

            # 验证内容不为空
            if not content or len(content.strip()) == 0:
                self.logger.error("❌ 检测内容为空，无法进行检测")
                raise Exception("检测内容为空，无法进行检测")

            # 确保内容长度符合要求（大于350字）
            if len(content) < 350:
                # 如果内容太短，重复内容直到达到最小长度
                repeat_times = (350 // len(content)) + 1
                test_content = (content + " ") * repeat_times
                test_content = test_content[:2000]  # 限制最大长度
                self.logger.info(f"📝 原内容太短({len(content)}字符)，已重复扩展")
            else:
                test_content = content[:2000]  # 限制到2000字符

            self.logger.info(f"📝 输入内容长度: {len(test_content)} 字符")
            self.logger.info(f"📝 输入内容预览: {test_content[:100]}...")
            self.logger.info("👀 请观察浏览器中文本内容的输入过程...")

            text_area.input(test_content)

            # 等待一下让内容输入完成，给用户时间观察 - 使用性能配置
            text_input_wait = ai_config["text_input_wait"]
            self.logger.info("⏳ 等待文本输入完成...")
            import time
            time.sleep(text_input_wait)

            # 调试：打印页面信息
            self.logger.info(f"🔍 页面标题: {page.title}")
            self.logger.info(f"🔍 当前URL: {page.url}")

            # 调试：查找页面上所有的按钮
            all_buttons = page.eles('tag:button')
            self.logger.info(f"🔍 页面上找到 {len(all_buttons)} 个按钮")
            for i, button in enumerate(all_buttons):
                try:
                    button_text = button.text.strip()
                    button_type = button.attr("type")
                    button_class = button.attr("class")
                    self.logger.info(f"🔍 按钮 {i+1}: 文本='{button_text}', 类型='{button_type}', 类名='{button_class}'")
                except Exception as e:
                    self.logger.info(f"🔍 按钮 {i+1}: 无法获取属性 - {e}")

            # 查找并点击检测按钮
            self.logger.info("🔍 查找检测按钮...")

            # 查找包含"立即检测"文本的按钮
            button_texts = ["立即检测", "检测", "开始检测", "提交", "开始", "分析", "识别"]

            detect_button = None

            # 先尝试精确匹配"立即检测"
            for text in button_texts:
                try:
                    self.logger.info(f"🔍 尝试查找包含文本 '{text}' 的按钮...")

                    # 使用DrissionPage的文本匹配
                    buttons_with_text = page.eles(f'tag:button@text():{text}')
                    if buttons_with_text:
                        detect_button = buttons_with_text[0]
                        self.logger.info(f"✅ 找到检测按钮，使用文本匹配: '{text}'")
                        break

                    # 尝试部分匹配
                    all_buttons = page.eles('tag:button')
                    for button in all_buttons:
                        try:
                            button_text = button.text.strip()
                            if text in button_text:
                                detect_button = button
                                self.logger.info(f"✅ 找到检测按钮，部分匹配: '{button_text}' 包含 '{text}'")
                                break
                        except:
                            continue

                    if detect_button:
                        break

                except Exception as e:
                    self.logger.debug(f"❌ 文本匹配 '{text}' 失败: {e}")
                    continue

            # 如果还没找到，尝试CSS选择器
            if not detect_button:
                button_selectors = [
                    'button[type="submit"]',
                    '.detect-button',
                    '.submit-button',
                    '.btn-primary',
                    '.btn-submit',
                    '.btn-detect'
                ]

                for selector in button_selectors:
                    try:
                        self.logger.info(f"🔍 尝试CSS选择器: {selector}")
                        detect_button = page.ele(selector, timeout=ai_config["button_find_timeout"])
                        if detect_button:
                            self.logger.info(f"✅ 找到检测按钮，使用选择器: {selector}")
                            break
                    except Exception as e:
                        self.logger.debug(f"❌ 选择器 '{selector}' 失败: {e}")
                        continue

            if not detect_button:
                self.logger.error("❌ 无法找到检测按钮")

                # 尝试查找其他可能的元素
                self.logger.info("🔍 尝试查找其他可能的提交元素...")

                # 查找所有可能的提交元素
                possible_elements = []

                # 查找所有div元素（可能是自定义按钮）
                try:
                    divs = page.eles('tag:div')
                    for div in divs:
                        text = div.text.strip()
                        if any(keyword in text for keyword in ["检测", "提交", "开始", "分析", "识别"]):
                            possible_elements.append(("div", text, div.attr("class")))
                except:
                    pass

                # 查找所有span元素
                try:
                    spans = page.eles('tag:span')
                    for span in spans:
                        text = span.text.strip()
                        if any(keyword in text for keyword in ["检测", "提交", "开始", "分析", "识别"]):
                            possible_elements.append(("span", text, span.attr("class")))
                except:
                    pass

                # 查找所有a元素
                try:
                    links = page.eles('tag:a')
                    for link in links:
                        text = link.text.strip()
                        if any(keyword in text for keyword in ["检测", "提交", "开始", "分析", "识别"]):
                            possible_elements.append(("a", text, link.attr("class")))
                except:
                    pass

                if possible_elements:
                    self.logger.info(f"🔍 找到 {len(possible_elements)} 个可能的提交元素:")
                    for elem_type, text, class_name in possible_elements:
                        self.logger.info(f"   {elem_type}: '{text}' (class: {class_name})")
                else:
                    self.logger.info("🔍 没有找到任何包含检测关键词的元素")

                # 尝试通过JavaScript触发检测
                self.logger.info("🔍 尝试通过JavaScript触发检测...")
                try:
                    # 尝试执行可能的JavaScript函数
                    js_commands = [
                        "document.querySelector('button[type=\"submit\"]')?.click()",
                        "document.querySelector('.el-button--primary')?.click()",
                        "document.querySelector('[class*=\"detect\"]')?.click()",
                        "document.querySelector('[class*=\"submit\"]')?.click()",
                    ]

                    for js_cmd in js_commands:
                        try:
                            page.run_js(js_cmd)
                            self.logger.info(f"✅ 执行JavaScript: {js_cmd}")
                            time.sleep(ai_config["js_execution_wait"])
                        except Exception as e:
                            self.logger.debug(f"JavaScript执行失败: {js_cmd} - {e}")
                            continue
                except Exception as e:
                    self.logger.info(f"🔍 JavaScript执行失败: {e}")
            else:
                # 点击检测按钮
                try:
                    self.logger.info("🔄 点击检测按钮...")
                    self.logger.info("👀 请观察浏览器中检测按钮的点击过程...")
                    detect_button.click()
                    time.sleep(ai_config["click_wait"])
                    self.logger.info("✅ 成功点击检测按钮")
                except Exception as e:
                    self.logger.error(f"❌ 点击检测按钮失败: {e}")

            # 等待检测完成 - 使用性能配置的智能轮询检查
            self.logger.info("⏳ 等待朱雀AI检测完成...")
            self.logger.info("👀 请观察浏览器中检测进度和结果的显示过程...")

            # 先等待5秒让朱雀检测有足够时间启动
            self.logger.info("⏳ 等待5秒让朱雀检测启动...")
            time.sleep(5)

            # 使用性能配置的轮询方式检查结果
            max_wait_time = ai_config["max_wait_time"]
            check_interval = ai_config["check_interval"]
            waited_time = 5  # 已经等待了5秒

            while waited_time < max_wait_time:
                time.sleep(check_interval)
                waited_time += check_interval

                # 检查是否有结果出现
                percentage_elements = page.eles('xpath://*[contains(text(), "%")]')
                if percentage_elements:
                    # 找到结果，提前退出
                    self.logger.info(f"✅ 检测完成，用时 {waited_time} 秒")
                    break

                if waited_time % 3 == 0:  # 每3秒输出一次进度
                    self.logger.info(f"⏳ 已等待 {waited_time}/{max_wait_time} 秒...")

            if waited_time >= max_wait_time:
                self.logger.info(f"⏰ 达到最大等待时间 {max_wait_time} 秒")

            # 检查是否有检测结果出现
            self.logger.info("🔍 开始查找检测结果...")

            # 检查页面状态
            page_content = page.html

            # 检查每日限制
            if self._check_daily_limit_exceeded(page_content):
                self.logger.warning("⚠️ 检测到'今日次数已用完'提示")
                raise Exception("今日次数已用完，需要切换指纹")

            # 检查验证码失败
            if self._check_verification_failure(page_content):
                self.verification_failure_count += 1
                self.logger.warning(f"⚠️ 检测到验证码失败 (第{self.verification_failure_count}次)")

                # 如果验证码失败次数过多，尝试切换代理
                if self.verification_failure_count >= 2:
                    self.logger.info("🔄 验证码失败次数过多，尝试切换代理...")
                    proxy_switched = await self._switch_proxy_if_needed()
                    if proxy_switched:
                        raise Exception("验证码失败，已切换代理，需要重新检测")
                    else:
                        raise Exception("验证码失败，代理切换失败")
                else:
                    raise Exception("验证码失败，需要重试")

            # 使用DrissionPage查找包含百分比的元素
            percentage_elements = page.eles('xpath://*[contains(text(), "%")]')
            for elem in percentage_elements:
                try:
                    text = elem.text.strip()
                    # 排除明显的页面介绍文本
                    if (text and len(text) < 200 and
                        not any(exclude in text.lower() for exclude in [
                            "accuracy rate", "准确率", "social media", "fake aigc",
                            "platforms", "news and image", "98%+", "detection assistant"
                        ])):

                        # 查找数字百分比
                        import re
                        percentage_matches = re.findall(r'(\d+(?:\.\d+)?)%', text)
                        for match in percentage_matches:
                            ai_prob = float(match)
                            # 合理的AI概率范围
                            if 0 <= ai_prob <= 100:
                                is_passed = ai_prob < self.threshold
                                self.logger.info(f"🎯 找到AI概率结果: {ai_prob}% - {text}")
                                self.logger.info(f"🚦 检测结果: {'通过' if is_passed else '未通过'} (阈值: {self.threshold}%)")
                                
                                return AIDetectionResult(
                                    ai_probability=ai_prob,
                                    is_passed=is_passed,
                                    detection_details={
                                        "raw_text": text, 
                                        "detector": "zhuque",
                                        "threshold": self.threshold,
                                        "status": "success"
                                    },
                                    detection_time=datetime.now(),
                                    success=True
                                )
                except:
                    continue

            # 如果没有找到结果，返回默认值
            self.logger.warning("🔍 没有找到明确的检测结果，返回默认值")
            ai_prob = 50.0
            is_passed = ai_prob < self.threshold
            
            return AIDetectionResult(
                ai_probability=ai_prob,
                is_passed=is_passed,
                detection_details={
                    "detector": "zhuque",
                    "threshold": self.threshold,
                    "status": "partial_success",
                    "note": "未找到明确的检测结果，使用默认值"
                },
                detection_time=datetime.now(),
                success=True,
                error="未找到明确的检测结果"
            )

        except Exception as e:
            error_msg = str(e)

            # 如果是需要切换指纹的错误，重新抛出异常让外层处理
            if any(indicator in error_msg for indicator in ["今日次数已用完", "检测次数已用完", "daily limit", "需要切换指纹"]):
                self.logger.error(f"检测过程中出现错误: {e}")
                raise e  # 重新抛出异常，让外层的重试逻辑处理

            # 其他错误返回失败结果
            self.logger.error(f"检测过程中出现错误: {e}")
            return AIDetectionResult(
                ai_probability=100.0,  # 检测失败时假设为100%AI内容
                is_passed=False,
                detection_details={"detector": "zhuque", "status": "error"},
                detection_time=datetime.now(),
                success=False,
                error=str(e)
            )

        finally:
            # 关闭浏览器
            if page:
                try:
                    page.quit()
                except:
                    pass


# Service instance
_ai_detector = None

def get_ai_detector() -> ZhuqueAIDetector:
    """Get AI detector service instance."""
    global _ai_detector
    if _ai_detector is None:
        _ai_detector = ZhuqueAIDetector()
    return _ai_detector
