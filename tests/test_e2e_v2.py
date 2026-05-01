"""FOR-BAZI E2E Test v2 - with MiMo API integration test."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

API_KEY = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")


async def run_tests():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        passed = 0
        failed = 0
        errors = []

        def check(name, condition, detail=""):
            nonlocal passed, failed
            if condition:
                passed += 1
                print(f"  PASS: {name}")
            else:
                failed += 1
                msg = f"  FAIL: {name}" + (f" -- {detail}" if detail else "")
                print(msg)
                errors.append(msg)

        # ── Test 1: Page loads (with API key in URL) ────────────────────
        print("\n=== Test 1: Page Load ===")
        base_url = "http://localhost:8501"
        if API_KEY:
            base_url += f"?ANTHROPIC_AUTH_TOKEN={API_KEY}"
        await page.goto(base_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        title = await page.title()
        check("Page title", "玄冥" in title, f"Got: {title}")
        await page.screenshot(path=str(SCREENSHOTS_DIR / "v2_01_load.png"))

        # ── Test 2: Sidebar with API key input ─────────────────────────
        print("\n=== Test 2: Sidebar ===")
        sidebar = page.locator('[data-testid="stSidebar"]')
        check("Sidebar visible", await sidebar.is_visible())

        api_key_input = page.locator('input[type="password"]').first
        check("API Key input", await api_key_input.is_visible())

        # ── Test 3: Select MiMo provider ───────────────────────────────
        print("\n=== Test 3: Provider Selection ===")
        provider_select = page.locator('[data-testid="stSelectbox"]').first
        await provider_select.click()
        await page.wait_for_timeout(500)

        mimo_option = page.locator('li:has-text("MiMo")')
        if await mimo_option.count() > 0:
            await mimo_option.click()
            await page.wait_for_timeout(2000)
            check("MiMo provider selectable", True)
        else:
            check("MiMo provider selectable", False, "Option not found")

        # Wait for Streamlit to fully rerun after provider change
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "v2_02_mimo.png"))

        # ── Test 4: API Key ────────────────────────────────────────────
        print("\n=== Test 4: API Key ===")
        # After MiMo is selected, the API key should be auto-filled from URL param
        # Verify by checking the input value
        api_key_input = page.locator('input[type="password"]').first
        input_value = await api_key_input.input_value()
        check("API Key auto-filled from URL", len(input_value) > 5, f"Value length: {len(input_value)}")

        # ── Test 5: Generate bazi ──────────────────────────────────────
        print("\n=== Test 5: Generate Bazi ===")
        gen_button = page.locator('button:has-text("生成命盘")')
        await gen_button.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        await gen_button.click()

        # Wait for the API greeting to appear (MiMo can be slow)
        try:
            await page.locator('[data-testid="stChatMessage"]').first.wait_for(
                state="attached", timeout=20000
            )
        except Exception:
            pass  # Will be caught by the check below
        await page.wait_for_timeout(2000)  # Extra buffer for render
        await page.screenshot(path=str(SCREENSHOTS_DIR / "v2_03_generated.png"))

        # Check for greeting in chat
        chat_messages = page.locator('[data-testid="stChatMessage"]')
        msg_count = await chat_messages.count()
        check("Greeting message from API", msg_count > 0, f"Got {msg_count} messages")

        # Check for errors
        error_msgs = page.locator('[data-testid="stException"], [data-testid="stError"]')
        error_count = await error_msgs.count()
        check("No API errors", error_count == 0, f"Got {error_count} errors")
        if error_count > 0:
            for i in range(error_count):
                error_text = await error_msgs.nth(i).inner_text()
                print(f"    Error: {error_text[:100]}")

        # ── Test 6: Four pillars rendered ──────────────────────────────
        print("\n=== Test 6: Pillars ===")
        pillars = page.locator('.bazi-pillar')
        pillar_count = await pillars.count()
        check("4 pillar cards", pillar_count == 4, f"Got {pillar_count}")

        # ── Test 7: Tabs ───────────────────────────────────────────────
        print("\n=== Test 7: Tabs ===")
        for tab_name in ["大运流年", "格局神煞", "五行精算"]:
            tab = page.locator(f'button:has-text("{tab_name}")').first
            visible = await tab.is_visible()
            check(f"Tab '{tab_name}'", visible)
            if visible:
                await tab.click()
                await page.wait_for_timeout(500)

        await page.screenshot(path=str(SCREENSHOTS_DIR / "v2_04_tabs.png"))

        # ── Test 8: Chat interaction ───────────────────────────────────
        print("\n=== Test 8: Chat ===")
        # Streamlit chat input: the container is a div, actual input is inner textarea
        chat_container = page.locator('[data-testid="stChatInput"]')
        chat_textarea = page.locator('[data-testid="stChatInput"] textarea')
        if await chat_container.is_visible():
            await chat_textarea.fill("请简单分析一下这个八字的五行特点，50字以内。")
            await page.keyboard.press("Enter")
            # Wait for new chat message to appear
            try:
                await page.locator('[data-testid="stChatMessage"]').nth(msg_count).wait_for(
                    state="attached", timeout=25000
                )
            except Exception:
                await page.wait_for_timeout(15000)  # Fallback fixed wait
            await page.screenshot(path=str(SCREENSHOTS_DIR / "v2_05_chat.png"))

            # Check for response
            new_msgs = page.locator('[data-testid="stChatMessage"]')
            new_count = await new_msgs.count()
            check("Chat response received", new_count > msg_count, f"Messages: {msg_count} -> {new_count}")

            # Check for errors
            new_errors = page.locator('[data-testid="stException"], [data-testid="stError"]')
            new_error_count = await new_errors.count()
            check("No chat errors", new_error_count == error_count, f"New errors: {new_error_count - error_count}")
            if new_error_count > error_count:
                for i in range(error_count, new_error_count):
                    error_text = await new_errors.nth(i).inner_text()
                    print(f"    Error: {error_text[:200]}")
        else:
            check("Chat input visible", False)

        # ── Summary ────────────────────────────────────────────────────
        print(f"\n{'='*50}")
        print(f"RESULTS: {passed} passed, {failed} failed")
        if errors:
            print(f"\nFailures:")
            for e in errors:
                print(f"  {e}")
        print(f"{'='*50}")

        await browser.close()
        return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
