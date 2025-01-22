from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import json
import time

START_URL = "https://neckarmedia.com/"  # The base site to start crawling
DOMAIN = "neckarmedia.com"
MAX_PAGES = 40

def is_valid_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False    
    if DOMAIN not in parsed.netloc:
        return False
    return True


def clean_text(html_content):
    """
    Removes script/style tags and extracts visible text
    while trimming excess whitespace.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove <script> and <style> elements
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    for tag in soup(["header"]):
        tag.decompose()

    for tag in soup(id="footer"):
        tag.decompose()

    text = soup.get_text(separator=" ")
    # Remove extra whitespace
    text = " ".join(text.split())
    return text

def crawl_site(start_url, max_pages=MAX_PAGES):
    """
    Crawls the site starting from 'start_url', up to 'max_pages' pages.
    Returns a list of dicts: [{url, text, title}, ...]
    """
    to_visit = [start_url]
    visited = set()
    crawled_data = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
                page_text = clean_text(resp.text)

                # Extract a simple <title> if present (not critical, but can be nice metadata)
                soup = BeautifulSoup(resp.text, "html.parser")
                page_title = soup.title.string.strip() if soup.title else ""

                # Store in results
                crawled_data.append({
                    "url": url,
                    "title": page_title,
                    "content": page_text
                })

                # Find links to follow
                for link_tag in soup.find_all("a", href=True):
                    absolute_link = urljoin(url, link_tag["href"])
                    if is_valid_url(absolute_link) and absolute_link not in visited:
                        to_visit.append(absolute_link)

            # Be polite, add a small delay
            time.sleep(1)

        except Exception as e:
            print(f"Error crawling {url}: {e}")

    return crawled_data

def main():
    # 1) Crawl
    print(f"Starting crawl at: {START_URL}")
    data = crawl_site(START_URL, MAX_PAGES)
    print(f"Crawled {len(data)} pages.")

    # 2) Output to JSON
    # This file will contain a list of objects, each with {url, title, content}
    output_file = "neckarmedia_crawl.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Output saved to {output_file}")

if __name__ == "__main__":
    main()