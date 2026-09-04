# Advanced Web Scraper — Amazon.in Product Scraper

A Python scraper that searches Amazon.in for a given keyword, collects product page links across multiple result pages, and extracts the **title, price, and rating** of each product into a CSV file.

---

## How It Works

The script has three parts:

### 1. `get_product_links(query, page_number=1)`
Builds a search URL (`https://www.amazon.in/s?k={query}&page={page_number}`), fetches the results page, and parses every `<a href>` tag on it. A link is kept as a product link only if:
- it contains `/dp/` (Amazon's standard pattern for a product detail page), **and**
- it does **not** come from `https://aax-eu-zaz.amazon.in` (Amazon's sponsored/ad-redirect domain — filtering this out avoids wasting requests on ad trackers instead of real product pages).

Relative links are converted to absolute URLs, query strings are stripped (`.split("?")[0]`), and duplicates are removed. It returns a clean, deduplicated list of product URLs for that page.

### 2. `scrap(amazon_url)`
Fetches a single product page and pulls out:

| Field | Source selector |
|---|---|
| Product name | `id="productTitle"` |
| Price | `class="a-price-whole"` |
| Rating | `span class="a-icon-alt"` |

If a field isn't found, it's logged as `"N/A"` instead of crashing — the script keeps going even if Amazon's layout differs on a given page. Each result (plus a timestamp) is appended as a row to `Scraped_Data.csv`, writing the header row automatically the first time the file is created.

### 3. `main()`
Orchestrates the whole run: for `pages_to_scrape` pages of results for `search_query`, it collects product links, then scrapes each one individually, pausing between requests (see below).

---

## Requirements

- **Python 3.8+**
- Packages:
  - [`curl_cffi`](https://github.com/lexiforest/curl_cffi)
  - `beautifulsoup4`

Everything else used (`csv`, `datetime`, `os`, `time`, `random`) is from the Python standard library.

### Install

```bash
pip install -r requirements.txt
```

or install the two packages directly:

```bash
pip install curl_cffi beautifulsoup4
```

---

## Usage

Edit the two variables at the top of `main()` to set what to search and how many result pages to crawl:

```python
def main():
    search_query = "Amd Ryzen 7"   # any Amazon search term
    pages_to_scrape = 3            # number of search-result pages to walk through
```

Then run:

```bash
python Advanced_Web_Scraper.py
```

Progress is printed to the console as it runs (page being searched, number of products found, each item logged as it's scraped).

### Output

Results are appended to `Scraped_Data.csv` in the same directory, with these columns:

| Product_Name | Price | Rating | Date | Time | URL |
|---|---|---|---|---|---|

Because the script **appends** rather than overwrites, you can run it repeatedly (e.g., on different search terms) and build up one running dataset. Delete or rename the CSV if you want a fresh file.

---

## Anti-Bot / Anti-Ban Strategy (read this before scaling up)

Amazon actively fingerprints and rate-limits automated traffic. This script layers a few defenses together — understanding each one matters if you plan to modify or scale it.

### 1. `curl_cffi` instead of `requests`
This is the most important design choice in the script. Standard Python HTTP libraries (`requests`, `urllib3`) produce a distinctive **TLS/JA3 handshake fingerprint** at the network level — separate from HTTP headers — that anti-bot systems (Akamai, PerimeterX, Cloudflare, and Amazon's own detection) use to flag traffic as non-browser, *even if the headers look perfectly legitimate*. `curl_cffi` wraps a patched `libcurl` that can reproduce the exact TLS fingerprint of real browsers, and it exposes a `requests`-compatible API (`from curl_cffi import requests`), which is why it's a near drop-in replacement here — same `.get()`, `.raise_for_status()`, and `requests.exceptions.RequestException` handling you'd use with plain `requests`.

> ⚠️ **Important gap to be aware of:** `curl_cffi` only spoofs a browser's TLS fingerprint when you pass an `impersonate` argument, e.g. `requests.get(url, headers=HEADERS, impersonate="chrome124")`. As currently written, this script's `.get()` calls **don't set `impersonate`**, so it's effectively running with `curl_cffi`'s default behavior rather than actively impersonating a browser at the TLS layer. If you're seeing bans/CAPTCHAs, adding `impersonate="chrome124"` (or a similarly current version) to both `requests.get()` calls is the single highest-impact fix.

### 2. Browser-like headers (`HEADERS`)
A full header set (`User-Agent`, `Accept`, `Accept-Language`, `Accept-Encoding`, `DNT`, `Connection`, `Upgrade-Insecure-Requests`) is sent with every request so traffic looks like a real Chrome browser at the HTTP layer, not a bare script with a minimal or missing header set.

### 3. Randomized delay between requests
```python
time.sleep(random.uniform(3, 7))
```
After scraping each product, the script waits a random 3–7 seconds before the next one. This is deliberately *randomized* rather than a fixed interval — a constant delay is itself a detectable bot signature, while a randomized human-like pace helps avoid tripping request-rate-based throttling or temporary IP bans. This is the main defense against **rate-based** detection, as opposed to the TLS/header defenses above which target **fingerprint-based** detection.

### 4. Filtering out ad-redirect links
Skipping `aax-eu-zaz.amazon.in` links means the scraper doesn't waste requests (and expose itself to more traffic volume than necessary) fetching sponsored-ad redirect pages instead of actual products.

---

## Known Limitations

- **Single IP, no proxy rotation** — all the above helps a script blend in, but sustained or high-volume scraping from one IP can still get rate-limited or banned. For serious scale, pair this with rotating residential/datacenter proxies.
- **No CAPTCHA handling** — if Amazon serves a CAPTCHA/verification page, `scrap()` will just fail to find the selectors and log `"N/A"` rows rather than detecting and solving/retrying.
- **No retry/backoff logic** — a failed request is logged and skipped rather than retried.
- **Selector fragility** — `productTitle`, `a-price-whole`, and `a-icon-alt` are Amazon's current class/id names. Amazon changes its markup periodically, which can silently break extraction (you'll see a lot of `"N/A"` rows rather than an error).
- **`impersonate` not set** — see the callout above.

---

## Disclaimer

Automated scraping of Amazon is restricted under Amazon's Conditions of Use, and scraping behavior/legality can vary by jurisdiction and use case. Use this script at your own discretion, respect `robots.txt` and rate limits, and avoid scraping personal data or reproducing content beyond fair use. This project is provided for educational purposes.

---

## License

Distributed under the MIT License — see [LICENSE](LICENSE) for details.
