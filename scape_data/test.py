from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import (
    relativedelta,
)
import re


def subtract_time(text):
    now = datetime.now()

    # Match a number and unit (e.g., "5 năm", "3 ngày", "7 giờ")
    match = re.search(r"(\d+)\s*(năm|tháng|ngày|giờ|phút)", text)
    if not match:
        raise ValueError("No valid time expression found in string.")

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "năm":
        result = now - relativedelta(years=value)
    elif unit == "tháng":
        result = now - relativedelta(months=value)
    elif unit == "ngày":
        result = now - timedelta(days=value)
    elif unit == "giờ":
        result = now - timedelta(hours=value)
    elif unit == "phút":
        result = now - timedelta(minutes=value)
    else:
        raise ValueError(f"Unknown time unit: {unit}")

    result = result.astimezone()
    formatted = result.strftime("%Y-%m-%dT%H:%M:%S%z")
    formatted = formatted[:-2] + ":" + formatted[-2:]

    return formatted


# 🔥 Examples
print(subtract_time("5 năm"))  # subtract 5 years
print(subtract_time("3 tháng"))  # subtract 3 months
print(subtract_time("7 ngày"))  # subtract 7 days
print(subtract_time("2 giờ"))  # subtract 2 hours
print(subtract_time("15 phút"))  # subtract 15 minutes
