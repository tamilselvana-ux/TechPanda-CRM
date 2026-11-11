import os
import subprocess

ASSETS_DIR = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\docs\assets"
os.makedirs(ASSETS_DIR, exist_ok=True)
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

BASE_STYLE = """
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px;
    background: #ffffff;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif;
    color: #0f172a;
  }
  .card {
    border: 1px solid #cbd5e1;
    border-radius: 14px;
    padding: 20px 24px;
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  }
  .title {
    font-size: 18px;
    font-weight: 800;
    color: #174b89;
    margin: 0 0 6px 0;
  }
  .subtitle {
    font-size: 12px;
    color: #64748b;
    margin: 0 0 18px 0;
  }
  svg { width: 100%; height: auto; display: block; }
</style>
"""

def render_svg_to_png(filename, width, height, title, subtitle, svg_body):
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{BASE_STYLE}</head>
<body>
  <div class="card" style="width:{width-48}px;">
    <div class="title">{title}</div>
    <div class="subtitle">{subtitle}</div>
    {svg_body}
  </div>
</body></html>"""
    temp_html = os.path.join(ASSETS_DIR, f"_tmp_{filename}.html")
    out_png = os.path.join(ASSETS_DIR, filename)
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html)
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        f"--window-size={width},{height}",
        "--force-device-scale-factor=2",
        f"--screenshot={out_png}",
        temp_html,
    ]
    subprocess.run(cmd, capture_output=True)
    if os.path.exists(temp_html):
        os.remove(temp_html)
    print(f"Generated diagram: {filename} ({os.path.getsize(out_png)//1024} KB)")

# 1. End-to-End Lead Workflow
render_svg_to_png(
    "diag_lead_intake_flow.png", 1100, 560,
    "End-to-End Lead Lifecycle Workflow",
    "From Multi-Channel Lead Intake & De-duplication through Allocation, Follow-Up, RNR Handling & Closure",
    """
    <svg viewBox="0 0 1000 410" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569"/>
        </marker>
      </defs>
      <!-- Row 1: Intake -> Dedup -> Allocation -> First Call -->
      <rect x="20" y="30" width="190" height="86" rx="10" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
      <text x="115" y="58" text-anchor="middle" font-weight="700" font-size="13" fill="#1e3a8a">1. Lead Intake</text>
      <text x="115" y="77" text-anchor="middle" font-size="11" fill="#334155">Meta FB/IG · Google Sheet</text>
      <text x="115" y="94" text-anchor="middle" font-size="11" fill="#334155">WhatsApp · Walk-in · Call</text>

      <line x1="210" y1="73" x2="255" y2="73" stroke="#475569" stroke-width="2" marker-end="url(#arr)"/>

      <rect x="260" y="30" width="200" height="86" rx="10" fill="#fefce8" stroke="#ca8a04" stroke-width="2"/>
      <text x="360" y="58" text-anchor="middle" font-weight="700" font-size="13" fill="#854d0e">2. De-duplication Check</text>
      <text x="360" y="77" text-anchor="middle" font-size="11" fill="#334155">Normalize Phone (10-digit)</text>
      <text x="360" y="94" text-anchor="middle" font-size="11" fill="#334155">Match -> Append Note / Skip</text>

      <line x1="460" y1="73" x2="505" y2="73" stroke="#475569" stroke-width="2" marker-end="url(#arr)"/>

      <rect x="510" y="30" width="210" height="86" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
      <text x="615" y="58" text-anchor="middle" font-weight="700" font-size="13" fill="#166534">3. Lead Allocation</text>
      <text x="615" y="77" text-anchor="middle" font-size="11" fill="#334155">Branch Ratio (%) + On Duty</text>
      <text x="615" y="94" text-anchor="middle" font-size="11" fill="#334155">Telecaller / Counselor / Manual</text>

      <line x1="720" y1="73" x2="765" y2="73" stroke="#475569" stroke-width="2" marker-end="url(#arr)"/>

      <rect x="770" y="30" width="205" height="86" rx="10" fill="#f8fafc" stroke="#174b89" stroke-width="2"/>
      <text x="872" y="58" text-anchor="middle" font-weight="700" font-size="13" fill="#174b89">4. First Call Attempt</text>
      <text x="872" y="77" text-anchor="middle" font-size="11" fill="#334155">Target: Within 15 Mins</text>
      <text x="872" y="94" text-anchor="middle" font-size="11" fill="#334155">Click-to-Dial / Phone Sync</text>

      <!-- Branching Down from First Call -->
      <line x1="872" y1="116" x2="872" y2="165" stroke="#475569" stroke-width="2" marker-end="url(#arr)"/>

      <!-- Decision Diamond / Split -->
      <rect x="750" y="170" width="240" height="48" rx="24" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/>
      <text x="870" y="199" text-anchor="middle" font-weight="700" font-size="12" fill="#0369a1">Call Answered by Student?</text>

      <!-- Left Path: Unanswered / RNR -->
      <line x1="750" y1="194" x2="485" y2="194" stroke="#dc2626" stroke-width="2" marker-end="url(#arr)"/>
      <text x="620" y="186" text-anchor="middle" font-size="11" font-weight="700" fill="#dc2626">NO (RNR / Busy / Switched Off)</text>

      <rect x="260" y="155" width="220" height="80" rx="10" fill="#fef2f2" stroke="#dc2626" stroke-width="2"/>
      <text x="370" y="180" text-anchor="middle" font-weight="700" font-size="13" fill="#991b1b">RNR / Missed Queue</text>
      <text x="370" y="198" text-anchor="middle" font-size="11" fill="#334155">Google Missed -> 15m Callback</text>
      <text x="370" y="214" text-anchor="middle" font-size="11" fill="#334155">&gt;=2 RNR Calls -> Repeat RNR List</text>

      <line x1="260" y1="194" x2="215" y2="194" stroke="#475569" stroke-width="2" marker-end="url(#arr)"/>

      <rect x="20" y="155" width="190" height="80" rx="10" fill="#fff7ed" stroke="#ea580c" stroke-width="2"/>
      <text x="115" y="180" text-anchor="middle" font-weight="700" font-size="13" fill="#9a3412">SLA Escalation</text>
      <text x="115" y="198" text-anchor="middle" font-size="11" fill="#334155">24h Fresh Uncontacted</text>
      <text x="115" y="214" text-anchor="middle" font-size="11" fill="#334155">7d Untouched -> Reassign</text>

      <!-- Down Path: Answered -> Follow-up -> Outcomes -->
      <line x1="870" y1="218" x2="870" y2="275" stroke="#16a34a" stroke-width="2" marker-end="url(#arr)"/>
      <text x="905" y="250" font-size="11" font-weight="700" fill="#16a34a">YES</text>

      <rect x="660" y="280" width="315" height="90" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
      <text x="817" y="305" text-anchor="middle" font-weight="700" font-size="13" fill="#166534">5. Counseling &amp; Follow-up Loop</text>
      <text x="817" y="324" text-anchor="middle" font-size="11" fill="#334155">Status: Interested · Demo Scheduled · Visit Scheduled</text>
      <text x="817" y="342" text-anchor="middle" font-size="11" fill="#334155">Send Brochure on WhatsApp · Audio Logged Automatically</text>

      <line x1="660" y1="325" x2="545" y2="325" stroke="#475569" stroke-width="2" marker-end="url(#arr)"/>

      <!-- Final Outcomes -->
      <rect x="290" y="275" width="250" height="48" rx="8" fill="#dcfce7" stroke="#15803d" stroke-width="2"/>
      <text x="415" y="304" text-anchor="middle" font-weight="700" font-size="12" fill="#14532d">WIN: Converted / Enrolled / Joined</text>

      <rect x="290" y="335" width="250" height="48" rx="8" fill="#fee2e2" stroke="#b91c1c" stroke-width="2"/>
      <text x="415" y="364" text-anchor="middle" font-weight="700" font-size="12" fill="#7f1d1d">CLOSED: Lost / Not Interested / Not Joined</text>

      <line x1="290" y1="299" x2="225" y2="299" stroke="#15803d" stroke-width="2" marker-end="url(#arr)"/>
      <rect x="20" y="275" width="200" height="55" rx="8" fill="#eef2ff" stroke="#4338ca" stroke-width="2"/>
      <text x="120" y="299" text-anchor="middle" font-weight="700" font-size="12" fill="#312e81">Accounts UTR Verify</text>
      <text x="120" y="317" text-anchor="middle" font-size="11" fill="#4338ca">Receipt PDF + Welcome Email</text>
    </svg>
    """
)

# 2. Walk-in Flow
render_svg_to_png(
    "diag_walkin_flow.png", 1100, 380,
    "Branch Walk-in Visitor Flow",
    "From QR Code / Reception Check-in & Token Generation to Counselor Assignment & Outcome",
    """
    <svg viewBox="0 0 1000 220" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arr2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#174b89"/>
        </marker>
      </defs>
      <rect x="15" y="45" width="180" height="110" rx="10" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
      <text x="105" y="75" text-anchor="middle" font-weight="700" font-size="13" fill="#1e3a8a">1. Student Arrives</text>
      <text x="105" y="96" text-anchor="middle" font-size="11" fill="#334155">Scans Branch QR Poster</text>
      <text x="105" y="114" text-anchor="middle" font-size="11" fill="#334155">OR Receptionist Clicks</text>
      <text x="105" y="132" text-anchor="middle" font-size="11" font-weight="700" fill="#1e40af">+ Register Walk-in</text>

      <line x1="195" y1="100" x2="230" y2="100" stroke="#174b89" stroke-width="2" marker-end="url(#arr2)"/>

      <rect x="235" y="45" width="180" height="110" rx="10" fill="#fefce8" stroke="#ca8a04" stroke-width="2"/>
      <text x="325" y="75" text-anchor="middle" font-weight="700" font-size="13" fill="#854d0e">2. Dedupe &amp; Token</text>
      <text x="325" y="96" text-anchor="middle" font-size="11" fill="#334155">Checks Phone in CRM</text>
      <text x="325" y="114" text-anchor="middle" font-size="11" fill="#334155">Assigns Token Number</text>
      <text x="325" y="132" text-anchor="middle" font-size="11" font-weight="700" fill="#854d0e">Status: Waiting</text>

      <line x1="415" y1="100" x2="450" y2="100" stroke="#174b89" stroke-width="2" marker-end="url(#arr2)"/>

      <rect x="455" y="45" width="185" height="110" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
      <text x="547" y="75" text-anchor="middle" font-weight="700" font-size="13" fill="#166534">3. Desk Assignment</text>
      <text x="547" y="96" text-anchor="middle" font-size="11" fill="#334155">Receptionist Checks</text>
      <text x="547" y="114" text-anchor="middle" font-size="11" fill="#334155">On-Duty Counselors</text>
      <text x="547" y="132" text-anchor="middle" font-size="11" font-weight="700" fill="#166534">Clicks Assign Counselor</text>

      <line x1="640" y1="100" x2="675" y2="100" stroke="#174b89" stroke-width="2" marker-end="url(#arr2)"/>

      <rect x="680" y="45" width="150" height="110" rx="10" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/>
      <text x="755" y="75" text-anchor="middle" font-weight="700" font-size="13" fill="#0369a1">4. Consultation</text>
      <text x="755" y="96" text-anchor="middle" font-size="11" fill="#334155">In Consultation</text>
      <text x="755" y="114" text-anchor="middle" font-size="11" fill="#334155">Demo / Fees Pitch</text>
      <text x="755" y="132" text-anchor="middle" font-size="11" fill="#334155">Notes Updated</text>

      <line x1="830" y1="100" x2="860" y2="100" stroke="#174b89" stroke-width="2" marker-end="url(#arr2)"/>

      <rect x="865" y="45" width="120" height="110" rx="10" fill="#dcfce7" stroke="#15803d" stroke-width="2"/>
      <text x="925" y="75" text-anchor="middle" font-weight="700" font-size="13" fill="#14532d">5. Outcome</text>
      <text x="925" y="96" text-anchor="middle" font-size="11" fill="#334155">Enrolled /</text>
      <text x="925" y="114" text-anchor="middle" font-size="11" fill="#334155">Follow-up /</text>
      <text x="925" y="132" text-anchor="middle" font-size="11" fill="#334155">No Show</text>
    </svg>
    """
)

# 3. Training vs Placement Flow
render_svg_to_png(
    "diag_training_vs_placement.png", 1000, 340,
    "Training vs. Placement Lead Category Handling",
    "Classification using Lead.category ('Training' vs 'Placement') at Intake & Counseling",
    """
    <svg viewBox="0 0 920 190" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arr3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#334155"/>
        </marker>
      </defs>
      <rect x="20" y="55" width="210" height="80" rx="10" fill="#f8fafc" stroke="#174b89" stroke-width="2"/>
      <text x="125" y="88" text-anchor="middle" font-weight="700" font-size="13" fill="#174b89">Lead Captured in CRM</text>
      <text x="125" y="110" text-anchor="middle" font-size="11" fill="#475569">Form / Sheet / Call / Walk-in</text>

      <line x1="230" y1="95" x2="290" y2="95" stroke="#334155" stroke-width="2" marker-end="url(#arr3)"/>

      <rect x="295" y="60" width="180" height="70" rx="35" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/>
      <text x="385" y="92" text-anchor="middle" font-weight="700" font-size="12" fill="#0369a1">Lead Category Selected</text>
      <text x="385" y="109" text-anchor="middle" font-size="11" fill="#0369a1">(Lead.category field)</text>

      <line x1="475" y1="80" x2="545" y2="45" stroke="#16a34a" stroke-width="2" marker-end="url(#arr3)"/>
      <line x1="475" y1="110" x2="545" y2="145" stroke="#7c3aed" stroke-width="2" marker-end="url(#arr3)"/>

      <rect x="550" y="10" width="350" height="74" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
      <text x="725" y="34" text-anchor="middle" font-weight="700" font-size="13" fill="#166534">Category: Training (Default)</text>
      <text x="725" y="53" text-anchor="middle" font-size="11" fill="#334155">Course pitch · Demo scheduling · Fee Installments</text>
      <text x="725" y="70" text-anchor="middle" font-size="11" fill="#334155">UTR Fee Verification &amp; Tax Receipt PDF</text>

      <rect x="550" y="106" width="350" height="74" rx="10" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2"/>
      <text x="725" y="130" text-anchor="middle" font-weight="700" font-size="13" fill="#5b21b6">Category: Placement</text>
      <text x="725" y="149" text-anchor="middle" font-size="11" fill="#334155">Tagged separately in Leads Filter &amp; Reports</text>
      <text x="725" y="166" text-anchor="middle" font-size="11" fill="#334155">Job readiness / placement support counseling</text>
    </svg>
    """
)

# 4. System Architecture Diagram
render_svg_to_png(
    "diag_system_architecture.png", 1100, 560,
    "DigiPanda / iTechPanda CRM — Technical Architecture",
    "Runtime Stack: Daphne ASGI · Django 5.1 · MySQL / SQLite · External Cloud APIs & Mobile Sync",
    """
    <svg viewBox="0 0 1000 410" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arr4" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569"/>
        </marker>
      </defs>
      <!-- Left: Clients -->
      <rect x="20" y="35" width="210" height="80" rx="10" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
      <text x="125" y="64" text-anchor="middle" font-weight="700" font-size="13" fill="#1e3a8a">Web Browsers (Staff)</text>
      <text x="125" y="84" text-anchor="middle" font-size="11" fill="#334155">HTTPS + WebSocket (WS)</text>
      <text x="125" y="100" text-anchor="middle" font-size="11" fill="#334155">10 Role Portals &amp; QR Pages</text>

      <rect x="20" y="155" width="210" height="80" rx="10" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
      <text x="125" y="184" text-anchor="middle" font-weight="700" font-size="13" fill="#166534">CallSync Android App</text>
      <text x="125" y="204" text-anchor="middle" font-size="11" fill="#334155">DRF Token Auth (/api/calls/)</text>
      <text x="125" y="220" text-anchor="middle" font-size="11" fill="#334155">Call Logs, Audio, Remote Dial</text>

      <rect x="20" y="275" width="210" height="80" rx="10" fill="#fff7ed" stroke="#ea580c" stroke-width="2"/>
      <text x="125" y="304" text-anchor="middle" font-weight="700" font-size="13" fill="#9a3412">Public Walk-in QR Forms</text>
      <text x="125" y="324" text-anchor="middle" font-size="11" fill="#334155">Mobile Browser Check-in</text>
      <text x="125" y="340" text-anchor="middle" font-size="11" fill="#334155">Token Generation</text>

      <!-- Middle: Web & App Server -->
      <line x1="230" y1="75" x2="295" y2="165" stroke="#475569" stroke-width="2" marker-end="url(#arr4)"/>
      <line x1="230" y1="195" x2="295" y2="195" stroke="#475569" stroke-width="2" marker-end="url(#arr4)"/>
      <line x1="230" y1="315" x2="295" y2="225" stroke="#475569" stroke-width="2" marker-end="url(#arr4)"/>

      <rect x="300" y="40" width="360" height="315" rx="14" fill="#f8fafc" stroke="#174b89" stroke-width="2.5"/>
      <text x="480" y="68" text-anchor="middle" font-weight="800" font-size="14" fill="#174b89">Application Server (Python 3.13 + Django 5.1)</text>
      <rect x="320" y="85" width="320" height="45" rx="8" fill="#e0f2fe" stroke="#0284c7" stroke-width="1.5"/>
      <text x="480" y="106" text-anchor="middle" font-weight="700" font-size="12" fill="#0369a1">Daphne ASGI + Django Channels</text>
      <text x="480" y="122" text-anchor="middle" font-size="10.5" fill="#334155">HTTP Views, DRF APIs &amp; Real-Time WhatsApp WebSockets</text>

      <rect x="320" y="142" width="152" height="75" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5"/>
      <text x="396" y="164" text-anchor="middle" font-weight="700" font-size="11.5" fill="#0f172a">Core CRM Engine</text>
      <text x="396" y="182" text-anchor="middle" font-size="10" fill="#475569">Intake &amp; Dedupe</text>
      <text x="396" y="196" text-anchor="middle" font-size="10" fill="#475569">Allocation &amp; SLA</text>
      <text x="396" y="210" text-anchor="middle" font-size="10" fill="#475569">Fees &amp; Receipts (PDF)</text>

      <rect x="488" y="142" width="152" height="75" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.5"/>
      <text x="564" y="164" text-anchor="middle" font-weight="700" font-size="11.5" fill="#0f172a">Background Syncs</text>
      <text x="564" y="182" text-anchor="middle" font-size="10" fill="#475569">FB Leads 48h Worker</text>
      <text x="564" y="196" text-anchor="middle" font-size="10" fill="#475569">WhatsApp Campaigns</text>
      <text x="564" y="210" text-anchor="middle" font-size="10" fill="#475569">Installment Reminders</text>

      <!-- Storage inside or below -->
      <rect x="320" y="232" width="152" height="105" rx="8" fill="#fefce8" stroke="#ca8a04" stroke-width="1.5"/>
      <text x="396" y="256" text-anchor="middle" font-weight="700" font-size="12" fill="#854d0e">Primary Database</text>
      <text x="396" y="276" text-anchor="middle" font-size="11" fill="#334155">MySQL (Production)</text>
      <text x="396" y="294" text-anchor="middle" font-size="11" fill="#334155">SQLite (Local Dev)</text>
      <text x="396" y="312" text-anchor="middle" font-size="10" fill="#64748b">Normalized Leads, Calls</text>

      <rect x="488" y="232" width="152" height="105" rx="8" fill="#f1f5f9" stroke="#64748b" stroke-width="1.5"/>
      <text x="564" y="256" text-anchor="middle" font-weight="700" font-size="12" fill="#334155">File &amp; Media Storage</text>
      <text x="564" y="276" text-anchor="middle" font-size="11" fill="#334155">private_media/</text>
      <text x="564" y="294" text-anchor="middle" font-size="10" fill="#475569">Audio Recordings</text>
      <text x="564" y="312" text-anchor="middle" font-size="10" fill="#475569">UTR Proofs (Auth-gated)</text>

      <!-- Right: External Integrations -->
      <line x1="660" y1="80" x2="735" y2="65" stroke="#475569" stroke-width="2" marker-end="url(#arr4)"/>
      <line x1="660" y1="145" x2="735" y2="145" stroke="#475569" stroke-width="2" marker-end="url(#arr4)"/>
      <line x1="660" y1="225" x2="735" y2="225" stroke="#475569" stroke-width="2" marker-end="url(#arr4)"/>
      <line x1="660" y1="305" x2="735" y2="305" stroke="#475569" stroke-width="2" marker-end="url(#arr4)"/>

      <rect x="740" y="30" width="240" height="65" rx="8" fill="#eff6ff" stroke="#1877f2" stroke-width="2"/>
      <text x="860" y="56" text-anchor="middle" font-weight="700" font-size="12" fill="#1877f2">Meta Graph API (Lead Ads)</text>
      <text x="860" y="75" text-anchor="middle" font-size="10.5" fill="#334155">Webhooks + 48h Polling</text>

      <rect x="740" y="112" width="240" height="65" rx="8" fill="#dcfce7" stroke="#25d366" stroke-width="2"/>
      <text x="860" y="138" text-anchor="middle" font-weight="700" font-size="12" fill="#15803d">WhatsApp Cloud API</text>
      <text x="860" y="157" text-anchor="middle" font-size="10.5" fill="#334155">Chat, Templates, Flows &amp; Voice Check</text>

      <rect x="740" y="194" width="240" height="65" rx="8" fill="#fefce8" stroke="#eab308" stroke-width="2"/>
      <text x="860" y="220" text-anchor="middle" font-weight="700" font-size="12" fill="#854d0e">Google Workspace APIs</text>
      <text x="860" y="239" text-anchor="middle" font-size="10.5" fill="#334155">Sheets, Forms &amp; Drive Recordings</text>

      <rect x="740" y="276" width="240" height="65" rx="8" fill="#f3e8ff" stroke="#7c3aed" stroke-width="2"/>
      <text x="860" y="302" text-anchor="middle" font-weight="700" font-size="12" fill="#5b21b6">SMTP Email &amp; AI Services</text>
      <text x="860" y="321" text-anchor="middle" font-size="10.5" fill="#334155">Receipts, Reminders, Credentials</text>
    </svg>
    """
)

# 5. ER Diagram
render_svg_to_png(
    "diag_er_database.png", 1100, 560,
    "Core Database Entity Relationships (ER Overview)",
    "Primary Models & Foreign Key Relationships in CRM_Integrated_v2",
    """
    <svg viewBox="0 0 1000 410" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arr5" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569"/>
        </marker>
      </defs>
      <!-- Branch & User -->
      <rect x="30" y="25" width="180" height="90" rx="8" fill="#f1f5f9" stroke="#475569" stroke-width="2"/>
      <text x="120" y="48" text-anchor="middle" font-weight="700" font-size="13" fill="#0f172a">Branch</text>
      <text x="42" y="68" font-size="10.5" fill="#334155">• id, name, code</text>
      <text x="42" y="84" font-size="10.5" fill="#334155">• address, phone</text>
      <text x="42" y="100" font-size="10.5" fill="#334155">• is_active</text>

      <rect x="30" y="150" width="190" height="110" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
      <text x="125" y="173" text-anchor="middle" font-weight="700" font-size="13" fill="#1e3a8a">User (accounts)</text>
      <text x="42" y="193" font-size="10.5" fill="#334155">• role (10 RBAC roles)</text>
      <text x="42" y="209" font-size="10.5" fill="#334155">• branch (FK), counselor</text>
      <text x="42" y="225" font-size="10.5" fill="#334155">• is_on_duty (allocation)</text>
      <text x="42" y="241" font-size="10.5" fill="#334155">• must_change_password</text>

      <!-- Lead (Central Hub) -->
      <rect x="360" y="100" width="260" height="190" rx="10" fill="#fefce8" stroke="#ca8a04" stroke-width="2.5"/>
      <text x="490" y="126" text-anchor="middle" font-weight="800" font-size="15" fill="#854d0e">Lead (Central Hub)</text>
      <text x="376" y="148" font-size="11" fill="#334155">• id, name, phone, normalized_phone</text>
      <text x="376" y="166" font-size="11" fill="#334155">• category (Training | Placement)</text>
      <text x="376" y="184" font-size="11" fill="#334155">• status (21 statuses) · visitor_status</text>
      <text x="376" y="202" font-size="11" fill="#334155">• channel (FK), product (FK), platform</text>
      <text x="376" y="220" font-size="11" fill="#334155">• assigned_telecaller / counselor / head</text>
      <text x="376" y="238" font-size="11" fill="#334155">• token_number, is_offline, rating</text>
      <text x="376" y="256" font-size="11" fill="#334155">• whatsapp_opt_out / consent_given</text>

      <!-- Connecting Lines to Lead -->
      <line x1="120" y1="115" x2="120" y2="150" stroke="#475569" stroke-width="1.8"/>
      <line x1="210" y1="70" x2="360" y2="145" stroke="#475569" stroke-width="1.8" marker-end="url(#arr5)"/>
      <line x1="220" y1="205" x2="360" y2="205" stroke="#2563eb" stroke-width="1.8" marker-end="url(#arr5)"/>

      <!-- FollowUp & Calls -->
      <rect x="740" y="25" width="230" height="90" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
      <text x="855" y="48" text-anchor="middle" font-weight="700" font-size="13" fill="#166534">FollowUp</text>
      <text x="754" y="68" font-size="10.5" fill="#334155">• lead (FK), assigned_user (FK)</text>
      <text x="754" y="84" font-size="10.5" fill="#334155">• follow_up_date, time, status</text>
      <text x="754" y="100" font-size="10.5" fill="#334155">• notes (Pending / Completed)</text>

      <rect x="740" y="140" width="230" height="105" rx="8" fill="#e0f2fe" stroke="#0284c7" stroke-width="2"/>
      <text x="855" y="163" text-anchor="middle" font-weight="700" font-size="13" fill="#0369a1">Calls &amp; Recordings</text>
      <text x="754" y="183" font-size="10.5" fill="#334155">• CallHistory (status, outcome, dur)</text>
      <text x="754" y="199" font-size="10.5" fill="#334155">• CallEvent (Google call / callback)</text>
      <text x="754" y="215" font-size="10.5" fill="#334155">• CallRecording (audio file / match)</text>
      <text x="754" y="231" font-size="10.5" fill="#334155">• CallDevice (sync_cutoff_date)</text>

      <rect x="740" y="270" width="230" height="115" rx="8" fill="#faf5ff" stroke="#7c3aed" stroke-width="2"/>
      <text x="855" y="293" text-anchor="middle" font-weight="700" font-size="13" fill="#5b21b6">Enrollment &amp; Fees</text>
      <text x="754" y="313" font-size="10.5" fill="#334155">• Enrollment (total_fee, status)</text>
      <text x="754" y="329" font-size="10.5" fill="#334155">• Installment (due_date, amount)</text>
      <text x="754" y="345" font-size="10.5" fill="#334155">• PaymentTransaction (utr, status)</text>
      <text x="754" y="361" font-size="10.5" fill="#334155">• ApprovedOffer, EmailLog</text>

      <!-- Bottom Left: FB & WhatsApp -->
      <rect x="30" y="295" width="235" height="90" rx="8" fill="#ecfdf5" stroke="#059669" stroke-width="2"/>
      <text x="147" y="318" text-anchor="middle" font-weight="700" font-size="13" fill="#065f46">FacebookLead &amp; Conversation</text>
      <text x="44" y="338" font-size="10.5" fill="#334155">• FacebookPage (sync_cutoff_date)</text>
      <text x="44" y="354" font-size="10.5" fill="#334155">• FacebookLead (leadgen_id, lead FK)</text>
      <text x="44" y="370" font-size="10.5" fill="#334155">• Conversation / Message (24h window)</text>

      <line x1="620" y1="135" x2="740" y2="70" stroke="#16a34a" stroke-width="1.8" marker-end="url(#arr5)"/>
      <line x1="620" y1="195" x2="740" y2="195" stroke="#0284c7" stroke-width="1.8" marker-end="url(#arr5)"/>
      <line x1="620" y1="255" x2="740" y2="325" stroke="#7c3aed" stroke-width="1.8" marker-end="url(#arr5)"/>
      <line x1="265" y1="340" x2="360" y2="265" stroke="#059669" stroke-width="1.8" marker-end="url(#arr5)"/>
    </svg>
    """
)

# 6. 48h Rolling Auto-Sync & Manual Override Diagram
render_svg_to_png(
    "diag_callsync_and_48h.png", 1000, 340,
    "48-Hour Rolling Auto-Sync Shield & Manual Override Flow",
    "Protects CRM Database Against Zombie Leads After Data Cleanup (Facebook Leads & CallSync)",
    """
    <svg viewBox="0 0 920 190" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arr6" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#174b89"/>
        </marker>
      </defs>
      <rect x="20" y="45" width="210" height="90" rx="10" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
      <text x="125" y="74" text-anchor="middle" font-weight="700" font-size="12.5" fill="#1e3a8a">Incoming Sync Event</text>
      <text x="125" y="94" text-anchor="middle" font-size="11" fill="#334155">1. Facebook Auto-Sync Worker</text>
      <text x="125" y="112" text-anchor="middle" font-size="11" fill="#334155">2. CallSync Logs &amp; Recordings</text>

      <line x1="230" y1="90" x2="280" y2="90" stroke="#174b89" stroke-width="2" marker-end="url(#arr6)"/>

      <rect x="285" y="45" width="215" height="90" rx="10" fill="#fefce8" stroke="#ca8a04" stroke-width="2"/>
      <text x="392" y="72" text-anchor="middle" font-weight="700" font-size="12.5" fill="#854d0e">Age Cutoff Check</text>
      <text x="392" y="92" text-anchor="middle" font-size="11" fill="#334155">Auto-Sync Limit: Last 48 Hrs</text>
      <text x="392" y="110" text-anchor="middle" font-size="11" fill="#334155">Respects Page/Device Cutoff Date</text>

      <line x1="500" y1="70" x2="575" y2="42" stroke="#16a34a" stroke-width="2" marker-end="url(#arr6)"/>
      <line x1="500" y1="110" x2="575" y2="140" stroke="#dc2626" stroke-width="2" marker-end="url(#arr6)"/>

      <rect x="580" y="12" width="315" height="65" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="2"/>
      <text x="737" y="36" text-anchor="middle" font-weight="700" font-size="12" fill="#166534">Within 48h OR Manual Override ON</text>
      <text x="737" y="56" text-anchor="middle" font-size="11" fill="#334155">Saved permanently into CRM DB (Dedupe applied)</text>

      <rect x="580" y="105" width="315" height="65" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="2"/>
      <text x="737" y="129" text-anchor="middle" font-weight="700" font-size="12" fill="#991b1b">Older than 48h (No Override)</text>
      <text x="737" y="149" text-anchor="middle" font-size="11" fill="#334155">Skipped safely — Zero old leads resurrected!</text>
    </svg>
    """
)
