# Meta Lead Ads Architecture Plan: Separating Facebook & Instagram Leads

## 1. Executive Context & Objective

DigiPanda CRM currently receives leads through Meta Lead Ads (instant forms running across Meta's ad network). Because Facebook and Instagram ad placements run under the same Meta Business Manager and Ad Account, all inbound leads are currently labeled as `Facebook`. 

**Goal:** Provide an end-to-end technical and operational architecture to cleanly capture, distinguish, filter, and report **Facebook** and **Instagram** leads separately throughout the CRM.

---

## 2. How Meta Identifies the Lead Platform

When a user submits a Meta Lead Form, Meta's API provides the exact origin platform.

### A. Direct Webhook & Meta Graph API
When fetching the lead details from Meta via `GET https://graph.facebook.com/v19.0/{leadgen_id}`:
```json
{
  "id": "123456789012345",
  "created_time": "2026-10-30T06:30:00+0000",
  "ad_id": "238510000000000",
  "ad_name": "Data Analytics - IG Reels Video Ad",
  "adset_name": "Chennai 18-28 IG Placement",
  "campaign_name": "Q4_Admissions_Drive",
  "form_id": "987654321098765",
  "platform": "ig",   <--- "fb" for Facebook, "ig" for Instagram
  "field_data": [
    { "name": "full_name", "values": ["Arun Kumar"] },
    { "name": "phone_number", "values": ["+919876543210"] },
    { "name": "email", "values": ["arun@example.com"] }
  ]
}
```

### B. Google Sheets / Integration Middlewares (Zapier, Make, Pabbly)
When Meta leads are routed via Google Sheets or Webhooks:
- Meta automatically includes a column named `platform` (values: `fb` or `ig`).
- If using UTM tracking links or custom form fields, `utm_source` equals `facebook` or `instagram`.

---

## 3. Recommended Implementation Plan

### Phase 1: Database Model & Normalization Update
1. **Update `CANONICAL_LEAD_SOURCES` & Normalization (`leads/models.py`)**:
   ```python
   CANONICAL_LEAD_SOURCES = [
       'WhatsApp',
       'Facebook',
       'Instagram',  # <-- Add Instagram as canonical source
       'Website',
       'Google Sheets',
       'Walk-in',
       'Google Call',
       'Manual',
   ]

   def normalize_lead_source(src: str, platform: str = '') -> str:
       if not src and not platform:
           return ''
       p = (platform or '').strip().lower()
       if p in ['ig', 'instagram']:
           return 'Instagram'
       if p in ['fb', 'facebook']:
           return 'Facebook'

       s = str(src).strip()
       sl = s.lower()
       if 'instagram' in sl or 'insta' in sl or sl == 'ig':
           return 'Instagram'
       if 'facebook' in sl or 'fb' in sl:
           return 'Facebook'
       if 'walk' in sl:
           return 'Walk-in'
       if 'whatsapp' in sl:
           return 'WhatsApp'
       if 'sheet' in sl:
           return 'Google Sheets'
       if 'google call' in sl or 'call' in sl:
           return 'Google Call'
       if 'web' in sl or 'google ad' in sl or 'seo' in sl:
           return 'Website'
       if 'manual' in sl:
           return 'Manual'
       return s
   ```

2. **Add Dedicated `platform` Field on `Lead` Model**:
   ```python
   # leads/models.py
   PLATFORM_CHOICES = (
       ('facebook', 'Facebook'),
       ('instagram', 'Instagram'),
       ('whatsapp', 'WhatsApp'),
       ('google', 'Google'),
       ('direct', 'Direct / Walk-in'),
       ('other', 'Other'),
   )
   platform = models.CharField(
       max_length=20,
       choices=PLATFORM_CHOICES,
       default='other',
       blank=True,
       db_index=True,
       help_text="Ad network origin platform (e.g. fb vs ig)"
   )
   ```

3. **Register Channels**:
   - Ensure `channels.Channel` has both:
     - `Facebook Ads` (Color: `#1877F2`, Icon: `facebook`)
     - `Instagram Ads` (Color: `#E1306C`, Icon: `instagram`)

---

### Phase 2: Ingestion & Webhook Pipeline
1. **Google Sheets Sync Engine (`leads/google_sheets.py` or webhook parser)**:
   - Read the incoming row/payload.
   - Check if a `platform` column exists.
   - If `row.get('platform') == 'ig'` or `'instagram'` in `campaign_name` or `ad_name`:
     - Assign `lead.source = 'Instagram'`
     - Assign `lead.channel = Channel.objects.get(name='Instagram Ads')`
     - Assign `lead.platform = 'instagram'`
   - Else if `'fb'` or `'facebook'`:
     - Assign `lead.source = 'Facebook'`
     - Assign `lead.channel = Channel.objects.get(name='Facebook Ads')`
     - Assign `lead.platform = 'facebook'`

---

### Phase 3: UI, Dashboards & Filtering
1. **Filter Dropdowns across All 18 CRM Pages**:
   - The Channel dropdown will show both **Facebook Ads** and **Instagram Ads**.
   - The Source dropdown will show both **Facebook** and **Instagram**.
2. **Dashboard Visual Breakdown**:
   - **Executive KPI Card**: Compare Facebook Inbound vs Instagram Inbound.
   - **Lead Acquisition Donut Chart**: Show breakdown of WhatsApp vs Facebook vs Instagram vs Google vs Walk-in.
   - **Telecaller Allocation**: Allow branch managers to set telecaller allocation rules specifically for Instagram leads (e.g., assign younger demographic / social media specialists).

---

### Phase 4: Historical Data Backfill (Migration)
1. Write a safe, reversible management script: `python manage.py backfill_meta_lead_platforms`.
2. Script logic:
   - Scan leads currently marked `Facebook`.
   - Inspect raw data in Google Sheet connections or lead `notes` / `utm_campaign`.
   - If `adset_name` or `placement` indicates Instagram, update `source = 'Instagram'`.

---

## 4. Summary & Next Steps for Founder

| Step | Action | Impact |
|---|---|---|
| **1** | Approve Plan | Sign-off on the schema and separation rules |
| **2** | Add Channels in CRM Master | Create "Instagram Ads" channel in `Master Setup -> Channels` |
| **3** | Model Migration | Run migration adding `platform` field to `Lead` |
| **4** | Ingestion Sync | Update webhook / Sheet sync to read the `platform` column |
