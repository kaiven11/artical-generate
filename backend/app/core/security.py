"""
Security utilities for the article migration tool.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from jose import JWTError, jwt
import logging

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption key for sensitive data
ENCRYPTION_KEY = settings.secret_key.encode()[:32].ljust(32, b'0')
cipher_suite = Fernet(Fernet.generate_key())


class SecurityManager:
    """Security management utilities."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize security manager.
        
        Args:
            encryption_key: Optional encryption key, uses default if not provided
        """
        if encryption_key:
            key = encryption_key.encode()[:32].ljust(32, b'0')
            self.cipher = Fernet(Fernet.generate_key())
        else:
            self.cipher = cipher_suite
    
    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt API key for secure storage.
        
        Args:
            api_key: Plain text API key
            
        Returns:
            str: Encrypted API key
        """
        try:
            encrypted = self.cipher.encrypt(api_key.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {e}")
            raise
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt API key for use.
        
        Args:
            encrypted_key: Encrypted API key
            
        Returns:
            str: Plain text API key
        """
        try:
            decrypted = self.cipher.decrypt(encrypted_key.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            raise
    
    def hash_content(self, content: str) -> str:
        """
        Generate hash for content deduplication.
        
        Args:
            content: Content to hash
            
        Returns:
            str: SHA256 hash of content
        """
        return hashlib.sha256(content.encode()).hexdigest()
    
    def generate_session_token(self) -> str:
        """
        Generate secure session token.
        
        Returns:
            str: Random session token
        """
        return secrets.token_urlsafe(32)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            bool: True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash password for storage.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Data to encode in token
            expires_delta: Token expiration time
            
        Returns:
            str: JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            dict: Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file operations.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        import re
        # Remove or replace dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        return sanitized
    
    def validate_url(self, url: str) -> bool:
        """
        Validate URL format and safety.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is valid and safe
        """
        import re
        from urllib.parse import urlparse
        
        try:
            # Basic URL format validation
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False
            
            # Check for allowed schemes
            if result.scheme not in ['http', 'https']:
                return False
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'javascript:',
                r'data:',
                r'file:',
                r'ftp:',
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"URL validation failed: {e}")
            return False


# Global security manager instance
security_manager = SecurityManager()


def get_security_manager() -> SecurityManager:
    """Get security manager instance."""
    return security_manager
