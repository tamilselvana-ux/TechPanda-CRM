# Stub & Incomplete-Code Scan

Run: 2026-11-11 16:25 · Root: `d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM`

**Blockers:** 0 · **Warnings:** 118 · **Verdict:** ✅ no stubs found

## 🚫 Blockers (must fix before 'done')
| Rule | File | Line | Code |
|---|---|---|---|
| — | — | — | none |

## ⚠️ Warnings (review)
| Rule | File | Line | Code |
|---|---|---|---|
| Hard-coded localhost URL | accounts\services.py | 133 | `base_url = getattr(settings, 'CRM_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')` |
| Hard-coded localhost URL | accounts\services.py | 286 | `base_url = getattr(settings, 'CRM_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')` |
| Hard-coded localhost URL | chat\tests_phase1_engine_hardening.py | 122 | `'https://127.0.0.1:8000/webhook',` |
| Debug output left in | chat\static\chat\flow_builder_dist\assets\flow_builder_app.js | 61 | ``)),u=h.reduce((p,y)=>p.concat(...y),[]);return[h,u]}return[[],[]]},[e]);return P.useEffect(()=>{const s=(t==n` |
| Debug output left in | chat\static\chat\flow_builder_dist\assets\flow_builder_app.js | 61 | ``)),u=h.reduce((p,y)=>p.concat(...y),[]);return[h,u]}return[[],[]]},[e]);return P.useEffect(()=>{const s=(t==n` |
| Debug output left in | chat\static\chat\flow_builder_dist\assets\flow_builder_app.js | 61 | ``)),u=h.reduce((p,y)=>p.concat(...y),[]);return[h,u]}return[[],[]]},[e]);return P.useEffect(()=>{const s=(t==n` |
| Hard-coded localhost URL | config\settings.py | 305 | `CRM_BASE_URL = os.getenv('CRM_BASE_URL', 'http://127.0.0.1:8000')` |
| alert() used for UX | fb_leads\templates\fb_leads\accounts.html | 456 | `alert(data.error // "Failed to update cutoff date");` |
| alert() used for UX | fb_leads\templates\fb_leads\accounts.html | 461 | `alert("Network error updating cutoff date");` |
| Hard-coded localhost URL | scratch\add_track_aa_todo.py | 18 | `- What: Verify in Chrome headless against live server (`http://127.0.0.1:8001/admin/dashboard/`) that clicking` |
| alert() used for UX | scratch\apply_remediations.py | 31 | `2. **Stored XSS:** Creating a lead with name `"><script>alert(1)</script>` must render escaped characters (`&q` |
| Hard-coded localhost URL | scratch\build_crawler_config.py | 7 | `"baseUrl": "http://127.0.0.1:8000",` |
| Hard-coded localhost URL | scratch\capture_after_screenshots.py | 109 | `tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9223/json').read().decode('utf-8'))` |
| Hard-coded localhost URL | scratch\capture_after_screenshots.py | 136 | `cdp.send("Page.navigate", {"url": "http://127.0.0.1:8000/admin/dashboard/"})` |
| Hard-coded localhost URL | scratch\capture_after_screenshots.py | 174 | `cdp.send("Page.navigate", {"url": "http://127.0.0.1:8000/accountant/dashboard/"})` |
| Hard-coded localhost URL | scratch\capture_all_baselines.py | 105 | `('accountant', 'http://127.0.0.1:8000/accountant/dashboard/'),` |
| Hard-coded localhost URL | scratch\capture_all_baselines.py | 106 | `('admin_leads', 'http://127.0.0.1:8000/admin/leads/'),` |
| Hard-coded localhost URL | scratch\capture_all_baselines.py | 107 | `('admin_dashboard', 'http://127.0.0.1:8000/admin/dashboard/'),` |
| Hard-coded localhost URL | scratch\capture_all_baselines.py | 111 | `tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode('utf-8'))` |
| Hard-coded localhost URL | scratch\capture_app_screenshots.py | 42 | `html = html.replace('href="/static/', 'href="http://127.0.0.1:8001/static/')` |
| Hard-coded localhost URL | scratch\capture_app_screenshots.py | 43 | `html = html.replace('src="/static/', 'src="http://127.0.0.1:8001/static/')` |
| Hard-coded localhost URL | scratch\capture_app_screenshots.py | 46 | `html = html.replace("<head>", '<head><base href="http://127.0.0.1:8001/">')` |
| Hard-coded localhost URL | scratch\capture_baseline_cdp.py | 104 | `tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json').read().decode('utf-8'))` |
| Hard-coded localhost URL | scratch\capture_baseline_cdp.py | 121 | `mid = cdp.send("Page.navigate", {"url": "http://127.0.0.1:8000/accountant/dashboard/"})` |
| Hard-coded localhost URL | scratch\check_calendar_render.py | 10 | `await page.goto('http://127.0.0.1:8000/accounts/login/')` |
| Hard-coded localhost URL | scratch\check_calendar_render.py | 17 | `await page.goto('http://127.0.0.1:8000/admin/leads/?view=all_active&sort=-created_at')` |
| Hard-coded localhost URL | scratch\mark_todo_track_z_done.py | 64 | `- Proof: Executed `test_new_enquiry_form.py` against live server (`http://127.0.0.1:8001/enquiry/` -> HTTP 200` |
| alert() used for UX | scratch\patch_accounts_template.py | 73 | `alert(data.error // "Failed to update cutoff date");` |
| alert() used for UX | scratch\patch_accounts_template.py | 78 | `alert("Network error updating cutoff date");` |
| alert() used for UX | scratch\patch_dashboard_html_dates.py | 242 | `alert('Validation Error: From Date cannot be after To Date.');` |
| alert() used for UX | scratch\patch_enrollment_form_html.py | 109 | `alert('First payment amount must be greater than zero.');` |
| alert() used for UX | scratch\patch_enrollment_form_html.py | 118 | `alert(`First payment amount (₹${val.toFixed(2)}) cannot exceed the total payable fee (₹${totalPayable.toFixed(` |
| alert() used for UX | scratch\patch_enrollment_form_html.py | 126 | `alert(`Transaction / Reference number is required for payment mode '${mode}'.`);` |
| alert() used for UX | scratch\patch_walkin_forms_list_html.py | 406 | `alert('Public link copied to clipboard: ' + url);` |
| alert() used for UX | scratch\security_audit_scanner.py | 162 | `name = '<script>alert("XSS_NAME")</script>'` |
| alert() used for UX | scratch\security_audit_scanner.py | 163 | `custom_fields = {'working_status': '<img src=x onerror=alert("XSS_STATUS")>'}` |
| alert() used for UX | static\js\crm.js | 246 | `alert('You have a completed call that still requires notes before calling another lead.');` |
| alert() used for UX | static\js\crm.js | 612 | `alert(res.data.error // 'Failed to start call.');` |
| alert() used for UX | static\js\crm.js | 1278 | `alert('Cannot save call notes: No active lead or call record associated with this form.');` |
| alert() used for UX | static\js\crm.js | 1305 | `alert(res.data.error // 'Failed to save call notes.');` |
| alert() used for UX | static\js\crm.js | 1321 | `alert('✓ ' + (res.data.message // 'Call notes saved successfully. You can now call another lead.'));` |
| alert() used for UX | static\js\crm.js | 1330 | `alert('An unexpected error occurred while saving call notes.');` |
| alert() used for UX | static\js\data-tables-enhanced.js | 255 | `alert('Please select a target status from the dropdown.');` |
| alert() used for UX | static\js\data-tables-enhanced.js | 261 | `alert('No leads selected.');` |
| alert() used for UX | templates\accountant\dashboard.html | 591 | `alert('Validation Error: From Date cannot be after To Date.');` |
| alert() used for UX | templates\accountant\verification_list.html | 270 | `<button type="button" class="btn btn-sm btn-outline-secondary" style="padding: 3px 8px; font-size: 0.75rem;" o` |
| alert() used for UX | templates\admin\leads_list.html | 425 | `alert('Please enter a name for this saved view.');` |
| alert() used for UX | templates\admin\leads_list.html | 441 | `alert('View "' + name + '" saved successfully to your top views bar!');` |
| alert() used for UX | templates\admin\leads_list.html | 1698 | `alert(data.error // 'Failed to load duplicate information.');` |
| alert() used for UX | templates\admin\leads_list.html | 2008 | `alert('Communication error: ' + err);` |
| alert() used for UX | templates\admin\leads_list.html | 2104 | `alert(data.error // 'Failed to dispatch counselor alert.');` |
| alert() used for UX | templates\admin\leads_list.html | 2116 | `alert("Request failed: " + err);` |
| alert() used for UX | templates\admin\leads_list.html | 2438 | `alert('Please select at least one lead from the table or apply a filter.');` |
| alert() used for UX | templates\admin\leads_list.html | 2532 | `alert(data.error // 'Failed to evaluate recipients');` |
| alert() used for UX | templates\admin\leads_list.html | 2556 | `alert('Communication error: ' + err);` |
| alert() used for UX | templates\admin\leads_list.html | 2584 | `alert('Please select at least one lead from the table.');` |
| alert() used for UX | templates\admin\lead_queues.html | 423 | `alert("Please select at least one lead from the table to assign.");` |
| alert() used for UX | templates\admin\lead_queues.html | 744 | `alert("Please select at least one target branch.");` |
| alert() used for UX | templates\admin\lead_queues.html | 748 | `alert("Please select at least one target telecaller.");` |
| alert() used for UX | templates\admin\lead_queues.html | 796 | `alert(breakdownMsg);` |
| alert() used for UX | templates\admin\lead_queues.html | 799 | `alert(`Error: ${result.error // 'Failed to assign leads.'}`);` |
| alert() used for UX | templates\admin\lead_queues.html | 804 | `alert(`Request error: ${err.message}`);` |
| alert() used for UX | templates\admin\offline_leads.html | 1055 | `alert(data.message // 'Sync complete!');` |
| alert() used for UX | templates\admin\offline_leads.html | 1059 | `alert('Sync error: ' + err);` |
| alert() used for UX | templates\admin\offline_leads.html | 1075 | `alert(`🟢 ${data.message}`);` |
| alert() used for UX | templates\admin\offline_leads.html | 1077 | `alert(`🔴 ${data.error}`);` |
| alert() used for UX | templates\admin\offline_leads.html | 1081 | `alert('Test connection error: ' + err);` |
| alert() used for UX | templates\admin\offline_leads.html | 1234 | `alert('Failed to inspect spreadsheet: ' + (data.error // 'Unknown error'));` |
| alert() used for UX | templates\admin\offline_leads.html | 1239 | `alert('Error inspecting spreadsheet mapping: ' + err);` |
| alert() used for UX | templates\admin\offline_leads.html | 1496 | `alert('Preview failed: ' + (data.error // 'Unknown error'));` |
| alert() used for UX | templates\admin\offline_leads.html | 1502 | `alert('Dry-run preview failed: ' + err);` |
| alert() used for UX | templates\admin\offline_leads.html | 1547 | `alert('🎉 Synchronization complete! ' + (syncData.sync_result?.message // 'Updated successfully.'));` |
| alert() used for UX | templates\admin\offline_leads.html | 1552 | `alert('✓ Column mapping configuration saved successfully!');` |
| alert() used for UX | templates\admin\offline_leads.html | 1561 | `alert('Error: ' + err);` |
| alert() used for UX | templates\admin\status_leads_list.html | 213 | `alert(data.error // 'Failed to update lead status');` |
| alert() used for UX | templates\admin\status_leads_list.html | 219 | `alert('Communication error: ' + err);` |
| alert() used for UX | templates\admin\walkin_desk.html | 892 | `alert(`Error updating visitor status: ${data.error // 'Failed'}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 895 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 928 | `alert(`Visitor Token #${data.token_number} generated! Visitor checked in successfully.`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 931 | `alert(`Error: ${data.error // 'Failed to check in visitor.'}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 936 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 969 | `alert(`Error: ${data.error // 'Failed to assign counselor.'}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 974 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\admin\walkin_forms_list.html | 406 | `alert('Public link copied to clipboard: ' + url);` |
| alert() used for UX | templates\admin\walkin_form_editor.html | 2941 | `alert('Error saving form: ' + (data.error // 'Server error'));` |
| alert() used for UX | templates\admin\walkin_form_editor.html | 2949 | `alert('Network error saving form. Please try again.');` |
| alert() used for UX | templates\admin_dashboard\dashboard.html | 617 | `alert('✅ ' + data.message);` |
| alert() used for UX | templates\admin_dashboard\dashboard.html | 620 | `alert('❌ ' + (data.error // 'Failed to enforce SLAs.'));` |
| alert() used for UX | templates\admin_dashboard\dashboard.html | 626 | `alert('Network error while running SLA escalation.');` |
| alert() used for UX | templates\chat\campaigns\campaign_composer.html | 999 | `alert('✓ ' + data.message);` |
| alert() used for UX | templates\chat\campaigns\campaign_composer.html | 1133 | `alert('✓ ' + data.message);` |
| alert() used for UX | templates\chat\campaigns\campaign_detail.html | 245 | `alert(data.error // 'Control action failed');` |
| alert() used for UX | templates\chat\campaigns\campaign_detail.html | 248 | `.catch(err => alert('Communication error: ' + err));` |
| alert() used for UX | templates\leads\enrollment_form.html | 512 | `alert('First payment amount must be greater than zero.');` |
| alert() used for UX | templates\leads\enrollment_form.html | 521 | `alert(`First payment amount (₹${val.toFixed(2)}) cannot exceed the total payable fee (₹${totalPayable.toFixed(` |
| alert() used for UX | templates\leads\enrollment_form.html | 529 | `alert(`Transaction / Reference number is required for payment mode '${mode}'.`);` |
| alert() used for UX | templates\leads\partials\bulk_edit_modal.html | 383 | `alert('Please select at least one lead from the table to bulk edit.');` |
| alert() used for UX | templates\leads\partials\bulk_edit_modal.html | 950 | `alert('Bulk operation error: ' + (res.error // 'Failed to apply changes.'));` |
| alert() used for UX | templates\leads\partials\bulk_edit_modal.html | 961 | `alert(res.message);` |
| alert() used for UX | templates\leads\partials\bulk_edit_modal.html | 972 | `alert('Communication error during execution: ' + err);` |
| alert() used for UX | templates\receptionist\dashboard.html | 692 | `alert("Please select at least one walk-in lead to assign.");` |
| alert() used for UX | templates\receptionist\dashboard.html | 718 | `alert("Please select at least one walk-in lead.");` |
| alert() used for UX | templates\receptionist\dashboard.html | 725 | `alert("Please select an eligible branch counselor.");` |
| alert() used for UX | templates\receptionist\dashboard.html | 752 | `alert(`Success: ${data.assigned_count} walk-in lead(s) successfully assigned to Counselor ${data.counselor_nam` |
| alert() used for UX | templates\receptionist\dashboard.html | 755 | `alert(`Error: ${data.error // 'Failed to assign leads.'}`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 760 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 971 | `alert("Please select an eligible active counselor.");` |
| alert() used for UX | templates\receptionist\dashboard.html | 1006 | `alert(`Student successfully assigned to Counselor ${data.counselor_name}!`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 1009 | `alert(`Error: ${data.error // 'Failed to assign counselor.'}`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 1014 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 1147 | `alert(`Visitor Token #${data.token_number} generated! Student checked in successfully.`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 1177 | `alert("Notice: Matching student record(s) already exist in the CRM. You can review history or assign the exist` |
| alert() used for UX | templates\receptionist\dashboard.html | 1179 | `alert(`Error: ${data.error // 'Failed to check in student.'}`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 1184 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\receptionist\lead_history.html | 395 | `alert("Please select an active counselor.");` |
| alert() used for UX | templates\receptionist\lead_history.html | 429 | `alert(`Student successfully assigned to Counselor ${data.counselor_name}!`);` |
| alert() used for UX | templates\receptionist\lead_history.html | 432 | `alert(`Error: ${data.error // 'Failed to assign counselor.'}`);` |
| alert() used for UX | templates\receptionist\lead_history.html | 437 | `alert(`Error: ${err.message}`);` |

