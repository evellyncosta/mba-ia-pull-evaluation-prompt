"""
Patch local para impedir retries inúteis em erros 403 do Gemini.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

import google.api_core.exceptions
from tenacity import before_sleep_log, retry, retry_if_exception, stop_after_attempt, wait_exponential


def _should_retry_google_error(exc: BaseException) -> bool:
    """
    Permite retry apenas para falhas transitórias.
    """
    if isinstance(exc, google.api_core.exceptions.PermissionDenied):
        return False

    return isinstance(
        exc,
        (
            google.api_core.exceptions.ResourceExhausted,
            google.api_core.exceptions.ServiceUnavailable,
        ),
    )


def patch_langchain_google_genai_retry() -> None:
    """
    Substitui o decorator interno do langchain_google_genai para não repetir 403.
    """
    try:
        from langchain_google_genai import chat_models
    except Exception:
        return

    if getattr(chat_models, "_retry_patch_applied", False):
        return

    logger = logging.getLogger(chat_models.__name__)

    def _create_retry_decorator() -> Callable[[Any], Any]:
        return retry(
            reraise=True,
            stop=stop_after_attempt(2),
            wait=wait_exponential(multiplier=2, min=1, max=60),
            retry=retry_if_exception(_should_retry_google_error),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )

    chat_models._create_retry_decorator = _create_retry_decorator
    chat_models._retry_patch_applied = True
