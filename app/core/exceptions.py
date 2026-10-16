class AppError(Exception):
    """Base exception for expected application-level failures."""


class ProviderNotConfiguredError(AppError):
    """Raised when an external AI provider has not been configured."""
