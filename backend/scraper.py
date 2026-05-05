"""
Promise vs Progress - Karnataka Road Infrastructure Scraper
============================================================
Scrapes project data from Karnataka PWD, government portals,
and news sources (The Hindu, Deccan Herald).

Run:
    python scraper.py

Output:
    projects.json (in the same directory)
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import logging
from datetime import datetime
from typing import Optional

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; PromiseVsProgress-Bot/1.0; "
        "+https://github.com/your-repo)"
    )
}

# Keywords that indicate road/infrastructure relevance
INFRASTRUCTURE_KEYWORDS = [
    "road", "highway", "flyover", "bridge", "underpass", "overpass",
    "expressway", "ring road", "bypass", "corridor", "signal", "junction",
    "infrastructure", "pwm", "public works", "nhai", "nh-", "state highway",
    "widening", "resurfacing", "pothole", "footpath", "metro road",
]

# Karnataka districts / cities used for location filtering
KARNATAKA_LOCATIONS = [
    "karnataka", "bengaluru", "bangalore", "mysuru", "mysore", "hubli",
    "dharwad", "belagavi", "belgaum", "mangaluru", "mangalore", "kalaburagi",
    "gulbarga", "ballari", "bellary", "shivamogga", "shimoga", "tumakuru",
    "tumkur", "udupi", "hassan", "davangere", "vijayapura", "bijapur",
    "raichur", "koppal", "gadag", "bagalkot", "chitradurga", "mandya",
    "chamarajanagar", "kodagu", "coorg", "chikkamagaluru", "chikmagalur",
    "bidar", "yadgir", "ramanagara", "chikkaballapur",
]

OUTPUT_FILE = "projects.json"

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_page(url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
    """Fetch a URL and return a BeautifulSoup object, or None on failure."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        log.warning(f"Could not fetch {url}: {e}")
        return None


def is_karnataka_related(text: str) -> bool:
    """Return True if the text mentions a Karnataka location."""
    text_lower = text.lower()
    return any(loc in text_lower for loc in KARNATAKA_LOCATIONS)


