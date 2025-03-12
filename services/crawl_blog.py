from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import json
import time

DOMAIN = "neckarmedia.com"
BASE_URL = "https://www.neckarmedia.com/news-blog/"
MAX_PAGES = 1000

def fetch_blog_links():
    response = requests.get(BASE_URL, timeout=10)
    if response.status_code != 200:
        print(f"Failed to fetch blog links: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    select_tag = soup.find("select", id="archives-dropdown-2")
    if not select_tag:
        print("Archive dropdown not found")
        return []
    
    options = select_tag.find_all("option")
    return [option["value"] for option in options if "value" in option.attrs and option["value"].strip()]

def fetch_blog_content(url):
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        print(f"Failed to fetch blog content: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    post_links = []

    for h2 in soup.find_all("h2", class_="post-title entry-title"):
        a_tag = h2.find("a")
        if a_tag:
            post_links.append(a_tag["href"])

    return post_links

def clean_text(html_content):
    """Removes script/style tags and extracts visible text."""
    soup = BeautifulSoup(html_content, "lxml")
    for tag in soup([
        "script", "style", "noscript", "header", "footer", "select",
        "nav", "form", "input", "button", "img"]):
        tag.decompose()
    classes_to_remove = ["address", "rplg", "nm_socket", "footer"]
    for class_name in classes_to_remove:
        elements = soup.find_all(class_=class_name)
        for element in elements:
            element.decompose()

    id_to_remove = ["footer", "header", "nav", "form", "input", "button", "img"]
    for id_name in id_to_remove:
        elements = soup.find_all(id=id_name)
        for element in elements:
            element.decompose()

    text = " ".join(soup.get_text(separator=" ").split())
    return text

def extract_date(soup):
    time_tag = soup.find("time", class_="date-container")
    return time_tag.text.strip() if time_tag else "Unknown"

def crawl_blog_post(url):
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        print(f"Failed to fetch post: {url}")
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title else "Untitled"
    content = clean_text(response.text)
    date = extract_date(soup)
    
    return {"url": url, "title": title, "content": content, "date": date}

def main():
    blog_links = fetch_blog_links()
    all_posts = set()
    for blog_link in blog_links:
        print(f"Fetching posts from: {blog_link}")
        posts = fetch_blog_content(blog_link)
        all_posts.update(posts)
        print(f"Found {len(posts)} posts")
        time.sleep(1)
    
    crawled_posts = []
    for post in all_posts:
        post_data = crawl_blog_post(post)
        if post_data:
            crawled_posts.append(post_data)
        time.sleep(1)

    with open("blog_posts.json", "w") as f:
        json.dump(crawled_posts, f, ensure_ascii=False, indent=4)
    print(f"Successfully crawled blog posts")

if __name__ == "__main__":
    main()