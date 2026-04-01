import feedparser


def fetch_want_to_read(rss_url: str) -> list[dict]:
    """Parse a Goodreads 'Want to Read' RSS feed and return a list of books."""
    feed = feedparser.parse(rss_url)
    books = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        author = entry.get("author_name", entry.get("author", "")).strip()
        if title:
            books.append({"title": title, "author": author})
    return books
