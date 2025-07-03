"""
Dev.to platform adapter for article extraction.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from ..base import BaseSourceAdapter, ArticleInfo, ArticleContent, PlatformInfo, AdapterType

logger = logging.getLogger(__name__)


class DevToAdapter(BaseSourceAdapter):
    """Dev.to platform adapter for article extraction."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Dev.to adapter."""
        super().__init__(config)
        self.base_url = "https://dev.to"
        self.api_url = "https://dev.to/api"
        self.session = requests.Session()
        
        # Set headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
    
    def get_platform_info(self) -> PlatformInfo:
        """Get Dev.to platform information."""
        return PlatformInfo(
            name="devto",
            display_name="Dev.to",
            type=AdapterType.SOURCE,
            features=["search", "extract", "api", "trending"],
            requires_auth=False,
            description="Dev.to is a community of software developers getting together to help one another out",
            version="1.0.0",
            website="https://dev.to"
        )
    
    async def test_connection(self) -> bool:
        """Test connection to Dev.to."""
        try:
            response = self.session.get(f"{self.api_url}/articles", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to Dev.to: {e}")
            return False
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for Dev.to adapter."""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "Dev.to API key (optional, for higher rate limits)"
                },
                "max_articles_per_search": {
                    "type": "integer",
                    "default": 30,
                    "description": "Maximum articles to return per search"
                },
                "tags_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["ai", "machinelearning", "deeplearning", "python", "javascript"],
                    "description": "Tags to filter articles"
                }
            }
        }
    
    async def search_articles(self, keywords: List[str], limit: int = 20) -> List[ArticleInfo]:
        """
        Search for articles on Dev.to.
        
        Args:
            keywords: Search keywords
            limit: Maximum number of articles to return
            
        Returns:
            List of article information
        """
        try:
            articles = []
            
            # Use Dev.to API for search
            params = {
                'per_page': min(limit, 1000),  # Dev.to API limit
                'state': 'fresh'
            }
            
            # Add API key if available
            api_key = self.config.get('api_key')
            if api_key:
                self.session.headers['api-key'] = api_key
            
            # Search by tags if keywords match common tags
            tags_filter = self.config.get('tags_filter', [])
            matching_tags = [tag for tag in tags_filter if any(keyword.lower() in tag.lower() for keyword in keywords)]
            
            if matching_tags:
                params['tag'] = ','.join(matching_tags[:5])  # Limit to 5 tags
            
            response = self.session.get(f"{self.api_url}/articles", params=params, timeout=15)
            response.raise_for_status()
            
            articles_data = response.json()
            
            for article_data in articles_data[:limit]:
                try:
                    article_info = self._parse_api_article(article_data)
                    if article_info and self._matches_keywords(article_info, keywords):
                        articles.append(article_info)
                except Exception as e:
                    logger.warning(f"Failed to parse article data: {e}")
                    continue
            
            logger.info(f"Found {len(articles)} articles for keywords: {keywords}")
            return articles
            
        except Exception as e:
            logger.error(f"Failed to search Dev.to articles: {e}")
            return []
    
    async def extract_content(self, url: str) -> ArticleContent:
        """
        Extract content from Dev.to article URL.
        
        Args:
            url: Article URL
            
        Returns:
            Article content with metadata
        """
        try:
            # Try API first if we can extract article ID
            article_id = self._extract_article_id(url)
            if article_id:
                try:
                    return await self._extract_via_api(article_id, url)
                except Exception as e:
                    logger.warning(f"API extraction failed, falling back to web scraping: {e}")
            
            # Fallback to web scraping
            return await self._extract_via_scraping(url)
            
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {e}")
            raise
    
    async def _extract_via_api(self, article_id: str, url: str) -> ArticleContent:
        """Extract content via Dev.to API."""
        try:
            response = self.session.get(f"{self.api_url}/articles/{article_id}", timeout=30)
            response.raise_for_status()
            
            article_data = response.json()
            
            return ArticleContent(
                title=article_data.get('title', 'Unknown Title'),
                content=article_data.get('body_markdown', '') or article_data.get('body_html', ''),
                author=article_data.get('user', {}).get('name'),
                publish_date=self._parse_date(article_data.get('published_at')),
                tags=article_data.get('tag_list', []),
                category=article_data.get('type_of'),
                source_url=url,
                platform="devto",
                metadata={
                    "extraction_method": "api",
                    "article_id": article_id,
                    "reading_time_minutes": article_data.get('reading_time_minutes'),
                    "public_reactions_count": article_data.get('public_reactions_count'),
                    "comments_count": article_data.get('comments_count')
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to extract via API: {e}")
            raise
    
    async def _extract_via_scraping(self, url: str) -> ArticleContent:
        """Extract content via web scraping."""
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
                platform="devto",
                metadata={
                    "extraction_method": "scraping"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to extract via scraping: {e}")
            raise
    
    def _parse_api_article(self, article_data: Dict[str, Any]) -> Optional[ArticleInfo]:
        """Parse API article data to ArticleInfo."""
        try:
            return ArticleInfo(
                title=article_data.get('title', 'Unknown Title'),
                url=article_data.get('url', ''),
                author=article_data.get('user', {}).get('name'),
                publish_date=self._parse_date(article_data.get('published_at')),
                summary=article_data.get('description'),
                tags=article_data.get('tag_list', []),
                platform="devto"
            )
        except Exception as e:
            logger.warning(f"Failed to parse API article: {e}")
            return None
    
    def _matches_keywords(self, article: ArticleInfo, keywords: List[str]) -> bool:
        """Check if article matches search keywords."""
        text_to_search = f"{article.title} {article.summary or ''} {' '.join(article.tags or [])}"
        text_lower = text_to_search.lower()
        
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def _extract_article_id(self, url: str) -> Optional[str]:
        """Extract article ID from Dev.to URL."""
        try:
            # Dev.to URLs format: https://dev.to/username/title-id
            parts = url.rstrip('/').split('/')
            if len(parts) >= 2:
                last_part = parts[-1]
                # ID is usually at the end after the last dash
                if '-' in last_part:
                    potential_id = last_part.split('-')[-1]
                    if potential_id.isdigit():
                        return potential_id
            return None
        except Exception:
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        selectors = [
            'h1.crayons-article__header__title',
            'h1[data-article-title]',
            'h1',
            '.article-header h1',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 5:
                    return title
        
        return "Unknown Title"
    
    def _extract_article_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content."""
        selectors = [
            '#article-body',
            '.crayons-article__main',
            '.article-body',
            'article .content',
            'main article'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Remove unwanted elements
                for unwanted in element.find_all(['script', 'style', 'nav', 'header', 'footer', '.article-actions']):
                    unwanted.decompose()
                
                content = element.get_text(separator='\n', strip=True)
                if content and len(content) > 100:
                    return content
        
        # Fallback
        paragraphs = soup.find_all('p')
        content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        return content or "Content extraction failed"
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author."""
        selectors = [
            '.crayons-article__header__meta a[href*="/"]',
            '.article-author-name',
            '[data-author-name]',
            '.author-name'
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
            'time[datetime]',
            '.crayons-article__header__meta time',
            '[data-published-at]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                date_str = element.get('datetime') or element.get('data-published-at') or element.get_text(strip=True)
                if date_str:
                    try:
                        return self._parse_date(date_str)
                    except Exception:
                        continue
        
        return None
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags."""
        tags = []
        
        selectors = [
            '.crayons-tag',
            '.article-tags a',
            '[data-tag]',
            '.tag'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                tag = element.get_text(strip=True).replace('#', '')
                if tag and tag not in tags:
                    tags.append(tag)
        
        return tags[:10]
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        try:
            import dateutil.parser
            return dateutil.parser.parse(date_str)
        except Exception:
            return None
