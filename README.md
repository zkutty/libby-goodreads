# libby-watchdog

Checks your Goodreads "Want to Read" shelf against Libby/OverDrive availability and sends a Telegram notification when books become available or land on a waitlist.

Runs daily via GitHub Actions and persists already-notified books in `state.json` so you only get one alert per book.

---

## Setup

### 1. Goodreads RSS URL

1. Go to [goodreads.com](https://www.goodreads.com) and sign in.
2. Navigate to your profile → **Want to Read** shelf.
3. Scroll to the bottom of the page and copy the **RSS** link. It looks like:
   ```
   https://www.goodreads.com/review/list_rss/12345678?shelf=to-read
   ```
4. Set this as `GOODREADS_RSS`.

> Note: your shelf must be set to **public** for the RSS feed to work.

### 2. Library Keys (OverDrive subdomains)

1. Go to [libbyapp.com](https://libbyapp.com) and find each of your libraries.
2. Each library's OverDrive URL looks like `https://berkeleypubliclibrary.overdrive.com`.
3. The subdomain before `.overdrive.com` is the key (e.g. `berkeleypubliclibrary`).
4. Set `LIBRARY_KEYS` as a comma-separated list:
   ```
   LIBRARY_KEYS=berkeleypubliclibrary,sdcl,nypl,oakland
   ```

Alternatively, open Libby, tap the menu → **Add a Library** → search for yours, then look at the URL in your browser.

### 3. Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts.
3. Copy the **token** BotFather gives you → `TELEGRAM_BOT_TOKEN`.
4. Start a conversation with your new bot (send it `/start`).
5. Get your chat ID by visiting:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
   Look for `"chat": {"id": 123456789}` in the response → `TELEGRAM_CHAT_ID`.

### 4. Running locally

```bash
cd libby-watchdog
pip install -r requirements.txt
cp .env.example .env
# fill in .env with your values
python main.py
```

### 5. GitHub Actions

1. Push this repo to GitHub.
2. Go to **Settings → Secrets and variables → Actions** and add:
   - `GOODREADS_RSS`
   - `LIBRARY_KEYS`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. The workflow runs daily at 9am Hawaii time. You can also trigger it manually from the **Actions** tab via **workflow_dispatch**.

The workflow commits an updated `state.json` after each run so previously notified books aren't re-alerted.

---

## How it works

1. Fetches your Goodreads "Want to Read" RSS feed via `feedparser`.
2. For each book, queries the OverDrive Thunder API (`thunder.api.overdrive.com/v2`) to check catalog availability at your library.
3. If a book is found in the catalog (available now **or** on waitlist), sends a Telegram message.
4. Records notified books in `state.json` to avoid duplicate alerts.
