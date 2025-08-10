from datetime import datetime, timedelta
from typing import Optional, Union
import time

DEFAULT_DATETIME_FORMAT = "%m/%d/%Y %H:%M:%S"

def get_current_time(offset_seconds: int = 0) -> datetime:
    """
    Returns the current local time as a datetime object, with optional offset in seconds.

    Args:
        offset_seconds (int): Number of seconds to add to the current time.
                              Positive for future time, negative for past time.
                              Default is 0 (no offset).

    Returns:
        datetime: Current timestamp, optionally offset by the specified number of seconds
    """
    now = datetime.now()
    
    if offset_seconds != 0:
        now += timedelta(seconds=offset_seconds)
        
    return now


def get_elapsed_time(start_time: Optional[datetime], end_time: Optional[datetime] = None) -> float:
    """
    Returns the number of seconds from now (or `end_time`) until `start_time`.

    Args:
        start_time: A datetime object in the past or future. Must not be None.
        end_time: Optional override for current time (defaults to now).

    Returns:
        float: Time delta in seconds.

    Raises:
        ValueError: If start_time is None.
    """
    if start_time is None:
        raise ValueError("start_time must not be None.")

    if end_time is None:
        end_time = datetime.now()

    return round((end_time - start_time).total_seconds(), 2)


def format_timestamp_for_sheets(ts: datetime, fmt: str = DEFAULT_DATETIME_FORMAT) -> str:
    """
    Formats a datetime object into a string suitable for Google Sheets.

    Args:
        ts: A datetime object.
        fmt: Format string (default matches typical Sheets format).

    Returns:
        A formatted string like "05/12/2025 21:34:00".
    """
    return ts.strftime(fmt)


def wait_until_elapsed(start_time: datetime, duration: float = 2.0) -> None:
    """
    Blocks execution until `duration` seconds have elapsed since `start_time`.

    Args:
        start_time (datetime): Reference point in time.
        duration (float): Minimum seconds to wait since start_time.
    """
    from utils.timer import get_elapsed_time  # Assuming you're following that module path

    while get_elapsed_time(start_time) < duration:
        time.sleep(0.05)  # Sleep to prevent busy looping


def convert_timestamp_to_safe_format(timestamp: str) -> str:
    """
    Converts a timestamp to a filesystem-safe format.
    
    Args:
        timestamp: Either a datetime object or a string in format "%m/%d/%Y %H:%M:%S"
        
    Returns:
        Filesystem-safe timestamp string in format "YYYYMMDD_HHMMSS"
    """
    if isinstance(timestamp, datetime):
        return timestamp.strftime("%Y%m%d_%H%M%S")
    
    parts = timestamp.split()
    date_parts = parts[0].split("/")
    time_parts = parts[1].split(":")
    return f"{date_parts[2]}{date_parts[0]}{date_parts[1]}_{time_parts[0]}{time_parts[1]}{time_parts[2]}"