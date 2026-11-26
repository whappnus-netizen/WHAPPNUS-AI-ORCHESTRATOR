class ProviderError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False, status_code: int | None = None):
        super().__init__(message)
        self.code, self.message, self.retryable, self.status_code = code, message, retryable, status_code


class NoProviderAvailable(ProviderError):
    def __init__(self):
        super().__init__('NO_PROVIDER_AVAILABLE', 'No configured provider can satisfy this request.')
