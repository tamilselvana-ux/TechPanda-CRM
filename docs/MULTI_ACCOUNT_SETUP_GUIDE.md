# TechPanda CRM: Multi-Account Setup Guide (8+ WhatsApp & Facebook Accounts)

This runbook provides step-by-step instructions to connect 8 or more distinct WhatsApp Cloud API numbers and Facebook Lead Ad developer accounts to TechPanda CRM, complete with branch routing and webhook synchronization.

You can configure your accounts using either **Method A (Direct Web UI - Recommended for non-technical users)** or **Method B (Bulk Configuration via .env)**.

---

## 1. Credentials Needed from Meta for Developers

Before starting, log in to [developers.facebook.com](https://developers.facebook.com/) and gather the following details for each developer account:

### For Each WhatsApp Number:
1. **Phone Number**: The international format number (e.g., `+91 95006 27756`).
2. **Phone Number ID**: Go to WhatsApp > API Setup > Step 1. Copy the **Phone number ID** (e.g., `129416667`).
3. **WhatsApp Business Account ID (WABA ID)**: In WhatsApp > API Setup, copy the **WhatsApp Business Account ID** (e.g., `2520938595057665`).
4. **Access Token**: A permanent System User Access Token generated in Meta Business Manager with permissions:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
5. **App Secret**: Found under App Settings > Basic > **App Secret**.
6. **Webhook Verify Token**: Any secure secret passphrase you choose (e.g., `techpanda-crm-2026`).

### For Each Facebook Page / Lead Ad Account:
1. **Page ID**: Found under Meta Business Suite > Settings > Pages.
2. **Page Access Token**: A permanent Page Access Token generated via Meta System User with permissions:
   - `leads_retrieval`
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_ads`
3. **Meta App Secret**: Found under App Settings > Basic > **App Secret**.
4. **Webhook Verify Token**: Your chosen verify token (e.g., `techpanda-crm-2026`).

---

## Method A: Connecting Accounts via the CRM Web UI (Fastest & User-Friendly)

### Part 1: Adding a WhatsApp Account in the Web UI
1. Log in to the CRM as Admin or Sales Head.
2. Navigate to **WhatsApp & Facebook Inbox** at `/chat/inbox/`.
3. In the left panel, click the **+ Add Account** button (or click the plus button next to the account switcher).
4. Fill in the modal fields:
   - **Account Name / Label**: E.g., `T. Nagar WhatsApp Line` or `Velachery Admissions`.
   - **Phone Number**: E.g., `+91 95006 27756`.
   - **Phone Number ID**: Paste the Phone Number ID from Meta.
   - **WhatsApp Business Account ID**: Paste the WABA ID.
   - **Assigned Branch**: Select the physical branch that owns this number (e.g., `T. Nagar`, `Velachery`, `Anna Nagar`). Incoming inquiries to this number will automatically assign to this branch.
   - **Access Token (Optional)**: Paste the permanent System User Token for this number.
   - **Meta App Secret (Optional)**: Paste the App Secret from Meta Developer Portal.
   - **Webhook Verify Token (Optional)**: Enter your verify token (e.g., `techpanda-crm-2026`).
5. Click **Add Account**.
6. Repeat this process for all 8 or more WhatsApp numbers.

---

### Part 2: Connecting a Facebook Lead Ad Account in the Web UI
1. Navigate to **Facebook Accounts & Pages** at `/fb/accounts/`.
2. Click **Connect Facebook Account**.
3. Fill in the modal fields:
   - **Account Name / Label**: E.g., `Anna Nagar Meta Ads Account`.
   - **Facebook User / Page Access Token**: Paste the token with lead retrieval permissions.
   - **Target Branch**: Select the branch that should receive leads from these Facebook pages (e.g., `Anna Nagar`).
   - **App ID (Optional)**: Paste the Meta App ID.
   - **Meta App Secret (Optional)**: Paste the App Secret.
   - **Webhook Verify Token (Optional)**: Enter your verify token.
4. Click **Connect Account**.
5. The CRM immediately verifies the token with Meta Graph API, imports all associated Facebook Pages, and assigns each imported page to the selected Target Branch.
6. Repeat this process for all other Facebook developer accounts.

---

## Method B: Bulk Setup via .env (Power User Workflow)

If you prefer to configure all 8+ developer accounts in your configuration file, open `CRM/.env` and define them using numbered variable blocks:

```env
# ----------------------------------------------------------------------
# WHATSAPP DEVELOPER ACCOUNTS (1 to 8+)
# ----------------------------------------------------------------------
WHATSAPP_1_NAME="T. Nagar Main Line"
WHATSAPP_1_PHONE="+91 95006 27756"
WHATSAPP_1_PHONE_ID="129416667"
WHATSAPP_1_WABA_ID="2520938595057665"
WHATSAPP_1_ACCESS_TOKEN="EAAxxxxxx_token_dev_1"
WHATSAPP_1_APP_SECRET="app_secret_dev_1"
WHATSAPP_1_VERIFY_TOKEN="techpanda-crm-2026"
WHATSAPP_1_BRANCH="T. Nagar"

WHATSAPP_2_NAME="Velachery Line"
WHATSAPP_2_PHONE="+91 98402 22222"
WHATSAPP_2_PHONE_ID="100000000000002"
WHATSAPP_2_WABA_ID="200000000000002"
WHATSAPP_2_ACCESS_TOKEN="EAAxxxxxx_token_dev_2"
WHATSAPP_2_APP_SECRET="app_secret_dev_2"
WHATSAPP_2_VERIFY_TOKEN="techpanda-crm-2026"
WHATSAPP_2_BRANCH="Velachery"

WHATSAPP_3_NAME="Anna Nagar Line"
WHATSAPP_3_PHONE="+91 98403 33333"
WHATSAPP_3_PHONE_ID="100000000000003"
WHATSAPP_3_WABA_ID="200000000000003"
WHATSAPP_3_ACCESS_TOKEN="EAAxxxxxx_token_dev_3"
WHATSAPP_3_APP_SECRET="app_secret_dev_3"
WHATSAPP_3_VERIFY_TOKEN="techpanda-crm-2026"
WHATSAPP_3_BRANCH="Anna Nagar"

# Continue for WHATSAPP_4_* through WHATSAPP_8_*

# ----------------------------------------------------------------------
# FACEBOOK LEAD AD ACCOUNTS (1 to 8+)
# ----------------------------------------------------------------------
FB_PAGE_1_NAME="T. Nagar TechPanda Page"
FB_PAGE_1_PAGE_ID="1257838164088995"
FB_PAGE_1_TOKEN="EAAxxxxxx_fb_token_1"
FB_PAGE_1_APP_ID="100000000000001"
FB_PAGE_1_APP_SECRET="fb_secret_dev_1"
FB_PAGE_1_VERIFY_TOKEN="techpanda-crm-2026"
FB_PAGE_1_BRANCH="T. Nagar"

FB_PAGE_2_NAME="Velachery Branch Page"
FB_PAGE_2_PAGE_ID="1257838164088996"
FB_PAGE_2_TOKEN="EAAxxxxxx_fb_token_2"
FB_PAGE_2_APP_ID="100000000000002"
FB_PAGE_2_APP_SECRET="fb_secret_dev_2"
FB_PAGE_2_VERIFY_TOKEN="techpanda-crm-2026"
FB_PAGE_2_BRANCH="Velachery"

# Continue for FB_PAGE_3_* through FB_PAGE_8_*
```

### Auto-Provisioning to Database:
Once configured in `.env`, run the automated provisioning command:
```bash
python CRM/manage.py sync_env_meta_accounts
```
This automatically creates or updates the database records, attaches branch foreign keys, and configures the multi-secret signature validator without manual clicking.

---

## 3. Configuring Meta Webhooks (Crucial Step for Inbound Messages & Leads)

For incoming WhatsApp messages and Facebook lead ads to reach TechPanda CRM automatically, configure the webhooks in the Meta Developer Portal for each of your apps:

### 1. WhatsApp Cloud API Webhook:
1. In Meta Developer Portal, select your WhatsApp App > **WhatsApp** > **Configuration**.
2. Click **Edit** under Webhook.
3. Set **Callback URL**: `https://<your-crm-domain>/chat/webhook/` (e.g., `https://crm.techpanda.com/chat/webhook/`).
4. Set **Verify Token**: Enter the same verify token you configured (e.g., `techpanda-crm-2026`).
5. Click **Verify and Save**.
6. Under Webhook fields, click **Manage** and subscribe to **`messages`**.

### 2. Facebook Lead Ads Webhook:
1. In Meta Developer Portal, select your Facebook App > **Webhooks** (under Products).
2. Choose **Page** from the dropdown and click **Subscribe to this object**.
3. Set **Callback URL**: `https://<your-crm-domain>/fb/webhook/` (e.g., `https://crm.techpanda.com/fb/webhook/`).
4. Set **Verify Token**: Enter your verify token (e.g., `techpanda-crm-2026`).
5. Click **Verify and Save**.
6. In the list of Page webhook fields, click **Subscribe** next to **`leadgen`**.
7. In Meta Business Manager, go to **Integrations** > **Leads Access** and confirm that CRM app access is granted for your Pages.

---

## 4. How Branch Routing Works Automatically

1. **WhatsApp Inquiries**:
   - When a student sends a message to WhatsApp Line 1, the CRM matches `phone_number_id = 129416667`.
   - Because Line 1 is assigned to `T. Nagar`, the new lead is created with `branch = T. Nagar`.
   - If a message arrives on Line 2 (`Velachery`), the lead is assigned to `branch = Velachery`.

2. **Facebook Leads**:
   - When a student submits a lead form on Facebook Page 1, Meta sends the `leadgen` event to `/fb/webhook/`.
   - The CRM finds Page 1 in the database and checks its assigned branch (`T. Nagar`).
   - The lead is automatically routed and allocated to `T. Nagar` staff (telecallers and counselors).

---

## 5. Inbound WhatsApp Delivery Diagnostic: Why You Can Send but Cannot Receive

If outbound messages work (meaning your `access_token` and `phone_number_id` are valid) but incoming messages from customers do NOT appear in the CRM inbox, check these 4 critical items:

### Item 1: Subscribe to the 'messages' Webhook Field in Meta Portal
Even after your Webhook Callback URL shows "Verified", Meta will NEVER send customer messages to your server until you explicitly subscribe to the field:
1. Go to developers.facebook.com > Your App > WhatsApp > Configuration.
2. In the Webhook section, click "Manage".
3. Find the row named "messages".
4. Click "Subscribe" (ensure the status indicates Subscribed).
5. Without this step, Meta completely discards incoming chat payloads.

### Item 2: Public HTTPS URL Accessibility (Localhost Limitation)
- Outbound messages work from any machine (including localhost) because your CRM initiates outbound HTTPS connections to graph.facebook.com.
- Inbound messages require Meta Cloud servers to make an incoming HTTP POST request to your CRM.
- If your server runs on localhost (127.0.0.1:8000), Meta cannot reach it. You must expose your server via a public HTTPS URL (using an active domain with SSL or an HTTPS tunnel such as ngrok: `ngrok http 8000`).

### Item 3: Valid Callback URL Routing
The CRM now resiliently accepts all standard callback URL paths:
- `https://<your-domain>/webhook/whatsapp/`
- `https://<your-domain>/webhook/`
- `https://<your-domain>/chat/webhook/`
- `https://<your-domain>/whatsapp/webhook/`

Ensure your Meta Webhook Callback URL uses HTTPS and points to one of these routes.

### Item 4: Matching App Secret (X-Hub-Signature-256 HMAC Validation)
Meta signs every incoming POST payload using your Meta App Secret. The CRM verifies this signature before processing the message.
- If `WHATSAPP_APP_SECRET` in `.env` is missing or does not match the App Secret in Meta Developer Portal (App Settings > Basic > App Secret), the server rejects the message with HTTP 403 (Bad signature).
- For multiple developer accounts, specify all secrets in `.env` separated by commas (e.g. `WHATSAPP_APP_SECRET="secret1, secret2"`) or use numbered variables `WHATSAPP_1_APP_SECRET="secret1"`, `WHATSAPP_2_APP_SECRET="secret2"`. Both single and comma-separated formats are automatically supported.
