from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os

app = Flask(__name__)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # FIX 1: Screen Size set karna zaroori hai
    chrome_options.add_argument("--window-size=1920,1080")
    # FIX 2: Asli User-Agent (Taaki website block na kare)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Render Path
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def solve_hubcloud_selenium(hubcloud_url):
    driver = None
    try:
        driver = get_driver()
        print(f"☁️ Opening: {hubcloud_url}")
        driver.get(hubcloud_url)
        
        # FIX 3: Wait time badhaya (Render thoda slow ho sakta hai)
        time.sleep(10)
        
        # Debugging: Check karo page ka Title kya hai (Logs mein dikhega)
        print(f"📄 Page Title: {driver.title}")

        # 1. 'var url' (Generator Link)
        html = driver.page_source
        match = re.search(r"var\s+url\s*=\s*['\"]([^'\"]+hubcloud\.php[^'\"]+)['\"]", html)
        
        if not match:
            # Agar fail ho, to thoda HTML print karo taaki pata chale hua kya
            print("❌ HTML Dump (First 500 chars):")
            print(html[:500])
            return {"status": "fail", "message": f"Generator Link nahi mila. Page Title: {driver.title}"}
        
        gen_url = match.group(1)
        print(f"🔗 Generator Link Found: {gen_url}")
        
        # 2. Generator Page
        driver.get(gen_url)
        time.sleep(8) # Button load hone ka wait
        
        # 3. Filter
        keep = ["fsl-cdn-1.sbs", "fukggl.buzz"]
        ignore = ["pixeldrain", "hubcdn", "telegram"]
        
        all_links = re.findall(r'https?://[^\s"\'<>]+', driver.page_source)
        
        for link in all_links:
            if any(k in link for k in keep) and not any(i in link for i in ignore):
                return {"status": "success", "final_link": link}
                
        return {"status": "fail", "message": "Link Filter nahi hua"}
        
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