def is_infrastructure_related(text: str) -> bool:
    """Return True if the text mentions road/infrastructure keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in INFRASTRUCTURE_KEYWORDS)


def extract_budget(text: str) -> str:
    """
    Try to pull a ₹ / Rs / crore / lakh figure from free text.
    Returns the first match found, or empty string.
    """
    patterns = [
        r"₹\s?[\d,]+(?:\.\d+)?\s?(?:crore|lakh|cr|l)?",
        r"Rs\.?\s?[\d,]+(?:\.\d+)?\s?(?:crore|lakh|cr|l)?",
        r"[\d,]+(?:\.\d+)?\s?(?:crore|lakh)\s?(?:rupees)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return ""


def extract_location(text: str) -> str:
    """Return the first Karnataka location found in text, or empty string."""
    text_lower = text.lower()
    for loc in KARNATAKA_LOCATIONS:
        if loc in text_lower:
            # Return the display name (title case)
            return loc.title()
    return ""


def build_project(
    name: str,
    location: str,
    budget: str,
    description: str,
    date: str,
    source: str,
) -> dict:
    """Assemble a clean project dictionary."""
    return {
        "name": name.strip(),
        "location": location.strip(),
        "budget": budget.strip(),
        "description": description.strip(),
        "date": date.strip(),
        "source": source.strip(),
        "scraped_at": datetime.utcnow().isoformat() + "Z",
    }


def is_valid_project(project: dict) -> bool:
    """A project must at minimum have a name and pass both filters."""
    combined = f"{project['name']} {project['description']} {project['location']}"
    return (
        bool(project["name"])
        and is_karnataka_related(combined)
        and is_infrastructure_related(combined)
    )

# ── Source 1: The Hindu – Karnataka infrastructure search ────────────────────

def scrape_the_hindu() -> list[dict]:
    """
    Scrape The Hindu's search results for Karnataka road/infrastructure news.
    The Hindu's search page returns articles with title, summary, and date.
    """
    log.info("Scraping The Hindu...")
    projects = []

    search_url = (
        "https://www.thehindu.com/search/?q=karnataka+road+infrastructure"
    )
    soup = get_page(search_url)
    if not soup:
        return projects

    # The Hindu search results sit in <div class="element"> blocks
    articles = soup.find_all("div", class_="element")

    for article in articles:
        title_tag = article.find("h3") or article.find("h2")
        summary_tag = article.find("p")
        date_tag = article.find("span", class_="dateline") or article.find("time")

        title = title_tag.get_text(strip=True) if title_tag else ""
        summary = summary_tag.get_text(strip=True) if summary_tag else ""
        date = date_tag.get_text(strip=True) if date_tag else ""

        combined = f"{title} {summary}"
        project = build_project(
            name=title,
            location=extract_location(combined),
            budget=extract_budget(combined),
            description=summary,
            date=date,
            source="The Hindu",
        )
        if is_valid_project(project):
            projects.append(project)

    log.info(f"  → {len(projects)} projects from The Hindu")
    return projects

# ── Source 2: Deccan Herald – Karnataka roads search ─────────────────────────

def scrape_deccan_herald() -> list[dict]:
    """
    Scrape Deccan Herald search for Karnataka road infrastructure news.
    """
    log.info("Scraping Deccan Herald...")
    projects = []

    search_url = (
        "https://www.deccanherald.com/search?q=karnataka+road+infrastructure"
    )
    soup = get_page(search_url)
    if not soup:
        return projects

    # Deccan Herald search results use <article> tags
    articles = soup.find_all("article")

    for article in articles:
        title_tag = article.find("h2") or article.find("h3")
        summary_tag = article.find("p")
        date_tag = article.find("time") or article.find(
            "span", class_=re.compile(r"date|time", re.I)
        )

        title = title_tag.get_text(strip=True) if title_tag else ""
        summary = summary_tag.get_text(strip=True) if summary_tag else ""
        date = ""
        if date_tag:
            date = date_tag.get("datetime", "") or date_tag.get_text(strip=True)

        combined = f"{title} {summary}"
        project = build_project(
            name=title,
            location=extract_location(combined),
            budget=extract_budget(combined),
            description=summary,
            date=date,
            source="Deccan Herald",
        )
        if is_valid_project(project):
            projects.append(project)

    log.info(f"  → {len(projects)} projects from Deccan Herald")
    return projects

# ── Source 3: Karnataka PWD (kpwd.karnataka.gov.in) ─────────────────────────

def scrape_karnataka_pwd() -> list[dict]:
    """
    Scrape the Karnataka Public Works Department portal.
    PWD publishes tender notices and project updates.
    """
    log.info("Scraping Karnataka PWD...")
    projects = []

    # PWD tenders / news page
    urls_to_try = [
        "https://kpwd.karnataka.gov.in/english",
        "https://kpwd.karnataka.gov.in/page/Tenders/en",
    ]

    for url in urls_to_try:
        soup = get_page(url)
        if not soup:
            continue

        # Look for any table rows or list items with project/tender info
        rows = soup.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            row_text = " ".join(c.get_text(strip=True) for c in cells)
            if not is_infrastructure_related(row_text):
                continue

            name = cells[0].get_text(strip=True)
            description = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            budget = extract_budget(row_text)
            date = cells[-1].get_text(strip=True) if len(cells) > 2 else ""

            project = build_project(
                name=name,
                location=extract_location(f"{name} {description}") or "Karnataka",
                budget=budget,
                description=description,
                date=date,
                source="Karnataka PWD",
            )
            if is_valid_project(project):
                projects.append(project)

        # Also grab any paragraph-style announcements
        for tag in soup.find_all(["li", "p"]):
            text = tag.get_text(strip=True)
            if len(text) < 30:
                continue
            if is_infrastructure_related(text) and is_karnataka_related(text):
                project = build_project(
                    name=text[:120],          # first 120 chars as a name proxy
                    location=extract_location(text) or "Karnataka",
                    budget=extract_budget(text),
                    description=text,
                    date="",
                    source="Karnataka PWD",
                )
                projects.append(project)

    log.info(f"  → {len(projects)} projects from Karnataka PWD")
    return projects

# ── Source 4: data.karnataka.gov.in (Open Data Portal) ──────────────────────

def scrape_karnataka_open_data() -> list[dict]:
    """
    Karnataka's open data portal sometimes lists road / PWD datasets.
    We scrape the dataset listing page for road-related entries.
    """
    log.info("Scraping Karnataka Open Data Portal...")
    projects = []

    url = "https://data.karnataka.gov.in/datasets?category=Infrastructure"
    soup = get_page(url)
    if not soup:
        return projects

    for item in soup.find_all(["li", "div", "tr"]):
        text = item.get_text(separator=" ", strip=True)
        if not is_infrastructure_related(text):
            continue

        title_tag = item.find(["h2", "h3", "h4", "a"])
        title = title_tag.get_text(strip=True) if title_tag else text[:100]

        project = build_project(
            name=title,
            location=extract_location(text) or "Karnataka",
            budget=extract_budget(text),
            description=text[:300],
            date="",
            source="Karnataka Open Data Portal",
        )
        if is_valid_project(project):
            projects.append(project)

    log.info(f"  → {len(projects)} projects from Karnataka Open Data Portal")
    return projects

# ── Deduplication ─────────────────────────────────────────────────────────────

def deduplicate(projects: list[dict]) -> list[dict]:
    """Remove projects with duplicate names (case-insensitive)."""
    seen = set()
    unique = []
    for p in projects:
        key = p["name"].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(p)
    return unique

# ── Save to JSON ──────────────────────────────────────────────────────────────

def save_to_json(projects: list[dict], filepath: str = OUTPUT_FILE) -> None:
    """Write the list of projects to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)
    log.info(f"Saved {len(projects)} projects → {filepath}")

# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_scraper() -> list[dict]:
    """
    Orchestrates all scrapers, merges results, deduplicates,
    and saves to projects.json.
    """
    log.info("=== Promise vs Progress Scraper Starting ===")

    all_projects: list[dict] = []

    # Run each scraper and collect results
    scrapers = [
        scrape_the_hindu,
        scrape_deccan_herald,
        scrape_karnataka_pwd,
        scrape_karnataka_open_data,
    ]

    for scraper_fn in scrapers:
        try:
            results = scraper_fn()
            all_projects.extend(results)
        except Exception as e:
            log.error(f"Scraper {scraper_fn.__name__} failed: {e}")

    # Clean up
    unique_projects = deduplicate(all_projects)
    log.info(
        f"Total collected: {len(all_projects)} | "
        f"After dedup: {len(unique_projects)}"
    )

    save_to_json(unique_projects)
    log.info("=== Scraper Done ===")
    return unique_projects


if __name__ == "__main__":
    run_scraper()