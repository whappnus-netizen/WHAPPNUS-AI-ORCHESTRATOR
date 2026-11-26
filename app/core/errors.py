class ProviderError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False, status_code: int | None = None, retry_after_seconds: float | None = None, fallback_allowed: bool = True):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds
        self.fallback_allowed = fallback_allowed

class NoProviderAvailable(ProviderError):
    def __init__(self):
        super().__init__("NO_PROVIDER_AVAILABLE", "No configured provider can satisfy this request.", fallback_allowed=False)
