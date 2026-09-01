import asyncio
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth
from utils import safe_text

DEFAULT_URL = (
    "https://www.linkedin.com/jobs/view/senior-software-engineer-%E2%80%93-go-golang-at-general-motors-4419969671"
    "?position=1&pageNum=0&refId=vvrA4%2BwwLmzn41Pdikm3hA%3D%3D&trackingId=aQqbYTpQOCq7l6%2BOLKO88Q%3D%3D"
)


async def fetch(job_page: Page):
    header = job_page.locator("div.top-card-layout__card")
    description = job_page.locator("div.show-more-less-html__markup")
    criteria_items = job_page.locator("ul.description__job-criteria-list > li")

    job_info = {}
    job_info["num_applicants"] = await safe_text(header.locator("span.num-applicants__caption"))
    job_info["description"] = await safe_text(description)

    try:
        await criteria_items.first.wait_for(state="visible")

        for i in range(await criteria_items.count()):
            item = criteria_items.nth(i)
            label = await safe_text(item.locator("h3.description__job-criteria-subheader"))
            value = await safe_text(item.locator("span.description__job-criteria-text--criteria"))
            job_info[label] = value
    except Exception as e:
        print(f"an error occured getting the job criteria: {e}")

    return job_info


if __name__ == "__main__":
    async def run():
        
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(DEFAULT_URL, wait_until="networkidle")
            print(await fetch(page))
            await browser.close()

    asyncio.run(run())
