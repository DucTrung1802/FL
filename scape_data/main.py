from web_scraper import WebScraper
import json


def main():
    web_scraper = WebScraper()

    url_list = json.load(open("input.json", "r", encoding="utf-8"))

    web_scraper.scrape_data(tinh_te_urls=url_list)


if __name__ == "__main__":
    main()
