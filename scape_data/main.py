from web_scraper import WebScraper
import json


def main():
    web_scraper = WebScraper()
    result = web_scraper.scrape_data(
        tinh_te_urls=[
            "https://tinhte.vn/thread/tren-tay-ireader-ocean4-turbo-2025-man-dep-may-nhe-de-cam.4036243/"
        ]
    )
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
