from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:3000/auth")
    page.wait_for_timeout(10000)

    # Login
    page.get_by_placeholder("you@example.com").fill("admin@titantrade.com")
    page.get_by_placeholder("Enter password").fill("adminpassword")
    page.get_by_role("button", name="Log In", exact=True).click()
    page.wait_for_timeout(5000)

    # Navigate to signals
    page.goto("http://localhost:3000/signals")
    page.wait_for_timeout(5000)

    # Change market to Indian
    page.get_by_test_id("market-select").click()
    page.wait_for_timeout(1000)
    page.get_by_text("Indian", exact=True).click()
    page.wait_for_timeout(2000)

    # Check Indian custom asset input
    page.get_by_test_id("asset-search-input").fill("NSE:TATASTEEL")
    page.wait_for_timeout(1000)

    # Change strategy to one of the new ones
    page.get_by_test_id("strategy-select").click()
    page.wait_for_timeout(1000)
    page.get_by_text("Elliott Wave Theory").click()
    page.wait_for_timeout(1000)

    # Generate signal
    page.get_by_test_id("generate-signal-btn").click()
    page.wait_for_timeout(10000)

    # Take screenshot at the key moment
    import os
    os.makedirs("/home/jules/verification/screenshots", exist_ok=True)
    os.makedirs("/home/jules/verification/videos", exist_ok=True)
    page.screenshot(path="/home/jules/verification/screenshots/verification.png")
    page.wait_for_timeout(1000)  # Hold final state for the video

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()
        try:
            run_cuj(page)
        except Exception as e:
            print(e)
            page.screenshot(path="/home/jules/verification/screenshots/verification_error.png")
        finally:
            context.close()  # MUST close context to save the video
            browser.close()
