from playwright.sync_api import sync_playwright

p = sync_playwright().start()
browser = p.chromium.launch(headless=False, slow_mo=100)
context = browser.new_context(
    storage_state=r'C:\Users\Administrator\weibo_crawler\output\weibo_storage_state.json',
    viewport={'width': 1920, 'height': 1080}
)
page = context.new_page()
page.goto(f'https://weibo.com/u/{1039916297}?tabtype=article', wait_until='domcontentloaded')
page.wait_for_timeout(4000)

# Try click article tab
for sel in ['a[href*="tabtype=article"]', 'text=文章']:
    try:
        page.click(sel, timeout=2000)
        print(f'Clicked: {sel}')
        page.wait_for_timeout(2500)
        break
    except Exception:
        pass

# Scroll a bit to load some cards
page.evaluate('window.scrollBy(0, 800)')
page.wait_for_timeout(2000)

# Collect ALL hrefs
hrefs = page.eval_on_selector_all('a[href]', 'els => els.map(e => e.href)')
unique = sorted(set(hrefs))

print(f'Total unique links on page: {len(unique)}')
print('\n--- Links containing article or p/ or wenda ---')
for h in unique:
    if 'article' in h or '/p/' in h or 'wenda' in h or 'ttarticle' in h:
        print(h)

print('\n--- Other weibo.com links (first 30) ---')
count = 0
for h in unique:
    if 'weibo.com' in h and count < 30:
        print(h)
        count += 1

print('\nPress Enter in console to close browser...')
page.wait_for_timeout(8000)
browser.close()
p.stop()
