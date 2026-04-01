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


def build_message(title: str, hits: list[dict]) -> str:
    """
    Build a single message for a book listing all libraries where it was found.

    Each hit dict must have: library_key, isAvailable, estimatedWaitDays, libby_url
    """
    any_available = any(h["isAvailable"] for h in hits)
    emoji = "📚" if any_available else "⏳"

    lines = [f"{emoji} <b>{title}</b> is on Libby:"]
    for hit in hits:
        link = f'<a href="{hit["libby_url"]}">{hit["library_key"]}</a>'
        if hit["isAvailable"]:
            lines.append(f"  • {link} — available NOW")
        else:
            wait = f"~{hit['estimatedWaitDays']} day wait" if hit["estimatedWaitDays"] else "waitlist"
            lines.append(f"  • {link} — {wait}")

    return "\n".join(lines)
