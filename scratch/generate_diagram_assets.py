import os
import urllib.request
import time

ASSETS_DIR = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\docs\assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

DIAGRAMS = {
    "arch_container_diagram.svg": """
flowchart TB
    subgraph Clients["Clients & Edge Devices"]
        Browser["Desktop & Mobile Web Browsers\\n(Counselors, Admins, Accountants)"]
        CallSyncApp["Android CallSync Native App\\n(Counselor Smartphones)"]
        LeadAdsUser["Prospective Student\\n(Meta Ads / WhatsApp)"]
    end

    subgraph Edge["Reverse Proxy & Gateway"]
        Nginx["Nginx Reverse Proxy\\n(SSL Termination, Static Assets, Proxy Buffer)"]
    end

    subgraph ApplicationServer["Application Runtime (Docker Container)"]
        Daphne["Daphne ASGI Server\\n(HTTP & WebSockets on Port 8000/8001)"]
        
        subgraph DjangoCore["Django Application Core (v5.1.15)"]
            AccountsModule["accounts: RBAC & Auth Engine"]
            LeadsModule["leads: Pipeline & Allocation Engine"]
            ChatModule["chat: WhatsApp Cloud Engine & Visual Flow"]
            CallsModule["calls: Telephony & CallSync Telemetry"]
            FinanceModule["finance: Invoicing, Receipts & Dunning"]
            CoursesModule["courses: Curriculum & Batches"]
        end

        subgraph BackgroundThreads["In-Process Background Workers"]
            FBSyncWorker["fb_leads.scheduler: Facebook Polling Daemon"]
            DunningCron["finance.dunning: Scheduled Overdue Reminders"]
            ChannelsLayer["Django Channels Layer\\n(InMemory / Redis Backed)"]
        end
    end

    subgraph Persistence["Data & Storage Layer"]
        MySQL[("MySQL 8.0 Primary DB\\n(InnoDB, utf8mb4)")]
        MediaStorage[("Local / Persistent Volume\\n(PDF Receipts, Audio, Lightbox Proofs)")]
    end

    subgraph ExternalServices["External Cloud APIs & Services"]
        MetaGraph["Meta Cloud Graph API v18.0\\n(WhatsApp Business & Lead Ads)"]
        OpenAI["AI LLM Services\\n(Objection Coach & WhatsApp Concierge)"]
        SMTPEmail["SMTP Gateway\\n(Gmail / Transactional Mail)"]
    end

    Browser -->|HTTPS / WSS| Nginx
    CallSyncApp -->|REST API over HTTPS| Nginx
    LeadAdsUser -->|Ad Submission / Chat| MetaGraph

    Nginx -->|Proxy HTTP & /ws/| Daphne
    Daphne --> DjangoCore

    DjangoCore --> ChannelsLayer
    DjangoCore --> MySQL
    DjangoCore --> MediaStorage

    FBSyncWorker -->|Periodic Polling| MetaGraph
    FBSyncWorker -->|Ingest Leads| LeadsModule
    ChatModule -->|Webhook & Send Message| MetaGraph
    CallsModule -->|AI Talk-tracks| OpenAI
    FinanceModule -->|Send Invoices/Alerts| SMTPEmail
""",

    "dataflow_meta_lead_ads.svg": """
sequenceDiagram
    autonumber
    participant Lead as Prospective Student
    participant Meta as Meta Graph API
    participant CRM as fb_leads App (Django)
    participant LeadEngine as leads.AllocationEngine
    participant Counselor as Counselor Screen

    Lead->>Meta: Submits Lead Ad Form
    par Webhook Notification (Real-Time)
        Meta->>CRM: HTTP POST /fb_leads/webhook/ (leadgen_id)
        CRM->>Meta: GET /{leadgen_id} (Fetch Field Data)
        Meta-->>CRM: Lead Details (Name, Phone, Course)
        CRM->>LeadEngine: Deduplicate & Ingest Lead
    and Background Auto-Sync Worker (Fallback)
        CRM->>Meta: Polling due pages every N minutes (fb_leads.scheduler)
        Meta-->>CRM: Missed lead submissions
        CRM->>LeadEngine: Deduplicate & Ingest Lead
    end
    LeadEngine->>LeadEngine: Check Counselor On-Duty Status & Assign
    LeadEngine-->>Counselor: WebSocket Push Notification (/ws/leads/)
""",

    "telephony_callsync_heartbeat.svg": """
sequenceDiagram
    autonumber
    participant Phone as Android CallSync App
    participant API as calls.views (DRF)
    participant DB as MySQL Database
    participant LeadRecord as Lead Timeline

    loop Every 60 Seconds (Heartbeat Telemetry)
        Phone->>API: POST /calls/api/callsync/heartbeat/ {battery: 84%, status: 'IDLE', wifi: true}
        API->>DB: Update CallDevice (battery_level, is_online, last_heartbeat)
    end

    opt Call Event Triggered
        Phone->>Phone: Native Cellular Call Connected
        Phone->>API: POST /calls/api/callsync/logs/ {lead_phone, duration: 184, recording_url}
        API->>DB: Save CallHistory Record
        API->>LeadRecord: Append Call Entry to Lead 360 Timeline
    end
""",

    "chat_whatsapp_24hr_window.svg": """
flowchart TD
    UserMsg["Incoming Student Message via WhatsApp"] --> Webhook["POST /webhook/whatsapp/"]
    Webhook --> VerifyHMAC{"Verify SHA256 Signature"}
    VerifyHMAC -- Invalid --> Reject["403 Forbidden"]
    VerifyHMAC -- Valid --> Ingest["Save to chat.Message & chat.Conversation"]
    
    Ingest --> ResetWindow["Update Conversation.last_incoming_at\\n(Opens 24-Hour Window)"]
    ResetWindow --> CheckBot{"Is AI Concierge Enabled\\nfor this Lead?"}
    
    CheckBot -- Yes --> AIResponse["chat.whatsapp.ai_concierge\\nGenerate Instant Course/Fee Answer"]
    AIResponse --> SendWA["POST to Meta Graph API\\nSend Text/Document"]
    
    CheckBot -- No --> AlertCounselor["Notify Counselor on Chat Screen\\n(Remaining Window Displayed in UI)"]
""",

    "er_diagram_models.svg": """
erDiagram
    BRANCH ||--o{ USER : employs
    BRANCH ||--o{ LEAD : owns
    BRANCH ||--o{ INVOICE : issues

    USER ||--o{ LEAD : assigned_to
    USER ||--o{ CALL_DEVICE : operates
    USER ||--o{ CALL_HISTORY : places
    USER ||--o{ ACTIVITY_LOG : initiates

    LEAD ||--o{ CALL_HISTORY : receives
    LEAD ||--o{ CONVERSATION : engages_in
    LEAD ||--o{ INVOICE : billed
    LEAD }|--|| LEAD_CHANNEL : acquired_from

    CONVERSATION ||--o{ MESSAGE : contains
    
    INVOICE ||--o{ INSTALLMENT : schedules
    INVOICE ||--o{ PAYMENT_TRANSACTION : collected_via
    INSTALLMENT ||--o{ PAYMENT_TRANSACTION : allocated_to

    BRANCH {
        int id PK
        string name
        string code
    }
    USER {
        int id PK
        string username
        string role
        boolean is_on_duty
    }
    LEAD {
        int id PK
        string full_name
        string phone
        string stage
    }
    CALL_DEVICE {
        int id PK
        string device_id
        int battery_level
        boolean is_online
    }
    INVOICE {
        int id PK
        string invoice_number
        decimal total_amount
    }
    INSTALLMENT {
        int id PK
        decimal amount
        date due_date
        string status
    }
    PAYMENT_TRANSACTION {
        int id PK
        string utr_number UK
        decimal amount
        string verification_status
    }
""",

    # SOP 01-10 Workflow Flowcharts
    "sop_01_flow.svg": """
flowchart LR
    A([Start Release]) --> B[Pre-flight Tests & Code Freeze]
    B --> C[Full MySQL Safety Dump]
    C --> D[Build Docker Container Image]
    D --> E[Execute Database Migrations]
    E --> F[Container Swap & Nginx Reload]
    F --> G{Smoke Test & Verify}
    G -- Passed --> H([Release Active])
    G -- Failed --> I[Trigger SOP-02 Rollback]
""",

    "sop_02_flow.svg": """
flowchart LR
    A([Incident Outage]) --> B[Declare Rollback & Halt Traffic]
    B --> C[Stop & Terminate Failed Container]
    C --> D{Were Migrations Destructive?}
    D -- Yes --> E[Restore DB from Pre-Release Backup]
    D -- No --> F[Keep Additive DB Schema]
    E --> G[Deploy Previous Docker Image]
    F --> G
    G --> H[Reload Nginx & Verify Login]
    H --> I([Service Restored])
""",

    "sop_03_flow.svg": """
flowchart LR
    A([New Engineer]) --> B[Clone Repository]
    B --> C[Create & Activate Python venv]
    C --> D[Install requirements.txt]
    D --> E[Configure Local .env]
    E --> F[Run Migrations & Create Superuser]
    F --> G[Run Unit Tests]
    G --> H([Developer Ready])
""",

    "sop_04_flow.svg": """
flowchart LR
    A([Backup Trigger]) --> B[Execute mysqldump with --single-transaction]
    B --> C[Gzip Compression]
    C --> D[Store Local Daily Volume]
    D --> E[Purge Backups > 30 Days]
    E --> F{Restore Drill?}
    F -- Yes --> G[Stream Unpack into Test DB & Verify Tables]
    F -- No --> H([Backup Complete])
    G --> H
""",

    "sop_05_flow.svg": """
flowchart LR
    A([Alert Detected]) --> B[Triage & Assign Severity SEV 1-4]
    B --> C[Page Incident Commander]
    C --> D[Inspect Logs & Server Telemetry]
    D --> E[Apply Fix or Restart Service]
    E --> F[Verify HTTP 200 & Notify Staff]
    F --> G[Conduct Blameless Post-Mortem in 24h]
    G --> H([Incident Closed])
""",

    "sop_06_flow.svg": """
flowchart LR
    A([Rotation Schedule]) --> B{Select Target Secret}
    B -- SECRET_KEY --> C[Generate Token & Restart Container]
    B -- MySQL Password --> D[ALTER USER in DB & Update .env]
    B -- Meta Token --> E[Generate Permanent System Token in WABA]
    B -- Gmail SMTP --> F[Generate Google App Password]
    C --> G[Verify Service Health & Zero Auth Errors]
    D --> G
    E --> G
    F --> G
    G --> H([Rotation Complete])
""",

    "sop_07_flow.svg": """
flowchart LR
    A([Continuous Monitoring]) --> B[External HTTP Health Probe]
    A --> C[CallSync Device Heartbeat Engine]
    A --> D[Database Processlist & Storage Thresholds]
    A --> E[Facebook Auto-Sync Worker Thread]
    B --> F{Threshold Breached?}
    C --> F
    D --> F
    E --> F
    F -- Yes --> G[Trigger Alert & Dispatch Ops Runbook]
    F -- No --> H([All Systems Operational])
""",

    "sop_08_flow.svg": """
flowchart LR
    A([User Request]) --> B{Action Type}
    B -- Onboarding --> C[Create User, Assign Role & Branch Scope]
    B -- Daily Presence --> D[Toggle Staff Duty On/Off Switch]
    B -- Campus Transfer --> E[Reassign Open Leads & Update Branch]
    B -- Offboarding --> F[Deactivate is_active & Re-allocate Leads]
    C --> G([Audit Logged])
    D --> G
    E --> G
    F --> G
""",

    "sop_09_flow.svg": """
flowchart LR
    A([Maintenance Engine]) --> B[Daily: Clear Expired Django Sessions]
    A --> C[Weekly: Logrotate & Compress Worker Logs]
    A --> D[Monthly: OPTIMIZE TABLE on MySQL DB]
    A --> E[Quarterly: pip-audit Vulnerability Scan]
    B --> F([System Optimized & Clean])
    C --> F
    D --> F
    E --> F
""",

    "sop_10_flow.svg": """
flowchart LR
    A([New Campus SIM]) --> B[Release Number from WhatsApp App]
    B --> C[Add Number in Meta Business Manager & Verify OTP]
    C --> D[Retrieve Phone Number ID & WABA ID]
    D --> E[Configure Webhook URL & Verify Token]
    E --> F[Submit & Approve Meta Message Templates]
    F --> G[Send Inbound Test Chat & Verify 24-hr Window]
    G --> H([WhatsApp Channel Live])
"""
}

def render_diagrams():
    print("Rendering Mermaid diagrams via Kroki...")
    for filename, code in DIAGRAMS.items():
        filepath = os.path.join(ASSETS_DIR, filename)
        url = "https://kroki.io/mermaid/svg"
        req = urllib.request.Request(
            url,
            data=code.strip().encode("utf-8"),
            headers={"Content-Type": "text/plain", "User-Agent": "Mozilla/5.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()
                with open(filepath, "wb") as f:
                    f.write(content)
                print(f"  [SUCCESS] {filename} ({len(content)} bytes)")
        except Exception as e:
            print(f"  [ERROR] Failed to render {filename}: {e}")
        time.sleep(0.3)

if __name__ == "__main__":
    render_diagrams()
