from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.chains.image_security import (
    _ACCOUNT_MAX_IMAGES_PER_DAY,
    MAX_IMAGES_PER_MINUTE,
    MAX_IMAGES_PER_USER_PER_DAY,
    ImageAccountLimitError,
    ImageRateLimitError,
    _user_image_log,
    check_account_limit,
    check_image_rate_limit,
    register_image_request,
)


def fresh_user(prefix: str, test_name: str) -> str:
    return f"{prefix}-{test_name}"


class TestCheckImageRateLimit:
    def test_passes_under_limit(self):
        user_id = fresh_user("rate", "passes")
        check_image_rate_limit(user_id)
        check_image_rate_limit(user_id)

    def test_blocks_at_per_minute_limit(self):
        user_id = fresh_user("rate", "blocks-minute")
        for _ in range(MAX_IMAGES_PER_MINUTE):
            _user_image_log[user_id].append(datetime.now())
        with pytest.raises(ImageRateLimitError):
            check_image_rate_limit(user_id)

    def test_blocks_at_daily_limit(self):
        user_id = fresh_user("rate", "blocks-daily")
        now = datetime.now()
        _user_image_log[user_id] = [
            now - timedelta(minutes=i + 10) for i in range(MAX_IMAGES_PER_USER_PER_DAY)
        ]
        with pytest.raises(ImageRateLimitError):
            check_image_rate_limit(user_id)

    def test_bypass_limits_skips_checks(self):
        user_id = fresh_user("rate", "bypass")
        for _ in range(MAX_IMAGES_PER_MINUTE + 1):
            check_image_rate_limit(user_id, bypass_limits=True)

    def test_clean_old_requests_removes_expired(self):
        user_id = fresh_user("rate", "clean")
        _user_image_log[user_id] = [
            datetime.now() - timedelta(days=2)
            for _ in range(MAX_IMAGES_PER_USER_PER_DAY)
        ]
        check_image_rate_limit(user_id)


class TestCheckAccountLimit:
    def test_blocks_at_account_max(self):
        with patch(
            "src.chains.image_security._account_image_count",
            _ACCOUNT_MAX_IMAGES_PER_DAY,
        ):
            with pytest.raises(ImageAccountLimitError):
                check_account_limit()


class TestRegisterImageRequest:
    def test_returns_false_before_last(self):
        user_id = fresh_user("register", "before-last")
        for i in range(MAX_IMAGES_PER_USER_PER_DAY - 1):
            result = register_image_request(user_id)
            assert result is False

    def test_returns_true_on_last(self):
        user_id = fresh_user("register", "on-last")
        for _ in range(MAX_IMAGES_PER_USER_PER_DAY - 1):
            register_image_request(user_id)
        result = register_image_request(user_id)
        assert result is True
