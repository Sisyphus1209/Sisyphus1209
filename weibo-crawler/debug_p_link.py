from playwright.sync_api import sync_playwright

p = sync_playwright().start()
browser = p.chromium.launch(headless=False)
context = browser.new_context(
    storage_state=r'C:\Users\Administrator\weibo_crawler\output\weibo_storage_state.json'
)
page = context.new_page()
page.goto('https://weibo.com/p/2304914009240924845421', wait_until='domcontentloaded')
page.wait_for_timeout(3000)

# List all iframes
iframes = page.frames
print('Total frames:', len(iframes))
for i, fr in enumerate(iframes):
    print(f'Frame {i}: url={fr.url[:120]}')
    try:
        title = fr.title()
        print(f'  title={title}')
    except Exception as e:
        print(f'  title error: {e}')
    try:
        # Check for unlock button inside iframe
        has_unlock = fr.locator('text=免费围观').count() > 0
        print(f'  has_unlock={has_unlock}')
    except Exception as e:
        print(f'  unlock check error: {e}')

# Also check main frame links
print('\nMain frame links containing p/:')
links = page.eval_on_selector_all('a[href]', 'els => els.map(e => e.href).filter(h => h && h.includes("/p/"))')
for l in set(links)[:10]:
    print(' ', l)

page.wait_for_timeout(5000)
browser.close()
p.stop()
