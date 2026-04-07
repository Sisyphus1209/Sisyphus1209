from playwright.sync_api import sync_playwright

p = sync_playwright().start()
browser = p.chromium.launch(headless=False, slow_mo=100)
context = browser.new_context(
    storage_state=r'C:\Users\Administrator\weibo_crawler\output\weibo_storage_state.json',
    viewport={'width': 1920, 'height': 1080}
)
page = context.new_page()

# Open a "good" one and a "bad" one for comparison
urls = [
    'https://weibo.com/ttwenda/p/show?id=2310685247181165822005',  # good
    'https://weibo.com/ttwenda/p/show?id=2310685268797694279944',  # bad (recommendations)
]

for url in urls:
    print(f'\n=== URL: {url} ===')
    page.goto(url, wait_until='domcontentloaded')
    page.wait_for_timeout(3000)
    print('Current URL:', page.url)
    print('Title:', page.title())
    
    # Check for iframes
    frames = page.frames
    print('Frames:', len(frames))
    for fr in frames:
        print(' ', fr.url[:100])
    
    # Check for "查看全文" or "进入问答" buttons
    btns = page.eval_on_selector_all(
        'a, button, span',
        'els => els.map(e => ({text: e.innerText?.trim(), href: e.href})).filter(x => x.text && (x.text.includes("全文") || x.text.includes("问答") || x.text.includes("详情") || x.text.includes("围观") || x.text.includes("查看")))'
    )
    print('Action buttons:', len(btns))
    for b in btns[:10]:
        print(' ', b)
    
    # Check all h1/h2
    headings = page.eval_on_selector_all('h1, h2, h3', 'els => els.map(e => e.innerText?.trim()).filter(Boolean)')
    print('Headings:', headings[:5])
    
    # Check if there's a specific data/answer div
    divs = page.eval_on_selector_all(
        'div[class*="answer"], div[class*="detail"], div[class*="content"], article',
        'els => els.map(e => ({cls: e.className, text: e.innerText?.trim()?.substring(0,80)})).filter(x => x.text && x.text.length > 20)'
    )
    print('Content divs:', len(divs))
    for d in divs[:5]:
        print(' ', d)

page.wait_for_timeout(5000)
browser.close()
p.stop()
