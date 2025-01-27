from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import json
import time

START_URL = "https://neckarmedia.com/"  # The base site to start crawling
DOMAIN = "neckarmedia.com"
SITEMAP_URL = urljoin(START_URL, "/sitemap.xml")
MAX_PAGES = 1000

def is_valid_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False    
    if DOMAIN not in parsed.netloc:
        return False
    if any(url.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".pdf"]):
        return False
    return True


def clean_text(html_content):
    """
    Removes script/style tags and extracts visible text
    while trimming excess whitespace.
    """
    soup = BeautifulSoup(html_content, "lxml")

    # Remove <script> and <style> elements
    for tag in soup(["script", "style", "noscript", "header", "footer", "select", "nav", "form", "input", "button", "img"]):
        tag.decompose()

    classes_to_remove = ["address", "rplg", "nm_socket", "footer"]
    for class_name in classes_to_remove:
        elements = soup.find_all(class_=class_name)
        for element in elements:
            element.decompose()

    text = soup.get_text(separator=" ")
    # Remove extra whitespace
    text = " ".join(text.split())
    return text

def get_sitemap_urls(sitemap_url, visited_sitemaps=None):
    if visited_sitemaps is None:
        visited_sitemaps = set()

    if sitemap_url in visited_sitemaps:
        print(f"Skipping already processed sitemap: {sitemap_url}")
        return []

    visited_sitemaps.add(sitemap_url)
    urls = []

    try:
        response = requests.get(sitemap_url, timeout=10)
        if response.status_code == 200:
            print(f"Processing sitemap: {sitemap_url}")
            tree = ET.fromstring(response.content)
            for elem in tree.iter():
                if elem.tag.endswith("loc"):
                    loc = elem.text.strip()
                    if loc.endswith(".xml"):  # Sub-sitemap
                        print(f"Found sub-sitemap: {loc}")
                        urls.extend(get_sitemap_urls(loc, visited_sitemaps))
                    elif is_valid_url(loc):  # Direct URL
                        print(f"Found URL: {loc}")
                        urls.append(loc)
    except Exception as e:
        print(f"Error fetching or parsing sitemap: {e}")
    return urls

def extract_internal_links(html_content, base_url):
    """
    Extracts all internal links from the given HTML content.
    """
    soup = BeautifulSoup(html_content, "lxml")
    links = set()

    for tag in soup.find_all("a", href=True):
        href = urljoin(base_url, tag["href"])  # Resolve relative URLs
        if is_valid_url(href):
            links.add(href)

    return links

def crawl_site(urls, max_pages=MAX_PAGES):
    """
    Crawls the list of URLs.
    """
    visited = set()
    to_visit = set(urls)
    crawled_data = []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop()
        normalized_url = url.rstrip("/")
        if normalized_url in visited:
            print(f"Skipping already visited URL: {url}")
            continue
        visited.add(normalized_url)
        print(f"Crawling {url}")

        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
                page_text = clean_text(resp.text)
                internal_links = extract_internal_links(resp.text, url)

                to_visit.update(internal_links - visited)
                # Extract title and save data
                soup = BeautifulSoup(resp.text, "html.parser")
                page_title = soup.title.string.strip() if soup.title else ""

                crawled_data.append({
                    "url": url,
                    "title": page_title,
                    "content": page_text
                })

            # Be polite
            time.sleep(1)

        except Exception as e:
            print(f"Error crawling {url}: {e}")

    return crawled_data

def main():
    print("Fetching sitemap...")
    sitemap_urls = get_sitemap_urls(SITEMAP_URL)
    print(f"Found {len(sitemap_urls)} URLs in the sitemap hierarchy.")

    print("Starting crawl...")
    data = crawl_site(sitemap_urls, MAX_PAGES)
    print(f"Crawled {len(data)} pages.")

    # Save results to JSON
    output_file = "neckarmedia_crawl.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Output saved to {output_file}")

if __name__ == "__main__":
    main()