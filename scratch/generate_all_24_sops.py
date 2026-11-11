import os

SOPS_DIR = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\docs\sops"
os.makedirs(SOPS_DIR, exist_ok=True)

SOPS = [
    {
        "id": "SOP-01",
        "filename": "SOP-01_start_of_day_check_and_duty_status.md",
        "title": "Start of Day Check & Duty Status (`On Duty`)",
        "role": "Telecaller / Counselor",
        "frequency": "Daily (at shift start)",
        "purpose": "Ensure your CRM account, duty availability, and CallSync phone are online before new leads are assigned.",
        "before": "Active CRM login (`TELECALLER` or `COUNSELOR` role) and the CallSync Android app signed in on your work mobile phone.",
        "steps": [
            "Open your browser and go to `/login/`.",
            "Enter your username or official email and password, then click **Sign In**.",
            "Check the top-right header bar and click the status pill until it turns green and reads **On Duty** *(Telecallers and Counselors marked **Out of Office** do not receive automatic leads)*.",
            "If you are a Telecaller, look next to the **On Duty** pill and verify the **CallSync** phone indicator is green *(online with healthy battery)*.",
            "Click **Dashboard** in the left menu and note your **Pending Follow-ups** and **New Unhandled Leads** counts.",
            "Click **Missed Calls** in the left menu to check if any student tried calling the Google Ads number overnight."
        ],
        "images": [
            ("Telecaller Dashboard Highlighting On Duty and CallSync Status Pills", "../assets/ui_telecaller_dashboard.png"),
            ("Counselor Portal Dashboard Overview", "../assets/ui_counselor_dashboard.png")
        ],
        "rules": [
            "Switch to **On Duty** within 5 minutes of starting your shift.",
            "Always switch to **Out of Office** before taking lunch breaks, extended meetings, or leaving for the day so fresh leads do not sit unanswered in your queue.",
            "Keep the CallSync Android app logged in and connected to mobile data or office Wi-Fi."
        ],
        "troubleshoot": [
            "**CallSync pill shows Offline or grey:** Unlock your work phone, open the CallSync app, verify internet connectivity, and wait 60 seconds for the heartbeat update. Contact Admin/IT if it stays offline.",
            "**Leads are not assigning to me:** Confirm your pill says **On Duty** (green) and ask your Branch Head to verify your percentage rule in **Lead Allocation Setup**."
        ],
        "checklist": [
            "Signed in to CRM portal",
            "Header pill set to **On Duty** (green)",
            "CallSync phone indicator active (if Telecaller)",
            "Checked **Missed Calls** and **Pending Follow-ups**"
        ],
        "owner": "Branch Head / Operations Lead"
    },
    {
        "id": "SOP-02",
        "filename": "SOP-02_calling_a_new_lead_and_click_to_dial.md",
        "title": "Calling a New Lead & Click-to-Dial",
        "role": "Telecaller / Counselor",
        "frequency": "Within 15 minutes of every new lead assignment",
        "purpose": "Contact freshly assigned student leads rapidly using CRM Click-to-Dial so every call is logged and recorded cleanly.",
        "before": "CRM status set to **On Duty** and CallSync Android app active on your mobile phone.",
        "steps": [
            "From the left menu, click **My Leads** (`/telecaller/leads/` or `/counselor/leads/`).",
            "Filter by status **New** (or click the **New Leads** KPI card on your Dashboard) to open the newest student enquiry first *(e.g. Priya S, `98xxxxxx10`)*.",
            "Check the **Category** (`Training` vs `Placement`), **Course**, **Branch**, and **Channel/Source** before dialing.",
            "Click the green **Start Call** button (Telecaller) or **Call Lead** button (Counselor) at the top of the Lead Detail screen.",
            "If using Remote Dial, unlock your mobile phone — CallSync automatically opens the phone dialer with the student's number pre-filled.",
            "Speak clearly, confirm whether the enquiry is for Training or Placement, and take brief notes during the call.",
            "Use the on-screen **AI Objection Coaching** quick cards if the student raises questions about fees, timings, or placements."
        ],
        "images": [
            ("Telecaller My Leads Queue", "../assets/ui_telecaller_leads.png"),
            ("Lead Detail Workbench — Call Action and History View", "../assets/ui_lead_detail.png")
        ],
        "rules": [
            "**15-Minute Rule:** First contact attempt on any new Facebook, WhatsApp, or Sheet lead must happen within **15 minutes**.",
            "**24-Hour SLA Limit:** Leads left untouched for **24 hours** trigger SLA escalation alerts to Branch Head and Admin.",
            "Never create duplicate entries for an existing phone number — search first using **Search leads... (Ctrl K)**."
        ],
        "troubleshoot": [
            "**Dialer did not pop up on phone:** Check the **CallSync** pill in the CRM header. If offline, dial directly from your phone using your assigned work SIM so CallSync still matches the audio recording.",
            "**Wrong number or spam:** Do not delete the lead; update status to **Lost** or **Not Interested** with a clear note."
        ],
        "checklist": [
            "Checked student source, course, and `Training`/`Placement` category before calling",
            "Clicked **Start Call** / **Call Lead** within 15 minutes",
            "Completed conversation or noted unanswered attempt"
        ],
        "owner": "Sales Head / Branch Head"
    },
    {
        "id": "SOP-03",
        "filename": "SOP-03_updating_call_outcome_status_and_notes.md",
        "title": "Updating Call Outcome, Lead Status & Follow-up Notes",
        "role": "Telecaller / Counselor",
        "frequency": "Immediately after every call",
        "purpose": "Save accurate call outcomes, status changes, and next follow-up reminders so the CRM reflects live pipeline truth.",
        "before": "Call completed or attempted on a lead inside your assigned queue.",
        "steps": [
            "On the Lead Detail screen, complete the **End Call / Log Call** popup (or click **Edit Notes & Status**).",
            "Choose the **Call Status** (`Completed`, `No Answer`, `Busy`, `Failed`) and **Call Outcome** (`Interested`, `Follow-up Required`, `Callback Requested`, `RNR`, `Not Interested`, `Converted`).",
            "Select the updated **Lead Status** from the 21 system statuses *(e.g. `Contacted`, `Interested`, `Follow-up`, `Demo Scheduled`, `Visit Scheduled`)*.",
            "Enter clear, factual remarks in **Notes** *(e.g. 'Prefers weekend Python batch; requested fee structure on WhatsApp')*.",
            "If the student requested a callback, select the **Next Follow-up Date** and **Follow-up Time**.",
            "Click **Update Status** / **Save** to commit the record and generate the activity log."
        ],
        "images": [
            ("Lead Detail Workbench — Status Update and Call Logging", "../assets/ui_lead_detail.png"),
            ("Scheduled Follow-ups Queue View", "../assets/ui_followups_list.png")
        ],
        "rules": [
            "Every connected call MUST result in an updated **Lead Status** and clear **Notes** before moving to the next lead.",
            "Always set a **Follow-up Date & Time** for leads marked **Follow-up**, **Interested**, **Discussion**, or **Later**.",
            "Leads with no status/activity updates for **7 days** are automatically flagged for SLA reassignment."
        ],
        "troubleshoot": [
            "**Button does not save:** Verify that mandatory fields (Lead Status and Follow-up Date if status is Follow-up) are filled.",
            "**Accidentally chose wrong status:** Re-open the lead, click **Edit Notes & Status**, and correct it immediately; the audit trail records the update."
        ],
        "checklist": [
            "Call Outcome recorded accurately",
            "Lead Status updated (`Contacted`, `Interested`, `Follow-up`, etc.)",
            "Factual remarks saved in Notes",
            "Next Follow-up Date & Time scheduled"
        ],
        "owner": "Sales Head / Branch Head"
    },
    {
        "id": "SOP-04",
        "filename": "SOP-04_handling_rnr_and_missed_call_callbacks.md",
        "title": "Handling RNR (Ring No Response) & Missed-Call Callbacks",
        "role": "Telecaller / Counselor",
        "frequency": "Twice daily (11:30 AM and 4:30 PM) + immediate check for Google Missed Calls",
        "purpose": "Systematically re-attempt unanswered enquiries and clear Google Ads missed-call alerts within SLA.",
        "before": "Signed in to CRM with **On Duty** active.",
        "steps": [
            "Click **Missed Calls** in the left navigation bar (`/calls/missed/`) whenever a red badge count appears.",
            "Call each missed Google Ads caller immediately; once reached, click **Mark Called Back** to clear the pending alert and auto-complete its 15-minute callback follow-up.",
            "For Counselor daily follow-up: open **RNR Follow-up** (`/counselor/rnr-leads/`) or **Unpicked Recalls** from the left menu.",
            "Review leads marked **No Answer**, **Busy**, or **Switched Off**, paying attention to repeat RNR leads (`>= 2` failed call attempts).",
            "Re-dial at a different time slot *(morning vs. late afternoon)* and send one polite **WhatsApp Template** introducing the institute if unreachable by voice.",
            "Update the call log and status after each retry attempt."
        ],
        "images": [
            ("Missed Google Ads Calls Queue and Callback Tracker", "../assets/ui_missed_calls.png"),
            ("Telecaller RNR Analytics & Attempts Breakdown", "../assets/ui_reports_rnr.png")
        ],
        "rules": [
            "**15-Minute Google Missed Call Rule:** Every missed or rejected Google Ads call creates an automatic Follow-up due in **15 minutes**.",
            "**Repeat RNR Metric:** Leads with **>= 2** RNR calls are highlighted in the Telecaller RNR Report.",
            "⚠ TO CONFIRM: Confirm whether leads reaching **3 unanswered calls** should automatically move into a separate Recall List or be marked `Not Interested` / `Lost` after a final WhatsApp message."
        ],
        "troubleshoot": [
            "**Missed call alert won't clear:** Ensure you clicked **Mark Called Back** (or completed an answered outgoing call recorded by CallSync matching the student's number)."
        ],
        "checklist": [
            "Cleared all red-badge **Missed Calls** within 15 minutes",
            "Reviewed **RNR Follow-up** / **Unpicked Recalls** queue",
            "Sent polite WhatsApp template after repeated RNR attempts"
        ],
        "owner": "Branch Head"
    },
    {
        "id": "SOP-05",
        "filename": "SOP-05_sending_brochure_and_fees_on_whatsapp.md",
        "title": "Sending Course Brochure & Fee Details on WhatsApp",
        "role": "Telecaller / Counselor / Sales Head",
        "frequency": "During or immediately after student qualification call",
        "purpose": "Share verified course brochures and fee details through the CRM WhatsApp Cloud API so all chats remain logged.",
        "before": "Student has not opted out (`whatsapp_opt_out` is False) and lead has a valid mobile number.",
        "steps": [
            "Open the student's Lead Detail screen (or click **WhatsApp Chats** in the left menu -> `/whatsapp/`).",
            "Click **Send WhatsApp** (or select the student's conversation thread in the Inbox).",
            "Check the **24-Hour Session Window** indicator at the top of the chat panel.",
            "If the 24-hour window is **Open** *(student messaged within the last 24 hours)*, type your message or attach the official PDF brochure and click **Send**.",
            "If the 24-hour window is **Closed** *(or contacting a new lead for the first time)*, click **Templates**, select an approved template *(e.g., Course Brochure / Fee Details)*, fill in variables *(student name `Priya S`, course name)*, and click **Send Template**.",
            "Confirm the green delivery tick appears in the message history."
        ],
        "images": [
            ("WhatsApp Omnichannel Inbox Highlighting 24-Hour Window & Templates", "../assets/ui_whatsapp_inbox.png"),
            ("Lead Detail View — Activity & Communication History", "../assets/ui_lead_detail.png")
        ],
        "rules": [
            "**Never send from personal WhatsApp:** Always use the CRM WhatsApp integration so management can audit communication and honor opt-outs.",
            "**Meta 24-Hour Rule:** Free-form text/PDF attachments only work if the student replied within the last 24 hours; outside 24 hours, approved **WhatsApp Templates** are mandatory.",
            "Respect **Opt-Out:** Never message a lead flagged `whatsapp_opt_out = True`."
        ],
        "troubleshoot": [
            "**Message input box is locked:** The 24-hour session window has expired. Switch to **Templates** and send an approved Meta template to reopen communication.",
            "**Template failed to send:** Verify the student's phone number includes a valid 10-digit number and contact Admin/IT to confirm WhatsApp Cloud API token health."
        ],
        "checklist": [
            "Verified student has not opted out of WhatsApp",
            "Checked 24-hour window status",
            "Sent approved template or brochure PDF via CRM Inbox",
            "Logged follow-up date to check student feedback"
        ],
        "owner": "Sales Head / Admin"
    },
    {
        "id": "SOP-06",
        "filename": "SOP-06_booking_demo_or_branch_visit.md",
        "title": "Booking a Demo Session or Branch Visit (Institute Visit)",
        "role": "Telecaller / Counselor",
        "frequency": "Whenever an interested student agrees to a trial class or campus visit",
        "purpose": "Schedule demo classes or branch visits in the CRM so Reception and Counselors are ready before the student arrives.",
        "before": "Qualified `Interested` lead with confirmed preferred branch, date, and time.",
        "steps": [
            "Open the student's Lead Detail screen and click **Edit Notes & Status**.",
            "Change **Lead Status** to **Demo Scheduled** (for online/classroom trial session) or **Visit Scheduled** / **Institute Visit** (for branch campus visit).",
            "Set the **Center Visit Date & Time** (`center_visit_date`) and verify the correct **Branch** is selected.",
            "Add a **Follow-up Reminder** scheduled 2 hours prior to the demo/visit for a confirmation call.",
            "Write clear remarks in **Notes** *(e.g. 'Scheduled Data Science demo on 12 Nov at 11:00 AM at Tnagar branch')* and click **Save**.",
            "Send a confirmation message with branch Google Maps location using **WhatsApp Templates**."
        ],
        "images": [
            ("Lead Detail Workbench — Scheduling Visit & Follow-up", "../assets/ui_lead_detail.png"),
            ("Pipeline Kanban Board Showing Scheduled Visit Stage", "../assets/ui_leads_kanban.png")
        ],
        "rules": [
            "Always confirm the **Branch** field matches the campus the student plans to visit so the Receptionist sees the lead during check-in.",
            "Call the student 2 hours before the scheduled slot to minimize **No Show** rates.",
            "After a completed visit without instant payment, update status to **Visited** or **Counseling** and set the next follow-up."
        ],
        "troubleshoot": [
            "**Student arrives at a different branch:** Receptionist searches the student's phone number on the Walk-in Desk; Branch Head/Admin updates the lead's Branch if needed."
        ],
        "checklist": [
            "Updated status to **Demo Scheduled** or **Visit Scheduled**",
            "Set exact **Branch** and **Center Visit Date**",
            "Scheduled reminder follow-up 2 hours before slot",
            "Sent WhatsApp confirmation with branch address"
        ],
        "owner": "Branch Head"
    },
    {
        "id": "SOP-07",
        "filename": "SOP-07_marking_admitted_or_lost_with_reason.md",
        "title": "Submitting Admission / Enrollment & Marking Lost (with Reason)",
        "role": "Counselor / Telecaller",
        "frequency": "Upon winning an admission or closing a dead lead",
        "purpose": "Convert admitted students into verified fee enrollments for Accounts, or close non-converting leads with accurate lost reasons.",
        "before": "Confirmed fee breakdown/approved offer (for admission) OR verified disqualification/refusal (for lost).",
        "steps": [
            "**For Admission (Won):** Open the Lead Detail screen and click **Enroll Student** (`/leads/<id>/enroll/`).",
            "Select the **Course/Program**, confirm any **Approved Offer**, verify **Total Fee** (including GST if applicable), and configure the **Installment Schedule** (due dates and amounts).",
            "Enter the first payment amount, payment mode (`UPI`, `Bank Transfer`, `Card`, `Cash`), **UTR / Transaction Reference**, and upload the payment screenshot, then click **Submit Enrollment**.",
            "Confirm the lead updates to **Enrolled** / **Converted** and enters the Accountant's **Payment Verification** queue.",
            "**For Lost / Not Interested (Closed-Lost):** Open Lead Detail, set **Lead Status** to **Lost**, **Not Interested**, or **Not Joined**.",
            "In **Notes**, record the exact reason *(e.g. 'Joined competitor institute', 'Fee budget mismatch', 'Moved out of city')* and click **Update Status**."
        ],
        "images": [
            ("Student Enrollment & Fee Installment Form", "../assets/ui_lead_enroll.png"),
            ("Lead Detail — Enrolled Badge & Action Controls", "../assets/ui_lead_detail.png")
        ],
        "rules": [
            "**Never fabricate UTR numbers:** Enter the exact UPI/bank UTR from the student's payment receipt; duplicate UTRs are blocked automatically by the Accounts shield.",
            "**Do not delete Lost leads:** Always keep them as **Lost** or **Not Interested** with reasons so marketing channel ROI reports remain accurate."
        ],
        "troubleshoot": [
            "**UTR Duplicate Alert shown:** Check with the student if they uploaded an old screenshot, or contact the Accountant on `/accountant/verification/`.",
            "**Payment Rejected by Accountant:** Open the Enrollment record, correct the reference/screenshot, and click **Resubmit Payment**."
        ],
        "checklist": [
            "Verified Course, Total Fee, and GST calculation",
            "Uploaded clear payment proof and exact UTR (for Admissions)",
            "Documented specific Lost reason in Notes (for Lost leads)"
        ],
        "owner": "Branch Head / Accountant"
    },
    {
        "id": "SOP-08",
        "filename": "SOP-08_listening_to_own_call_recordings.md",
        "title": "Listening to Own Call Recordings & Coaching Review",
        "role": "Telecaller / Counselor",
        "frequency": "Daily self-review / as needed before follow-up calls",
        "purpose": "Replay synced call recordings attached to a student record to recall commitments and improve pitch quality.",
        "before": "Logged into CRM; CallSync Android app or Google Drive sync has linked audio to the lead.",
        "steps": [
            "Open the student's Lead Detail screen (or click **Call Recordings** if accessible).",
            "Scroll down to the **Call Recordings** card (`lead_recordings_card`) on the Lead Detail page.",
            "Locate the recording matching the date, time, and duration of your conversation.",
            "Click the **Play (▶)** button inside the built-in HTML audio player to listen directly in the browser.",
            "Review any fee discounts, batch dates, or objections mentioned by the student before placing your next call."
        ],
        "images": [
            ("Call Recordings Archive & Embedded Audio Player", "../assets/ui_call_recordings.png"),
            ("Lead Detail Screen Linking Audio Recordings to Calls", "../assets/ui_lead_detail.png")
        ],
        "rules": [
            "Audio files are stored in secure `private_media/` storage and must NEVER be downloaded or shared on external personal apps.",
            "Only business calls matching a CRM lead are linked; personal phone calls remain `UNMATCHED` and never create CRM leads."
        ],
        "troubleshoot": [
            "**Recording missing for a call made 5 minutes ago:** CallSync uploads audio when the phone finishes compressing the call and has internet; wait 2–3 minutes and refresh.",
            "**Recording older than 48 hours not uploaded:** Default auto-sync window is 48 hours; ask Admin/IT if historical audio upload override is needed."
        ],
        "checklist": [
            "Opened Lead Detail **Call Recordings** section",
            "Played prior conversation audio cleanly in browser",
            "Used past context for accurate follow-up"
        ],
        "owner": "Branch Head"
    },
    {
        "id": "SOP-09",
        "filename": "SOP-09_registering_a_branch_walk_in.md",
        "title": "Registering a Branch Walk-in Enquiry",
        "role": "Receptionist",
        "frequency": "Immediately when any prospective student visits the branch",
        "purpose": "Check in every campus visitor digitally with de-duplication and a sequential queue token.",
        "before": "Logged into the Receptionist portal (`/receptionist/dashboard/`) at the front desk.",
        "steps": [
            "Greet the visitor and ask for their 10-digit mobile number.",
            "Click **+ Register Walk-in Student** on the **Walk-in Desk** (`/receptionist/dashboard/`) — OR ask the student to scan the printed branch **QR Code Standee** (`/enquiry/`).",
            "Enter the student's phone number first so the CRM checks for an existing enquiry or earlier telecaller record (`check-existing`).",
            "Complete the student's **Full Name**, **Email**, **Course/Program**, **Category** (`Training` or `Placement`), and **Branch**.",
            "Submit the form. Note the auto-generated **Token Number** *(e.g. `TK-014`)* and verify visitor status becomes **Waiting**.",
            "Hand over or verbally share the Token Number to the student and ask them to take a seat in the waiting lounge."
        ],
        "images": [
            ("Receptionist Walk-in Desk with + Register Walk-in Student Button", "../assets/ui_receptionist_desk.png"),
            ("Public Student Walk-in QR Self-Registration Form", "../assets/ui_walkin_form_public.png")
        ],
        "rules": [
            "Never create a second lead if the student already exists from Facebook, Google, or a Telecaller call — checking phone first links the walk-in visit cleanly to the original record!",
            "Every physical visitor must be logged with a Token Number within 2 minutes of arrival."
        ],
        "troubleshoot": [
            "**QR Standee link doesn't load on student's phone:** Register the student directly from your desk PC using **+ Register Walk-in Student**.",
            "**Missing QR Poster at desk:** Click **Walk-in QR Standee** or `/receptionist/qr-standee/` and print a fresh branch QR poster."
        ],
        "checklist": [
            "Checked phone number for existing CRM record",
            "Captured Name, Course, and Training/Placement category",
            "Issued Token Number (`Waiting` status active)"
        ],
        "owner": "Branch Head / Admin"
    },
    {
        "id": "SOP-10",
        "filename": "SOP-10_assigning_walk_in_to_counselor.md",
        "title": "Assigning a Walk-in Visitor to Branch Counselor / Branch Head",
        "role": "Receptionist",
        "frequency": "Immediately after issuing a walk-in token",
        "purpose": "Route waiting campus visitors smoothly to an available On-Duty Counselor without double-booking.",
        "before": "Walk-in visitor registered with status **Waiting** on `/receptionist/dashboard/`.",
        "steps": [
            "Locate the newly checked-in student row on the **Walk-in Desk** table.",
            "Click **Assign Counselor** in the **Actions** column (or check multiple boxes and click **Bulk Assign** if assigning a group).",
            "In the **Assign to Branch Counselor** modal, open the **Select Branch Counselor** dropdown.",
            "Look at the live status indicator next to each name and pick an available **`🟢 [On Duty]`** counselor *(avoid `🔴 [Out of Office]` unless instructed)*.",
            "Type brief desk context in **Handoff Reason / Desk Notes** *(e.g. 'Walk-in for Java Full Stack fee discussion')*.",
            "Click **Confirm & Assign**, review the confirmation box, and click **Yes, Assign Now**."
        ],
        "images": [
            ("Receptionist Walk-in Desk — Counselor Assignment & Queue Actions", "../assets/ui_receptionist_desk.png"),
            ("Branch Walk-in Visitor End-to-End Flowchart", "../assets/diag_walkin_flow.png")
        ],
        "rules": [
            "Target waiting time before counselor handoff: **under 10 minutes**.",
            "If the lead was already handled earlier by a Telecaller, **never wipe the history** — clicking **View History** lets you brief the Counselor on past discussions.",
            "⚠ TO CONFIRM: Currently the Receptionist modal lists **Branch Counselors** in the dropdown (`counselors`). Confirm whether **Branch Heads** should also appear as selectable assignees on this screen."
        ],
        "troubleshoot": [
            "**No active counselors shown in dropdown:** All counselors in the branch may be toggled `Out of Office` or unassigned to the branch. Alert the Branch Head immediately to step in or toggle a counselor On Duty."
        ],
        "checklist": [
            "Selected an **On Duty** (`🟢`) Branch Counselor",
            "Added brief handoff notes for the counselor",
            "Completed two-step confirmation (**Yes, Assign Now**)",
            "Directed student to counselor cabin"
        ],
        "owner": "Branch Head"
    },
    {
        "id": "SOP-11",
        "filename": "SOP-11_managing_reception_visitor_log.md",
        "title": "Managing the Reception Visitor Queue & Live Log",
        "role": "Receptionist",
        "frequency": "Continuously during branch hours + end-of-day reconciliation",
        "purpose": "Keep the live visitor log accurate across Waiting, In Consultation, Completed, Cancelled, and No Show states.",
        "before": "Active Receptionist login on `/receptionist/dashboard/`.",
        "steps": [
            "Keep `/receptionist/dashboard/` open on the reception monitor and review the top KPI tiles (**Total Walk-ins**, **Waiting**, **Assigned**, **Completed**).",
            "For visitors who booked an appointment earlier (`Visit Scheduled`) and arrived today, search by name/phone and verify check-in.",
            "Click **History** on any student row to review past touchpoints, course interest, and assigned telecaller/counselor.",
            "Use the **From Date / To Date** filters to review yesterday's or weekly walk-in footfall.",
            "At closing time (6:30 PM / shift end), ensure zero active walk-ins remain stuck in **Waiting** — escalate any unserved visitor to the Branch Head or mark confirmed departures as **No Show** / **Cancelled**."
        ],
        "images": [
            ("Receptionist Walk-in Desk KPIs and Live Visitor Table", "../assets/ui_receptionist_desk.png"),
            ("Printable Branch QR Standee Poster View", "../assets/ui_walkin_qr_standee.png")
        ],
        "rules": [
            "End-of-day rule: Every physical walk-in registered during the day must end in `In Consultation`, `Completed`, `Cancelled`, or `No Show` before desk logout.",
            "Keep the physical QR Standee Poster clean and visible at the reception counter."
        ],
        "troubleshoot": [
            "**Duplicate walk-in created by mistake:** Flag both IDs to Admin/Branch Head so they can merge via `/admin/duplicate-leads/` without losing conversation notes."
        ],
        "checklist": [
            "All arriving visitors logged and assigned",
            "Appointment arrivals matched against existing records",
            "Zero unresolved `Waiting` tokens left at end of day"
        ],
        "owner": "Branch Head"
    },
    {
        "id": "SOP-12",
        "filename": "SOP-12_daily_lead_allocation_and_duty_check.md",
        "title": "Daily Lead Allocation & Unattended Queue Check",
        "role": "Branch Head / Sales Head / Branch Admin",
        "frequency": "Twice daily (10:15 AM and 3:00 PM)",
        "purpose": "Verify incoming branch leads are routing fairly to On-Duty staff and clear any unassigned queues.",
        "before": "Branch Head, Branch Admin, or Sales Head login access.",
        "steps": [
            "Open your Dashboard (`/manager/branch-head/dashboard/` or `/manager/dashboard/`).",
            "Click **Branch Telecallers** (`/branch-head/telecallers/`) and confirm which staff members are currently **On Duty** vs **Out of Office**.",
            "Open **Lead Allocation Setup** (`/admin/settings/lead-setup/`) in the left menu.",
            "Select your **Branch** (and optional **Channel**) and verify that active On-Duty telecaller percentages add up to **exact 100%**.",
            "Click **Leads** (`/branch-head/leads/`) and filter by **Unassigned** / **Untouched Queue** to identify any leads stuck pending assignment (for example, if everyone was Out of Office when a midnight Facebook lead arrived).",
            "Select unassigned leads and use **Bulk Assign** to distribute them immediately to available On-Duty telecallers."
        ],
        "images": [
            ("Branch Head Operations Dashboard", "../assets/ui_branch_head_dashboard.png"),
            ("Lead Allocation Setup & Percentage Split Rules", "../assets/ui_lead_allocation_setup.png")
        ],
        "rules": [
            "Total active allocation split per branch/channel MUST equal **exact 100%** — the system rejects any save totaling under or over 100%.",
            "If an employee goes on planned leave, temporarily set their allocation percentage to **0%** and redistribute to present staff (or remind them to toggle **Out of Office**)."
        ],
        "troubleshoot": [
            "**Save error: 'Total percentage allocation must equal 100%':** Adjust one or more telecallers' percentages so all active rows sum to 100.",
            "**Leads arriving from a new channel unassigned:** Add a branch-level fallback rule (`All Channels`) summing to 100%."
        ],
        "checklist": [
            "Verified team On-Duty status matches physical attendance",
            "Confirmed **Lead Allocation Setup** ratios equal 100%",
            "Cleared any **Unassigned** or **Untouched** queue backlogs"
        ],
        "owner": "Sales Head"
    },
    {
        "id": "SOP-13",
        "filename": "SOP-13_reviewing_missed_followups_and_sla_escalations.md",
        "title": "Reviewing Missed Follow-ups & SLA Escalated Leads",
        "role": "Branch Head / Sales Head",
        "frequency": "Daily (12:00 PM and 5:30 PM)",
        "purpose": "Spot overdue follow-ups and 24-hour/7-day SLA breaches early so warm leads are never abandoned.",
        "before": "Logged into Branch Head, Sales Head, or Admin dashboard.",
        "steps": [
            "On your Dashboard, click the **Overdue Follow-ups** KPI tile (red badge) to jump straight to missed scheduled callbacks.",
            "Review why the scheduled time passed without completion and reassign leads belonging to absent staff to an On-Duty counselor/telecaller.",
            "Open **Missed Calls** (`/calls/missed/`) to check for any Google Ads callbacks open longer than 15 minutes.",
            "Review **New Unhandled Leads** older than 24 hours; if SLA escalation has not yet run via cron, Admins can click **Enforce SLAs Now** on `/admin/dashboard/` to execute `run_lead_sla_escalation`.",
            "Notify team members via branch huddle or WhatsApp update to clear all overdue items before shift end."
        ],
        "images": [
            ("Admin & Management Dashboard Highlighting Enforce SLAs Now & Overdue KPIs", "../assets/ui_admin_dashboard.png"),
            ("Follow-ups Queue Filtered for Overdue Callbacks", "../assets/ui_followups_list.png")
        ],
        "rules": [
            "**Fresh Lead SLA:** Maximum **24 hours** before a `New` lead is escalated.",
            "**In-Progress SLA:** Leads untouched for **7 days** are automatically flagged/reassigned to keep pipelines moving.",
            "**Google Missed Call SLA:** Maximum **15 minutes** to return missed inbound ad calls."
        ],
        "troubleshoot": [
            "**Staff insists they called the student:** Ask them to check `My Calls` on the Lead Detail screen — if they forgot to click **Update Status** or dialed from a personal phone without CallSync, the CRM still counts it as untouched."
        ],
        "checklist": [
            "Zero missed Google Ads calls open >15 minutes",
            "Reviewed and cleared **Overdue Follow-ups** KPI",
            "Reassigned leads of absent/on-leave staff"
        ],
        "owner": "Sales Head"
    },
    {
        "id": "SOP-14",
        "filename": "SOP-14_weekly_counsellor_review_using_recordings.md",
        "title": "Weekly Team Call Recording & RNR Quality Review",
        "role": "Branch Head / Sales Head",
        "frequency": "Weekly (every Saturday morning or Friday afternoon)",
        "purpose": "Audit actual call recordings and telecaller RNR ratios to coach counselors on pitch quality and objection handling.",
        "before": "Branch Head, Sales Head, or Admin access to `/reports/telecaller-rnr/` and `/call-recordings/`.",
        "steps": [
            "Open **Telecaller RNR Report** (`/reports/telecaller-rnr/`), filter by your branch and the past 7 days.",
            "Compare each staff member's **Connection Rate %**, **RNR Rate %**, **Repeat RNR Leads (`>=2` calls)**, and **Average Attempts per Lead**.",
            "Click any telecaller's RNR metric or open **Call Recordings** (`/call-recordings/`) filtered by user and date range.",
            "Listen to 3–5 sample recordings per counselor/telecaller: 2 short/rejected calls, 2 demo bookings, and 1 lost lead call.",
            "Evaluate greeting clarity, Training vs Placement discovery, objection rebuttal (using AI Coaching best practices), and follow-up closing.",
            "Conduct a 15-minute 1-on-1 coaching session with each staff member sharing exact improvement actions."
        ],
        "images": [
            ("Telecaller RNR Analytics Report — Attempts & Connection Rates", "../assets/ui_reports_rnr.png"),
            ("Call Recordings Archive & Quality Playback Screen", "../assets/ui_call_recordings.png")
        ],
        "rules": [
            "Audit at least **5 recordings per active telecaller/counselor** every week.",
            "Flag suspiciously short connected calls (<15 seconds) marked `Interested` or excessive RNR rates (>65%) for live call shadowing."
        ],
        "troubleshoot": [
            "**Telecaller has zero recordings in archive:** Check `/call-recordings/` or ask Admin to inspect `CallDevice` sync status — the employee may be dialing from a personal number instead of their CallSync work phone."
        ],
        "checklist": [
            "Exported/reviewed weekly **Telecaller RNR Report**",
            "Listened to 3–5 call recordings per team member",
            "Documented coaching feedback for each counselor/telecaller"
        ],
        "owner": "Sales Head"
    },
    {
        "id": "SOP-15",
        "filename": "SOP-15_monthly_branch_performance_report.md",
        "title": "Monthly Branch Performance & Source Conversion Report",
        "role": "Branch Head / Sales Head / Admin",
        "frequency": "Monthly (between the 1st and 3rd of each month)",
        "purpose": "Analyze branch lead volume by marketing source, conversion rates, and revenue realization for leadership review.",
        "before": "Authorized access to `/admin/reports/` or `/manager/reports/`.",
        "steps": [
            "Open **Reports & Analytics** (`/admin/reports/` or `/manager/reports/`).",
            "Set the date range picker to the **previous calendar month** *(e.g., 1st to 31st)* and select your target branch (or **All Branches**).",
            "Review the **Branch-Wise Lead Summary Table** comparing all 9 channels (`Meta WhatsApp`, `Meta Lead Form`, `Website`, `Instagram`, `Google Calls`, `Influencer`, etc.) against **Converted/Enrolled** counts.",
            "Inspect the **Call Outcomes & Lead Quality** bar chart and **Google Sheet Live Sync** tally.",
            "Cross-check **Enrolled Students** revenue metrics against verified receipts in `/accountant/dashboard/`.",
            "Export or screenshot key charts and summarize top-performing channels and underperforming sources for marketing budget review."
        ],
        "images": [
            ("Reports & Analytics — Branch & Channel Conversion Summary", "../assets/ui_admin_reports.png"),
            ("Pipeline Overview & Revenue KPIs", "../assets/ui_admin_dashboard.png")
        ],
        "rules": [
            "Ensure all month-end pending enrollments are submitted by Counselors and verified by Accounts **before generating final monthly numbers**.",
            "Reconcile Google Sheet counts (`Sync Sheets`) before finalizing channel attribution."
        ],
        "troubleshoot": [
            "**Channel numbers look lower than Meta Ads Manager:** Check `/facebook-leads/` for leads in the **Not added to CRM** error KPI card, or verify page cutoff dates on `/facebook-leads/accounts/`."
        ],
        "checklist": [
            "Filtered report for exact previous calendar month",
            "Verified Google Sheets and Facebook lead counts synced",
            "Cross-checked conversion count against Finance verified enrollments",
            "Shared monthly summary with Management"
        ],
        "owner": "Founder / Sales Head"
    },
    {
        "id": "SOP-16",
        "filename": "SOP-16_recording_and_verifying_fee_payments.md",
        "title": "Recording & Verifying Student Fee Payments (UTR Shield)",
        "role": "Accountant / Finance Head",
        "frequency": "Continuously during working hours / Daily bank reconciliation",
        "purpose": "Verify student fee payment proofs against bank statements using the UTR Shield before issuing official PDF tax receipts.",
        "before": "Accountant or Finance Head login access to `/accountant/verification/`.",
        "steps": [
            "Open **Payment Verification** in the left menu (`/accountant/verification/`).",
            "Filter by date range or pending status to view newly submitted payment transactions from Counselors.",
            "Click on the attached **Payment Screenshot / Proof** thumbnail to open the verification lightbox and inspect the **Amount**, **Date**, and **UTR / Reference Number**.",
            "Cross-verify the exact UTR number and amount directly in the institute's official bank statement / merchant settlement portal.",
            "Ensure the **UTR Duplicate Shield** shows zero duplicate claims *(a red warning badge flags if that UTR was already used on another student)*.",
            "If genuine and credited in bank, click **Approve** — CRM immediately generates the **Tax Receipt PDF** (`/enrollments/receipt/<id>/pdf/`) and emails the student.",
            "If the credit is missing, blurry, or mismatched, click **Reject**, enter a clear rejection reason, so the Counselor can resubmit."
        ],
        "images": [
            ("Accountant Payment Verification Queue with Lightbox & UTR Duplicate Shield", "../assets/ui_accountant_verification.png"),
            ("Finance Head Overview & Pending Approvals Dashboard", "../assets/ui_finance_dashboard.png")
        ],
        "rules": [
            "**Never approve without bank confirmation:** Always match the exact UTR against live bank credit.",
            "**Zero UTR Reuse:** Never override a Duplicate UTR warning unless proven to be a split bank adjustment verified by Finance Head.",
            "Official receipts contain statutory institute details (GSTIN, PAN, Authorized Signature) and are logged in **Student Email Logs**."
        ],
        "troubleshoot": [
            "**Student didn't receive receipt email:** Open **Student Email Logs** (`/admin/email-logs/`) or click **View Receipt PDF** on the enrollment to download and share manually via WhatsApp/email.",
            "**Proof image too blurry to read:** Click **Reject** with note `'Upload clear screenshot showing full 12-digit UTR number'`."
        ],
        "checklist": [
            "Inspected proof image and matched exact UTR in bank statement",
            "Confirmed zero duplicate UTR flags",
            "Clicked **Approve** (verified receipt email & PDF generated) or **Reject** with reason"
        ],
        "owner": "Finance Head"
    },
    {
        "id": "SOP-17",
        "filename": "SOP-17_sending_and_tracking_installment_reminders.md",
        "title": "Sending & Tracking Installment Due Reminders",
        "role": "Accountant / Finance Head / Admin",
        "frequency": "Daily automated run + Weekly manual overdue audit",
        "purpose": "Ensure upcoming and overdue student fee installments are reminded on time and collected without revenue leakage.",
        "before": "Accountant, Finance Head, or Admin access to `/accountant/dashboard/` and `/finance/pending/`.",
        "steps": [
            "Open **Financial Dashboard** (`/accountant/dashboard/`) or **Pending Payments** (`/finance/pending/`).",
            "Check the **Overdue Installments** and **Outstanding Balance** KPI tiles.",
            "Verify that the scheduled automated command `send_installment_reminders` ran cleanly (check **Student Email Logs** at `/admin/email-logs/`).",
            "If a manual batch reminder is needed for upcoming due dates, click **Trigger Installment Reminders** (`/enrollments/reminders/trigger/`).",
            "For installments overdue more than 7 days, notify the assigned Counselor and Branch Head via the student record so they place a courtesy reminder call.",
            "When the student pays, follow **SOP-16** to verify UTR and update the installment status to **Paid**."
        ],
        "images": [
            ("Finance Dashboard Showing Receivables & Overdue Installments", "../assets/ui_finance_dashboard.png"),
            ("Admin Dashboard Collections & Installment Overview", "../assets/ui_admin_dashboard.png")
        ],
        "rules": [
            "Installment due dates must match the signed enrollment schedule; only authorized roles may reschedule an installment via `/enrollments/installments/<id>/update/`.",
            "Every automated reminder email is permanently logged in `PaymentEmailLog`."
        ],
        "troubleshoot": [
            "**Student claims they did not get email reminder:** Check the student's email spelling on their Lead profile and inspect bounce/delivery status in **Student Email Logs**."
        ],
        "checklist": [
            "Reviewed **Overdue Installments** KPI",
            "Verified **Student Email Logs** show successful reminder dispatch",
            "Escalated >7-day overdue accounts to Branch Head / Counselor"
        ],
        "owner": "Finance Head"
    },
    {
        "id": "SOP-18",
        "filename": "SOP-18_handling_fee_refund_requests.md",
        "title": "Handling Fee Refund Requests & Voided Receipts",
        "role": "Accountant / Finance Head / Admin",
        "frequency": "As requested (rare exception)",
        "purpose": "Document the controlled exception handling for fee refund requests while highlighting the current code-vs-policy gap.",
        "before": "Written student request approved by Branch Head and Finance Head.",
        "steps": [
            "Review the official receipt terms printed in `leads/constants.py` *(which currently state: 'Fees once paid for the training program are non-refundable and non-transferable under any circumstances')*.",
            "If Management grants a rare written exception, verify original verified payment records in **Student Enrollments** and `/accountant/verification/`.",
            "Check `PaymentTransaction` status in Django Admin *(only **Superadmin / Finance Head** should inspect `/django-admin/` if adjusting a verified record)*.",
            "⚠ TO CONFIRM: Because there is currently **no automated Refund button or workflow** in the Accountant web UI (even though `PaymentTransaction.Status.REFUNDED` exists in the database model), obtain explicit Finance Head approval before updating any transaction status via Django Admin or recording a negative expense entry in **Expenses** (`/finance/expenses/`).",
            "Archive the written approval note in the student's Lead **Notes** and update Lead Status to **Not Joined** or **Lost**."
        ],
        "images": [
            ("Accountant Payment Verification Queue", "../assets/ui_accountant_verification.png"),
            ("Finance Head Dashboard & Approvals Ledger", "../assets/ui_finance_dashboard.png")
        ],
        "rules": [
            "**⚠ TO CONFIRM (Policy vs Code Gap):** Clarify with Founder/Finance whether refunds are strictly prohibited per receipt T&Cs (`leads/constants.py`) OR whether a dedicated Accountant **Process Refund** UI workflow should be built for `Status.REFUNDED`.",
            "Accountants must NEVER delete verified payment rows; any adjustment must preserve audit history."
        ],
        "troubleshoot": [
            "**Need to void a wrongly approved receipt:** Escalate immediately to **Admin / Superadmin** and **Finance Head** with the transaction ID and bank reference."
        ],
        "checklist": [
            "Checked written approval from Management & Finance Head",
            "Preserved full audit notes on student enrollment",
            "Confirmed database & financial ledger reconciliation"
        ],
        "owner": "Finance Head / Founder"
    },
    {
        "id": "SOP-19",
        "filename": "SOP-19_adding_removing_users_and_setting_roles.md",
        "title": "Adding/Deactivating Users, Assigning Roles & Resetting Passwords",
        "role": "Admin / Superadmin (and Branch Head / Sales Head for scoped team creation)",
        "frequency": "Whenever staff join, change branches/roles, or leave the institute",
        "purpose": "Provision new CRM accounts securely with strict least-privilege roles and deactivate departing staff immediately.",
        "before": "Admin / Superadmin login access and staff member's official email, branch, and reporting manager.",
        "steps": [
            "Open the **Team & Staff** menu in the left sidebar and click the exact role group (**Sales Heads**, **Branch Heads**, **Branch Admins**, **Counselors**, **Telecallers**, **Receptionists**, or **Accountants**).",
            "Click **+ Create / Add User** (`create_user`), enter Full Name, Username, Official Email, Phone, **Role**, **Branch**, and reporting **Counselor** (for Telecallers).",
            "Save the user — CRM generates a single-use 24-hour password setup invitation link (`invitation_status`, `PASSWORD_RESET_TIMEOUT = 86400`).",
            "If the link expires before first login, click **Resend Invitation** on the user's detail card (or use **Set Password** if an immediate reset is requested).",
            "**When a staff member leaves:** Never delete their historical user record *(which would orphan lead/call history)* — instead click **Toggle / Deactivate (`is_active = False`)**, set `is_on_duty = False`, and reassign their active leads via **Bulk Assign**."
        ],
        "images": [
            ("Admin Telecallers Management Listing", "../assets/ui_admin_telecallers.png"),
            ("User Profile & Password Management Screen", "../assets/ui_user_profile.png")
        ],
        "rules": [
            "**Deactivate, Never Delete:** Always set `is_active = False` for departed staff within **1 hour** of exit so session cookies and CallSync DRF tokens stop working immediately.",
            "**Minimum Privilege:** Assign only the exact role needed (`Telecaller` vs `Counselor` vs `Receptionist`).",
            "Note: No **Trainer** role exists in `UserRole` (`⚠ TO CONFIRM`)."
        ],
        "troubleshoot": [
            "**New user didn't receive invitation email:** Check SMTP settings via `python manage.py test_smtp_email`, inspect spam folder, or click **Resend Invitation**.",
            "**Blocked at login with `must_change_password`:** Guide the user to set a fresh strong password on the prompt screen."
        ],
        "checklist": [
            "Created user in exact role & branch",
            "Sent single-use 24-hour invitation link",
            "Deactivated departing staff (`is_active = False`) and reassigned open leads"
        ],
        "owner": "Admin / IT Lead"
    },
    {
        "id": "SOP-20",
        "filename": "SOP-20_connecting_facebook_page_and_sync_cutoff.md",
        "title": "Connecting a Facebook Page & Setting Lead Sync Cutoff Dates",
        "role": "Admin / Superadmin / IT",
        "frequency": "When onboarding a new Meta Business Page or resetting historical boundaries",
        "purpose": "Connect Meta Lead Ad forms safely, map pages to CRM branches, and enforce 48-hour auto-sync + cutoff shields.",
        "before": "Meta App ID/Secret (`FB_APP_SECRET`, `FB_VERIFY_TOKEN`) configured in `.env`, plus Admin access to `/facebook-leads/accounts/`.",
        "steps": [
            "Navigate to **Master Setup → Facebook Connections** (`/facebook-leads/accounts/`).",
            "[SCREENSHOT: Meta Business Suite — App Dashboard Leadgen Webhook Subscription & Page Access Token]",
            "Click **Connect Facebook Account**, enter/authorize the Meta User or System User Access Token, and save.",
            "Under connected **Facebook Pages**, select the default **CRM Branch** for each page so leads route directly to that branch's percentage allocation.",
            "Toggle **Auto-Sync** ON (recommended interval: **3 Minutes**) and toggle **Webhook Subscribed** ON.",
            "Set **Sync Cutoff Date** (`sync_cutoff_date`, e.g. today's date) — any Facebook submission older than this date will **never** be re-imported even if you purge old leads later.",
            "Verify recent submissions appear under **Calls & WhatsApp → Facebook Leads** (`/facebook-leads/`), and test the **From Date / To Date** filters and **Sync Leads** modal."
        ],
        "images": [
            ("Facebook Connections & Page Cutoff Date Configuration", "../assets/ui_fb_accounts.png"),
            ("Facebook Leads Listing with Date Filters & Sync Leads Modal", "../assets/ui_fb_leads.png")
        ],
        "rules": [
            "**48-Hour Auto-Sync Protection:** Background auto-sync checks only the last **48 hours** (`auto_since = now - 48h`) and obeys `sync_cutoff_date`, preventing 1-year-old deleted leads from reappearing.",
            "**Manual Recovery:** If a token expired for a week, click **Sync Leads → Custom Date Range** (or **All Time**) on `/facebook-leads/` to recover missed dates manually."
        ],
        "troubleshoot": [
            "**Facebook Leads showing 'Not added to CRM' error:** Click the red **Not added to CRM** KPI tile to read `crm_error` (usually missing phone number or invalid branch).",
            "**Webhook stopped receiving live leads:** Re-verify `FB_VERIFY_TOKEN` and `FB_APP_SECRET` in `.env` and confirm **Webhook Subscribed** is active."
        ],
        "checklist": [
            "Page mapped to correct CRM **Branch**",
            "**Auto-Sync** (3 min) and **Webhook** enabled",
            "**Sync Cutoff Date** configured",
            "Test lead synced cleanly into `/facebook-leads/`"
        ],
        "owner": "Admin / IT Lead"
    },
    {
        "id": "SOP-21",
        "filename": "SOP-21_connecting_whatsapp_business_number.md",
        "title": "Connecting a WhatsApp Business Number & Templates",
        "role": "Admin / Superadmin / IT",
        "frequency": "When onboarding a WhatsApp Business API sender or syncing approved templates",
        "purpose": "Link Meta WhatsApp Cloud API phone numbers and templates to the CRM Inbox and Campaign engine.",
        "before": "Meta Business Manager WABA credentials (`WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_BUSINESS_ACCOUNT_ID`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`).",
        "steps": [
            "Ensure the 5 WhatsApp environment variables above are set in `.env` (or configure additional senders inside `/whatsapp/campaigns/` -> `WhatsAppSender`).",
            "[SCREENSHOT: Meta WhatsApp Manager — Phone Number ID, WABA ID & Webhook Callback Setup]",
            "In Meta App Dashboard, set the Webhook Callback URL to `https://itechpandacrm.in/webhook/whatsapp/` with verify token matching `WHATSAPP_VERIFY_TOKEN` and subscribe to `messages`.",
            "Open **WhatsApp Campaigns** (`/whatsapp/campaigns/`) or **WhatsApp Chats** (`/whatsapp/`).",
            "Create or sync your Meta-approved **WhatsApp Templates** (Brochures, Fee Reminders, Welcome Messages) so staff can message leads outside the 24-hour window.",
            "Send a test inbound message from a test phone to verify real-time arrival in `/whatsapp/` via Daphne WebSockets."
        ],
        "images": [
            ("WhatsApp Omnichannel Inbox & Real-Time Thread View", "../assets/ui_whatsapp_inbox.png"),
            ("WhatsApp Campaigns & Template Sender Management", "../assets/ui_whatsapp_campaigns.png")
        ],
        "rules": [
            "**Strict Security:** Every inbound webhook from Meta is verified via `X-Hub-Signature-256` HMAC using `WHATSAPP_APP_SECRET`.",
            "**Production Scaling:** Run Daphne (`config.asgi:application`) so WebSocket live chat updates arrive without manual refresh."
        ],
        "troubleshoot": [
            "**Inbound messages don't appear in Inbox:** Check `/webhook/whatsapp/` logs for HMAC signature mismatch or verify Daphne is running.",
            "**Campaign stays Pending:** Ensure `python manage.py run_campaign_worker` is active."
        ],
        "checklist": [
            "Env vars (`WHATSAPP_*`) verified (never committed to Git)",
            "Webhook verified and subscribed to `messages`",
            "Approved Templates synced",
            "Real-time test message received in `/whatsapp/`"
        ],
        "owner": "Admin / IT Lead"
    },
    {
        "id": "SOP-22",
        "filename": "SOP-22_installing_and_pairing_callsync_android_app.md",
        "title": "Installing & Pairing the Call Sync Android App",
        "role": "Admin / IT (with Telecaller)",
        "frequency": "When setting up a new work phone or onboarding a telecaller",
        "purpose": "Install and link the companion Android app (`CRMCallSync`) so Google Ads calls, click-to-dial, and audio recordings sync within the 48-hour shield.",
        "before": "Android smartphone with institute SIM card, CallSync APK installed, and active CRM `TELECALLER` / `COUNSELOR` login.",
        "steps": [
            "Install the `CRMCallSync` Android APK on the staff member's work mobile phone.",
            "[SCREENSHOT: CallSync Android App — Server URL, CRM Login & SIM Selection Screen]",
            "Open **CallSync** on the phone, enter the CRM server URL (`https://itechpandacrm.in`), and sign in using the employee's CRM username and password (`/api/auth/token/`).",
            "Grant all requested Android permissions: **Phone / Call Logs**, **Contacts**, **Microphone / Storage (Call Recordings)**, and disable Battery Optimization so background sync stays alive.",
            "Inside the CallSync app settings, select the **Google Ads SIM slot** (or `All SIMs`) and select the phone's system Call Recording folder.",
            "Open the CRM in a desktop browser logged in as that Telecaller and verify the header **CallSync** pill turns green (showing live battery % and online status).",
            "Place one 10-second test call and verify the call log appears in `My Calls` and the recording appears under `/call-recordings/`."
        ],
        "images": [
            ("48-Hour Rolling Auto-Sync Shield & Manual Override Flow", "../assets/diag_callsync_and_48h.png"),
            ("Telecaller Header Showing Live CallSync Connectivity Indicator", "../assets/ui_telecaller_dashboard.png")
        ],
        "rules": [
            "**48-Hour Rolling Sync Default:** Automatic call log ingestion (`CALL_SYNC_MAX_AGE_HOURS = 48`) and recording upload (`RECORDING_MAX_AGE_HOURS = 48`) skip records older than 48 hours so old phone history never resurrects deleted leads.",
            "**Manual Historical Override:** If an Admin needs older records from a phone, open Django Admin → `Call Devices` (`/django-admin/calls/calldevice/`), check **Allow historical sync**, or pass `manual_override: true` (can combine with `sync_cutoff_date`).",
            "**Zero-Zombie Recordings:** Call recordings never create new leads."
        ],
        "troubleshoot": [
            "**Phone shows Offline in CRM header:** Check Android Battery Optimization settings ('Unrestricted' required for CallSync) and confirm mobile data/Wi-Fi is on.",
            "**Audio rejected with HTTP 400 (`older than 48-hour rolling sync window`):** Expected safety guard for old SD card recordings; toggle **Allow historical sync** on the device in Admin only if you intentionally want older audio imported."
        ],
        "checklist": [
            "Signed into CallSync Android app with staff credentials",
            "Call Log, Storage, and Battery Unrestricted permissions granted",
            "Google Ads SIM mapped correctly",
            "Green **CallSync** indicator verified on CRM header"
        ],
        "owner": "Admin / IT Lead"
    },
    {
        "id": "SOP-23",
        "filename": "SOP-23_daily_backup_check_and_deploying_updates.md",
        "title": "Daily Database/Recording Backup Check & Deploying Updates",
        "role": "Admin / IT / DevOps",
        "frequency": "Daily (backup check at 9:00 AM) + On approved release deployments",
        "purpose": "Protect all student, lead, payment, and call recording data with daily verified backups and zero-downtime update deployments.",
        "before": "SSH/Server access to production host and verified backup directory.",
        "steps": [
            "**Daily Backup Check:** Verify last night's MySQL database dump (`mysqldump`) completed with non-zero file size and recent timestamp.",
            "Verify `CRM/private_media/` (call recordings) and `CRM/media/` (payment screenshots) synced cleanly to backup storage.",
            "**Deploying an Update (with Founder approval):** Run a fresh pre-deploy database backup first.",
            "Pull approved changes (`git pull origin main`) and activate the virtual environment.",
            "Install any updated dependencies (`pip install -r requirements.txt`), apply migrations (`python manage.py migrate`), and collect static assets (`python manage.py collectstatic --noinput`).",
            "Run `python manage.py check` (must return `0 issues`), restart the **Daphne ASGI** service, and verify `/login/` and `/admin/dashboard/` return HTTP 200."
        ],
        "images": [
            ("System Technical Architecture — Daphne ASGI, MySQL & Private Media", "../assets/diag_system_architecture.png"),
            ("Admin Dashboard Post-Deployment Health Verification", "../assets/ui_admin_dashboard.png")
        ],
        "rules": [
            "**Backup First, Deploy Second:** Never run `migrate` on production without a same-day MySQL dump.",
            "**Never commit `.env` or `db.sqlite3`:** Verify `.gitignore` stays intact before every Git push.",
            "Confirm background cron/workers (`run_lead_sla_escalation`, `send_installment_reminders`, `run_campaign_worker`) remain active after restart."
        ],
        "troubleshoot": [
            "**`OperationalError: Unknown column ...` after deploy:** Run `python manage.py migrate` immediately and restart Daphne (note: `accounts`, `calls`, and `fb_leads` `apps.py` also run MySQL column self-healing on boot).",
            "**UI looks unstyled after deploy:** Re-run `python manage.py collectstatic --noinput`."
        ],
        "checklist": [
            "Verified daily MySQL dump & `private_media/` backup",
            "Ran `migrate`, `collectstatic`, and `manage.py check` (0 issues)",
            "Verified HTTP 200 login and Facebook auto-sync startup log"
        ],
        "owner": "Admin / IT Lead"
    },
    {
        "id": "SOP-24",
        "filename": "SOP-24_login_password_and_data_privacy_rules.md",
        "title": "Login, Password Security & Student Data Privacy Rules",
        "role": "Everyone (All CRM Staff Roles)",
        "frequency": "Always / Mandatory daily compliance",
        "purpose": "Protect student personal information, financial records, and institute accounts from unauthorized sharing or breach.",
        "before": "Any active CRM user account across all 10 roles.",
        "steps": [
            "Always log in using your own individual username/email at `/login/` — **never share passwords** with colleagues.",
            "When signing in for the first time via an invitation link, set a strong unique password immediately (`must_change_password`).",
            "To update your password anytime, click your name/avatar in the top-right header -> **View Profile & Change Password** (`/profile/change-password/`).",
            "When stepping away from a shared reception or branch computer, lock your Windows/Mac screen (`Win + L`) or click **Logout** in the top-right header.",
            "Never screenshot, export, or save student phone numbers, email lists, UTR proofs, or call recordings onto personal WhatsApp, personal Google Drive, or USB drives."
        ],
        "images": [
            ("User Profile & Change Password Screen", "../assets/ui_user_profile.png"),
            ("Universal Branded CRM Sign-In Portal", "../assets/ui_login.png")
        ],
        "rules": [
            "Single-use invitation/reset links expire automatically after **24 hours**.",
            "Unauthorized CSV exports (`/leads/export/`) or attempting to access another user's URL returns 403/404 and records an audit trail under your username.",
            "Use masked dummy examples *(e.g. `Priya S`, `98xxxxxx10`)* whenever sharing screenshots in internal training chats."
        ],
        "troubleshoot": [
            "**Forgot password:** Click **Forgot Password** on `/login/` or ask an Admin to click **Resend Invitation**.",
            "**Suspected unauthorized login:** Report immediately to Admin/Branch Head so your password is reset and active sessions invalidated."
        ],
        "checklist": [
            "Using unique personal login (no shared accounts)",
            "Screen locked or logged out when unattended",
            "Zero student phone numbers/audio downloaded to personal devices"
        ],
        "owner": "Founder / Admin / Security Lead"
    }
]

