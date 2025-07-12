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

    # Special case: handle "một năm" as 1 year
    text = text.strip()
    if re.search(r"\bmột\s+năm\b", text, re.IGNORECASE):
        value = 1
        unit = "năm"
    else:
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

        try:
            content = comment_element.xpath(
                './div[contains(@class, "thread-comment__container")]'
                '/div[contains(@class, "thread-comment__wrapper")]'
                '/div[contains(@class, "thread-comment__box")]'
                '/div[contains(@class, "thread-comment__content")]'
                '//span[contains(@class, "xf-body-paragraph")]/text()'
            )[0]
        except IndexError:
            try:
                content = "".join(
                    comment_element.xpath(
                        './div[contains(@class, "thread-comment__container")]'
                        '/div[contains(@class, "thread-comment__wrapper")]'
                        '/div[contains(@class, "thread-comment__box")]'
                        '/div[contains(@class, "thread-comment__content")]'
                        '/div/div[contains(@class, "xfBodyContainer")]/div/text()'
                    )
                ).strip()
            except IndexError:
                content = None  # fallback if nothing found

        sub_comments = []
        try:
            sub_comment_container_element = comment_element.xpath(
                './div[contains(@class, "thread-comment__container")]'
                '/div[contains(@class, "thread-comment__wrapper")]'
                '/div[contains(@class, "thread-comments__container")]'
            )
            if sub_comment_container_element:
                sub_comment_elements = sub_comment_container_element[0].xpath(
                    './div/div[contains(@class, "thread-comment")]'
                )
                for sub_comment_element in sub_comment_elements:
                    sub_comments.append(
                        self._extract_comment_internal(sub_comment_element)
                    )

        except:
            pass

        comment = {
            "author_name": author_name,
            "author_rank": author_rank,
            "time_past": subtract_time(time_past_str),
            "content": str(content).strip(),
            "sub_comments": sub_comments,
        }

        return comment

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

    def extract_comments_in_a_page(
        self, web_driver: ChromiumDriver, tree: html.HtmlElement
    ) -> List:
        # Click load more comments
        # Find all "Load More" buttons
        buttons = web_driver.find_elements(
            By.CSS_SELECTOR,
            "button.jsx-4001123469.thread-comments__load-more",
        )

        for button in buttons:
            try:
                # Wait until button is clickable
                WebDriverWait(web_driver, 10).until(EC.element_to_be_clickable(button))
                button.click()
                time.sleep(2)
                print("Clicked a 'Load More' button")
            except Exception as e:
                print(f"Could not click a button: {e}")

        # Update tree
        tree = self._update_lxml_tree(web_driver)

        # Extract nested comments
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

        comment_dictionary = self.extract_comments(comment_section=comment_section)

        return number_of_comments, comment_dictionary

    def scrape_data(self, tinh_te_urls: List):
        web_driver, tree = self._initialize_web_driver_and_lxml_tree()

        if tinh_te_urls and isinstance(tinh_te_urls, list):
            for url in tinh_te_urls:
                (web_driver, tree) = self._navigate_to_url(
                    web_driver=web_driver, url=url
                )

                # Find all pages
                page_numbers = None
                try:
                    half = (
                        len(
                            web_driver.find_elements(
                                By.CSS_SELECTOR,
                                "a.jsx-2305813501.page",
                            )
                        )
                        // 2
                    )
                    page_numbers = range(0, half)
                except:
                    pass

                number_of_comments = 0
                comment_list = []

                if not page_numbers:
                    number_of_comments_in_page, comment_dictionary_in_page = (
                        self.extract_comments_in_a_page(
                            web_driver=web_driver, tree=tree
                        )
                    )
                    number_of_comments = number_of_comments_in_page
                    comment_list = comment_dictionary_in_page
                else:
                    number_of_comments_in_page, comment_dictionary_in_page = (
                        self.extract_comments_in_a_page(
                            web_driver=web_driver, tree=tree
                        )
                    )
                    number_of_comments = number_of_comments_in_page
                    comment_list.extend(comment_dictionary_in_page)

                    for index in page_numbers[1:]:
                        pages = web_driver.find_elements(
                            By.CSS_SELECTOR,
                            "a.jsx-2305813501.page",
                        )
                        href = pages[index].get_attribute("href")
                        web_driver.get(href)

                        tree = self._update_lxml_tree(web_driver=web_driver)

                        title_xpath = '//*[@id="__next"]/div[1]/div/div[2]/div[2]/div[1]/div/div/div[1]/main/div[1]/div/h1'

                        # Wait until the element is present
                        WebDriverWait(web_driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, title_xpath))
                        )

                        number_of_comments_in_page, comment_dictionary_in_page = (
                            self.extract_comments_in_a_page(
                                web_driver=web_driver, tree=tree
                            )
                        )
                        comment_list.extend(comment_dictionary_in_page)

        return {
            "url": url,
            "number_of_comment": number_of_comments,
            "comments": comment_list,
        }
