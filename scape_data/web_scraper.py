from selenium import webdriver
from selenium.webdriver.chromium.webdriver import ChromiumDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from lxml import html

import time
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import (
    relativedelta,
)
import re
from typing import Tuple, List, Dict

SCRAPER_BASE_WAIT_TIME = 1


def subtract_time(text):
    now = datetime.now()

    # Match a number and unit (e.g., "5 năm", "3 ngày", "7 giờ")
    match = re.search(r"(\d+)\s*(năm|tháng|ngày|giờ|phút)", text)
    if not match:
        raise ValueError("No valid time expression found in string.")

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "năm":
        result = now - relativedelta(years=value)
    elif unit == "tháng":
        result = now - relativedelta(months=value)
    elif unit == "ngày":
        result = now - timedelta(days=value)
    elif unit == "giờ":
        result = now - timedelta(hours=value)
    elif unit == "phút":
        result = now - timedelta(minutes=value)
    else:
        raise ValueError(f"Unknown time unit: {unit}")

    result = result.astimezone()
    formatted = result.strftime("%Y-%m-%dT%H:%M:%S%z")
    formatted = formatted[:-2] + ":" + formatted[-2:]

    return formatted


class WebScraper:
    def __init__(self):
        self._chrome_options = Options()
        self._chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )

    def _initialize_web_driver_and_lxml_tree(
        self,
    ) -> Tuple[ChromiumDriver, html.HtmlElement]:
        web_driver: ChromiumDriver = webdriver.Chrome(options=self._chrome_options)
        tree = html.fromstring(web_driver.page_source)

        return (web_driver, tree)

    def _update_lxml_tree(self, web_driver: ChromiumDriver) -> html.HtmlElement:
        return html.fromstring(web_driver.page_source)

    def _navigate_to_url(
        self, web_driver: ChromiumDriver, url: str
    ) -> Tuple[ChromiumDriver, html.HtmlElement]:
        web_driver.get(url)
        time.sleep(SCRAPER_BASE_WAIT_TIME)
        tree = self._update_lxml_tree(web_driver)

        return (web_driver, tree)

    def _click_element(self, web_driver: ChromiumDriver, xpath: str) -> None:
        element = WebDriverWait(web_driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()

    def _extract_text_by_xpath(self, tree: html.HtmlElement, xpath: str) -> str:
        """
        Extracts text content from the first element matching the XPath.
        """
        result = tree.xpath(xpath)
        if result:
            return (
                result[0].strip()
                if isinstance(result[0], str)
                else result[0].text_content().strip()
            )
        return ""

    def _extract_comment_internal(self, comment_element: html.HtmlElement) -> Dict:
        author_name = comment_element.xpath(
            './div[contains(@class, "thread-comment__container")]'
            '/div[contains(@class, "thread-comment__wrapper")]'
            '/div[contains(@class, "thread-comment__box")]'
            '/div[contains(@class, "thread-comment__author-container")]'
            '/div[contains(@class, "thread-comment__author")]'
            '/a[contains(@class, "author-name")]/text()'
        )[0]
        author_rank = comment_element.xpath(
            './div[contains(@class, "thread-comment__container")]'
            '/div[contains(@class, "thread-comment__wrapper")]'
            '/div[contains(@class, "thread-comment__box")]'
            '/div[contains(@class, "thread-comment__author-container")]'
            '/div[contains(@class, "thread-comment__author")]'
            '/div[contains(@class, "author-rank")]/text()'
        )[0]
        time_past_str = comment_element.xpath(
            './div[contains(@class, "thread-comment__container")]'
            '/div[contains(@class, "thread-comment__wrapper")]'
            '/div[contains(@class, "thread-comment__box")]'
            '/div[contains(@class, "thread-comment__author-container")]'
            '/div[contains(@class, "thread-comment__author")]'
            '/a[contains(@class, "thread-comment__date")]'
            "/span/text()"
        )[0]
        content = comment_element.xpath(
            './div[contains(@class, "thread-comment__container")]'
            '/div[contains(@class, "thread-comment__wrapper")]'
            '/div[contains(@class, "thread-comment__box")]'
            '/div[contains(@class, "thread-comment__content")]'
            '//span[contains(@class, "xf-body-paragraph")]/text()'
        )[0]

        return {
            "author_name": author_name,
            "author_rank": author_rank,
            "time_past": subtract_time(time_past_str),
            "content": str(content).strip(),
        }

    def extract_comments(self, comment_section: html.HtmlElement) -> List:
        """
        Recursively extract comment data and nested replies
        """

        if comment_section and isinstance(comment_section, list):
            comment_section = comment_section[0]

        outer_comment_elements = comment_section.xpath(
            './div[contains(@class, "thread-comment")]'
        )

        comment_list = []
        for outer_comment in outer_comment_elements:
            comment_list.append(self._extract_comment_internal(outer_comment))

        return comment_list

    def scrape_data(self, tinh_te_urls: List):
        web_driver, tree = self._initialize_web_driver_and_lxml_tree()

        if tinh_te_urls and isinstance(tinh_te_urls, list):
            for url in tinh_te_urls:
                (web_driver, tree) = self._navigate_to_url(
                    web_driver=web_driver, url=url
                )

                number_of_comments = 0
                try:
                    number_of_comments = int(
                        self._extract_text_by_xpath(
                            tree=tree,
                            xpath='//*[@id="__next"]/div[1]/div/div[2]/div[2]/div[1]/div/div/div[1]/div[2]/div[1]/div[1]/div[2]/span/span',
                        )
                    )
                except:
                    pass

                comment_section = tree.xpath(
                    '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div[1]/div/div/div[1]/div[3]/div[2]/div'
                )

                comment_dictionary = self.extract_comments(
                    comment_section=comment_section
                )

        return {
            "url": url,
            "number_of_comments": number_of_comments,
            "comments": comment_dictionary,
        }
