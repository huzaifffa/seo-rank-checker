import sys
import time
import traceback
from urllib.parse import urlparse, parse_qs, unquote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def wait_for_captcha(browser) -> None:
    input("CAPTCHA detected. Please solve it in the browser, then press Enter to continue...")
    time.sleep(2)


def is_captcha(page_source: str) -> bool:
    page_source = page_source.lower()
    return "unusual traffic" in page_source or "captcha" in page_source or "are you a robot" in page_source


def get_real_url(href: str) -> str:
    if not href:
        return href
    parsed = urlparse(href)
    netloc = parsed.netloc
    if not netloc:
        parsed = urlparse("https://www.google.com" + href)
        netloc = parsed.netloc
    if "google.com" in netloc:
        if parsed.path == "/url":
            return parse_qs(parsed.query).get("q", [""])[0]
        if parsed.path == "/goto":
            return unquote(parse_qs(parsed.query).get("url", [""])[0])
    return href


def normalize_domain(raw: str) -> str:
    if not raw:
        return ""
    raw = raw.strip().lower()
    if "://" not in raw:
        raw = "//" + raw
    parsed = urlparse(raw)
    host = parsed.netloc or parsed.path
    host = host.split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host


def check_ranking(domain: str, keyword: str, max_pages: int = 10) -> dict:
    browser = webdriver.Chrome()
    browser.get("https://www.google.com")

    if is_captcha(browser.page_source):
        wait_for_captcha(browser)

    search_box = browser.find_element(By.NAME, "q")
    search_box.send_keys(keyword)
    search_box.submit()

    time.sleep(2)

    if is_captcha(browser.page_source):
        wait_for_captcha(browser)

    position = None

    for page in range(1, max_pages + 1):
        if is_captcha(browser.page_source):
            wait_for_captcha(browser)

        results = browser.find_elements(By.CSS_SELECTOR, "div.g")
        for idx, result in enumerate(results):
            try:
                link = result.find_element(By.CSS_SELECTOR, "a")
                href = get_real_url(link.get_attribute("href"))
                if href:
                    parsed = urlparse(href)
                    result_domain = normalize_domain(parsed.netloc)
                    print(f'  [PAGE {page}] pos {idx+1}: {result_domain} -> {href}')
                    if normalize_domain(domain) == result_domain:
                        position = (page - 1) * 10 + idx + 1
                        browser.quit()
                        return {"keyword": keyword, "rank": position, "page": page, "url": href}
            except Exception:
                continue

        try:
            next_button = browser.find_element(By.ID, "pnnext")
            next_button.click()
            time.sleep(2)
        except Exception:
            break

    browser.quit()
    return {"keyword": keyword, "rank": "Not Found", "page": "Not Found"}


if __name__ == "__main__":
    if len(sys.argv) == 3:
        domain = sys.argv[1]
        keyword = sys.argv[2]
    else:
        domain = input("Enter domain: ").strip()
        keyword = input("Enter keyword: ").strip()

    result = check_ranking(domain, keyword)
    print(result)
