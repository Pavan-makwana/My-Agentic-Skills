"""
enrich_company_details.py
--------------------------
Enriches each filtered food company with publicly available contact details:
  - Business email address
  - Phone / WhatsApp number
  - Google Maps / Business Profile link
  - Social media profiles (Instagram / LinkedIn / Facebook)
  - Website status (Has Website: Yes/No — no-website companies are HIGH PRIORITY)

Input:  mca_leads/YYYY-MM/food_leads_raw_YYYY-MM.csv
Output: mca_leads/YYYY-MM/food_business_leads_YYYY-MM.xlsx

Usage:
    python scripts/enrich_company_details.py [path_to_raw_csv]

Enrichment uses the DuckDuckGo Search API (no API key required) and
scrapes the top search results for contact information.
"""

import os
import sys
import re
import time
import random
import pathlib
import datetime
import glob
import base64
import urllib.parse
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ── Configuration ─────────────────────────────────────────────────────────────
LEADS_ROOT = pathlib.Path("mca_leads")
REQUEST_DELAY_MIN = 1.5   # seconds between web requests
REQUEST_DELAY_MAX = 3.5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)
PHONE_PATTERN = re.compile(
    r"(?:\+91[\s\-]?)?(?:0)?[6-9]\d{9}"
)


def _decode_bing_url(bing_url: str) -> str:
    """Extract and decode the destination URL from a Bing redirect link."""
    try:
        parsed = urllib.parse.urlparse(bing_url)
        qs = urllib.parse.parse_qs(parsed.query)
        if "u" in qs:
            val = qs["u"][0]
            if val.startswith("a1"):
                b64 = val[2:]
                decoded = base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4)).decode("utf-8")
                return decoded
    except Exception:
        pass
    return bing_url


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web for company contact details and official site.
    Returns a list of dicts: [{'title': ..., 'url': ..., 'snippet': ...}]
    """
    results = []
    try:
        url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select("li.b_algo")[:max_results]:
                link_el = item.select_one("h2 a")
                if not link_el or not link_el.get("href"):
                    continue
                raw_url = link_el["href"]
                clean_url = _decode_bing_url(raw_url)
                title = link_el.get_text(strip=True)
                snippet_el = item.select_one(".b_caption p, .b_snippet, p")
                snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
                results.append({
                    "title": title,
                    "url": clean_url,
                    "snippet": snippet,
                })
    except Exception as e:
        print(f"    [search] Query error for {query!r}: {e}")
    return results


def scrape_page(url: str) -> str:
    """Fetch a URL and return its visible text content (truncated)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove script/style
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:5000]
    except Exception:
        return ""


def extract_emails(text: str) -> list[str]:
    found = EMAIL_PATTERN.findall(text)
    # Filter out common false positives
    return [e for e in found if not e.endswith((".png", ".jpg", ".gif", ".css"))]


def extract_phones(text: str) -> list[str]:
    return PHONE_PATTERN.findall(text)


def find_social_profiles(text: str, url: str) -> dict:
    """Extract social media links from text or URL context."""
    profiles = {}
    for platform, patterns in {
        "instagram": [r"instagram\.com/[\w.]+"],
        "linkedin":  [r"linkedin\.com/(?:company|in)/[\w\-]+"],
        "facebook":  [r"facebook\.com/[\w.\-]+"],
    }.items():
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                profiles[platform] = "https://" + m.group().lstrip("https://").lstrip("http://")
    return profiles


# Directory & registry domains to exclude when looking for an official website
DIRECTORY_DOMAINS = [
    "zaubacorp.com", "tofler.in", "instafinancials.com", "mca.gov.in",
    "indiamart.com", "justdial.com", "sulekha.com", "tradeindia.com",
    "facebook.com", "instagram.com", "linkedin.com", "twitter.com",
    "youtube.com", "wikipedia.org", "google.com", "bing.com",
    "quickr.com", "olx.in", "magicbricks.com", "99acres.com",
    "reddit.com", "quora.com", "github.com", "pinterest.com",
    "tripadvisor.com", "zomato.com", "swiggy.com",
]

# Educational or generic content domains that might match keywords (e.g. "Gupta Empire")
EXCLUDE_KEYWORD_DOMAINS = [
    "upsc", "study", "exam", "history", "wikipedia", "dictionary", "thehindu",
    "timesofindia", "ndtv", "news18", "hindustantimes", "britannica",
]


