#!/usr/bin/env python3
"""刪除 index.html 中已過期的月份區塊（該月公告 + 聖工安排表圖片）。

規則：某個月份的區塊，從「下個月的最後一天」（台灣時間）起刪除。
  例：九月份區塊 → 10/31 起刪除；十月份區塊 → 11/30 起刪除。
這和網頁本身的「自動隱藏」規則一致，差別是這個程式會真的把內容從檔案中移除。

用法：
  python3 prune_months.py                       # 處理目前資料夾的 index.html
  python3 prune_months.py index.html --dry-run  # 只顯示會刪除什麼，不修改檔案
  python3 prune_months.py index.html --today 2026-10-31   # 模擬指定日期（測試用）
"""
import argparse
import calendar
import re
import sys
from datetime import date, datetime, timedelta, timezone

# 台灣沒有日光節約時間，直接用 UTC+8
TAIPEI = timezone(timedelta(hours=8))

# 一個月份區塊：<section class="month" data-month="YYYY-MM"> ... </section>
# （區塊裡面不可以再包含其他 <section>）
SECTION = re.compile(
    r'[ \t]*<section class="month" data-month="(\d{4})-(\d{2})">.*?</section>[ \t]*\n?',
    re.DOTALL,
)
# 頁首的「最後更新　2026.10.24 18:25」（中間是全形空白）
STAMP = re.compile(r"(最後更新\u3000)\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}")


def removal_date(year: int, month: int) -> date:
    """該月份區塊開始刪除的日期 = 下個月的最後一天。"""
    ny, nm = (year + 1, 1) if month == 12 else (year, month + 1)
    return date(ny, nm, calendar.monthrange(ny, nm)[1])


def prune(html: str, today: date):
    """回傳 (刪除後的 html, 被刪除的月份清單)。"""
    removed = []

    def repl(m):
        year, month = int(m.group(1)), int(m.group(2))
        if today >= removal_date(year, month):
            removed.append(f"{year}-{month:02d}")
            return ""
        return m.group(0)

    new_html = SECTION.sub(repl, html)
    if removed:
        # 清掉刪除後留下的多餘空行
        new_html = re.sub(r"\n{3,}", "\n\n", new_html)
    return new_html, removed


def main() -> int:
    ap = argparse.ArgumentParser(description="刪除 index.html 中已過期的月份區塊")
    ap.add_argument("file", nargs="?", default="index.html")
    ap.add_argument("--today", help="模擬今天的日期 YYYY-MM-DD（測試用）")
    ap.add_argument("--dry-run", action="store_true", help="只顯示結果，不修改檔案")
    args = ap.parse_args()

    now = datetime.now(TAIPEI)
    today = date.fromisoformat(args.today) if args.today else now.date()

    with open(args.file, encoding="utf-8") as f:
        html = f.read()

    new_html, removed = prune(html, today)
    if not removed:
        print(f"{today}：沒有需要刪除的月份。")
        return 0

    print(f"{today}：刪除月份區塊 {', '.join(removed)}")
    if args.dry_run:
        return 0

    # 同步更新頁首的「最後更新」時間
    stamp = now.strftime("%Y.%m.%d %H:%M")
    new_html = STAMP.sub(lambda m: m.group(1) + stamp, new_html)

    with open(args.file, "w", encoding="utf-8") as f:
        f.write(new_html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
