from web_scraper import WebScraper
import json


def main():
    web_scraper = WebScraper()
    result = web_scraper.scrape_data(
        tinh_te_urls=[
            "https://tinhte.vn/thread/deepseek-ai-tan-dung-tot-tai-nguyen-nho-nang-luc-lap-trinh-gan-dat-muc-assembly.3953999/"
        ]
    )
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
