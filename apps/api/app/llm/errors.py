class LLMError(Exception):
    error_type = "unknown_error"
    retryable = False

    def __init__(self, message: str, *, retryable: bool | None = None):
        super().__init__(message)
        if retryable is not None:
            self.retryable = retryable


class ProviderTimeoutError(LLMError):
    error_type = "provider_timeout"
    retryable = True


class ProviderRateLimitError(LLMError):
    error_type = "provider_rate_limit"
    retryable = True


class ProviderAuthError(LLMError):
    error_type = "provider_auth_error"


class ProviderServerError(LLMError):
    error_type = "provider_server_error"
    retryable = True


class InvalidRequestError(LLMError):
    error_type = "invalid_request"


class StreamInterruptedError(LLMError):
    error_type = "stream_interrupted"
    retryable = True


class UserCancelledError(LLMError):
    error_type = "user_cancelled"


def normalize_exception(exc: Exception) -> tuple[str, str, bool]:
    if isinstance(exc, LLMError):
        return exc.error_type, str(exc), exc.retryable
    return "unknown_error", str(exc), False

