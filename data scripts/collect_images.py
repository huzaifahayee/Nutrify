"""Phase 2 - Collection: scrape images per dish and log every source.

Usage:  python collect_images.py --per-query 80
Output: data/raw/<dish>/*.jpg  and  data/raw_metadata.csv
"""
import argparse
import csv
from pathlib import Path

from icrawler.builtin import BingImageCrawler
from icrawler.downloader import ImageDownloader

from config import DISHES, QUERY_TEMPLATES, RAW, RAW_META, META_COLUMNS

CURRENT = {"dish": "", "query": ""}


def guess_setting(query: str) -> str:
    if "homemade" in query:
        return "home"
    if "restaurant" in query:
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


def main(per_query: int):
    RAW.mkdir(parents=True, exist_ok=True)
    if not RAW_META.exists():
        with open(RAW_META, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=META_COLUMNS).writeheader()

    for slug, name in DISHES.items():
        out_dir = RAW / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, template in enumerate(QUERY_TEMPLATES):
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
    main(ap.parse_args().per_query)
