from web_scraper import WebScraper
import json


def main():
    web_scraper = WebScraper()
    result = web_scraper.scrape_data(
        tinh_te_urls=[
            "https://tinhte.vn/thread/v-v-xu-ly-cac-vi-pham-tren-group-tinh-te-tren-fb.2819224/"
        ]
    )
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
