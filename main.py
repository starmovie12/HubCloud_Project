from flask import Flask, request, jsonify
import requests
import re
import os

app = Flask(__name__)

# --- HEADER SETTINGS (Fake Browser) ---
# HubCloud ko lagega ye asli Chrome browser hai
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://hubcloud.foo/' 
}

# --- LOGIC: HubCloud -> Final Link ---
def solve_hubcloud_logic(hubcloud_url):
    try:
        # Step A: HubCloud page se 'Generator Link' nikalna
        session = requests.Session() # Session maintain karega cookies ke liye
        response = session.get(hubcloud_url, headers=HEADERS, timeout=10)
        
        # 'var url' dhundo (Jo agla page hai)
        match = re.search(r"var\s+url\s*=\s*['\"]([^'\"]+hubcloud\.php[^'\"]+)['\"]", response.text)
        
        if not match:
            return {"status": "fail", "message": "Generator Link nahi mila (Regex Fail)"}
        
        gen_url = match.group(1)
        
        # Step B: Generator Page par jakar Final Link uthana
        # Thoda wait (sleep) server side manage karega request time se
        resp_gen = session.get(gen_url, headers=HEADERS, timeout=10)
        
        # Step C: Filter (FSL / Fukggl)
        keep = ["fsl-cdn-1.sbs", "fukggl.buzz"]
        ignore = ["pixeldrain", "hubcdn", "telegram"]
        
        all_links = re.findall(r'https?://[^\s"\'<>]+', resp_gen.text)
        
        for link in all_links:
            if any(k in link for k in keep) and not any(i in link for i in ignore):
                return {"status": "success", "final_link": link}

        return {"status": "fail", "message": "Final link filter nahi hua"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- WEBSITE LINK ---
@app.route('/')
def home():
    return "API-2 (HubCloud) is Ready! ☁️"

@app.route('/solve-cloud', methods=['GET'])
def solve_cloud():
    target_url = request.args.get('url')
    
    if not target_url:
        return jsonify({"error": "URL missing"}), 400

    # Logic call karo
    result = solve_hubcloud_logic(target_url)
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001)) # Port 5001 rakha hai alag pehchan ke liye
    app.run(host='0.0.0.0', port=port)
