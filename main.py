from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium_stealth import stealth
import time
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def setup_driver():
    """Setup Chrome driver with stealth mode for headless Linux server"""
    chrome_options = Options()
    
    # Essential headless configurations for Docker/Render
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Window and performance settings
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-notifications')
    
    # User agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Additional flags
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-dev-tools')
    
    # Exclude automation switches
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Apply stealth settings
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
    except Exception as e:
        logger.error(f"Failed to create driver: {e}")
        raise

def bypass_cloudflare(driver, timeout=40):
    """Wait for Cloudflare challenge to complete"""
    logger.info("Attempting to bypass Cloudflare...")
    start_time = time.time()
    
    try:
        # Wait for page to load initially
        time.sleep(5)
        
        # Check if "Just a moment" title is present
        while time.time() - start_time < timeout:
            title = driver.title.lower()
            
            if "just a moment" in title:
                logger.info("Cloudflare challenge detected, waiting...")
                time.sleep(3)
                continue
            
            # Check if download button is present (success indicator)
            try:
                driver.find_element(By.ID, "download")
                logger.info("Cloudflare bypassed successfully!")
                return True
            except:
                time.sleep(2)
                continue
        
        logger.warning("Cloudflare bypass timeout")
        return False
        
    except Exception as e:
        logger.error(f"Error during Cloudflare bypass: {e}")
        return False

def filter_links(links):
    """Filter links based on whitelist and blacklist"""
    filtered = []
    
    # KEEP patterns (whitelist)
    whitelist = [
        r'r2\.dev',
        r'fsl-lover\.buzz',
        r'fsl-cdn-1\.sbs',
        r'fukggl\.buzz'
    ]
    
    # IGNORE patterns (blacklist)
    blacklist = [
        r'pixeldrain',
        r'hubcdn',
        r'workers\.dev',
        r'\.zip$'
    ]
    
    for link in links:
        # Skip if matches blacklist
        if any(re.search(pattern, link, re.IGNORECASE) for pattern in blacklist):
            continue
        
        # Keep if matches whitelist
        if any(re.search(pattern, link, re.IGNORECASE) for pattern in whitelist):
            if link not in filtered:  # Avoid duplicates
                filtered.append(link)
    
    return filtered

def scrape_hubcloud(url):
    """Main scraping function"""
    driver = None
    
    try:
        logger.info(f"Starting scrape for URL: {url}")
        driver = setup_driver()
        
        # Step 1: Open the URL
        driver.get(url)
        logger.info("Page loaded, checking for Cloudflare...")
        
        # Step 2: Bypass Cloudflare
        if not bypass_cloudflare(driver):
            return {
                "success": False,
                "error": "Failed to bypass Cloudflare",
                "links": []
            }
        
        # Additional wait for page stability
        time.sleep(3)
        
        # Step 3: Find the download button
        logger.info("Looking for download button...")
        try:
            download_btn = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "download"))
            )
            download_href = download_btn.get_attribute('href')
            logger.info(f"Download button found: {download_href}")
            
            # Step 4: Click and handle redirect
            current_window = driver.current_window_handle
            download_btn.click()
            logger.info("Button clicked, waiting for redirect...")
            
            # Wait for potential new window/tab
            time.sleep(3)
            
            # Check if new window opened
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1])
                logger.info("Switched to new window")
            
            # Step 5: Wait for redirect to complete (10-15 seconds)
            time.sleep(12)
            
            current_url = driver.current_url
            logger.info(f"Final URL after redirect: {current_url}")
            
            # Step 6: Scrape all links
            logger.info("Scraping links from final page...")
            all_links = []
            
            # Method 1: Get links from anchor tags
            try:
                anchor_tags = driver.find_elements(By.TAG_NAME, 'a')
                for anchor in anchor_tags:
                    try:
                        href = anchor.get_attribute('href')
                        if href and href.startswith('http'):
                            all_links.append(href)
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Error getting anchor tags: {e}")
            
            # Method 2: Extract from page source using regex
            try:
                page_source = driver.page_source
                # Match URLs containing our whitelist domains
                url_pattern = r'https?://[^\s<>"\']+(?:r2\.dev|fsl-lover\.buzz|fsl-cdn-1\.sbs|fukggl\.buzz)[^\s<>"\']*'
                source_links = re.findall(url_pattern, page_source)
                all_links.extend(source_links)
            except Exception as e:
                logger.warning(f"Error extracting from page source: {e}")
            
            # Remove duplicates
            all_links = list(set(all_links))
            logger.info(f"Total links found: {len(all_links)}")
            
            # Step 7: Filter links
            filtered_links = filter_links(all_links)
            logger.info(f"Filtered links: {len(filtered_links)}")
            
            return {
                "success": True,
                "url": url,
                "final_url": current_url,
                "total_links_found": len(all_links),
                "links": filtered_links
            }
            
        except TimeoutException:
            logger.error("Download button not found (timeout)")
            return {
                "success": False,
                "error": "Download button not found",
                "links": []
            }
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return {
                "success": False,
                "error": str(e),
                "links": []
            }
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return {
            "success": False,
            "error": str(e),
            "links": []
        }
    
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Driver closed successfully")
            except:
                pass

@app.route('/solve-cloud', methods=['GET'])
def solve_cloud():
    """API endpoint to solve Cloudflare and scrape links"""
    
    # Get URL from query parameter
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            "success": False,
            "error": "Missing 'url' parameter"
        }), 400
    
    # Validate URL
    if not url.startswith('http'):
        return jsonify({
            "success": False,
            "error": "Invalid URL format"
        }), 400
    
    logger.info(f"Received request for URL: {url}")
    
    # Scrape the URL
    result = scrape_hubcloud(url)
    
    # Return JSON response
    status_code = 200 if result["success"] else 500
    return jsonify(result), status_code

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "service": "HubCloud Cloudflare Bypass API",
        "status": "running",
        "endpoints": {
            "/solve-cloud": "GET - Bypass Cloudflare and scrape links",
            "parameters": "url (required)"
        },
        "example": "/solve-cloud?url=https://hubcloud.foo/drive/yourfile"
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

## **Updated requirements.txt**
```
Flask==3.0.0
selenium==4.15.2
selenium-stealth==1.0.6
Werkzeug==3.0.1
gunicorn==21.2.0
requests==2.32.3
