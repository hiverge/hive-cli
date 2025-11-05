import hashlib
from datetime import datetime, timezone


def humanize_time(timestamp: str) -> str:
    creation_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    t = datetime.now(timezone.utc) - creation_time

    if t.days > 0:
        age = f"{t.days}d"
    elif t.seconds >= 3600:
        age = f"{t.seconds // 3600}h"
    elif t.seconds >= 60:
        age = f"{t.seconds // 60}m"
    else:
        age = f"{t.seconds}s"

    return age


def now_2_hash() -> str:
    timestamp = str(int(datetime.now(timezone.utc).timestamp()))
    unique_hash = hashlib.sha1(timestamp.encode()).hexdigest()[:7]

    return unique_hash
