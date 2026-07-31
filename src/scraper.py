from __future__ import annotations
import hashlib
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import feedparser

def _mk_id(url: str, title: str) -> str:
    import hashlib
    return hashlib.sha256((url + "|" + title).encode("utf-8")).hexdigest()

def fetch_from_rss(feed_url: str) -> List[Dict]:
    d = feedparser.parse(feed_url)
    items: List[Dict] = []
    for e in d.entries[:30]:
        url = e.get("link") or ""
        title = e.get("title") or ""
        summary = e.get("summary", "")
        published = e.get("published", "")
        if not url or not title:
            continue
        # чистим html из summary
        text_summary = BeautifulSoup(summary, "html.parser").get_text(" ", strip=True) if summary else ""
        items.append({
            "id": _mk_id(url, title),
            "url": url,
            "title": title.strip(),
            "summary": text_summary,
            "published": published,
        })
    return items

def fetch_from_html(list_url: str, item_selector: str, title_selector: str, link_selector: str) -> List[Dict]:
    """
    Универсальный HTML-парсер. НУЖНО настроить селекторы под сайт.
    Пример: item_selector='article', title_selector='h2', link_selector='a'
    """
    r = requests.get(list_url, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items: List[Dict] = []
    for node in soup.select(item_selector)[:30]:
        title_node = node.select_one(title_selector)
        link_node = node.select_one(link_selector)
        if not title_node or not link_node or not link_node.get("href"):
            continue
        title = title_node.get_text(" ", strip=True)
        url = link_node.get("href")
        if url.startswith("/"):
            from urllib.parse import urljoin
            url = urljoin(list_url, url)
        items.append({
            "id": _mk_id(url, title),
            "url": url,
            "title": title,
            "summary": "",
            "published": "",
        })
    return items
