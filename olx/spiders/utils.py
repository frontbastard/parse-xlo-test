import locale
import re
from datetime import datetime

locale.setlocale(locale.LC_TIME, 'uk_UA.UTF-8')


def parse_date(raw_date):
    if not raw_date:
        return None

    today = datetime.now()
    date_match = re.search(
        r"(\d{1,2}\s\w+\s\d{4})", raw_date
    )

    if date_match:
        date_str = date_match.group(1)
        parsed_date = datetime.strptime(
            date_str, "%d %B %Y"
        )
    else:
        parsed_date = today

    return parsed_date.date()


def get_price_details(text: str) -> [int, None]:
    if text:
        match = re.search(r"(\d[\d\s]*)", text)
        if match:
            return {
                "value": int(match.group(1).replace(" ", "")),
                "currency": "USD" if "$" in text else "UAH"
            }
    return None
