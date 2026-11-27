class ProviderError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = False,
        status_code: int | None = None,
        retry_after_seconds: float | None = None,
        fallback_allowed: bool = True,
        provider: str | None = None,
        provider_error_code: str | None = None,
        provider_error_type: str | None = None,
        provider_request_id: str | None = None,
        provider_message: str | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds
        self.fallback_allowed = fallback_allowed
        self.provider = provider
        self.provider_error_code = provider_error_code
        self.provider_error_type = provider_error_type
        self.provider_request_id = provider_request_id
        self.provider_message = provider_message


class NoProviderAvailable(ProviderError):
    def __init__(self):
        super().__init__(
            "NO_PROVIDER_AVAILABLE",
            "No configured provider can satisfy this request.",
            fallback_allowed=False,
        )
