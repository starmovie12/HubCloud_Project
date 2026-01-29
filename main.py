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
    
    # Render par Chrome yahan hota hai
    chrome_options.binary_location = "/usr/bin/google-chrome"
    
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def solve_hubcloud_selenium(hubcloud_url):
    driver = None
    try:
        driver = get_driver()
        print(f"☁️ Opening: {hubcloud_url}")
        driver.get(hubcloud_url)
        time.sleep(5)
        
        # 1. 'var url' (Generator Link)
        html = driver.page_source
        match = re.search(r"var\s+url\s*=\s*['\"]([^'\"]+hubcloud\.php[^'\"]+)['\"]", html)
        
        if not match:
            return {"status": "fail", "message": "Generator Link nahi mila"}
        
        gen_url = match.group(1)
        
        # 2. Generator Page
        driver.get(gen_url)
        time.sleep(6)
        
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
    # Render Docker port 10000 use karta hai
    app.run(host='0.0.0.0', port=10000)
