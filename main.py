import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

from goodreads import fetch_want_to_read
from libby import check_availability
from notify import build_message, send_telegram

load_dotenv()

GOODREADS_RSS = os.environ["GOODREADS_RSS"]
LIBRARY_KEYS = [k.strip() for k in os.environ["LIBRARY_KEYS"].split(",") if k.strip()]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

STATE_FILE = Path(__file__).parent / "state.json"
RENOTIFY_DAYS = 7


def load_state() -> dict:
    """Return full state dict with 'notified' and 'statuses' sections."""
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text())
        return {
            "notified": data.get("notified", {}),
            "statuses": data.get("statuses", {}),
        }
    return {"notified": {}, "statuses": {}}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def should_notify(notified: dict[str, str], key: str) -> bool:
    if key not in notified:
        return True
    last = datetime.fromisoformat(notified[key])
    return datetime.now(timezone.utc) - last >= timedelta(days=RENOTIFY_DAYS)


def became_available(statuses: dict, state_key: str, hits: list[dict]) -> bool:
    """Return True if any hit changed from waitlist to available since last check."""
    for hit in hits:
        if not hit["isAvailable"]:
            continue
        status_key = f"{state_key}|{hit['library_key']}"
        prev = statuses.get(status_key, {})
        if isinstance(prev, dict) and prev.get("status") == "waitlist":
            return True
    return False


def main() -> None:
    state = load_state()
    notified = state["notified"]
    statuses = state["statuses"]
    print(f"Loaded {len(notified)} tracked book(s) from state.")

    books = fetch_want_to_read(GOODREADS_RSS)
    print(f"Found {len(books)} book(s) on 'Want to Read' shelf.")
    print(f"Checking against {len(LIBRARY_KEYS)} library/libraries: {', '.join(LIBRARY_KEYS)}")

    newly_notified: dict[str, str] = {}

    for book in books:
        title = book["title"]
        author = book["author"]
        state_key = f"{title}|{author}"

        due_for_renotify = should_notify(notified, state_key)

        if not due_for_renotify:
            # Still check availability to detect status changes
            pass

        print(f"  Checking: {title} by {author}")

        hits: list[dict] = []
        for library_key in LIBRARY_KEYS:
            try:
                result = check_availability(library_key, title, author)
            except Exception as exc:
                print(f"    ERROR at {library_key}: {exc}")
                continue

            if result is None:
                print(f"    {library_key}: not in catalog")
                continue

            result["library_key"] = library_key
            hits.append(result)
            status = "AVAILABLE" if result["isAvailable"] else f"~{result['estimatedWaitDays']}d wait"
            print(f"    {library_key}: {status}")

        if not hits:
            print(f"    Not found at any library.")
            continue

        # Check for status changes BEFORE updating statuses
        newly_available = became_available(statuses, state_key, hits)

        # Now update statuses for all hits
        for hit in hits:
            status_key = f"{state_key}|{hit['library_key']}"
            statuses[status_key] = {
                "status": "available" if hit["isAvailable"] else "waitlist",
                "estimatedWaitDays": hit.get("estimatedWaitDays"),
            }
        if newly_available:
            print(f"    Status change detected: now available!")
        elif not due_for_renotify:
            last = notified[state_key][:10]
            print(f"    [skip] notified {last}, within {RENOTIFY_DAYS}-day window")
            continue

        message = build_message(title, hits, newly_available=newly_available)
        send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
        now = datetime.now(timezone.utc).isoformat()
        print(f"    Notification sent ({len(hits)} library/libraries).")
        newly_notified[state_key] = now

    notified.update(newly_notified)
    state["notified"] = notified
    state["statuses"] = statuses
    save_state(state)
    print(f"Done. Sent {len(newly_notified)} new notification(s).")


if __name__ == "__main__":
    main()
