"""
scripts/article_text.py

Lấy nội dung bài viết dạng chữ thuần để routine cloud (không có mạng) có đủ
chất liệu viết tóm tắt chi tiết:

1. html_to_text(): bỏ thẻ HTML, ảnh và câu "The post ... appeared first on ..."
   mà WordPress chèn cuối mỗi entry.
2. feed_entry_text(): lấy toàn văn từ trường content (content:encoded) của feed
   nếu có — WordPress (WAN-IFRA, Nieman Lab, Poynter, Press Gazette...) thường kèm sẵn.
3. fetch_page_text(): với feed không kèm toàn văn, tải trang bài gốc và trích
   phần nội dung chính bằng trafilatura. Chỉ gọi cho tin MỚI để không tải lại
   hàng trăm trang mỗi ngày.
"""

from __future__ import annotations

import re
import sys

import requests
from bs4 import BeautifulSoup

from scripts.discover_feed import HEADERS

CONTENT_MAX_CHARS = 3000
PAGE_TIMEOUT = 15

_WP_FOOTER = re.compile(r"The post .{0,400}? appeared first on .{0,200}?\.?\s*$", re.S)


def html_to_text(html: str) -> str:
    if not html:
        return ""
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    text = _WP_FOOTER.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, limit: int = CONTENT_MAX_CHARS) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = cut.rfind(". ")
    return (cut[: end + 1] if end > limit * 0.6 else cut) + " […]"


def feed_entry_text(entry) -> str:
    contents = entry.get("content") or []
    best = max((c.get("value", "") for c in contents), key=len, default="")
    return truncate(html_to_text(best))


def fetch_page_text(url: str) -> str:
    try:
        import trafilatura
    except ImportError:
        print("  [!] Chưa cài trafilatura — bỏ qua bước tải trang bài gốc.", file=sys.stderr)
        return ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=PAGE_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [!] Không tải được {url}: {e}", file=sys.stderr)
        return ""
    text = trafilatura.extract(resp.text, url=url, include_comments=False, include_tables=False) or ""
    return truncate(re.sub(r"\s+", " ", text).strip())