def has_website(company_name: str, city: str) -> tuple[bool, str]:
    """
    Check if the company has an active official website.
    Verifies that the candidate domain/title is genuinely affiliated
    with the company rather than an unrelated educational or news page.
    Returns (has_website: bool, website_url: str).
    """
    query = f'"{company_name}" {city} official website'
    results = web_search(query, max_results=5)
    time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

    # Clean name tokens for relevance checking (ignore corporate suffixes)
    clean_name = re.sub(r"\b(pvt|private|ltd|limited|llp|inc|co|corp|services)\b", "", company_name, flags=re.I)
    name_tokens = [tok.lower() for tok in re.findall(r"\w{3,}", clean_name)]

    for r in results:
        url = r.get("url", "")
        url_lower = url.lower()
        title_lower = r.get("title", "").lower()
        snippet_lower = r.get("snippet", "").lower()

        if not url.startswith("http"):
            continue

        # Skip generic directories and portals
        if any(d in url_lower for d in DIRECTORY_DOMAINS):
            continue

        # Skip government, educational, or official portals
        if any(gov in url_lower for gov in [".gov", ".nic.in", ".ac.in", ".edu", "wikipedia"]):
            continue

        # Skip document / file downloads
        if url_lower.endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")):
            continue

        # Skip news/educational/exam resources
        if any(ex in url_lower for ex in EXCLUDE_KEYWORD_DOMAINS):
            continue

        # Check if the domain, title, or snippet shares keywords with the company name
        parsed = urllib.parse.urlparse(url_lower)
        netloc = parsed.netloc

        domain_has_match = any(tok in netloc for tok in name_tokens)
        title_has_match = any(tok in title_lower for tok in name_tokens)
        snippet_has_match = any(tok in snippet_lower for tok in name_tokens)

        if domain_has_match or (title_has_match and snippet_has_match):
            return True, url

    return False, ""


def enrich_company(row: pd.Series) -> pd.Series:
    """Enrich a single company row with contact details."""
    name = str(row.get("company_name", "")).strip()
    city = str(row.get("state", "")).strip()
    directors = str(row.get("directors", "")).strip()
    existing_email = str(row.get("email", "")).strip()

    print(f"  [enrich] {name} ({city})")

    result = {
        "enriched_email":     existing_email,
        "phone":              "",
        "whatsapp_hint":      "",
        "google_maps_link":   "",
        "instagram":          "",
        "linkedin":           "",
        "facebook":           "",
        "has_website":        "Unknown",
        "website_url":        "",
        "priority":           "Normal",
    }

    # Build search query
    query = f'"{name}" {city} contact email phone'
    results = web_search(query, max_results=5)
    time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

    all_text = " ".join(r.get("snippet", "") + " " + r.get("title", "") for r in results)

    # Scrape top candidate result for deeper info if relevant
    for r in results[:2]:
        url = r.get("url", "")
        if not any(d in url.lower() for d in DIRECTORY_DOMAINS):
            page_text = scrape_page(url)
            all_text += " " + page_text
            break

    # Extract email
    if not existing_email or "@" not in existing_email:
        emails = extract_emails(all_text)
        if emails:
            result["enriched_email"] = emails[0]

    # Extract phone
    phones = extract_phones(all_text)
    if phones:
        result["phone"] = phones[0]
        result["whatsapp_hint"] = f"https://wa.me/91{re.sub(r'[^0-9]', '', phones[0])[-10:]}"

    # Google Maps search link
    result["google_maps_link"] = (
        f"https://www.google.com/maps/search/{requests.utils.quote(name + ' ' + city)}"
    )

    # Social profiles
    socials = find_social_profiles(all_text, "")
    result.update(socials)

    # Website check
    site_found, site_url = has_website(name, city)
    result["has_website"] = "Yes" if site_found else "No"
    result["website_url"] = site_url
    if not site_found:
        result["priority"] = "HIGH — No Website"

    return pd.Series(result)


def find_raw_leads_file() -> pathlib.Path | None:
    pattern = str(LEADS_ROOT / "**" / "food_leads_raw_*.csv")
    files = glob.glob(pattern, recursive=True)
    if not files:
        return None
    return pathlib.Path(max(files, key=os.path.getmtime))


def main(raw_csv: pathlib.Path | None = None) -> str | None:
    if raw_csv is None:
        raw_csv = find_raw_leads_file()
    if raw_csv is None:
        print("[enrich] No raw leads CSV found. Run filter_food_companies.py first.")
        return None

    df = pd.read_csv(raw_csv, dtype=str).fillna("")
    print(f"[enrich] Enriching {len(df):,} companies ...")

    enriched_cols = df.apply(enrich_company, axis=1)
    df = pd.concat([df, enriched_cols], axis=1)

    today = datetime.date.today()
    month_str = today.strftime("%Y-%m")
    out_dir = LEADS_ROOT / month_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"food_business_leads_{month_str}.xlsx"

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Food Leads", index=False)

        # Auto-fit columns
        ws = writer.sheets["Food Leads"]
        for col_cells in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col_cells)
            ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 4, 60)

    print(f"[enrich] ✅ Saved enriched leads to {out_path}")
    return str(out_path)


if __name__ == "__main__":
    arg = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    result = main(arg)
    if not result:
        sys.exit(1)
