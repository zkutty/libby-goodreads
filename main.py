import json
import os
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


def load_state() -> set[str]:
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text())
        return set(data.get("notified", []))
    return set()


def save_state(notified: set[str]) -> None:
    STATE_FILE.write_text(json.dumps({"notified": sorted(notified)}, indent=2))


def main() -> None:
    notified = load_state()
    print(f"Loaded {len(notified)} already-notified book(s) from state.")

    books = fetch_want_to_read(GOODREADS_RSS)
    print(f"Found {len(books)} book(s) on 'Want to Read' shelf.")
    print(f"Checking against {len(LIBRARY_KEYS)} library/libraries: {', '.join(LIBRARY_KEYS)}")

    newly_notified: list[str] = []

    for book in books:
        title = book["title"]
        author = book["author"]
        state_key = f"{title}|{author}"

        if state_key in notified:
            print(f"  [skip] {title} — already notified")
            continue

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

        message = build_message(title, hits)
        send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
        print(f"    Notification sent ({len(hits)} library/libraries).")
        newly_notified.append(state_key)

    notified.update(newly_notified)
    save_state(notified)
    print(f"Done. Sent {len(newly_notified)} new notification(s).")


if __name__ == "__main__":
    main()
