import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        
        # 1. Login
        await page.goto('http://127.0.0.1:8000/accounts/login/')
        await page.fill('input[name="username"]', 'test_admin_nav')
        await page.fill('input[name="password"]', 'AdminTest@2026!')
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        
        # 2. Go to leads list
        await page.goto('http://127.0.0.1:8000/admin/leads/?view=all_active&sort=-created_at')
        await page.wait_for_load_state('networkidle')
        
        # 3. Find and click trigger
        trigger = page.locator('.tp-smart-date-trigger').first
        await trigger.click()
        await page.wait_for_timeout(500)
        
        # 4. Take screenshot
        out_path = r'C:\Users\tamil\.gemini\antigravity\brain\364306a8-735f-4286-9c22-bb9e159eba4d\actual_smart_calendar_leads.png'
        await page.screenshot(path=out_path)
        print('Screenshot saved to:', out_path)
        
        # Check elements inside popover
        months = await page.locator('.tp-smart-month').count()
        titles = await page.locator('.tp-month-title').all_inner_texts()
        print('Number of months rendered:', months)
        print('Titles:', titles)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
