from bs4 import BeautifulSoup
from curl_cffi import requests
import csv
import datetime
import os
import time
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def get_product_links(query, page_number=1):
    search_url = f"https://www.amazon.in/s?k={query}&page={page_number}"
    print(f"Searching: {search_url}")
    
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Search Network error: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all('a', href=True)

    product_links = []

    for link in links:
        link_href = link['href']
             
        if "https://aax-eu-zaz.amazon.in" not in link_href:
            if "/dp/" in link_href: 
                if "https" in link_href:
                    full_url = link_href
                else:
                    full_url = "https://www.amazon.in" + link_href
                    
                clean_url = full_url.split("?")[0]
                
                if clean_url not in product_links:
                    product_links.append(clean_url)
                
    return product_links


def scrap(amazon_url):
    current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    current_date = datetime.datetime.today().strftime("%Y-%m-%d")

    try:
        response = requests.get(amazon_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[{current_time}] Network error on {amazon_url}: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find(id="productTitle")
    price_tag = soup.find(class_="a-price-whole")
    rating_tag = soup.find("span", class_="a-icon-alt") 

    title = title_tag.get_text(strip=True) if title_tag else "N/A"
    price = price_tag.get_text(strip=True).replace(",", "").replace(".", "") if price_tag else "N/A"
    rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

    head = ["Product_Name", "Price", "Rating", "Date", "Time", "URL"]
    data = [title, price, rating, current_date, current_time, amazon_url]

    file_exists = os.path.isfile("Scraped_Data.csv")

    with open("Scraped_Data.csv", "a", newline='', encoding='UTF8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(head)
        writer.writerow(data)
        
    print(f"Logged: {title[:30]}... | ₹{price}")

def main():
    search_query = "Amd Ryzen 7"
    pages_to_scrape = 3
    
    for page in range(1, pages_to_scrape + 1):
        print(f"\n--- Scraping Page {page} ---")
        links = get_product_links(search_query, page_number=page)
        
        print(f"Found {len(links)} products on page {page}.")
        
        for url in links:
            scrap(url)
            # Crucial: Sleep between 3 and 7 seconds between each product to avoid bans
            time.sleep(random.uniform(3, 7)) 

if __name__ == "__main__":
    main()