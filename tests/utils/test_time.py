import hashlib
from datetime import datetime, timezone
from unittest.mock import patch

from src.hive_cli.utils.time import now_2_hash


def test_now_2_hash():
    fixed_timestamp = 1700000000
    fixed_datetime = datetime.fromtimestamp(fixed_timestamp, tz=timezone.utc)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_datetime

    with patch("src.hive_cli.utils.time.datetime", FixedDateTime):
        expected_hash = hashlib.sha1(str(fixed_timestamp).encode()).hexdigest()[:7]
        assert now_2_hash() == expected_hash
