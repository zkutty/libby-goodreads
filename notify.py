import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram(token: str, chat_id: str, message: str) -> None:
    """Send an HTML-formatted message via Telegram bot."""
    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()


def build_message(
    title: str,
    is_available: bool,
    wait_days: int | None,
    libby_url: str,
    library_key: str,
) -> str:
    link = f'<a href="{libby_url}">{title}</a>'
    if is_available:
        return f"📚 {link} is available on Libby NOW! [{library_key}]"
    else:
        wait = f"~{wait_days} day wait" if wait_days else "waitlist"
        return f"⏳ {link} is on Libby ({wait}) [{library_key}]"
