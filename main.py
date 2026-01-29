from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import time
import re
import os

app = Flask(__name__)

# --- BROWSER SETUP (ULTRA STEALTH MODE) ---
def get_driver():
    options = Options()
    options.add_argument("--headless=new") # Latest Headless Technology
    options.add_argument("start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Chrome Path on Render
    options.binary_location = "/usr/bin/google-chrome"
    
    # Automation Detection Disable
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # --- STEALTH LIBRARY ACTIVATION ---
    # Ye hai wo High-Tech Cheez jo Cloudflare ki 'G**d Faad' degi
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver

# --- MAIN LOGIC ---
def solve_hubcloud_final(hubcloud_url):
    driver = None
    try:
        driver = get_driver()
        print(f"🚀 [STEP 1] Opening HubCloud: {hubcloud_url}")
        driver.get(hubcloud_url)
        
        # 1. CLOUDFLARE BYPASS CHECK
        print("⚔️ [STEP 2] Fighting Cloudflare...")
        time.sleep(8) # Stealth mode apna kaam karega
        
        # 2. FIND & CLICK BUTTON (As per your instruction)
        try:
            print("🔍 [STEP 3] Looking for Button (id='download')...")
            download_btn = driver.find_element(By.ID, "download")
            
            # Link pehle hi nikal lo (Backup ke liye)
            redirect_link = download_btn.get_attribute("href")
            print(f"🔗 Button Link Found: {redirect_link}")
            
            # CLICK THE BUTTON (Taaki genuine lagge)
            driver.execute_script("arguments[0].click();", download_btn)
            
        except Exception as e:
            # Agar Click fail hua, to nikaley hue link par seedha jao
            if 'redirect_link' in locals() and redirect_link:
                print("⚠️ Click failed, forcing redirection...")
                driver.get(redirect_link)
            else:
                return {"status": "fail", "message": f"Download button nahi mila. Title: {driver.title}"}

        # 3. REDIRECT WAIT (Gamerxyt -> Carnewz)
        print("⏳ [STEP 4] Waiting for Redirection (10s)...")
        time.sleep(12) # Gamerxyt thoda time leta hai
        
        # 4. FILTER FINAL LINKS
        print(f"📄 [STEP 5] Final Page Reached: {driver.title}")
        page_source = driver.page_source
        
        # --- YOUR STRICT FILTER LIST ---
        keep_domains = [
            "r2.dev", 
            "fsl-lover.buzz", 
            "fsl-cdn-1.sbs", 
            "fukggl.buzz"
        ]
        
        ignore_domains = [
            "pixeldrain", 
            "hubcdn", 
            "workers.dev",
            ".zip" 
        ]
        
        all_links = re.findall(r'https?://[^\s"\'<>]+', page_source)
        final_results = []
        
        for link in all_links:
            # Sirf wahi links jo list mein hain
            if any(k in link for k in keep_domains) and not any(i in link for i in ignore_domains):
                if link not in final_results:
                    final_results.append(link)

        if final_results:
            return {
                "status": "success",
                "total_found": len(final_results),
                "final_links": final_results
            }
        else:
            # Agar links nahi mile, to HTML debug ke liye save nahi karenge, bas fail denge
            return {
                "status": "fail", 
                "message": "Final page load hua par LINKS filter nahi huye.",
                "current_url": driver.current_url
            }

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
