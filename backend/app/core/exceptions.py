class ConfigurationError(RuntimeError):
    """Raised when a required integration configuration is missing."""


class IntegrationError(RuntimeError):
    """Raised when an external integration fails safely."""
