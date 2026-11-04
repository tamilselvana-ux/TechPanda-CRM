import os, sys, time, json, urllib.request, subprocess
from pathlib import Path

# Launch Chrome with remote debugging
chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
user_data = r'D:\temp_chrome_session'
os.makedirs(user_data, exist_ok=True)

proc = subprocess.Popen([
    chrome,
    '--headless=new',
    f'--user-data-dir={user_data}',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--no-first-run',
    'about:blank'
])

time.sleep(1.5)

try:
    # Query DevTools HTTP endpoint
    req = urllib.request.urlopen('http://127.0.0.1:9222/json')
    tabs = json.loads(req.read().decode('utf-8'))
    print("Chrome DevTools ready, active targets:", len(tabs))
finally:
    proc.terminate()
    proc.wait()
