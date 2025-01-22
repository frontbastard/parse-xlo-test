import re
from datetime import datetime


def parse_date(raw_date):
    if not raw_date:
        return None

    today = datetime.now()
    date_match = re.search(
        r"(\d{1,2}\s\w+\s\d{4})", raw_date
    )
    time_match = re.search(
        r"(\d{1,2}:\d{2})", raw_date
    )

    if date_match:
        date_str = date_match.group(1)
        parsed_date = datetime.strptime(
            date_str, "%d %B %Y"
        )
    else:
        parsed_date = today

    if time_match:
        time_str = time_match.group(1)
        parsed_time = datetime.strptime(time_str, "%H:%M").time()
        parsed_date = parsed_date.replace(
            hour=parsed_time.hour, minute=parsed_time.minute, second=0,
            microsecond=0
        )

    return parsed_date


def extract_main_price(text: str) -> [int, ValueError]:
    if text:
        match = re.search(r"(\d[\d\s]*)", text)
        if match:
            return int(match.group(1).replace(" ", ""))
        else:
            raise ValueError("No number found in the input text.")
    return None
