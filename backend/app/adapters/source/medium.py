"""
Medium platform adapter for article extraction.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from ..base import BaseSourceAdapter, ArticleInfo, ArticleContent, PlatformInfo, AdapterType

logger = logging.getLogger(__name__)


class MediumAdapter(BaseSourceAdapter):
    """Medium platform adapter for article extraction."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Medium adapter."""
        super().__init__(config)
        self.base_url = "https://medium.com"
        self.search_url = "https://medium.com/search"
        self.session = requests.Session()
        
        # Set headers to mimic browser and ensure fresh content
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache, no-store, must-revalidate',  # 禁用缓存
            'Pragma': 'no-cache',  # HTTP/1.0 缓存控制
            'Expires': '0'  # 立即过期
        })
    
    def get_platform_info(self) -> PlatformInfo:
        """Get Medium platform information."""
        return PlatformInfo(
            name="medium",
            display_name="Medium",
            type=AdapterType.SOURCE,
            features=["search", "extract", "trending"],
            requires_auth=False,
            description="Medium is a popular publishing platform for articles and blogs",
            version="1.0.0",
            website="https://medium.com"
        )
    
    async def test_connection(self) -> bool:
        """Test connection to Medium."""
        try:
            response = self.session.get(self.base_url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to Medium: {e}")
            return False
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for Medium adapter."""
        return {
            "type": "object",
            "properties": {
                "use_freedium": {
                    "type": "boolean",
                    "default": True,
                    "description": "Use Freedium.cfd to bypass Medium paywall"
                },
                "freedium_url": {
                    "type": "string",
                    "default": "https://freedium.cfd",
                    "description": "Freedium service URL"
                },
                "max_articles_per_search": {
                    "type": "integer",
                    "default": 20,
                    "description": "Maximum articles to return per search"
                }
            }
        }
    
    async def search_articles(self, keywords: List[str], limit: int = 20) -> List[ArticleInfo]:
        """
        Search for articles on Medium using direct search for keywords, RSS only when keywords are empty.

        Args:
            keywords: Search keywords
            limit: Maximum number of articles to return

        Returns:
            List of article information sorted by quality score
        """
        try:
            # If no keywords provided, use RSS feeds for general content
            if not keywords or all(not kw.strip() for kw in keywords):
                logger.info("No keywords provided, using RSS feeds for general content")
                articles_from_rss = await self._search_via_rss([], limit)
                sorted_articles = self._filter_by_relevance(articles_from_rss, [])
                return sorted_articles[:limit]

            # For keyword searches, ONLY use direct search to ensure relevance
            logger.info(f"Starting direct search for keywords: {keywords}")
            articles_from_search = await self._search_via_direct(keywords, limit)

            # Remove duplicates based on URL
            seen_urls = set()
            unique_articles = []
            for article in articles_from_search:
                if article.url not in seen_urls:
                    seen_urls.add(article.url)
                    unique_articles.append(article)

            logger.info(f"After deduplication: {len(unique_articles)} unique articles")

            # Score and sort articles by keyword relevance and quality
            sorted_articles = self._filter_by_relevance(unique_articles, keywords)
            logger.info(f"After relevance filtering: {len(sorted_articles)} relevant articles")

            # Return top articles based on limit, but be more lenient if we don't have enough
            if len(sorted_articles) < limit:
                logger.info(f"Only {len(sorted_articles)} relevant articles found, returning all")
                selected_articles = sorted_articles
            else:
                selected_articles = sorted_articles[:limit]

            logger.info(f"Selected {len(selected_articles)} articles from {len(sorted_articles)} total for keywords: {keywords}")

            return selected_articles

        except Exception as e:
            logger.error(f"Failed to search Medium articles: {e}")
            return []

    async def search_by_tag(self, tag: str, limit: int = 20) -> List[ArticleInfo]:
        """
        Search for articles on Medium using tag-based search via /tag/{tag}/archive URL.

        Args:
            tag: The tag to search for (e.g., 'artificial-intelligence', 'machine-learning')
            limit: Maximum number of articles to return

        Returns:
            List of article information from the tag archive
        """
        try:
            logger.info(f"Starting tag-based search for tag: {tag}")

            # Use the tag archive URL format with timestamp to ensure fresh data
            import time
            timestamp = int(time.time())
            tag_url = f"https://medium.com/tag/{tag}/archive?t={timestamp}"

            logger.info(f"🔄 使用带时间戳的URL确保获取最新数据: {tag_url}")

            # Use requests first for faster initial load
            articles = await self._search_tag_with_requests(tag_url, tag, limit)

            # If we don't have enough articles, try with Selenium for dynamic content
            if len(articles) < limit:
                logger.info(f"Only found {len(articles)} articles with requests, trying Selenium for more")
                selenium_articles = await self._search_tag_with_selenium(tag_url, tag, limit - len(articles))

                # Merge results, avoiding duplicates
                seen_urls = {article.url for article in articles}
                for article in selenium_articles:
                    if article.url not in seen_urls:
                        articles.append(article)
                        seen_urls.add(article.url)

            logger.info(f"Tag search completed: found {len(articles)} total articles for tag: {tag}")
            return articles[:limit]

        except Exception as e:
            logger.error(f"Failed to search Medium articles by tag '{tag}': {e}")
            return []

    async def _search_tag_with_requests(self, tag_url: str, tag: str, limit: int) -> List[ArticleInfo]:
        """Search tag archive using requests library."""
        try:
            articles = []

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = self.session.get(tag_url, headers=headers, timeout=15)
            response.raise_for_status()

            # Parse the tag archive page
            soup = BeautifulSoup(response.content, 'html.parser')
            article_elements = self._find_article_elements(soup)

            logger.info(f"Found {len(article_elements)} raw articles with requests for tag: {tag}")

            for element in article_elements[:limit * 2]:  # Get more than needed for filtering
                try:
                    if isinstance(element, ArticleInfo):
                        articles.append(element)
                    else:
                        article_info = self._parse_search_result_with_metrics(element)
                        if article_info and self._is_medium_article_url(article_info.url):
                            articles.append(article_info)

                        if len(articles) >= limit:
                            break

                except Exception as e:
                    logger.warning(f"Failed to extract article info from element: {e}")
                    continue

            logger.info(f"Extracted {len(articles)} valid articles from tag archive with requests")
            return articles

        except Exception as e:
            logger.error(f"Tag search with requests failed: {e}")
            return []

    async def _search_tag_with_selenium(self, tag_url: str, tag: str, limit: int) -> List[ArticleInfo]:
        """Search tag archive using Selenium for dynamic content."""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.common.exceptions import TimeoutException, NoSuchElementException

            articles = []

            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

            driver = webdriver.Chrome(options=chrome_options)

            try:
                driver.get(tag_url)
                wait = WebDriverWait(driver, 10)

                # Wait for articles to load
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))

                # Try to click "Show more" button if it exists to load more articles
                max_clicks = 3  # Limit the number of "show more" clicks
                clicks = 0

                while clicks < max_clicks and len(articles) < limit:
                    try:
                        # Look for "Show more" or "See more" button
                        show_more_selectors = [
                            "button[data-testid='show-more']",
                            "button:contains('Show more')",
                            "button:contains('See more')",
                            ".show-more-button",
                            "[data-action='show-more']"
                        ]

                        show_more_button = None
                        for selector in show_more_selectors:
                            try:
                                show_more_button = driver.find_element(By.CSS_SELECTOR, selector)
                                if show_more_button.is_displayed() and show_more_button.is_enabled():
                                    break
                            except NoSuchElementException:
                                continue

                        if show_more_button:
                            driver.execute_script("arguments[0].click();", show_more_button)
                            # Wait for new content to load
                            time.sleep(2)
                            clicks += 1
                        else:
                            break

                    except Exception as e:
                        logger.debug(f"Could not click show more button: {e}")
                        break

                # Extract articles from the page
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                article_elements = self._find_article_elements(soup)

                logger.info(f"Found {len(article_elements)} articles with Selenium for tag: {tag}")

                for element in article_elements[:limit * 2]:
                    try:
                        if isinstance(element, ArticleInfo):
                            articles.append(element)
                        else:
                            article_info = self._parse_search_result_with_metrics(element)
                            if article_info and self._is_medium_article_url(article_info.url):
                                articles.append(article_info)

                            if len(articles) >= limit:
                                break

                    except Exception as e:
                        logger.warning(f"Failed to extract article info from element: {e}")
                        continue

            finally:
                driver.quit()

            logger.info(f"Extracted {len(articles)} valid articles from tag archive with Selenium")
            return articles

        except Exception as e:
            logger.error(f"Tag search with Selenium failed: {e}")
            return []
    
    async def extract_content(self, url: str) -> ArticleContent:
        """
        Extract content from Medium article URL.
        
        Args:
            url: Article URL
            
        Returns:
            Article content with metadata
        """
        try:
            # Check if we should use Freedium
            use_freedium = self.config.get('use_freedium', True)
            
            if use_freedium:
                content = await self._extract_via_freedium(url)
            else:
                content = await self._extract_direct(url)
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {e}")
            raise
    
    async def _extract_via_freedium(self, url: str) -> ArticleContent:
        """Extract content via Freedium service."""
        try:
            # Ensure URL is properly formatted
            if not url.startswith('http'):
                url = f"https://medium.com{url}"

            # Construct Freedium URL: https://freedium.cfd/https://medium.com/...
            freedium_url = self.config.get('freedium_url', 'https://freedium.cfd')
            freedium_article_url = f"{freedium_url}/{url}"

            logger.info(f"Extracting via Freedium: {freedium_article_url}")

            # Set headers to mimic browser for Freedium
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = self.session.get(freedium_article_url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract article content from Freedium page
            title = self._extract_title_from_freedium(soup)
            content = self._extract_content_from_freedium(soup)
            author = self._extract_author_from_freedium(soup)
            publish_date = self._extract_publish_date_from_freedium(soup)
            tags = self._extract_tags_from_freedium(soup)

            # Validate extraction
            if not content or len(content) < 100:
                logger.warning("Freedium extraction returned insufficient content, trying direct method")
                return await self._extract_direct(url)

            return ArticleContent(
                title=title,
                content=content,
                author=author,
                publish_date=publish_date,
                tags=tags,
                source_url=url,
                platform="medium",
                metadata={
                    "extraction_method": "freedium",
                    "freedium_url": freedium_article_url,
                    "content_length": len(content),
                    "extraction_success": True
                }
            )

        except Exception as e:
            logger.error(f"Failed to extract via Freedium: {e}")
            # Fallback to direct extraction
            return await self._extract_direct(url)

    async def _search_via_rss(self, keywords: List[str], limit: int = 20) -> List[ArticleInfo]:
        """Search for articles using Medium RSS feeds."""
        articles = []

        try:
            # Create RSS URLs for each keyword
            rss_urls = []
            for keyword in keywords:
                # Clean keyword for URL
                clean_keyword = keyword.lower().replace(' ', '-').replace('_', '-')
                rss_url = f"https://medium.com/feed/tag/{clean_keyword}"
                rss_urls.append(rss_url)

            # Also add some general high-quality RSS feeds
            general_feeds = [
                "https://medium.com/feed/tag/life",
                "https://medium.com/feed/tag/productivity",
                "https://medium.com/feed/tag/technology",
                "https://medium.com/feed/tag/programming",
                "https://medium.com/feed/tag/business"
            ]

            # Combine and deduplicate
            all_feeds = list(set(rss_urls + general_feeds))

            logger.info(f"Searching {len(all_feeds)} RSS feeds for keywords: {keywords}")

            # Fetch articles from each RSS feed
            for rss_url in all_feeds[:5]:  # Limit to 5 feeds to avoid too many requests
                try:
                    feed_articles = await self._fetch_rss_articles(rss_url, limit // len(all_feeds) + 5)
                    articles.extend(feed_articles)

                    if len(articles) >= limit * 2:  # Stop if we have enough
                        break

                except Exception as e:
                    logger.warning(f"Failed to fetch RSS from {rss_url}: {e}")
                    continue

            logger.info(f"Fetched {len(articles)} articles from RSS feeds")
            return articles

        except Exception as e:
            logger.error(f"RSS search failed: {e}")
            return []

    async def _fetch_rss_articles(self, rss_url: str, limit: int = 10) -> List[ArticleInfo]:
        """Fetch articles from a single RSS feed."""
        try:
            response = self.session.get(rss_url, timeout=15)
            response.raise_for_status()

            # Parse RSS XML
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')

            articles = []
            for item in items[:limit]:
                try:
                    article_info = self._parse_rss_item(item)
                    if article_info:
                        articles.append(article_info)
                except Exception as e:
                    logger.warning(f"Failed to parse RSS item: {e}")
                    continue

            return articles

        except Exception as e:
            logger.warning(f"Failed to fetch RSS feed {rss_url}: {e}")
            return []

    def _parse_rss_item(self, item) -> Optional[ArticleInfo]:
        """Parse RSS item to ArticleInfo."""
        try:
            # Extract basic info
            title_elem = item.find('title')
            title = title_elem.text if title_elem else "Unknown Title"

            link_elem = item.find('link')
            url = link_elem.text if link_elem else None

            if not url:
                return None

            # Extract description/summary
            desc_elem = item.find('description') or item.find('content:encoded')
            summary = None
            if desc_elem:
                # Clean HTML from description
                desc_soup = BeautifulSoup(desc_elem.text, 'html.parser')
                summary = desc_soup.get_text(strip=True)[:300]

            # Extract author
            author_elem = item.find('dc:creator') or item.find('author')
            author = author_elem.text if author_elem else None

            # Extract publish date
            pub_date_elem = item.find('pubDate')
            publish_date = None
            if pub_date_elem:
                try:
                    from dateutil import parser as date_parser
                    publish_date = date_parser.parse(pub_date_elem.text)
                except Exception:
                    pass

            # Extract categories/tags
            category_elems = item.find_all('category')
            tags = [cat.text for cat in category_elems if cat.text]

            # Calculate initial quality score based on available data
            quality_score = self._calculate_rss_quality_score(title, summary, publish_date, tags)

            article_info = ArticleInfo(
                title=title,
                url=url,
                author=author,
                summary=summary,
                publish_date=publish_date,
                tags=tags,
                platform="medium"
            )

            # Add metadata
            article_info.metadata = {
                'quality_score': quality_score,
                'source': 'rss',
                'claps': 0,  # Not available in RSS
                'responses': 0,  # Not available in RSS
                'reading_time': self._estimate_reading_time(summary or title)
            }

            return article_info

        except Exception as e:
            logger.warning(f"Failed to parse RSS item: {e}")
            return None

    def _calculate_rss_quality_score(self, title: str, summary: str,
                                   publish_date: Optional[datetime], tags: List[str]) -> float:
        """Calculate quality score for RSS articles."""
        score = 0.0

        # Title quality (20 points)
        if title and len(title) > 10:
            score += 20
        elif title:
            score += 10

        # Summary quality (20 points)
        if summary and len(summary) > 100:
            score += 20
        elif summary:
            score += 10

        # Recency (30 points)
        if publish_date:
            try:
                # Handle timezone-aware vs timezone-naive datetime comparison
                now = datetime.now()
                if publish_date.tzinfo is not None:
                    # If publish_date is timezone-aware, make now timezone-aware too
                    from datetime import timezone
                    now = datetime.now(timezone.utc)
                    if publish_date.tzinfo != timezone.utc:
                        # Convert to UTC for comparison
                        publish_date = publish_date.astimezone(timezone.utc)
                elif now.tzinfo is not None:
                    # If now is timezone-aware but publish_date is not, make publish_date aware
                    from datetime import timezone
                    publish_date = publish_date.replace(tzinfo=timezone.utc)

                days_old = (now - publish_date).days
                if days_old <= 7:
                    score += 30
                elif days_old <= 30:
                    score += 25
                elif days_old <= 90:
                    score += 15
                else:
                    score += 5
            except Exception as e:
                logger.warning(f"Error calculating date difference: {e}")
                score += 10  # Default score if date calculation fails
        else:
            score += 10  # Default if no date

        # Tags quality (15 points)
        if tags:
            score += min(len(tags) * 3, 15)

        # Content length estimation (15 points)
        content_length = len(summary or '') + len(title or '')
        if content_length > 200:
            score += 15
        elif content_length > 100:
            score += 10
        else:
            score += 5

        return min(score, 100)

    def _estimate_reading_time(self, text: str) -> int:
        """Estimate reading time in minutes."""
        if not text:
            return 0

        words = len(text.split())
        # Average reading speed: 200-250 words per minute
        return max(1, words // 225)

    async def _search_via_direct(self, keywords: List[str], limit: int = 20) -> List[ArticleInfo]:
        """Search for articles using Medium's direct search with dynamic content loading."""
        try:
            articles = []
            query = " ".join(keywords)

            # First try with requests (faster)
            articles = await self._search_with_requests(query, limit)

            # If we don't have enough articles, try with Selenium for dynamic content
            if len(articles) < limit:
                logger.info(f"Only found {len(articles)} articles with requests, trying Selenium for more")
                selenium_articles = await self._search_with_selenium(query, limit - len(articles))

                # Merge results, avoiding duplicates
                seen_urls = {article.url for article in articles}
                for article in selenium_articles:
                    if article.url not in seen_urls:
                        articles.append(article)
                        seen_urls.add(article.url)

            logger.info(f"Direct search completed: found {len(articles)} total articles")
            return articles[:limit]  # Return only the requested number

        except Exception as e:
            logger.error(f"Direct search failed: {e}")
            return []

    async def _search_with_requests(self, query: str, limit: int) -> List[ArticleInfo]:
        """Search using requests library (faster but limited)."""
        try:
            articles = []
            # Add timestamp to ensure fresh data
            import time
            timestamp = int(time.time())
            search_url = f"https://medium.com/search?q={query}&t={timestamp}"

            logger.info(f"🔄 使用带时间戳的搜索URL确保获取最新数据: {search_url}")

            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()

            # Parse search results
            soup = BeautifulSoup(response.content, 'html.parser')
            article_elements = self._find_article_elements(soup)

            logger.info(f"Found {len(article_elements)} raw articles with requests for query: {query}")

            # Parse each article
            for element in article_elements:
                try:
                    if isinstance(element, ArticleInfo):
                        articles.append(element)
                    else:
                        article_info = self._parse_search_result_with_metrics(element)
                        if article_info:
                            articles.append(article_info)

                    if len(articles) >= limit:
                        break

                except Exception as e:
                    logger.warning(f"Failed to parse article element: {e}")
                    continue

            return articles

        except Exception as e:
            logger.error(f"Requests search failed: {e}")
            return []

    async def _search_with_selenium(self, query: str, limit: int) -> List[ArticleInfo]:
        """Search using Selenium to handle dynamic content and 'Show more' buttons."""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options

            import time

            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

            driver = webdriver.Chrome(options=chrome_options)
            articles = []

            try:
                search_url = f"https://medium.com/search?q={query}"
                logger.info(f"Loading search page with Selenium: {search_url}")

                driver.get(search_url)

                # Wait for initial content to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                )

                # Scroll and click "Show more" to load more articles
                max_attempts = 5  # Increase attempts
                articles_before = 0

                for attempt in range(max_attempts):
                    # Scroll to bottom to trigger loading
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)  # Longer wait for content to load

                    # Count current articles
                    current_articles = driver.find_elements(By.TAG_NAME, "article")
                    current_count = len(current_articles)
                    logger.info(f"Attempt {attempt + 1}: Found {current_count} articles on page")

                    # Look for "Show more" button and click it
                    show_more_clicked = False
                    try:
                        # Try multiple XPath expressions for "Show more" button
                        show_more_xpaths = [
                            "//button[contains(text(), 'Show more')]",
                            "//button[contains(text(), 'Load more')]",
                            "//div[contains(text(), 'Show more')]",
                            "//span[contains(text(), 'Show more')]",
                            "//*[contains(text(), 'Show more') and (@role='button' or name()='button')]",
                            "//button[contains(@class, 'show-more')]",
                            "//div[contains(@class, 'show-more')]"
                        ]

                        for xpath in show_more_xpaths:
                            try:
                                show_more_elements = driver.find_elements(By.XPATH, xpath)
                                for element in show_more_elements:
                                    if element.is_displayed() and element.is_enabled():
                                        # Scroll to the element first
                                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                        time.sleep(1)

                                        # Try clicking with JavaScript
                                        driver.execute_script("arguments[0].click();", element)
                                        logger.info(f"Clicked 'Show more' button using XPath: {xpath} (attempt {attempt + 1})")
                                        show_more_clicked = True
                                        time.sleep(4)  # Wait longer for new content to load
                                        break

                                if show_more_clicked:
                                    break

                            except Exception as e:
                                logger.debug(f"XPath {xpath} failed: {e}")
                                continue

                        # Also try CSS selectors
                        if not show_more_clicked:
                            css_selectors = [
                                'button[data-testid*="show"]',
                                'button[data-testid*="more"]',
                                'button[data-testid*="load"]',
                                '[role="button"]:contains("Show more")',
                                '.js-showMoreButton',
                                'button:contains("Show more")'
                            ]

                            for selector in css_selectors:
                                try:
                                    if ':contains(' in selector:
                                        continue  # Skip CSS :contains for now
                                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                    for element in elements:
                                        if element.is_displayed() and element.is_enabled():
                                            driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                            time.sleep(1)
                                            driver.execute_script("arguments[0].click();", element)
                                            logger.info(f"Clicked 'Show more' button using CSS: {selector} (attempt {attempt + 1})")
                                            show_more_clicked = True
                                            time.sleep(4)
                                            break
                                    if show_more_clicked:
                                        break
                                except Exception as e:
                                    logger.debug(f"CSS selector {selector} failed: {e}")
                                    continue

                        if not show_more_clicked:
                            logger.info(f"No 'Show more' button found on attempt {attempt + 1}")

                    except Exception as e:
                        logger.warning(f"Error looking for 'Show more' button: {e}")

                    # Check if new articles were loaded
                    time.sleep(2)
                    new_articles = driver.find_elements(By.TAG_NAME, "article")
                    new_count = len(new_articles)

                    if new_count > current_count:
                        logger.info(f"Successfully loaded more articles: {current_count} -> {new_count}")
                        articles_before = new_count
                    elif new_count == articles_before and attempt > 0:
                        logger.info(f"No new articles loaded, stopping pagination")
                        break

                    # Check if we have enough articles
                    if new_count >= limit:
                        logger.info(f"Reached target limit of {limit} articles")
                        break

                # Parse the final page content
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                # First try Apollo state
                apollo_articles = self._extract_from_apollo_state(soup)
                logger.info(f"Found {len(apollo_articles)} articles from Apollo state")

                # Also try DOM parsing to get more articles
                dom_articles = self._parse_articles_from_dom(soup)
                logger.info(f"Found {len(dom_articles)} additional articles from DOM parsing")

                # Combine all articles and deduplicate
                all_selenium_articles = apollo_articles + dom_articles
                existing_urls = set()

                for article in all_selenium_articles:
                    if len(articles) >= limit:
                        break
                    if article.url and article.url not in existing_urls:
                        articles.append(article)
                        existing_urls.add(article.url)
                        logger.debug(f"Added article: {article.title[:50]}... - {article.url}")
                    else:
                        logger.debug(f"Skipped article (no URL or duplicate): {article.title[:50] if article.title else 'No title'}...")

                logger.info(f"Total articles collected with Selenium: {len(articles)}")

            finally:
                driver.quit()

            return articles

        except ImportError:
            logger.warning("Selenium not available, skipping dynamic content loading")
            return []
        except Exception as e:
            logger.error(f"Selenium search failed: {e}")
            return []

    def _filter_by_relevance(self, articles: List[ArticleInfo], keywords: List[str]) -> List[ArticleInfo]:
        """Score articles by keyword relevance and return all articles sorted by relevance."""
        if not keywords:
            return articles

        keywords_lower = [kw.lower() for kw in keywords]

        # Score all articles for relevance
        for article in articles:
            relevance_score = 0

            # Check title relevance (higher weight)
            title_lower = (article.title or '').lower()
            for keyword in keywords_lower:
                if keyword in title_lower:
                    relevance_score += 10

            # Check summary relevance (medium weight)
            summary_lower = (article.summary or '').lower()
            for keyword in keywords_lower:
                if keyword in summary_lower:
                    relevance_score += 5

            # Check tags relevance (lower weight)
            if article.tags:
                tags_lower = [tag.lower() for tag in article.tags]
                for keyword in keywords_lower:
                    for tag in tags_lower:
                        if keyword in tag:
                            relevance_score += 3

            # Give basic score to articles without keyword matches but with substantial content
            if relevance_score == 0:
                title_lower = (article.title or '').lower()
                summary_lower = (article.summary or '').lower()

                # Give basic score to articles that look substantial
                if len(title_lower) > 10 and len(summary_lower) > 20:
                    relevance_score = 1
                # Give higher score to tech/programming related articles
                tech_indicators = ['python', 'programming', 'code', 'tech', 'data', 'ai', 'ml', 'dev', 'software', 'web']
                life_indicators = ['life', 'personal', 'growth', 'self', 'motivation', 'success', 'career', 'productivity']
                if any(indicator in title_lower or indicator in summary_lower
                       for indicator in tech_indicators + life_indicators):
                    relevance_score = 2

            # Update quality score with relevance for all articles
            if hasattr(article, 'metadata') and article.metadata:
                original_score = article.metadata.get('quality_score', 0)
                article.metadata['quality_score'] = original_score + relevance_score
                article.metadata['relevance_score'] = relevance_score
            else:
                # Create metadata if it doesn't exist
                article.metadata = {
                    'quality_score': relevance_score,
                    'relevance_score': relevance_score,
                    'source': 'rss'
                }

        # Sort articles by combined quality score (original quality + relevance)
        sorted_articles = sorted(articles,
                               key=lambda x: x.metadata.get('quality_score', 0) if hasattr(x, 'metadata') and x.metadata else 0,
                               reverse=True)

        logger.info(f"Scored and sorted {len(sorted_articles)} articles by relevance for keywords: {keywords}")
        return sorted_articles
    
    async def _extract_direct(self, url: str) -> ArticleContent:
        """Extract content directly from Medium."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article content
            title = self._extract_title(soup)
            content = self._extract_article_content(soup)
            author = self._extract_author(soup)
            publish_date = self._extract_publish_date(soup)
            tags = self._extract_tags(soup)
            
            return ArticleContent(
                title=title,
                content=content,
                author=author,
                publish_date=publish_date,
                tags=tags,
                source_url=url,
                platform="medium",
                metadata={
                    "extraction_method": "direct"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to extract directly from Medium: {e}")
            raise
    
    def _find_article_elements(self, soup: BeautifulSoup) -> List:
        """Find article elements using Apollo state data or fallback to selectors."""
        # Check if we're redirected to login page
        if soup.find('form', {'data-testid': 'loginForm'}) or 'signin' in soup.get_text().lower():
            logger.warning("Redirected to login page, Medium may require authentication")
            return []

        # First try to extract from Apollo state (modern Medium approach)
        apollo_articles = self._extract_from_apollo_state(soup)
        if apollo_articles:
            logger.info(f"Found {len(apollo_articles)} articles from Apollo state")
            return apollo_articles

        # Fallback to traditional selectors
        selectors = [
            'article[data-testid="story"]',
            'div[data-testid="story"]',
            'div[data-testid="post-preview"]',
            'article',
            'div.postArticle',
            'div.streamItem',
            'div[class*="story"]',
            'div[class*="post"]',
            # Additional selectors for search results
            'div[role="article"]',
            'div[data-module="SearchResults"] > div',
            '.js-postListItem'
        ]

        elements = []
        for selector in selectors:
            found = soup.select(selector)
            if found:
                # Filter out non-article elements
                valid_elements = []
                for element in found:
                    # Check if element contains article-like content
                    if self._is_valid_article_element(element):
                        valid_elements.append(element)

                if valid_elements:
                    elements.extend(valid_elements)
                    logger.info(f"Found {len(valid_elements)} articles using selector: {selector}")
                    break

        # Enhanced fallback: look for article links in the page
        if not elements:
            elements = self._find_article_links_fallback(soup)

        return elements[:100]  # Increased limit to get more articles

    def _parse_articles_from_dom(self, soup: BeautifulSoup) -> List[ArticleInfo]:
        """Parse articles directly from DOM elements when Apollo state is insufficient."""
        articles = []

        # Look for article containers with various selectors
        article_selectors = [
            'article[data-testid="story"]',
            'div[data-testid="story"]',
            'div[data-testid="post-preview"]',
            'article',
            'div.postArticle',
            'div.streamItem',
            'div[class*="story"]',
            'div[role="article"]'
        ]

        for selector in article_selectors:
            elements = soup.select(selector)
            logger.info(f"Found {len(elements)} elements with selector: {selector}")

            for element in elements:
                try:
                    article_info = self._parse_dom_article_element(element)
                    if article_info and article_info.url:
                        # Check if we already have this article
                        if not any(a.url == article_info.url for a in articles):
                            articles.append(article_info)
                            if len(articles) >= 50:  # Reasonable limit
                                break
                except Exception as e:
                    logger.debug(f"Failed to parse DOM element: {e}")
                    continue

            if articles:
                break  # Use first successful selector

        logger.info(f"Parsed {len(articles)} articles from DOM")
        return articles

    def _parse_dom_article_element(self, element) -> Optional[ArticleInfo]:
        """Parse a single article element from DOM."""
        try:
            # Extract title
            title_selectors = ['h1', 'h2', 'h3', 'h4', '[data-testid*="title"]', '.title', 'a[data-testid="post-preview-title"]']
            title = None
            title_element = None

            for selector in title_selectors:
                title_element = element.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    if title:
                        break

            if not title:
                return None

            # Extract URL - try multiple approaches
            url = None

            # First try to find link in title element
            if title_element:
                link_element = title_element.find('a')
                if link_element and link_element.get('href'):
                    url = link_element['href']

            # If no URL in title, look for any article link in the element
            if not url:
                # Try various link selectors
                link_selectors = [
                    'a[href*="medium.com"]',
                    'a[href*="/@"]',
                    'a[href]',
                    'h1 a', 'h2 a', 'h3 a'
                ]

                for selector in link_selectors:
                    link_element = element.select_one(selector)
                    if link_element and link_element.get('href'):
                        potential_url = link_element['href']
                        # Check if it looks like an article URL
                        if ('medium.com' in potential_url or
                            potential_url.startswith('/') or
                            '/@' in potential_url):
                            url = potential_url
                            break

            # Clean up URL
            if url:
                if url.startswith('/'):
                    url = 'https://medium.com' + url
                elif not url.startswith('http'):
                    url = 'https://medium.com/' + url

                # Basic validation - must contain medium.com or look like an article
                if not ('medium.com' in url or '/@' in url):
                    return None
            else:
                return None

            # Extract author
            author_selectors = ['[data-testid="authorName"]', '.author', '[rel="author"]', 'a[href*="@"]']
            author = "Unknown Author"
            for selector in author_selectors:
                author_element = element.select_one(selector)
                if author_element:
                    author = author_element.get_text(strip=True)
                    if author:
                        break

            # Extract summary/subtitle
            summary_selectors = ['[data-testid="post-preview-description"]', '.subtitle', '.description', 'p']
            summary = ""
            for selector in summary_selectors:
                summary_element = element.select_one(selector)
                if summary_element:
                    summary = summary_element.get_text(strip=True)
                    if len(summary) > 20:  # Only use substantial summaries
                        break

            # Create article info
            article_info = ArticleInfo(
                title=title,
                url=url,
                author=author,
                summary=summary,
                platform="medium"
            )

            # Add basic metadata
            article_info.metadata = {
                'source': 'dom_parsing',
                'quality_score': 1  # Basic score for DOM-parsed articles
            }

            return article_info

        except Exception as e:
            logger.debug(f"Failed to parse DOM article element: {e}")
            return None

    def _extract_from_apollo_state(self, soup: BeautifulSoup) -> List:
        """Extract article data from Medium's Apollo state."""
        try:
            # Find the Apollo state script
            scripts = soup.find_all('script')
            apollo_data = None

            for script in scripts:
                if script.string and '__APOLLO_STATE__' in script.string:
                    # Extract the JSON data
                    script_content = script.string
                    start = script_content.find('window.__APOLLO_STATE__ = ') + len('window.__APOLLO_STATE__ = ')
                    end = script_content.find('</script>', start)
                    if end == -1:
                        end = len(script_content)

                    json_str = script_content[start:end].strip()
                    if json_str.endswith(';'):
                        json_str = json_str[:-1]

                    import json
                    apollo_data = json.loads(json_str)
                    break

            if not apollo_data:
                return []

            # Extract posts from search results
            articles = []
            root_query = apollo_data.get('ROOT_QUERY', {})

            # Look for search results - try multiple patterns
            for key, value in root_query.items():
                if key.startswith('search(') and isinstance(value, dict):
                    search_ref = value.get('__ref')
                    if search_ref and search_ref in apollo_data:
                        search_data = apollo_data[search_ref]

                        # Look for posts in search data
                        for search_key, search_value in search_data.items():
                            if 'posts-' in search_key and isinstance(search_value, dict):
                                items = search_value.get('items', [])
                                for item in items:
                                    if isinstance(item, dict) and '__ref' in item:
                                        post_ref = item['__ref']
                                        if post_ref in apollo_data:
                                            post_data = apollo_data[post_ref]
                                            article_info = self._parse_apollo_post(post_data, apollo_data)
                                            if article_info:
                                                articles.append(article_info)

            # Also look for posts directly in apollo_data (fallback)
            if len(articles) < 20:  # If we don't have enough articles, try direct approach
                for key, value in apollo_data.items():
                    if key.startswith('Post:') and isinstance(value, dict):
                        article_info = self._parse_apollo_post(value, apollo_data)
                        if article_info and article_info not in articles:
                            articles.append(article_info)
                            if len(articles) >= 50:  # Reasonable limit
                                break

            return articles

        except Exception as e:
            logger.warning(f"Failed to extract from Apollo state: {e}")
            return []

    def _parse_apollo_post(self, post_data: dict, apollo_data: dict) -> Optional[ArticleInfo]:
        """Parse post data from Apollo state."""
        try:
            title = post_data.get('title', 'Unknown Title')
            url = post_data.get('mediumUrl', '')

            # Extract author
            author = "Unknown Author"
            creator_ref = post_data.get('creator', {})
            if isinstance(creator_ref, dict) and '__ref' in creator_ref:
                creator_data = apollo_data.get(creator_ref['__ref'], {})
                author = creator_data.get('name', 'Unknown Author')

            # Extract summary
            summary = ""
            preview_content = post_data.get('extendedPreviewContent', {})
            if preview_content:
                summary = preview_content.get('subtitle', '')

            # Extract metrics
            claps = post_data.get('clapCount', 0)
            responses = post_data.get('postResponses', {}).get('count', 0)
            reading_time = post_data.get('readingTime', 0)

            # Extract publish date
            publish_date = None
            first_published = post_data.get('firstPublishedAt')
            if first_published:
                from datetime import datetime
                publish_date = datetime.fromtimestamp(first_published / 1000)

            article_info = ArticleInfo(
                title=title,
                url=url,
                author=author,
                summary=summary,
                publish_date=publish_date,
                platform="medium"
            )

            # Add metrics to metadata
            metrics = {
                'claps': claps,
                'responses': responses,
                'reading_time': int(reading_time),
                'source': 'apollo_state'
            }

            article_info.metadata = {
                **metrics,
                'quality_score': self._calculate_quality_score(metrics, publish_date)
            }

            return article_info

        except Exception as e:
            logger.warning(f"Failed to parse Apollo post: {e}")
            return None

    def _is_valid_article_element(self, element) -> bool:
        """Check if element is a valid article element."""
        # Must contain a title-like element
        title_selectors = ['h1', 'h2', 'h3', 'h4', '[data-testid*="title"]', '.title']
        has_title = any(element.select(selector) for selector in title_selectors)

        # Must contain a link to an article
        links = element.find_all('a', href=True)
        has_article_link = any(
            self._is_medium_article_url(link['href'])
            for link in links
        )

        # Should not be navigation or footer elements
        text = element.get_text().lower()
        is_nav = any(nav_word in text for nav_word in ['navigation', 'footer', 'header', 'menu'])

        return has_title and has_article_link and not is_nav

    def _is_medium_article_url(self, url: str) -> bool:
        """Check if URL is a Medium article URL."""
        if not url:
            return False

        # Medium article patterns
        patterns = [
            r'medium\.com/@[\w\-\.]+/[\w\-]+',  # @username/article-title
            r'medium\.com/[\w\-]+/[\w\-]+',     # publication/article-title
            r'[\w\-]+\.medium\.com/[\w\-]+',    # subdomain.medium.com/article
            r'medium\.com/p/[a-f0-9]+',         # medium.com/p/hash
        ]

        import re
        return any(re.search(pattern, url) for pattern in patterns)

    def _find_article_links_fallback(self, soup: BeautifulSoup) -> List:
        """Fallback method to find article links."""
        elements = []

        # Find all links that look like Medium articles
        all_links = soup.find_all('a', href=True)
        article_links = [
            link for link in all_links
            if self._is_medium_article_url(link['href'])
        ]

        # Group links by their parent containers
        containers = {}
        for link in article_links:
            # Find the closest container that might represent an article
            container = link.find_parent(['div', 'article', 'section'])
            if container and container not in containers:
                containers[container] = link

        # Return unique containers
        elements = list(containers.keys())
        logger.info(f"Fallback found {len(elements)} potential article containers")

        return elements

    def _parse_search_result_with_metrics(self, element) -> Optional[ArticleInfo]:
        """Parse search result element with engagement metrics."""
        try:
            # Extract title
            title_elem = self._find_title_element(element)
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

            # Extract URL
            url = self._extract_article_url(element)
            if not url:
                return None

            # Extract author
            author = self._extract_author_from_search(element)

            # Extract summary/subtitle
            summary = self._extract_summary_from_search(element)

            # Extract engagement metrics
            metrics = self._extract_engagement_metrics(element)

            # Extract publish date
            publish_date = self._extract_publish_date_from_search(element)

            article_info = ArticleInfo(
                title=title,
                url=url,
                author=author,
                summary=summary,
                publish_date=publish_date,
                platform="medium"
            )

            # Add metrics to metadata
            article_info.metadata = {
                'claps': metrics.get('claps', 0),
                'responses': metrics.get('responses', 0),
                'reading_time': metrics.get('reading_time', 0),
                'quality_score': self._calculate_quality_score(metrics, publish_date)
            }

            return article_info

        except Exception as e:
            logger.warning(f"Failed to parse search result with metrics: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        # Try multiple selectors for title
        selectors = [
            'h1',
            '[data-testid="storyTitle"]',
            '.graf--title',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 5:  # Basic validation
                    return title
        
        return "Unknown Title"
    
    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content."""
        # Try multiple selectors for content
        selectors = [
            'article',
            '[data-testid="storyContent"]',
            '.postArticle-content',
            '.section-content',
            'main'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Remove unwanted elements
                for unwanted in element.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    unwanted.decompose()
                
                # Extract text content
                content = element.get_text(separator='\n', strip=True)
                if content and len(content) > 100:  # Basic validation
                    return content
        
        # Fallback: get all paragraph text
        paragraphs = soup.find_all('p')
        content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        return content or "Content extraction failed"
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author."""
        selectors = [
            '[data-testid="authorName"]',
            '.author-name',
            '[rel="author"]',
            '.byline-name'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text(strip=True)
                if author:
                    return author
        
        return None
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract article publish date."""
        selectors = [
            '[data-testid="storyPublishDate"]',
            'time[datetime]',
            '.published-date',
            '[datetime]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Try to get datetime attribute first
                date_str = element.get('datetime') or element.get_text(strip=True)
                if date_str:
                    try:
                        # Parse various date formats
                        return self._parse_date(date_str)
                    except Exception:
                        continue
        
        return None
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags."""
        tags = []
        
        # Try multiple selectors for tags
        selectors = [
            '.tag',
            '.tags a',
            '[data-testid="tag"]',
            '.topic-tag'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                tag = element.get_text(strip=True)
                if tag and tag not in tags:
                    tags.append(tag)
        
        return tags[:10]  # Limit to 10 tags
    
    def _find_title_element(self, element):
        """Find title element in article."""
        selectors = ['h2', 'h3', 'h1', '[data-testid="post-preview-title"]', '.graf--title']
        for selector in selectors:
            title_elem = element.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                return title_elem
        return None

    def _extract_article_url(self, element) -> Optional[str]:
        """Extract article URL from element."""
        # Look for links that point to Medium articles
        links = element.find_all('a', href=True)

        for link in links:
            href = link['href']

            # Skip non-article URLs
            if any(skip in href for skip in [
                'signin', 'signup', 'login', 'register',
                'sitemap', 'search', 'about', 'help',
                'privacy', 'terms', 'contact'
            ]):
                continue

            # Check if it's a valid Medium article URL
            if self._is_medium_article_url(href):
                # Normalize URL
                if href.startswith('/'):
                    return f"https://medium.com{href}"
                elif href.startswith('//'):
                    return f"https:{href}"
                else:
                    return href

        return None

    def _extract_author_from_search(self, element) -> Optional[str]:
        """Extract author from search result."""
        selectors = [
            'a[rel="author"]',
            '[data-testid="authorName"]',
            '.author-name',
            'a[href*="@"]'
        ]

        for selector in selectors:
            author_elem = element.select_one(selector)
            if author_elem:
                author = author_elem.get_text(strip=True)
                if author and len(author) > 1:
                    return author
        return None

    def _extract_summary_from_search(self, element) -> Optional[str]:
        """Extract summary from search result."""
        selectors = [
            '[data-testid="post-preview-content"]',
            '.graf--p',
            'p',
            '.subtitle'
        ]

        for selector in selectors:
            summary_elem = element.select_one(selector)
            if summary_elem:
                summary = summary_elem.get_text(strip=True)
                if summary and len(summary) > 20:  # Meaningful summary
                    return summary[:200] + '...' if len(summary) > 200 else summary
        return None

    def _extract_engagement_metrics(self, element) -> Dict[str, int]:
        """Extract claps, responses, and reading time."""
        metrics = {'claps': 0, 'responses': 0, 'reading_time': 0}

        # Extract claps (likes)
        clap_patterns = [
            r'(\d+(?:\.\d+)?[kK]?)\s*clap',
            r'(\d+(?:\.\d+)?[kK]?)\s*👏',
            r'clap.*?(\d+(?:\.\d+)?[kK]?)',
        ]

        # Extract responses (comments)
        response_patterns = [
            r'(\d+(?:\.\d+)?[kK]?)\s*response',
            r'(\d+(?:\.\d+)?[kK]?)\s*comment',
            r'response.*?(\d+(?:\.\d+)?[kK]?)',
        ]

        # Extract reading time
        reading_time_patterns = [
            r'(\d+)\s*min\s*read',
            r'(\d+)\s*minute',
            r'read.*?(\d+)\s*min',
        ]

        text_content = element.get_text()

        # Parse claps
        for pattern in clap_patterns:
            import re
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                metrics['claps'] = self._parse_number_with_k(match.group(1))
                break

        # Parse responses
        for pattern in response_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                metrics['responses'] = self._parse_number_with_k(match.group(1))
                break

        # Parse reading time
        for pattern in reading_time_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                metrics['reading_time'] = int(match.group(1))
                break

        return metrics

    def _parse_number_with_k(self, num_str: str) -> int:
        """Parse number string that might contain 'k' suffix."""
        try:
            num_str = num_str.lower().strip()
            if 'k' in num_str:
                return int(float(num_str.replace('k', '')) * 1000)
            return int(float(num_str))
        except:
            return 0

    def _extract_publish_date_from_search(self, element) -> Optional[datetime]:
        """Extract publish date from search result."""
        selectors = [
            'time[datetime]',
            '[data-testid="storyPublishDate"]',
            '.published-date'
        ]

        for selector in selectors:
            date_elem = element.select_one(selector)
            if date_elem:
                date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                if date_str:
                    return self._parse_date(date_str)

        # Try to extract relative dates like "3 days ago"
        text = element.get_text()
        import re
        relative_patterns = [
            r'(\d+)\s*day[s]?\s*ago',
            r'(\d+)\s*hour[s]?\s*ago',
            r'(\d+)\s*week[s]?\s*ago',
            r'(\d+)\s*month[s]?\s*ago'
        ]

        for pattern in relative_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_relative_date(match.group(0))

        return None

    def _parse_relative_date(self, relative_str: str) -> datetime:
        """Parse relative date string to datetime."""
        from datetime import timedelta
        import re

        now = datetime.now()

        if 'hour' in relative_str:
            hours = int(re.search(r'(\d+)', relative_str).group(1))
            return now - timedelta(hours=hours)
        elif 'day' in relative_str:
            days = int(re.search(r'(\d+)', relative_str).group(1))
            return now - timedelta(days=days)
        elif 'week' in relative_str:
            weeks = int(re.search(r'(\d+)', relative_str).group(1))
            return now - timedelta(weeks=weeks)
        elif 'month' in relative_str:
            months = int(re.search(r'(\d+)', relative_str).group(1))
            return now - timedelta(days=months * 30)

        return now

    def _calculate_quality_score(self, metrics: Dict[str, int], publish_date: Optional[datetime]) -> float:
        """Calculate quality score based on engagement and recency."""
        score = 0.0

        # Engagement score (40% of total)
        claps = metrics.get('claps', 0)
        responses = metrics.get('responses', 0)

        # Normalize engagement (logarithmic scale to handle viral posts)
        import math
        engagement_score = (math.log10(claps + 1) * 10 + math.log10(responses + 1) * 15) * 0.4
        score += min(engagement_score, 40)  # Cap at 40 points

        # Recency score (30% of total)
        if publish_date:
            try:
                # Handle timezone-aware vs timezone-naive datetime comparison
                now = datetime.now()
                if publish_date.tzinfo is not None:
                    # If publish_date is timezone-aware, make now timezone-aware too
                    from datetime import timezone
                    now = datetime.now(timezone.utc)
                    if publish_date.tzinfo != timezone.utc:
                        # Convert to UTC for comparison
                        publish_date = publish_date.astimezone(timezone.utc)
                elif now.tzinfo is not None:
                    # If now is timezone-aware but publish_date is not, make publish_date aware
                    from datetime import timezone
                    publish_date = publish_date.replace(tzinfo=timezone.utc)

                days_old = (now - publish_date).days
                if days_old <= 7:
                    recency_score = 30  # Recent articles get full points
                elif days_old <= 30:
                    recency_score = 25  # Month-old articles
                elif days_old <= 90:
                    recency_score = 15  # Quarter-old articles
                else:
                    recency_score = 5   # Older articles
                score += recency_score
            except Exception as e:
                logger.warning(f"Error calculating recency score: {e}")
                score += 15  # Default score if calculation fails
        else:
            score += 15  # Default score if no date

        # Reading time score (20% of total)
        reading_time = metrics.get('reading_time', 0)
        if 3 <= reading_time <= 15:  # Sweet spot for reading time
            score += 20
        elif 1 <= reading_time <= 20:
            score += 15
        else:
            score += 10

        # Content quality indicators (10% of total)
        # This is a placeholder - could be enhanced with NLP analysis
        score += 10

        return min(score, 100)  # Cap at 100

    def _rank_articles_by_quality(self, articles: List[ArticleInfo]) -> List[ArticleInfo]:
        """Rank articles by quality score."""
        return sorted(articles,
                     key=lambda x: x.metadata.get('quality_score', 0) if hasattr(x, 'metadata') and x.metadata else 0,
                     reverse=True)

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        try:
            import dateutil.parser
            return dateutil.parser.parse(date_str)
        except Exception:
            # Fallback parsing
            return datetime.now()

    def _extract_title_from_freedium(self, soup: BeautifulSoup) -> str:
        """Extract title from Freedium page."""
        selectors = [
            'h1.graf--title',
            'h1[data-testid="storyTitle"]',
            'h1.p-name',
            'h1',
            '.post-title',
            'title'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 5 and 'Freedium' not in title:
                    return title

        return "Unknown Title"

    def _extract_content_from_freedium(self, soup: BeautifulSoup) -> str:
        """Extract main content from Freedium page."""
        # Freedium typically preserves Medium's article structure
        selectors = [
            'article',
            '.postArticle-content',
            '.section-content',
            '.post-content',
            'main',
            '[data-testid="storyContent"]'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Remove unwanted elements
                for unwanted in element.find_all(['script', 'style', 'nav', 'header', 'footer', '.sidebar', '.related-posts']):
                    unwanted.decompose()

                # Extract text content with proper formatting
                content = self._extract_formatted_text(element)
                if content and len(content) > 100:
                    return content

        # Fallback: extract all paragraphs
        paragraphs = soup.find_all('p')
        content_parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Filter out short/empty paragraphs
                content_parts.append(text)

        content = '\n\n'.join(content_parts)
        return content if content else "Content extraction failed"

    def _extract_formatted_text(self, element) -> str:
        """Extract text with basic formatting preserved."""
        content_parts = []

        # Process different elements to maintain structure
        for child in element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote']):
            text = child.get_text(strip=True)
            if text:
                if child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    content_parts.append(f"\n## {text}\n")
                elif child.name == 'blockquote':
                    content_parts.append(f"\n> {text}\n")
                elif child.name == 'li':
                    content_parts.append(f"• {text}")
                else:
                    content_parts.append(text)

        return '\n\n'.join(content_parts)

    def _extract_author_from_freedium(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from Freedium page."""
        selectors = [
            '[data-testid="authorName"]',
            '.author-name',
            '[rel="author"]',
            '.byline-name',
            '.p-author',
            'a[href*="@"]'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text(strip=True)
                if author and len(author) > 1:
                    return author

        return None

    def _extract_publish_date_from_freedium(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract publish date from Freedium page."""
        selectors = [
            'time[datetime]',
            '[data-testid="storyPublishDate"]',
            '.published-date',
            '.post-date'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                date_str = element.get('datetime') or element.get_text(strip=True)
                if date_str:
                    try:
                        return self._parse_date(date_str)
                    except Exception:
                        continue

        return None

    def _extract_tags_from_freedium(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags from Freedium page."""
        tags = []

        selectors = [
            '.tag',
            '.tags a',
            '[data-testid="tag"]',
            '.topic-tag',
            'a[href*="/tag/"]'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                tag = element.get_text(strip=True)
                if tag and tag not in tags:
                    tags.append(tag)

        return tags[:10]  # Limit to 10 tags
