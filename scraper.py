"""
GitHub Trending Daily Scraper
Fetches https://github.com/trending and extracts top repositories data.
Runs in GitHub Actions, outputs JSON to data/YYYY-MM-DD.json
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://github.com/trending"
DATA_DIR = "data"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def parse_stars(text: str) -> int:
    """Parse star count string like '1,234' or '1.2k' into integer."""
    text = text.strip().replace(",", "").lower()
    if "k" in text:
        return int(float(text.replace("k", "")) * 1000)
    try:
        return int(text)
    except ValueError:
        return 0


def fetch_trending(since: str = "daily", language: str = "") -> list[dict]:
    """Fetch trending repositories from GitHub."""
    url = BASE_URL
    params = {}
    if since and since != "daily":
        params["since"] = since
    if language:
        url += f"/{language}"

    resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    repos = []

    for article in soup.find_all("article", class_="Box-row"):
        try:
            repo = {}

            # Extract owner/repo from <h2>
            h2 = article.find("h2", class_="h3")
            if not h2:
                continue
            link = h2.find("a")
            if not link:
                continue
            href = link.get("href", "").strip().lstrip("/")
            parts = href.split("/")
            if len(parts) >= 2:
                repo["owner"] = parts[0].strip()
                repo["name"] = parts[1].strip()
            else:
                continue

            # Extract description
            desc_el = article.find("p", class_="col-9")
            repo["description"] = desc_el.get_text(strip=True) if desc_el else ""

            # Extract language
            lang_el = article.find("span", itemprop="programmingLanguage")
            repo["language"] = lang_el.get_text(strip=True) if lang_el else ""

            # Extract stars, forks, stars today from the f6 div
            f6 = article.find("div", class_="f6")
            stars_total = 0
            stars_today = 0
            forks = 0

            if f6:
                links = f6.find_all("a")
                for a in links:
                    text = a.get_text(strip=True)
                    href_attr = a.get("href", "")
                    if "/stargazers" in href_attr:
                        stars_total = parse_stars(text)
                    elif "/forks" in href_attr:
                        forks = parse_stars(text)

                # Stars today is usually in a <span> without link
                spans = f6.find_all("span", class_="d-inline-block")
                for span in spans:
                    text = span.get_text(strip=True)
                    if "star" in text.lower():
                        # Extract number from "1,234 stars today"
                        num_match = re.search(r"[\d,]+", text)
                        if num_match and "today" in text.lower():
                            stars_today = parse_stars(num_match.group())

            repo["stars"] = stars_total
            repo["stars_today"] = stars_today
            repo["forks"] = forks

            repos.append(repo)
        except Exception as e:
            print(f"Warning: failed to parse article: {e}", file=sys.stderr)
            continue

    return repos


def save_results(repos: list[dict]) -> str:
    """Save results to a date-stamped JSON file. Returns the file path."""
    os.makedirs(DATA_DIR, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(DATA_DIR, f"{today}.json")

    output = {
        "date": today,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(repos),
        "repositories": repos,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return filepath


def generate_readme(repos: list[dict], today: str) -> str:
    """Generate README.md with top 10 trending repos. Returns the file path."""
    top10 = repos[:10]

    lines = [
        "# GitHub Trending Top 10 - Daily Report",
        "",
        f"**Date:** {today}",
        f"**Total repos scraped:** {len(repos)}",
        "",
        "| # | Repository | Stars | Stars Today | Language | Description |",
        "|---|------------|------:|--------:|----------|-------------|",
    ]

    for i, repo in enumerate(top10, 1):
        desc = repo["description"].replace("|", "\\|")[:120]
        lines.append(
            f"| {i} | **{repo['owner']}/{repo['name']}** "
            f"| {repo['stars']:,} "
            f"| +{repo['stars_today']:,} "
            f"| {repo['language']} "
            f"| {desc} |"
        )

    lines.extend([
        "",
        "---",
        f"*Auto-generated by [GitHub Actions](https://github.com/dongminchris-dot/github-trending-data/actions) at {datetime.now(timezone.utc).isoformat()}*",
    ])

    readme_path = "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return readme_path


def main():
    print("Fetching GitHub trending repositories...")
    repos = fetch_trending(since="daily")
    print(f"Found {len(repos)} repositories")

    filepath = save_results(repos)
    print(f"JSON saved to {filepath}")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    readme_path = generate_readme(repos, today)
    print(f"README saved to {readme_path}")

    # Print summary for workflow log
    print("\n--- Top 10 ---")
    for i, repo in enumerate(repos[:10], 1):
        print(
            f"  {i:2d}. {repo['owner']}/{repo['name']} "
            f"{repo['stars']:,} stars (+{repo['stars_today']:,} today) "
            f"[{repo['language']}]"
        )
        if repo["description"]:
            print(f"      {repo['description'][:100]}")


if __name__ == "__main__":
    main()
