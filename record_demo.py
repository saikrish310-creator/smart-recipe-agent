import asyncio
import os
import shutil
import time
from playwright.async_api import async_playwright

APP_URL = "https://smart-recipe-frontend-182366599973.us-east1.run.app"
OUTPUT_DIR = "/config/Desktop/Session1/smart-recipe-agent/demo_videos"
ARTIFACT_DIR = "/config/.gemini/antigravity/brain/f4d073a8-14d6-405e-af70-59fedceb6b81"

async def record():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        print(f"Opening {APP_URL}...")
        await page.goto(APP_URL, wait_until="networkidle")
        await asyncio.sleep(2)

        # Prompt 1: Core Recipe Concierge feature
        prompt1 = "Show my saved recipes and list their prep times"
        print(f"Sending prompt 1: '{prompt1}'")
        await page.fill("#input", prompt1)
        await asyncio.sleep(1)
        await page.click("button.submit-btn")

        print("Waiting for response 1...")
        await page.wait_for_selector(".msg-row.agent .bubble:not(:has(.typing-dots))", timeout=30000)
        await asyncio.sleep(4)

        # Prompt 2: Tool call, online recipe lookup, and image generation
        prompt2 = "Search online for an authentic Margherita pizza recipe and generate a photo for it"
        print(f"Sending prompt 2: '{prompt2}'")
        await page.fill("#input", prompt2)
        await asyncio.sleep(1)
        await page.click("button.submit-btn")

        print("Waiting for response 2...")
        await page.wait_for_selector(".msg-row.agent:nth-of-type(4) .bubble:not(:has(.typing-dots))", timeout=45000)
        await asyncio.sleep(6)

        video = page.video
        await context.close()
        await browser.close()

        video_path = await video.path()
        final_video_path = os.path.join(OUTPUT_DIR, "smart_recipe_demo.webm")
        shutil.copy(video_path, final_video_path)

        # Copy to artifact directory for embedding in walkthrough/artifact
        artifact_video_path = os.path.join(ARTIFACT_DIR, "smart_recipe_demo.webm")
        shutil.copy(video_path, artifact_video_path)

        print(f"Demo video successfully recorded and saved to:\n  - {final_video_path}\n  - {artifact_video_path}")
        return final_video_path

if __name__ == "__main__":
    asyncio.run(record())
