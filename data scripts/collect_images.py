"""Phase 2 - Collection: scrape images per dish and log every source.

Usage:  python collect_images.py --per-query 80
Top-up: python collect_images.py --dishes chicken_karahi aloo_gosht --set extra --per-query 60
Output: data/raw/<dish>/*.jpg  and  data/raw_metadata.csv
"""
import argparse
import csv
from pathlib import Path

from icrawler.builtin import BingImageCrawler
from icrawler.downloader import ImageDownloader

from config import (DISHES, QUERY_TEMPLATES, EXTRA_TEMPLATES, RAW, RAW_META,
                    META_COLUMNS)

CURRENT = {"dish": "", "query": ""}


def guess_setting(query: str) -> str:
    if "homemade" in query or "home cooked" in query:
        return "home"
    if "restaurant" in query or "dhaba" in query:
        return "restaurant"
    return "unknown"


class LoggingDownloader(ImageDownloader):
    """Saves the image and appends its URL to the metadata CSV."""

    def process_meta(self, task):
        if not task.get("success"):
            return
        row = {
            "filename": Path(task["filename"]).name,
            "dish": CURRENT["dish"],
            "source": "bing_scrape",
            "url": task["file_url"],
            "license": "unknown (web scrape, academic use)",
            "setting": guess_setting(CURRENT["query"]),
        }
        with open(RAW_META, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=META_COLUMNS).writerow(row)


def main(per_query: int, dishes, template_set: str):
    RAW.mkdir(parents=True, exist_ok=True)
    if not RAW_META.exists():
        with open(RAW_META, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=META_COLUMNS).writeheader()

    templates = EXTRA_TEMPLATES if template_set == "extra" else QUERY_TEMPLATES
    selected = {k: v for k, v in DISHES.items() if not dishes or k in dishes}
    for slug, name in selected.items():
        out_dir = RAW / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        for template in templates:
            query = template.format(n=name)
            CURRENT.update(dish=slug, query=query)
            print(f"[{slug}] {query}")
            crawler = BingImageCrawler(
                storage={"root_dir": str(out_dir)},
                downloader_cls=LoggingDownloader,
                feeder_threads=1, parser_threads=1, downloader_threads=4,
            )
            # file_idx_offset avoids overwriting files from earlier queries
            crawler.crawl(keyword=query, max_num=per_query,
                          file_idx_offset="auto", min_size=(200, 200))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-query", type=int, default=80)
    ap.add_argument("--dishes", nargs="+", choices=list(DISHES),
                    help="only scrape these dish slugs (default: all)")
    ap.add_argument("--set", dest="template_set", choices=["default", "extra"],
                    default="default", help="which query wording to use")
    a = ap.parse_args()
    main(a.per_query, a.dishes, a.template_set)
