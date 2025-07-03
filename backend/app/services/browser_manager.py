"""
Browser manager for handling fingerprint browser sessions and anti-detection.
"""

import asyncio
import logging
import random
import secrets
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from ..core.config import get_browser_config

logger = logging.getLogger(__name__)


@dataclass
class BrowserProfile:
    """Browser profile configuration."""
    id: int
    name: str
    user_agent: str
    screen_resolution: str
    timezone: str
    language: str
    proxy_config: Dict[str, Any]
    fingerprint_config: Dict[str, Any]
    is_active: bool = True
    last_used_at: Optional[datetime] = None


@dataclass
class BrowserSession:
    """Browser session information."""
    id: str
    profile_id: int
    created_at: datetime
    last_activity_at: datetime
    is_active: bool = True
    page_instance: Any = None  # DrissionPage instance


class FingerprintGenerator:
    """Generate random browser fingerprints for anti-detection."""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ]
        
        self.screen_resolutions = [
            "1920x1080", "1366x768", "1440x900", "1536x864", "1280x720"
        ]
        
        self.timezones = [
            "Asia/Shanghai", "America/New_York", "Europe/London", 
            "Asia/Tokyo", "Europe/Paris", "America/Los_Angeles"
        ]
        
        self.languages = [
            "zh-CN,zh;q=0.9,en;q=0.8",
            "en-US,en;q=0.9",
            "zh-CN,zh;q=0.9",
            "en-GB,en;q=0.9"
        ]
    
    def generate_fingerprint(self, seed: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate random browser fingerprint.
        
        Args:
            seed: Optional seed for reproducible fingerprints
            
        Returns:
            Dict containing fingerprint configuration
        """
        if seed:
            random.seed(seed)
        
        return {
            "user_agent": random.choice(self.user_agents),
            "screen_resolution": random.choice(self.screen_resolutions),
            "timezone": random.choice(self.timezones),
            "language": random.choice(self.languages),
            "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
            "hardware_concurrency": random.choice([4, 6, 8, 12, 16]),
            "device_memory": random.choice([4, 8, 16, 32]),
            "color_depth": random.choice([24, 30, 32]),
            "pixel_ratio": random.choice([1, 1.25, 1.5, 2]),
        }


class BrowserManager:
    """Browser manager for handling fingerprint browser sessions."""
    
    def __init__(self, chrome_path: Optional[str] = None, user_data_dir: Optional[str] = None):
        """
        Initialize browser manager.
        
        Args:
            chrome_path: Path to fingerprint chromium executable
            user_data_dir: User data directory for browser profiles
        """
        self.config = get_browser_config()
        self.chrome_path = chrome_path or self.config.chrome_path
        self.user_data_dir = user_data_dir or self.config.user_data_directory
        
        self.sessions: Dict[str, BrowserSession] = {}
        self.profiles: List[BrowserProfile] = []
        self.fingerprint_generator = FingerprintGenerator()
        
        # Session management
        self.max_sessions = 5
        self.session_timeout = timedelta(hours=2)
        
        # Initialize default profiles
        self._initialize_default_profiles()
    
    def _initialize_default_profiles(self):
        """Initialize default browser profiles."""
        for i in range(3):  # Create 3 default profiles
            fingerprint = self.fingerprint_generator.generate_fingerprint()
            profile = BrowserProfile(
                id=i + 1,
                name=f"Profile_{i + 1}",
                user_agent=fingerprint["user_agent"],
                screen_resolution=fingerprint["screen_resolution"],
                timezone=fingerprint["timezone"],
                language=fingerprint["language"],
                proxy_config={},
                fingerprint_config=fingerprint
            )
            self.profiles.append(profile)
    
    async def create_session(self, profile_id: Optional[int] = None) -> BrowserSession:
        """
        Create a new browser session.
        
        Args:
            profile_id: Optional profile ID, uses random if not specified
            
        Returns:
            BrowserSession: Created session
        """
        try:
            # Clean up expired sessions
            await self._cleanup_expired_sessions()
            
            # Check session limit
            if len(self.sessions) >= self.max_sessions:
                await self._cleanup_oldest_session()
            
            # Select profile
            if profile_id is None:
                profile = random.choice(self.profiles)
            else:
                profile = next((p for p in self.profiles if p.id == profile_id), None)
                if not profile:
                    raise ValueError(f"Profile {profile_id} not found")
            
            # Generate session ID
            session_id = secrets.token_urlsafe(16)
            
            # Create DrissionPage instance
            page_instance = await self._create_page_instance(profile)
            
            # Create session
            session = BrowserSession(
                id=session_id,
                profile_id=profile.id,
                created_at=datetime.utcnow(),
                last_activity_at=datetime.utcnow(),
                page_instance=page_instance
            )
            
            self.sessions[session_id] = session
            profile.last_used_at = datetime.utcnow()
            
            logger.info(f"Created browser session {session_id} with profile {profile.id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create browser session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[BrowserSession]:
        """
        Get browser session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            BrowserSession or None if not found
        """
        session = self.sessions.get(session_id)
        if session and session.is_active:
            session.last_activity_at = datetime.utcnow()
            return session
        return None
    
    async def close_session(self, session_id: str) -> bool:
        """
        Close browser session.
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if session was closed
        """
        try:
            session = self.sessions.get(session_id)
            if session:
                # Close page instance
                if session.page_instance:
                    try:
                        session.page_instance.quit()
                    except Exception as e:
                        logger.warning(f"Error closing page instance: {e}")
                
                # Remove session
                session.is_active = False
                del self.sessions[session_id]
                
                logger.info(f"Closed browser session {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to close session {session_id}: {e}")
            return False
    
    async def randomize_fingerprint(self, profile_id: int) -> bool:
        """
        Randomize fingerprint for a profile.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            bool: True if fingerprint was randomized
        """
        try:
            profile = next((p for p in self.profiles if p.id == profile_id), None)
            if not profile:
                return False
            
            # Generate new fingerprint
            new_fingerprint = self.fingerprint_generator.generate_fingerprint()
            
            # Update profile
            profile.user_agent = new_fingerprint["user_agent"]
            profile.screen_resolution = new_fingerprint["screen_resolution"]
            profile.timezone = new_fingerprint["timezone"]
            profile.language = new_fingerprint["language"]
            profile.fingerprint_config = new_fingerprint
            
            logger.info(f"Randomized fingerprint for profile {profile_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to randomize fingerprint: {e}")
            return False
    
    async def _create_page_instance(self, profile: BrowserProfile):
        """Create DrissionPage instance with fingerprint configuration."""
        try:
            # Import DrissionPage
            from DrissionPage import ChromiumPage, ChromiumOptions
            
            # Configure ChromiumOptions
            options = ChromiumOptions()
            
            # Set browser path if available
            if self.chrome_path:
                options.set_browser_path(self.chrome_path)
            
            # Set user data directory
            if self.user_data_dir:
                options.set_user_data_path(f"{self.user_data_dir}/profile_{profile.id}")
            
            # Basic fingerprint configuration
            fingerprint_seed = f"profile_{profile.id}_{int(time.time())}"
            options.set_argument(f"--fingerprint={fingerprint_seed}")
            
            # Platform and browser configuration
            options.set_argument("--fingerprint-platform=windows")
            options.set_argument("--fingerprint-brand=Chrome")
            options.set_argument(f"--lang={profile.language.split(',')[0]}")
            options.set_argument(f"--timezone={profile.timezone}")
            
            # Window size
            width, height = profile.screen_resolution.split('x')
            options.set_argument(f"--window-size={width},{height}")
            
            # Proxy configuration
            if profile.proxy_config and profile.proxy_config.get("enabled"):
                proxy_url = profile.proxy_config.get("url")
                if proxy_url:
                    options.set_argument(f"--proxy-server={proxy_url}")
            
            # Anti-detection arguments
            options.set_argument("--disable-blink-features=AutomationControlled")
            options.set_argument("--disable-dev-shm-usage")
            options.set_argument("--no-sandbox")
            options.set_argument("--disable-web-security")
            options.set_argument("--disable-features=VizDisplayCompositor")
            
            # Force visible mode for observation - NEVER use headless
            # options.set_argument("--headless=new")  # Commented out to ensure visible mode
            # Explicitly disable any headless flags
            options.set_argument("--no-headless")
            
            # Create page instance
            page = ChromiumPage(addr_or_opts=options)
            
            # Apply additional fingerprint settings
            await self._apply_fingerprint_settings(page, profile)
            
            return page
            
        except ImportError:
            logger.error("DrissionPage not installed. Please install: pip install DrissionPage")
            raise
        except Exception as e:
            logger.error(f"Failed to create page instance: {e}")
            raise
    
    async def _apply_fingerprint_settings(self, page, profile: BrowserProfile):
        """Apply fingerprint settings to page instance."""
        try:
            # Override navigator properties
            fingerprint_script = f"""
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined
            }});
            
            Object.defineProperty(navigator, 'userAgent', {{
                get: () => '{profile.user_agent}'
            }});
            
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{profile.fingerprint_config.get("platform", "Win32")}'
            }});
            
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {profile.fingerprint_config.get("hardware_concurrency", 8)}
            }});
            
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {profile.fingerprint_config.get("device_memory", 8)}
            }});
            
            Object.defineProperty(screen, 'colorDepth', {{
                get: () => {profile.fingerprint_config.get("color_depth", 24)}
            }});
            
            Object.defineProperty(window, 'devicePixelRatio', {{
                get: () => {profile.fingerprint_config.get("pixel_ratio", 1)}
            }});
            """
            
            page.run_js(fingerprint_script)
            
        except Exception as e:
            logger.warning(f"Failed to apply fingerprint settings: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_activity_at > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.close_session(session_id)
    
    async def _cleanup_oldest_session(self):
        """Clean up the oldest session to make room for new ones."""
        if not self.sessions:
            return
        
        oldest_session_id = min(
            self.sessions.keys(),
            key=lambda sid: self.sessions[sid].created_at
        )
        await self.close_session(oldest_session_id)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        active_sessions = len([s for s in self.sessions.values() if s.is_active])
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": active_sessions,
            "max_sessions": self.max_sessions,
            "profiles_count": len(self.profiles),
            "session_timeout_hours": self.session_timeout.total_seconds() / 3600
        }


# Global browser manager instance
browser_manager = BrowserManager()


def get_browser_manager() -> BrowserManager:
    """Get browser manager instance."""
    return browser_manager
