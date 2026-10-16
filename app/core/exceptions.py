class AppError(Exception):
    """Base exception for expected application-level failures."""


class AIProviderError(AppError):
    """Raised when an AI provider request fails or returns an invalid response."""


class ProviderNotConfiguredError(AIProviderError):
    """Raised when an external AI provider has not been configured."""
