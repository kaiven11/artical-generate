"""
Content extraction service using Freedium.cfd for Medium articles.
"""

import asyncio
import logging
import re
import time
import os
from typing import Dict, Optional, Any
from urllib.parse import urlparse, urljoin
import aiohttp
from bs4 import BeautifulSoup
from dataclasses import dataclass

from ..core.performance_config import get_performance_config
from datetime import datetime

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    DRISSION_AVAILABLE = True
except ImportError:
    DRISSION_AVAILABLE = False
    ChromiumPage = None
    ChromiumOptions = None


@dataclass
class ExtractedContent:
    """Extracted article content."""
    title: str
    content: str
    author: Optional[str] = None
    publish_date: Optional[str] = None
    tags: list = None
    summary: Optional[str] = None
    word_count: int = 0
    reading_time: int = 0
    source_url: str = ""
    extraction_method: str = ""
    success: bool = True
    error: Optional[str] = None


class ContentExtractor:
    """Content extraction service."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.freedium_base = "https://freedium.cfd"

        # 使用性能配置
        self.perf_config = get_performance_config()
        extraction_config = self.perf_config.get_content_extraction_config()

        self.timeout = aiohttp.ClientTimeout(total=extraction_config["http_timeout"])
        
    async def extract_content(self, url: str) -> ExtractedContent:
        """
        Extract content from article URL.

        Args:
            url: Article URL to extract content from

        Returns:
            ExtractedContent with extracted article data
        """
        self.logger.info("="*80)
        self.logger.info(f"🚀 开始内容提取流程: {url}")
        self.logger.info(f"🔧 DrissionPage可用性: {DRISSION_AVAILABLE}")
        self.logger.info("="*80)

        # Try different extraction methods
        methods = [
            ("freedium", self._extract_via_freedium),
            ("direct", self._extract_direct),
        ]

        for method_name, method_func in methods:
            try:
                self.logger.info(f"🔄 尝试提取方法: {method_name}")
                self.logger.info(f"📋 即将调用方法: {method_func.__name__}")

                result = await method_func(url)

                self.logger.info(f"📊 方法 {method_name} 执行完成，成功: {result.success}")
                if result.success and result.content:
                    result.extraction_method = method_name
                    self.logger.info(f"✅ 使用 {method_name} 方法成功提取内容")
                    return result
                else:
                    self.logger.warning(f"⚠️ 方法 {method_name} 未能提取到有效内容")

            except Exception as e:
                self.logger.error(f"💥 提取方法 {method_name} 失败: {e}")
                import traceback
                self.logger.error(f"📋 错误详情: {traceback.format_exc()}")
                continue
        
        # All methods failed
        return ExtractedContent(
            title="",
            content="",
            source_url=url,
            success=False,
            error="All extraction methods failed"
        )
    
    async def _extract_via_freedium(self, url: str) -> ExtractedContent:
        """Extract content using Freedium.cfd service with visual browser."""
        if not DRISSION_AVAILABLE:
            raise RuntimeError("DrissionPage not installed. Please install: pip install DrissionPage")

        # Ensure URL is properly formatted for Freedium
        # Freedium expects: https://freedium.cfd/https://medium.com/...
        if not url.startswith('http'):
            url = f"https://{url}"

        # Construct Freedium URL correctly (no + prefix needed)
        freedium_url = f"{self.freedium_base}/{url}"
        self.logger.info(f"🔗 原始URL: {url}")
        self.logger.info(f"🌐 使用可视化浏览器访问 Freedium: {freedium_url}")
        
        page = None
        try:
            # 创建浏览器配置
            options = self._create_browser_options()
            
            # 创建浏览器实例
            self.logger.info("🚀 启动Chrome浏览器进行内容提取...")
            self.logger.info("📺 浏览器将以可视化模式运行，您可以看到整个提取过程")
            self.logger.info("🔥 浏览器窗口即将弹出，请注意观察！")
            self.logger.info("📋 正在创建 ChromiumPage 实例...")

            try:
                page = ChromiumPage(addr_or_opts=options)
                self.logger.info("✅ ChromiumPage 实例创建成功!")
            except Exception as e:
                self.logger.error(f"💥 ChromiumPage 创建失败: {e}")
                import traceback
                self.logger.error(f"📋 错误详情: {traceback.format_exc()}")
                raise

            # 确保窗口激活并置于前台
            self.logger.info("🔧 正在配置浏览器窗口...")
            try:
                page.set.window.max()  # 最大化窗口
                self.logger.info("✅ 窗口最大化成功")
            except Exception as e:
                self.logger.warning(f"⚠️ 窗口最大化失败: {e}")

            try:
                # 尝试置于前台（如果方法存在）
                if hasattr(page.set.window, 'to_front'):
                    page.set.window.to_front()
                    self.logger.info("✅ 窗口置于前台成功")
                else:
                    self.logger.info("ℹ️ 窗口置于前台方法不可用，跳过")
            except Exception as e:
                self.logger.warning(f"⚠️ 窗口置于前台失败: {e}")

            self.logger.info("✅ Chrome浏览器启动成功!")
            self.logger.info("🌐 浏览器窗口已打开，正在访问Freedium...")
            self.logger.info("👁️ 请查看弹出的浏览器窗口！")
            
            # 给用户时间观察浏览器窗口 - 使用性能配置
            extraction_config = self.perf_config.get_content_extraction_config()
            startup_wait = extraction_config["browser_startup_wait"]
            self.logger.info(f"⏳ 等待{startup_wait}秒，让您观察浏览器窗口...")
            time.sleep(startup_wait)

            # 访问Freedium页面
            self.logger.info(f"📄 正在访问页面: {freedium_url}")
            self.logger.info("👀 请观察浏览器窗口中的页面加载过程...")
            page.get(freedium_url)

            # 等待页面加载，给用户时间观察 - 使用性能配置
            page_load_wait = extraction_config["page_load_wait"]
            self.logger.info("⏳ 等待页面加载完成...")
            time.sleep(page_load_wait)
            
            # 获取页面标题
            page_title = page.title
            self.logger.info(f"📝 页面标题: {page_title}")
            
            # 等待内容加载完成 - 使用性能配置
            content_load_wait = extraction_config["content_load_wait"]
            self.logger.info("⏳ 等待页面内容加载...")
            time.sleep(content_load_wait)
            
            # 获取页面HTML
            html = page.html
            self.logger.info(f"📊 页面HTML长度: {len(html)} 字符")
            
            # 解析内容
            result = self._parse_freedium_html(html, url)
            
            if result.success:
                self.logger.info("✅ 内容提取成功!")
                self.logger.info(f"📰 文章标题: {result.title}")
                self.logger.info(f"👤 作者: {result.author or '未知'}")
                self.logger.info(f"📝 内容长度: {result.word_count} 词")
                self.logger.info(f"📝 实际内容长度: {len(result.content)} 字符")
                self.logger.info(f"⏱️ 预计阅读时间: {result.reading_time} 分钟")
                self.logger.info(f"📄 内容预览: {result.content[:200]}...")
            else:
                self.logger.warning("⚠️ 内容提取不完整，尝试增强提取...")
                # 尝试更积极的提取方法
                result = self._enhanced_content_extraction(page, url)
                
            return result
            
        except Exception as e:
            self.logger.error(f"💥 浏览器内容提取失败: {e}")
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
        
        # 指定Chrome浏览器路径（指纹浏览器）
        chrome_path = r"C:\Users\asus\AppData\Local\Chromium\Application\chrome.exe"
        self.logger.info(f"🔧 使用指纹浏览器路径: {chrome_path}")
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
        
        # 窗口配置 - 强制可视化模式，确保用户能看到浏览器操作
        options.set_argument("--window-size=1400,900")  # 更大的窗口
        options.set_argument("--window-position=50,50")   # 靠近屏幕左上角
        options.set_argument("--start-maximized")         # 启动时最大化
        options.set_argument("--disable-web-security")    # 禁用web安全限制
        options.set_argument("--disable-features=VizDisplayCompositor")
        options.set_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # 强制禁用无头模式 - 确保浏览器窗口可见
        # 绝对不使用无头模式
        options.set_argument("--disable-headless")
        options.set_argument("--no-headless")

        # 确保窗口在前台显示
        options.set_argument("--force-device-scale-factor=1")
        options.set_argument("--high-dpi-support=1")
        
        self.logger.info("🔧 浏览器配置: 可视化模式，1200x800窗口")
        return options
    
    async def _extract_direct(self, url: str) -> ExtractedContent:
        """Extract content directly from the original URL."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession(timeout=self.timeout, headers=headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Direct access returned status {response.status}")
                
                html = await response.text()
                return self._parse_medium_html(html, url)
    
    def _parse_freedium_html(self, html: str, source_url: str) -> ExtractedContent:
        """Parse HTML content from Freedium.cfd."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = ""
        title_selectors = ['h1', 'title', '[data-testid="storyTitle"]']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                break
        
        # Extract main content
        content = ""
        content_selectors = [
            'article',
            '[data-testid="storyContent"]',
            '.story-content',
            'main',
            '.post-content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select('script, style, nav, header, footer, .ad, .advertisement'):
                    unwanted.decompose()
                
                content = content_elem.get_text().strip()
                break
        
        # Extract author
        author = ""
        author_selectors = [
            '[data-testid="authorName"]',
            '.author-name',
            '[rel="author"]',
            '.byline-author'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get_text().strip()
                break
        
        # Extract publish date
        publish_date = ""
        date_selectors = [
            'time[datetime]',
            '[data-testid="storyPublishDate"]',
            '.publish-date'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                publish_date = date_elem.get('datetime') or date_elem.get_text().strip()
                break
        
        # Calculate word count and reading time
        word_count = len(content.split()) if content else 0
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute
        
        # Generate summary (first 200 characters)
        summary = content[:200] + "..." if len(content) > 200 else content
        
        return ExtractedContent(
            title=title,
            content=content,
            author=author,
            publish_date=publish_date,
            summary=summary,
            word_count=word_count,
            reading_time=reading_time,
            source_url=source_url,
            success=bool(title and content)
        )
    
    def _parse_medium_html(self, html: str, source_url: str) -> ExtractedContent:
        """Parse HTML content from Medium directly."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Medium-specific selectors
        title = ""
        title_elem = soup.select_one('h1[data-testid="storyTitle"], h1.graf--title')
        if title_elem:
            title = title_elem.get_text().strip()
        
        # Extract content paragraphs
        content_parts = []
        content_selectors = [
            'article section p',
            '.story-content p',
            '[data-testid="storyContent"] p'
        ]
        
        for selector in content_selectors:
            paragraphs = soup.select(selector)
            if paragraphs:
                content_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                break
        
        content = "\n\n".join(content_parts)
        
        # Extract author
        author = ""
        author_elem = soup.select_one('[data-testid="authorName"], .author-name')
        if author_elem:
            author = author_elem.get_text().strip()
        
        # Calculate metrics
        word_count = len(content.split()) if content else 0
        reading_time = max(1, word_count // 200)
        summary = content[:200] + "..." if len(content) > 200 else content
        
        return ExtractedContent(
            title=title,
            content=content,
            author=author,
            summary=summary,
            word_count=word_count,
            reading_time=reading_time,
            source_url=source_url,
            success=bool(title and content)
        )
    
    def _enhanced_content_extraction(self, page, url: str) -> ExtractedContent:
        """增强的内容提取方法，直接从页面DOM获取内容"""
        try:
            self.logger.info("🔍 使用增强提取方法...")
            
            # 获取页面标题
            title = ""
            try:
                title_elem = page.ele('tag:h1')
                if title_elem:
                    title = title_elem.text.strip()
                    self.logger.info(f"📰 提取到标题: {title}")
            except:
                pass
            
            # 获取作者信息
            author = ""
            try:
                # 尝试多种作者选择器
                author_selectors = ['[data-testid="authorName"]', '.author', '.byline', 'a[rel="author"]']
                for selector in author_selectors:
                    try:
                        author_elem = page.ele(selector)
                        if author_elem:
                            author = author_elem.text.strip()
                            self.logger.info(f"👤 提取到作者: {author}")
                            break
                    except:
                        continue
            except:
                pass
            
            # 获取所有段落内容
            content_parts = []
            try:
                # 获取所有段落
                paragraphs = page.eles('tag:p')
                self.logger.info(f"📝 找到 {len(paragraphs)} 个段落")
                
                for i, p in enumerate(paragraphs):
                    try:
                        text = p.text.strip()
                        if text and len(text) > 20:  # 过滤太短的段落
                            content_parts.append(text)
                            if i < 3:  # 只显示前3个段落的预览
                                self.logger.info(f"📄 段落 {i+1}: {text[:100]}...")
                    except:
                        continue
                        
            except Exception as e:
                self.logger.warning(f"段落提取失败: {e}")
            
            # 组合内容
            content = "\n\n".join(content_parts)

            # 清理Freedium平台自己的内容
            content = self._clean_freedium_content(content)

            if not content:
                # 尝试获取整个文章体
                try:
                    article_elem = page.ele('tag:article')
                    if article_elem:
                        content = article_elem.text.strip()
                        content = self._clean_freedium_content(content)
                        self.logger.info("📄 从article标签获取内容")
                except:
                    pass
            
            if not content:
                # 最后尝试获取main标签内容
                try:
                    main_elem = page.ele('tag:main')
                    if main_elem:
                        content = main_elem.text.strip()
                        self.logger.info("📄 从main标签获取内容")
                except:
                    pass
            
            # 计算指标
            word_count = len(content.split()) if content else 0
            reading_time = max(1, word_count // 200)
            summary = content[:200] + "..." if len(content) > 200 else content
            
            self.logger.info(f"✅ 增强提取完成: 标题={'有' if title else '无'}, 内容={len(content)}字符, {word_count}词")
            
            return ExtractedContent(
                title=title or "未提取到标题",
                content=content,
                author=author or "未知作者",
                summary=summary,
                word_count=word_count,
                reading_time=reading_time,
                source_url=url,
                extraction_method="enhanced",
                success=bool(content)  # 只要有内容就算成功
            )
            
        except Exception as e:
            self.logger.error(f"💥 增强提取失败: {e}")
            return ExtractedContent(
                title="提取失败",
                content="",
                source_url=url,
                success=False,
                error=str(e)
            )

    def _clean_freedium_content(self, content: str) -> str:
        """清理Freedium平台自己的内容，只保留原始文章内容"""
        if not content:
            return content

        # Freedium平台内容的标识
        freedium_markers = [
            "Dear Freedium users,",
            "We've updated our donation options",
            "Your contributions are invaluable",
            "Choose Your Preferred Donation Platform:",
            "Sometimes we have problems displaying some Medium posts",
            "If you have a problem that some images aren't loading",
            "try using VPN",
            "Cloudflare's bot detection algorithms"
        ]

        lines = content.split('\n')
        cleaned_lines = []
        skip_mode = False

        for line in lines:
            line_stripped = line.strip()

            # 检查是否是Freedium平台内容的开始
            if any(marker in line_stripped for marker in freedium_markers):
                skip_mode = True
                continue

            # 如果在跳过模式中，检查是否遇到了真正的文章内容
            if skip_mode:
                # 如果这行看起来像是文章内容的开始（长度足够且不是平台信息）
                if (len(line_stripped) > 50 and
                    not any(marker in line_stripped for marker in freedium_markers) and
                    not line_stripped.startswith('http') and
                    not 'donation' in line_stripped.lower() and
                    not 'support' in line_stripped.lower() and
                    not 'freedium' in line_stripped.lower()):
                    skip_mode = False
                    cleaned_lines.append(line)
                continue

            # 正常模式，保留内容
            if line_stripped:  # 只保留非空行
                cleaned_lines.append(line)

        cleaned_content = '\n'.join(cleaned_lines).strip()

        # 如果清理后内容太短，返回原内容
        if len(cleaned_content) < len(content) * 0.3:
            self.logger.warning("清理后内容过短，返回原内容")
            return content

        self.logger.info(f"内容清理完成: {len(content)} -> {len(cleaned_content)} 字符")
        return cleaned_content


# Service instance
_content_extractor = None

def get_content_extractor() -> ContentExtractor:
    """Get content extractor service instance."""
    global _content_extractor
    if _content_extractor is None:
        _content_extractor = ContentExtractor()
    return _content_extractor