def write_sop_files():
    index_rows = []
    for sop in SOPS:
        path = os.path.join(SOPS_DIR, sop["filename"])
        steps_md = "\n".join(f"{idx+1}. {s}" for idx, s in enumerate(sop["steps"]))
        imgs_md = "\n".join(f"![{cap}]({rel})" for cap, rel in sop["images"])
        rules_md = "\n".join(f"- {r}" for r in sop["rules"])
        trouble_md = "\n".join(f"- {t}" for t in sop["troubleshoot"])
        check_md = "\n".join(f"- [ ] {c}" for c in sop["checklist"])

        md = f"""# {sop['id']}: {sop['title']}

**SOP ID:** {sop['id']}  
**Role(s):** {sop['role']}  
**Frequency:** {sop['frequency']}  
**Owner:** {sop['owner']}  
**Next Review Date:** 10 May 2027  

---

## Purpose
{sop['purpose']}

## Who Does It
{sop['role']}

## When / How Often
{sop['frequency']}

## Before You Start
{sop['before']}

---

## Visual Reference & Workflow

{imgs_md}

---

## Step-by-Step Procedure

{steps_md}

---

## Rules & Timings

{rules_md}

---

## If Something Goes Wrong

{trouble_md}

---

## Completion Checklist

{check_md}

---

**Document Owner:** {sop['owner']}  
**Version:** 2.0 · **Last Reviewed:** 10 November 2026 · **Next Review Date:** 10 May 2027
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        index_rows.append(f"| **{sop['id']}** | {sop['title']} | {sop['role']} | {sop['frequency']} | [{sop['filename']}]({sop['filename']}) |")
        print(f"Wrote {sop['filename']}")

    index_md = f"""# iTechPanda / DigiPanda CRM — Standard Operating Procedures (SOP Index)

**Version:** 2.0  
**Effective Date:** 10 November 2026  
**System:** `https://itechpandacrm.in` (`CRM_Integrated_v2`)  

This manual provides clear, step-by-step operating procedures for every staff role in the training institute.

![End-to-End Lead Lifecycle Reference](../assets/diag_lead_intake_flow.png)

---

## Master SOP Directory (SOP-01 to SOP-24)

| SOP # | Title | Role | Frequency | File Link |
|---|---|---|---|---|
{chr(10).join(index_rows)}

---

> **Note:** Earlier technical DevOps reference SOPs from v1.0 are preserved under `_technical_archive/`.
"""
    with open(os.path.join(SOPS_DIR, "00_SOP_Index.md"), "w", encoding="utf-8") as f:
        f.write(index_md)
    print("Wrote 00_SOP_Index.md")

if __name__ == "__main__":
    write_sop_files()
