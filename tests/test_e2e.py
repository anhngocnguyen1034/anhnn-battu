"""
FOR-BAZI 生产级端到端测试
使用 Playwright 测试 Streamlit UI 的完整功能。
"""
import asyncio
import os
import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)


async def run_tests():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        errors = []
        passed = 0
        failed = 0

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

        # ── Test 1: Page loads ──────────────────────────────────────────
        print("\n=== Test 1: Page Load ===")
        try:
            await page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            title = await page.title()
            check("Page title contains '玄冥'", "玄冥" in title, f"Got: {title}")
            await page.screenshot(path=str(SCREENSHOTS_DIR / "01_page_load.png"))
            check("Page loaded without crash", True)
        except Exception as e:
            check("Page load", False, str(e))
            await browser.close()
            return

        # ── Test 2: Sidebar visible ────────────────────────────────────
        print("\n=== Test 2: Sidebar ===")
        sidebar = page.locator('[data-testid="stSidebar"]')
        sidebar_visible = await sidebar.is_visible()
        if not sidebar_visible:
            # Try to expand sidebar
            expand_btn = page.locator('button[aria-label=""]').first
            if await expand_btn.is_visible():
                await expand_btn.click()
                await page.wait_for_timeout(1000)
                sidebar_visible = await sidebar.is_visible()
        check("Sidebar is visible", sidebar_visible)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "02_sidebar.png"))

        # ── Test 3: Model config section ───────────────────────────────
        print("\n=== Test 3: Model Config ===")
        provider_select = page.locator('[data-testid="stSelectbox"]').first
        check("Provider selectbox exists", await provider_select.is_visible())

        # Check for API key input
        api_key_input = page.locator('input[type="password"]').first
        api_key_visible = await api_key_input.is_visible()
        check("API Key input exists", api_key_visible)

        # ── Test 4: Bazi input section ─────────────────────────────────
        print("\n=== Test 4: Bazi Input ===")
        # Check date input exists
        date_input = page.locator('[data-testid="stDateInput"]').first
        check("Date input exists", await date_input.is_visible())

        # Check time input exists
        time_input = page.locator('[data-testid="stTimeInput"]').first
        check("Time input exists", await time_input.is_visible())

        # Check gender radio
        gender_radio = page.locator('[data-testid="stRadio"]').first
        check("Gender radio exists", await gender_radio.is_visible())

        # ── Test 5: Generate button ────────────────────────────────────
        print("\n=== Test 5: Generate Button ===")
        gen_button = page.locator('button:has-text("生成命盘")')
        check("Generate button exists", await gen_button.is_visible())
        await page.screenshot(path=str(SCREENSHOTS_DIR / "03_before_generate.png"))

        # ── Test 6: Generate bazi chart (without API key) ──────────────
        print("\n=== Test 6: Generate Bazi Chart ===")
        await gen_button.click()
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "04_after_generate.png"))

        # Check if bazi chart rendered
        pillar_cards = page.locator('.bazi-pillar')
        pillar_count = await pillar_cards.count()
        check("Four pillar cards rendered", pillar_count == 4, f"Got {pillar_count} pillars")

        # Check for day master
        day_master_text = await page.locator('.bazi-pillar').nth(2).inner_text()
        check("Day pillar has content", len(day_master_text) > 5, f"Content: {day_master_text[:50]}")

        # ── Test 7: Tabs exist ─────────────────────────────────────────
        print("\n=== Test 7: Tabs ===")
        tabs = page.locator('[data-testid="stTabs"]')
        tabs_visible = await tabs.is_visible()
        check("Tabs container visible", tabs_visible)

        tab_buttons = page.locator('[data-testid="stTabs"] button')
        tab_count = await tab_buttons.count()
        check("Four tabs exist", tab_count == 4, f"Got {tab_count} tabs")
        await page.screenshot(path=str(SCREENSHOTS_DIR / "05_tabs.png"))

        # ── Test 8: Click each tab ─────────────────────────────────────
        print("\n=== Test 8: Tab Navigation ===")
        tab_names = ["原局排盘", "大运流年", "格局神煞", "五行精算"]
        for i, name in enumerate(tab_names):
            try:
                tab_btn = page.locator(f'button:has-text("{name}")')
                if await tab_btn.is_visible():
                    await tab_btn.click()
                    await page.wait_for_timeout(500)
                    await page.screenshot(path=str(SCREENSHOTS_DIR / f"06_tab_{i+1}_{name}.png"))
                    check(f"Tab '{name}' clickable", True)
                else:
                    check(f"Tab '{name}' visible", False, "Button not found")
            except Exception as e:
                check(f"Tab '{name}'", False, str(e))

        # ── Test 9: Wuxing colors ──────────────────────────────────────
        print("\n=== Test 9: Wuxing Colors ===")
        colored_spans = page.locator('.bazi-pillar span[style*="color"]')
        colored_count = await colored_spans.count()
        check("Wuxing colored characters exist", colored_count >= 8, f"Got {colored_count} colored spans")

        # ── Test 10: Chat input ────────────────────────────────────────
        print("\n=== Test 10: Chat Input ===")
        chat_input = page.locator('[data-testid="stChatInput"]')
        chat_visible = await chat_input.is_visible()
        check("Chat input exists", chat_visible)

        if chat_visible:
            await page.screenshot(path=str(SCREENSHOTS_DIR / "07_chat_input.png"))

        # ── Test 11: Info message without API key ──────────────────────
        print("\n=== Test 11: No API Key Warning ===")
        warning = page.locator('[data-testid="stWarning"]')
        info_msg = page.locator('[data-testid="stInfo"]')
        has_warning = await warning.count() > 0
        has_info = await info_msg.count() > 0
        check("Warning or info message shown (no API key)", has_warning or has_info)

        # ── Test 12: Sidebar advanced settings ─────────────────────────
        print("\n=== Test 12: Advanced Settings ===")
        expander = page.locator('text="高级设置"')
        if await expander.count() > 0:
            await expander.click()
            await page.wait_for_timeout(500)
            streaming_toggle = page.locator('text="流式输出"')
            check("Streaming toggle exists", await streaming_toggle.count() > 0)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "08_advanced_settings.png"))
        else:
            check("Advanced settings expander", False, "Not found")

        # ── Test 13: Ding Gong / Tai Yuan display ──────────────────────
        print("\n=== Test 13: Ming Gong / Tai Yuan ===")
        page_text = await page.content()
        check("命宫 displayed", "命宫" in page_text)
        check("胎元 displayed", "胎元" in page_text)

        # ── Test 14: Shengong / Taixi display ──────────────────────────
        print("\n=== Test 14: Shen Gong / Tai Xi ===")
        check("身宫 displayed", "身宫" in page_text)
        check("胎息 displayed", "胎息" in page_text)

        # ── Summary ────────────────────────────────────────────────────
        print(f"\n{'='*50}")
        print(f"RESULTS: {passed} passed, {failed} failed")
        if errors:
            print(f"\nFailures:")
            for e in errors:
                print(f"  {e}")
        print(f"\nScreenshots saved to: {SCREENSHOTS_DIR}")
        print(f"{'='*50}")

        await browser.close()
        return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
