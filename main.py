from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os

app = Flask(__name__)

# --- BROWSER SETUP (STEALTH MODE) ---
def get_driver():
    options = Options()
    options.add_argument("--headless=new") # Naya Headless Mode
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    options.binary_location = "/usr/bin/google-chrome"
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# --- MAIN LOGIC ---
def solve_hubcloud_final(hubcloud_url):
    driver = None
    try:
        driver = get_driver()
        print(f"🚀 Step 1: Opening HubCloud: {hubcloud_url}")
        driver.get(hubcloud_url)
        
        # 1. Cloudflare Bypass (Wait for 'Just a moment' to go)
        for i in range(10):
            if "Just a moment" not in driver.title:
                break
            time.sleep(2)
        
        time.sleep(3) # Page load hone ka wait
        
        # 2. 'Generate Direct Download Link' Button Dhoondo
        try:
            # HTML mein id="download" hai (Aapke source code ke hisaab se)
            btn = driver.find_element(By.ID, "download")
            redirect_link = btn.get_attribute("href")
            print(f"🔗 Step 2: Found Redirect Link: {redirect_link}")
        except:
            return {"status": "fail", "message": "Download button (id='download') nahi mila. Cloudflare issue?"}

        # 3. Redirect Link par Jao (Gamerxyt -> Carnewz)
        print("🔄 Step 3: Visiting Redirect Link (Waiting for Final Page)...")
        driver.get(redirect_link)
        
        # Yahan redirect hone mein time lagta hai, isliye wait zaroori hai
        time.sleep(8) 
        
        # 4. Ab hum Final Page (Carnewz) par hain. Links nikalo.
        print(f"📄 Step 4: Final Page Title: {driver.title}")
        page_source = driver.page_source
        
        # --- FILTERS (Aapki List ke hisaab se) ---
        
        # Ye links chahiye
        keep_domains = [
            "r2.dev", 
            "fsl-lover.buzz", 
            "fsl-cdn-1.sbs", 
            "fukggl.buzz"
        ]
        
        # Ye links nahi chahiye
        ignore_domains = [
            "pixeldrain", 
            "hubcdn", 
            "workers.dev", 
            ".zip" # Zip file ignore karne ke liye
        ]
        
        # Regex se saare HTTP links nikalo
        all_links = re.findall(r'https?://[^\s"\'<>]+', page_source)
        
        final_results = []
        
        for link in all_links:
            # Check 1: Kya ye hamare kaam ka domain hai?
            is_useful = any(domain in link for domain in keep_domains)
            
            # Check 2: Kya ye ignore list mein to nahi?
            is_ignored = any(bad in link for bad in ignore_domains)
            
            if is_useful and not is_ignored:
                if link not in final_results: # Duplicate hatane ke liye
                    final_results.append(link)

        if final_results:
            return {
                "status": "success",
                "total_found": len(final_results),
                "final_links": final_results
            }
        else:
            return {"status": "fail", "message": "Final Page load hua par LINKS filter nahi huye.", "current_url": driver.current_url}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if driver:
            driver.quit()

@app.route('/solve-cloud', methods=['GET'])
def solve_cloud():
    target_url = request.args.get('url')
    if not target_url: return jsonify({"error": "URL missing"}), 400

    result = solve_hubcloud_final(target_url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
