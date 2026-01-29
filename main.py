from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium_stealth import stealth
import time
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    driver.set_page_load_timeout(60)
    return driver

def bypass_cloudflare(driver, timeout=40):
    logger.info("Bypassing Cloudflare...")
    start_time = time.time()
    time.sleep(5)
    
    while time.time() - start_time < timeout:
        title = driver.title.lower()
        if "just a moment" in title:
            logger.info("Cloudflare detected, waiting...")
            time.sleep(3)
            continue
        try:
            driver.find_element(By.ID, "download")
            logger.info("Cloudflare bypassed!")
            return True
        except:
            time.sleep(2)
    return False

def filter_links(links):
    filtered = []
    whitelist = [r'r2\.dev', r'fsl-lover\.buzz', r'fsl-cdn-1\.sbs', r'fukggl\.buzz']
    blacklist = [r'pixeldrain', r'hubcdn', r'workers\.dev', r'\.zip$']
    
    for link in links:
        if any(re.search(p, link, re.IGNORECASE) for p in blacklist):
            continue
        if any(re.search(p, link, re.IGNORECASE) for p in whitelist):
            if link not in filtered:
                filtered.append(link)
    return filtered

def scrape_hubcloud(url):
    driver = None
    try:
        logger.info(f"Scraping: {url}")
        driver = setup_driver()
        driver.get(url)
        
        if not bypass_cloudflare(driver):
            return {"success": False, "error": "Cloudflare bypass failed", "links": []}
        
        time.sleep(3)
        
        download_btn = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "download"))
        )
        download_href = download_btn.get_attribute('href')
        logger.info(f"Button found: {download_href}")
        
        download_btn.click()
        time.sleep(3)
        
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
        
        time.sleep(12)
        current_url = driver.current_url
        logger.info(f"Final URL: {current_url}")
        
        all_links = []
        anchor_tags = driver.find_elements(By.TAG_NAME, 'a')
        for anchor in anchor_tags:
            try:
                href = anchor.get_attribute('href')
                if href and href.startswith('http'):
                    all_links.append(href)
            except:
                pass
        
        page_source = driver.page_source
        url_pattern = r'https?://[^\s<>"\']+(?:r2\.dev|fsl-lover\.buzz|fsl-cdn-1\.sbs|fukggl\.buzz)[^\s<>"\']*'
        source_links = re.findall(url_pattern, page_source)
        all_links.extend(source_links)
        all_links = list(set(all_links))
        
        filtered_links = filter_links(all_links)
        logger.info(f"Found {len(filtered_links)} valid links")
        
        return {
            "success": True,
            "url": url,
            "final_url": current_url,
            "total_links_found": len(all_links),
            "links": filtered_links
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"success": False, "error": str(e), "links": []}
    finally:
        if driver:
            driver.quit()

@app.route('/solve-cloud', methods=['GET'])
def solve_cloud():
    url = request.args.get('url')
    if not url:
        return jsonify({"success": False, "error": "Missing url parameter"}), 400
    if not url.startswith('http'):
        return jsonify({"success": False, "error": "Invalid URL"}), 400
    
    result = scrape_hubcloud(url)
    status_code = 200 if result["success"] else 500
    return jsonify(result), status_code

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "HubCloud Cloudflare Bypass API",
        "status": "running",
        "endpoint": "/solve-cloud?url=YOUR_URL"
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

## **Step 2: requirements.txt**
```
Flask==3.0.0
selenium==4.15.2
selenium-stealth==1.0.6
Werkzeug==3.0.1
gunicorn==21.2.0
requests==2.32.3
