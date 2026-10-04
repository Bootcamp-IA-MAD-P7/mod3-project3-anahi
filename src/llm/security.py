from collections import defaultdict
from datetime import datetime, timedelta

MAX_REQUESTS_PER_MINUTE = 5
MAX_REQUESTS_PER_DAY = 200
MAX_TOKENS_PER_CALL = 2000
MAX_TOKENS_PER_DAY = 20000
TIMEOUT_SECONDS = 40


_request_log: dict[str, list[datetime]] = defaultdict(list)
_token_log: dict[str, int] = defaultdict(int)


class RateLimitError(Exception):
    pass


class TokenLimitError(Exception):
    pass


def _clean_old_requests(user_id: str) -> None:
    cutoff = datetime.now() - timedelta(days=1)
    _request_log[user_id] = [t for t in _request_log[user_id] if t > cutoff]


def check_rate_limit(user_id: str, bypass_limits: bool = False) -> None:
    if bypass_limits:
        return
    _clean_old_requests(user_id)
    now = datetime.now()

    one_minute_ago = now - timedelta(minutes=1)
    recent_requests = [t for t in _request_log[user_id] if t > one_minute_ago]
    if len(recent_requests) >= MAX_REQUESTS_PER_MINUTE:
        raise RateLimitError(
            f"You've reached the limit of {MAX_REQUESTS_PER_MINUTE} requests per minute"
            ". Please wait a moment before trying again"
        )

    if len(_request_log[user_id]) >= MAX_REQUESTS_PER_DAY:
        raise RateLimitError(
            f"You've reached the daily limit of {MAX_REQUESTS_PER_DAY} requests"
            ". Please try again tomorrow"
        )


def check_token_limit(
    user_id: str, tokens_to_use: int, bypass_limits: bool = False
) -> None:
    if bypass_limits:
        return
    if tokens_to_use > MAX_TOKENS_PER_CALL:
        raise TokenLimitError(
            f"Requested {tokens_to_use} tokens exceeds the per-call limit"
            f" of {MAX_TOKENS_PER_CALL}"
        )

    if _token_log[user_id] + tokens_to_use > MAX_TOKENS_PER_DAY:
        remaining = MAX_TOKENS_PER_DAY - _token_log[user_id]
        raise TokenLimitError(
            f"This request would exceed your daily token limit"
            f". You have {remaining} tokens remaining today"
        )


def register_request(user_id: str, tokens_used: int) -> None:
    _request_log[user_id].append(datetime.now())
    _token_log[user_id] += tokens_used


def get_user_stats(user_id: str) -> dict:
    _clean_old_requests(user_id)
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)
    recent = [t for t in _request_log[user_id] if t > one_minute_ago]

    stats = {
        "requests_this_minute": len(recent),
        "requests_today": len(_request_log[user_id]),
    }
    if _token_log[user_id] > 0:
        stats["tokens_used_today"] = _token_log[user_id]
        stats["tokens_remaining_today"] = MAX_TOKENS_PER_DAY - _token_log[user_id]
    return stats
