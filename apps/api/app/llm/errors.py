import re


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


class ProviderModelInvalidError(LLMError):
    error_type = "invalid_provider_model_combo"


class ProviderModelNotFoundError(LLMError):
    error_type = "provider_invalid_model"


class ProviderNotFoundError(LLMError):
    error_type = "provider_not_found"


def sanitize_error_message(message: str) -> str:
    cleaned = message or ""
    cleaned = re.sub(r"https?://\S+", "[redacted-url]", cleaned)
    cleaned = re.sub(r"Bearer\s+[A-Za-z0-9._\-]+", "Bearer [REDACTED]", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"([?&](?:key|api_key|token)=)[^&\s]+", r"\1[REDACTED]", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"AIza[0-9A-Za-z\-_]+", "[REDACTED]", cleaned)
    cleaned = re.sub(r"sk-[A-Za-z0-9\-_.]+", "[REDACTED]", cleaned)
    return cleaned.strip()


def normalize_exception(exc: Exception) -> tuple[str, str, bool]:
    if isinstance(exc, LLMError):
        return exc.error_type, sanitize_error_message(str(exc)), exc.retryable
    return "unknown_error", sanitize_error_message(str(exc)), False
