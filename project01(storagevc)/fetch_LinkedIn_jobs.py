from  urllib.parse import quote_plus
import json
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from fetch_specific_LinkiedIn_job import fetch as fetch_specific_job
from utils import safe_text, safe_attr, log_job

def build_search_url(keywords: str, location: str) -> str:
    return (
        "https://www.linkedin.com/jobs/search"
        f"?keywords={quote_plus(keywords)}"
        f"&location={quote_plus(location)}"
        "&position=1&pageNum=0"
    )
    



async def main(
    keywords: str = "junior software engineer",
    location: str = "United States",
):
    linked_in_data = {"count": 0, "data": []}

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        list_page = await browser.new_page()
        detail_page = await browser.new_page()

        search_url = build_search_url(keywords, location)
        print("scraping url:", search_url)
        await list_page.goto(search_url)

        job_cards = list_page.locator("ul.jobs-search__results-list > li")
        linked_in_data["count"] = min(await job_cards.count(), 9)
        print(f'{linked_in_data["count"]} jobs to scrape ')

        for i in range(linked_in_data["count"]):
            card = job_cards.nth(i)
            info_url = await safe_attr(card.locator("a.base-card__full-link"), "href")

            details = None

            job_info = {
                "title": await safe_text(card.locator("h3.base-search-card__title")),
                "company": await safe_text(card.locator("h4.base-search-card__subtitle")),
                "location": await safe_text(card.locator(".job-search-card__location")),
                "date": await safe_text(card.locator("time")),
                "Job Details URL": info_url,
            }
            if info_url:
                try:
                    await detail_page.goto(info_url, wait_until="domcontentloaded")
                    details = await fetch_specific_job(detail_page)
                    job_info["details"] = details
                except Exception as e:
                    print(f"an error occured getting the job details for {info_url}: {e}")
                    job_info["details"] = None
                    continue
            log_job(i, linked_in_data["count"], job_info)
            linked_in_data["data"].append(job_info)
            await asyncio.sleep(2)

        await browser.close()

    with open("linkedIn_data.json", "w", encoding="utf-8") as f:
        json.dump(linked_in_data, f, indent=4, ensure_ascii=False)
    return linked_in_data["data"]


if __name__ == "__main__":
    asyncio.run(main())
