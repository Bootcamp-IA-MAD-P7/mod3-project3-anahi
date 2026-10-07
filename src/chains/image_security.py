from collections import defaultdict
from datetime import datetime, timedelta

MAX_IMAGES_PER_USER_PER_DAY = 5
MAX_IMAGES_PER_MINUTE = 2
_ACCOUNT_MAX_IMAGES_PER_DAY = 100


_user_image_log: dict[str, list[datetime]] = defaultdict(list)
_account_image_count: int = 0


class ImageRateLimitError(Exception):
    pass


class ImageAccountLimitError(Exception):
    pass


class ImageLimitWarning(Exception):
    pass


def _clean_old_image_requests(user_id: str) -> None:
    cutoff = datetime.now() - timedelta(days=1)
    _user_image_log[user_id] = [t for t in _user_image_log[user_id] if t > cutoff]


def check_image_rate_limit(user_id: str, bypass_limits: bool = False) -> None:
    if bypass_limits:
        return
    _clean_old_image_requests(user_id)
    now = datetime.now()

    one_minute_ago = now - timedelta(minutes=1)
    recent = [t for t in _user_image_log[user_id] if t > one_minute_ago]
    if len(recent) >= MAX_IMAGES_PER_MINUTE:
        raise ImageRateLimitError(
            f"You've reached the limit of {MAX_IMAGES_PER_MINUTE} "
            "image generations per minute"
            " Please wait before trying again"
        )

    if len(_user_image_log[user_id]) >= MAX_IMAGES_PER_USER_PER_DAY:
        raise ImageRateLimitError("You've reached your daily image limit")


def check_account_limit() -> None:
    if _account_image_count >= _ACCOUNT_MAX_IMAGES_PER_DAY:
        raise ImageAccountLimitError("Account daily image quota exhausted")


def register_image_request(user_id: str) -> bool:
    global _account_image_count
    _user_image_log[user_id].append(datetime.now())
    _account_image_count += 1
    return len(_user_image_log[user_id]) == MAX_IMAGES_PER_USER_PER_DAY
