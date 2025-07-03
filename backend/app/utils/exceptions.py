"""
Custom exceptions for the article migration tool.
"""


class BaseAppException(Exception):
    """Base application exception."""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ConfigurationError(BaseAppException):
    """Configuration related errors."""
    pass


class DatabaseError(BaseAppException):
    """Database related errors."""
    pass


class APIException(BaseAppException):
    """API related exceptions."""
    pass


class TranslationException(BaseAppException):
    """Translation related exceptions."""
    pass


class DetectionException(BaseAppException):
    """Detection related exceptions."""
    pass


class PublishException(BaseAppException):
    """Publishing related exceptions."""
    pass


class BrowserException(BaseAppException):
    """Browser related exceptions."""
    pass


class AdapterException(BaseAppException):
    """Adapter related exceptions."""
    pass


class TaskException(BaseAppException):
    """Task processing exceptions."""
    pass


class ValidationError(BaseAppException):
    """Data validation errors."""
    pass


class AuthenticationError(BaseAppException):
    """Authentication errors."""
    pass


class RateLimitError(BaseAppException):
    """Rate limiting errors."""
    pass


class NetworkError(BaseAppException):
    """Network related errors."""
    pass
