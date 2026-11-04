import os, sys, time, json, urllib.request, subprocess, socket, base64
from pathlib import Path

# Setup Django session
sys.path.insert(0, os.path.abspath('CRM_Integrated_v2/CRM'))
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

    def close(self):
        self.sock.close()

# Launch Chrome
chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
user_data = r'D:\temp_chrome_session'
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

out_dir = Path('docs/qa/calendar_baseline')
out_dir.mkdir(parents=True, exist_ok=True)

test_targets = [
    ('accountant', 'http://127.0.0.1:8000/accountant/dashboard/'),
    ('admin_leads', 'http://127.0.0.1:8000/admin/leads/'),
    ('admin_dashboard', 'http://127.0.0.1:8000/admin/dashboard/'),
]

try:
    tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode('utf-8'))
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

    viewports = [
        ('desktop', 1366, 768, False),
        ('mobile', 390, 844, True),
    ]

    themes = ['light', 'dark']

    for name, url in test_targets:
        for vp_name, w, h, is_mobile in viewports:
            for theme in themes:
                # Set theme in document
                mid = cdp.send("Page.navigate", {"url": url})
                cdp.recv(mid)
                time.sleep(0.8)
                
                # Apply theme via JS
                script = f"""
                document.documentElement.setAttribute('data-theme', '{theme}');
                document.body.className = '{theme}-theme';
                localStorage.setItem('techpanda_theme', '{theme}');
                localStorage.setItem('digipanda_theme', '{theme}');
                """
                mid = cdp.send("Runtime.evaluate", {"expression": script})
                cdp.recv(mid)
                time.sleep(0.3)

                cdp.send("Emulation.setDeviceMetricsOverride", {
                    "width": w, "height": h, "deviceScaleFactor": 1, "mobile": is_mobile
                })
                time.sleep(0.3)

                mid = cdp.send("Page.captureScreenshot")
                resp = cdp.recv(mid)

                fname = f"baseline_{name}_{vp_name}_{theme}.png"
                fpath = out_dir / fname
                with open(fpath, 'wb') as f:
                    f.write(base64.b64decode(resp['result']['data']))
                print(f"Captured: {fname} ({os.path.getsize(fpath):,} bytes)")

    cdp.close()
finally:
    proc.terminate()
    proc.wait()

print("All baseline screenshots captured successfully.")
