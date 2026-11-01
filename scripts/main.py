"""
scripts/main.py

Orchestrator chính — chạy các nguồn dạng RSS/Atom (rss, github_atom),
lọc ra tin mới so với lần chạy trước, xuất kết quả thành new_items.json.

LƯU Ý VỀ GMAIL: các nguồn "type: gmail" trong sources.yaml KHÔNG được xử lý ở
đây, vì việc tự dựng xác thực Gmail API trong script là một lớp phức tạp
không cần thiết — Claude Code routine đã có sẵn Gmail connector (MCP) đang kết
nối. Nên: script này lo phần RSS/GitHub (rẻ, không cần auth, chạy được độc
lập), còn Claude sẽ tự gọi Gmail connector để tìm newsletter mới trong bước
sau, dựa theo truy vấn ghi trong sources.yaml. Xem README.md để biết luồng đầy đủ.

Chạy: python -m scripts.main
Output: new_items.json ở thư mục gốc repo — Claude đọc file này để viết bản tóm tắt.
"""

import json
import sys
from pathlib import Path

import feedparser
import yaml

from scripts.article_text import feed_entry_text, fetch_page_text, html_to_text, truncate
from scripts.dedup_store import load_state, save_state, filter_new_items
from scripts.discover_feed import discover_feed

ROOT = Path(__file__).parent.parent
SOURCES_PATH = ROOT / "config" / "sources.yaml"
OUTPUT_PATH = ROOT / "new_items.json"

MAX_ITEMS_PER_SOURCE = 15  # tránh một nguồn đăng dồn dập chiếm hết context
SUMMARY_MAX_CHARS = 800
PAGE_FETCH_MIN_CHARS = 600  # content_text ngắn hơn mức này thì tải trang bài gốc

# Loại sự kiện GitHub (phần giữa "tag:github.com,2008:" và "/" trong id) bị bỏ vì chỉ là
# hoạt động thường ngày, không phải công cụ mới. Loại chưa gặp vẫn được giữ lại.
GITHUB_NOISE_PREFIXES = ("push", "star", "pr_", "issue_", "reviewcomment_", "delete")


def load_sources() -> list[dict]:
    return yaml.safe_load(SOURCES_PATH.read_text(encoding="utf-8"))


def fetch_rss_items(source: dict) -> list[dict]:
    feed_url = source.get("feed_url")
    if not feed_url:
        feed_url = discover_feed(source["url"])
        if not feed_url:
            print(f"  [!] Không tìm được feed cho '{source['name']}' — bỏ qua, cần kiểm tra thủ công.")
            return []
        print(f"  [i] Tự dò được feed cho '{source['name']}': {feed_url}")

    parsed = feedparser.parse(feed_url)
    items = []
    for entry in parsed.entries[:MAX_ITEMS_PER_SOURCE]:
        items.append({
            "id": entry.get("id") or entry.get("link"),
            "title": entry.get("title", "(không có tiêu đề)"),
            "link": entry.get("link", ""),
            "published": entry.get("published", entry.get("updated", "")),
            "summary_raw": truncate(html_to_text(entry.get("summary", "")), SUMMARY_MAX_CHARS),
            "content_text": feed_entry_text(entry),
        })
    return items


def is_github_noise(entry_id: str) -> bool:
    kind = entry_id.split("2008:", 1)[-1].split("/", 1)[0]
    return kind.startswith(GITHUB_NOISE_PREFIXES)


def fetch_github_atom_items(source: dict) -> list[dict]:
    # GitHub cung cấp Atom feed hoạt động công khai của mọi user tại <user>.atom
    feed_url = source["url"].rstrip("/") + ".atom"
    parsed = feedparser.parse(feed_url)
    items = []
    for entry in parsed.entries[:MAX_ITEMS_PER_SOURCE]:
        entry_id = entry.get("id") or entry.get("link")
        if is_github_noise(entry_id):
            continue
        items.append({
            "id": entry_id,
            "title": entry.get("title", "(không có tiêu đề)"),
            "link": entry.get("link", ""),
            "published": entry.get("published", entry.get("updated", "")),
            "summary_raw": truncate(html_to_text(entry.get("summary", "")), SUMMARY_MAX_CHARS),
            "content_text": "",
        })
    return items


def fill_missing_content(items: list[dict]) -> None:
    for item in items:
        if len(item["content_text"]) >= PAGE_FETCH_MIN_CHARS or not item["link"]:
            continue
        page_text = fetch_page_text(item["link"])
        if len(page_text) > len(item["content_text"]):
            item["content_text"] = page_text


def main():
    sources = load_sources()
    state = load_state()
    result = {"ai": [], "tools": [], "market": [], "gmail_pending": []}

    for source in sources:
        name, group, type_ = source["name"], source["group"], source["type"]
        print(f"Đang xử lý: {name} ({type_})")

        if type_ == "rss":
            items = fetch_rss_items(source)
        elif type_ == "github_atom":
            items = fetch_github_atom_items(source)
        elif type_ == "gmail":
            # Không fetch ở đây — chỉ chuyển tiếp truy vấn để Claude tự tìm qua Gmail connector.
            result["gmail_pending"].append({"name": name, "group": group, "gmail_query": source["url"]})
            continue
        else:
            print(f"  [!] Loại nguồn không hỗ trợ: {type_}")
            continue

        new_items = filter_new_items(name, items, state)
        if type_ == "rss":
            fill_missing_content(new_items)
        for item in new_items:
            item["source"] = name
        result[group].extend(new_items)
        print(f"  -> {len(new_items)} tin mới")

    save_state(state)
    OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã ghi kết quả vào {OUTPUT_PATH}")
    print(f"Còn {len(result['gmail_pending'])} nguồn Gmail cần Claude tự tra cứu qua connector.")


if __name__ == "__main__":
    main()
