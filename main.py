from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os
import random

app = Flask(__name__)

def get_driver():
    options = Options()
    
    # --- CLOUDFLARE BYPASS SETTINGS (सबसे ज़रूरी) ---
    # 1. New Headless Mode (Old wala pakda jata hai)
    options.add_argument("--headless=new")
    
    # 2. Automation Flags Chhupana
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # 3. Window Size (Mobile na samjhe)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # 4. Asli User Agent (Taaki Robot na lage)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    # Render Path
    options.binary_location = "/usr/bin/google-chrome"
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 5. Javascript Trick (Navigator property chhupana)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def solve_hubcloud_selenium(hubcloud_url):
    driver = None
    try:
        driver = get_driver()
        print(f"☁️ Opening: {hubcloud_url}")
        driver.get(hubcloud_url)
        
        # --- CLOUDFLARE CHECK LOOP ---
        # "Just a moment" hatne ka wait karenge (Max 30 seconds)
        print("⏳ Checking for Cloudflare...")
        for i in range(15):
            title = driver.title
            print(f"   Wait {i*2}s - Title: {title}")
            
            if "Just a moment" not in title and "Cloudflare" not in title:
                break # Cloudflare hat gaya!
            
            time.sleep(2)
        
        # Page load hone ke baad thoda aur wait
        time.sleep(3)
        
        # Ab HTML uthao
        html = driver.page_source
        
        # 1. 'var url' dhoondo (Aapke screenshot wala code)
        match = re.search(r"var\s+url\s*=\s*['\"]([^'\"]+hubcloud\.php[^'\"]+)['\"]", html)
        
        if not match:
            # Agar ab bhi nahi mila, matlab IP Blocked hai
            return {"status": "fail", "message": f"Cloudflare Bypass Failed. Title: {driver.title}"}
        
        gen_url = match.group(1)
        print(f"🔗 Generator Link Found: {gen_url}")
        
        # 2. Generator Page par jao
        driver.get(gen_url)
        time.sleep(5) 
        
        # 3. Final Filter
        keep = ["fsl-cdn-1.sbs", "fukggl.buzz"]
        ignore = ["pixeldrain", "hubcdn", "telegram"]
        
        all_links = re.findall(r'https?://[^\s"\'<>]+', driver.page_source)
        
        for link in all_links:
            if any(k in link for k in keep) and not any(i in link for i in ignore):
                return {"status": "success", "final_link": link}
                
        return {"status": "fail", "message": "Generator Page Load hua, par Final Link nahi mila"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if driver:
            driver.quit()

@app.route('/solve-cloud', methods=['GET'])
def solve_cloud():
    target_url = request.args.get('url')
    if not target_url: return jsonify({"error": "URL missing"}), 400

    result = solve_hubcloud_selenium(target_url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
