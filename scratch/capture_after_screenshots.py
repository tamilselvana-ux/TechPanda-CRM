import os, sys, time, json, urllib.request, subprocess, socket, base64
from pathlib import Path

# Setup Django session for authenticated screenshots
sys.path.insert(0, os.path.abspath('d:/CRM_Integrated_v2/CRM_Integrated_v2/CRM'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore

User = get_user_model()
admin = User.objects.filter(is_superuser=True).first() or User.objects.filter(role='admin').first()

session = SessionStore()
session['_auth_user_id'] = str(admin.pk)
session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
session['_auth_user_hash'] = admin.get_session_auth_hash()
session.save()
session_key = session.session_key
print(f"Session key created: {session_key}")

class SimpleCDP:
    def __init__(self, ws_url):
        parts = ws_url.replace('ws://', '').split('/', 1)
        host, port = parts[0].split(':')
        self.path = '/' + parts[1]
        self.sock = socket.create_connection((host, int(port)))
        self._handshake(parts[0])
        self._msg_id = 0

    def _handshake(self, host_hdr):
        key = base64.b64encode(os.urandom(16)).decode('ascii')
        req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {host_hdr}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode('ascii'))
        resp = b""
        while b"\r\n\r\n" not in resp:
            resp += self.sock.recv(1024)

    def send(self, method, params=None):
        self._msg_id += 1
        msg = {"id": self._msg_id, "method": method, "params": params or {}}
        data = json.dumps(msg).encode('utf-8')
        length = len(data)
        frame = bytearray([0x81])
        if length < 126:
            frame.append(0x80 | length)
        elif length < 65536:
            frame.append(0x80 | 126)
            frame.extend(length.to_bytes(2, 'big'))
        else:
            frame.append(0x80 | 127)
            frame.extend(length.to_bytes(8, 'big'))
        mask = os.urandom(4)
        frame.extend(mask)
        frame.extend(bytearray([b ^ mask[i % 4] for i, b in enumerate(data)]))
        self.sock.sendall(frame)
        return self._msg_id

    def recv(self, match_id=None):
        while True:
            b1, b2 = self.sock.recv(2)
            length = b2 & 0x7F
            if length == 126:
                length = int.from_bytes(self.sock.recv(2), 'big')
            elif length == 127:
                length = int.from_bytes(self.sock.recv(8), 'big')
            payload = b""
            while len(payload) < length:
                payload += self.sock.recv(length - len(payload))
            msg = json.loads(payload.decode('utf-8'))
            if match_id is None or msg.get('id') == match_id:
                return msg

    def eval(self, expr):
        mid = self.send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        return self.recv(mid)

    def close(self):
        self.sock.close()

# Launch Chrome
chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
user_data = r'D:\temp_chrome_session_after'
proc = subprocess.Popen([
    chrome,
    '--headless=new',
    f'--user-data-dir={user_data}',
    '--remote-debugging-port=9223',
    '--disable-gpu',
    '--no-first-run',
    'about:blank'
])

time.sleep(2.0)

out_dir = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\docs\qa\calendar"
os.makedirs(out_dir, exist_ok=True)

try:
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9223/json').read().decode('utf-8'))
    ws_url = [t['webSocketDebuggerUrl'] for t in tabs if t.get('type') == 'page'][0]
    cdp = SimpleCDP(ws_url)
    
    cdp.send("Network.enable")
    cdp.send("Page.enable")
    
    cdp.send("Network.setCookie", {
        "name": "sessionid",
        "value": session_key,
        "domain": "127.0.0.1",
        "path": "/"
    })
    
    def capture(name, width, height, is_mobile):
        cdp.send("Emulation.setDeviceMetricsOverride", {
            "width": width, "height": height, "deviceScaleFactor": 1, "mobile": is_mobile
        })
        time.sleep(0.4)
        mid = cdp.send("Page.captureScreenshot")
        resp = cdp.recv(mid)
        target = os.path.join(out_dir, name)
        with open(target, 'wb') as f:
            f.write(base64.b64decode(resp['result']['data']))
        print(f"Captured: {name} ({width}x{height})")

    # 1. Admin Dashboard
    cdp.send("Page.navigate", {"url": "http://127.0.0.1:8000/admin/dashboard/"})
    time.sleep(1.2)

    # 1A. Desktop Light Closed
    cdp.eval("document.documentElement.setAttribute('data-theme', 'light'); document.body.className='light-theme'; if (window.CalendarDrawer) window.CalendarDrawer.close();")
    capture("admin_1366_light_closed.png", 1366, 768, False)

    # 1B. Desktop Light Open
    cdp.eval("if (window.CalendarDrawer) { var btn = document.querySelector('.calendar-drawer-trigger'); window.CalendarDrawer.open(btn); }")
    time.sleep(0.5)
    capture("admin_1366_light_open.png", 1366, 768, False)

    # 1C. Desktop Dark Open
    cdp.eval("document.documentElement.setAttribute('data-theme', 'dark'); document.body.className='dark-theme';")
    time.sleep(0.3)
    capture("admin_1366_dark_open.png", 1366, 768, False)

    # 1D. Desktop Dark Closed
    cdp.eval("if (window.CalendarDrawer) window.CalendarDrawer.close();")
    time.sleep(0.3)
    capture("admin_1366_dark_closed.png", 1366, 768, False)

    # 2. Mobile Views (390px)
    # 2A. Mobile Light Closed
    cdp.eval("document.documentElement.setAttribute('data-theme', 'light'); document.body.className='light-theme'; if (window.CalendarDrawer) window.CalendarDrawer.close();")
    capture("admin_390_light_closed.png", 390, 844, True)

    # 2B. Mobile Light Open (Bottom sheet!)
    cdp.eval("if (window.CalendarDrawer) { var btn = document.querySelector('.calendar-drawer-trigger'); window.CalendarDrawer.open(btn); }")
    time.sleep(0.5)
    capture("admin_390_light_open.png", 390, 844, True)

    # 2C. Mobile Dark Open
    cdp.eval("document.documentElement.setAttribute('data-theme', 'dark'); document.body.className='dark-theme';")
    time.sleep(0.3)
    capture("admin_390_dark_open.png", 390, 844, True)

    # 3. Accountant Dashboard
    cdp.send("Page.navigate", {"url": "http://127.0.0.1:8000/accountant/dashboard/"})
    time.sleep(1.2)

    # 3A. Desktop Light Open
    cdp.eval("document.documentElement.setAttribute('data-theme', 'light'); document.body.className='light-theme'; if (window.CalendarDrawer) { var btn = document.querySelector('#customRangeToggleBtn, .calendar-drawer-trigger'); window.CalendarDrawer.open(btn); }")
    time.sleep(0.5)
    capture("accountant_1366_light_open.png", 1366, 768, False)

    # 3B. Mobile Light Open
    capture("accountant_390_light_open.png", 390, 844, True)

    cdp.close()
    print("ALL SCREENSHOTS CAPTURED SUCCESSFULLY!")

finally:
    proc.terminate()
    proc.wait()
