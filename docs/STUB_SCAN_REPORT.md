# Stub & Incomplete-Code Scan

Run: 2026-11-27 13:25 · Root: `D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM`

**Blockers:** 0 · **Warnings:** 125 · **Verdict:** ✅ no stubs found

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
| alert() used for UX | chat\static\chat\js\inbox.js | 1277 | `alert(`One-Click Sync Completed!\n\n` +` |
| alert() used for UX | chat\static\chat\js\inbox.js | 1287 | `alert('Sync error: ' + (data.error // data.detail // 'Unable to sync accounts.'));` |
| alert() used for UX | chat\static\chat\js\inbox.js | 1290 | `alert('One-Click Sync request failed: ' + err.message);` |
| Hard-coded localhost URL | config\settings.py | 328 | `CRM_BASE_URL = os.getenv('CRM_BASE_URL', 'http://127.0.0.1:8000')` |
| alert() used for UX | fb_leads\templates\fb_leads\accounts.html | 483 | `alert(`One-Click Sync Completed!\n\n` +` |
| alert() used for UX | fb_leads\templates\fb_leads\accounts.html | 490 | `alert('Sync failed: ' + (data.error // 'Unknown error'));` |
| alert() used for UX | fb_leads\templates\fb_leads\accounts.html | 497 | `alert('Error running One-Click Sync: ' + err.message);` |
| Hard-coded localhost URL | scratch\add_track_aa_todo.py | 18 | `- What: Verify in Chrome headless against live server (`http://127.0.0.1:8001/admin/dashboard/`) that clicking` |
| Hard-coded localhost URL | scratch\mark_todo_track_aa_done.py | 14 | `- What: Verify in Chrome headless against live server (`http://127.0.0.1:8001/admin/dashboard/`) that clicking` |
| Hard-coded localhost URL | scratch\mark_todo_track_z_done.py | 64 | `- Proof: Executed `test_new_enquiry_form.py` against live server (`http://127.0.0.1:8001/enquiry/` -> HTTP 200` |
| alert() used for UX | scratch\patch_campaign_composer.py | 45 | `alert('Branch assignment is required. Please select a branch for this WhatsApp number.');` |
| alert() used for UX | scratch\update_leads_list_telecrm.py | 833 | `alert('Please enter a name for your custom view tab.');` |
| alert() used for UX | scratch\update_leads_list_telecrm.py | 879 | `alert(data.message // 'Error saving custom view.');` |
| alert() used for UX | scratch\update_leads_list_telecrm.py | 884 | `alert('Failed to save custom view. Please check connection.');` |
| alert() used for UX | scratch\update_leads_list_telecrm.py | 914 | `alert(data.message // 'Error deleting view.');` |
| alert() used for UX | scratch\update_leads_list_telecrm.py | 919 | `alert('Failed to delete view.');` |
| alert() used for UX | static\js\crm.js | 246 | `alert('You have a completed call that still requires notes before calling another lead.');` |
| alert() used for UX | static\js\crm.js | 612 | `alert(res.data.error // 'Failed to start call.');` |
| alert() used for UX | static\js\crm.js | 1278 | `alert('Cannot save call notes: No active lead or call record associated with this form.');` |
| alert() used for UX | static\js\crm.js | 1305 | `alert(res.data.error // 'Failed to save call notes.');` |
| alert() used for UX | static\js\crm.js | 1321 | `alert(' ' + (res.data.message // 'Call notes saved successfully. You can now call another lead.'));` |
| alert() used for UX | static\js\crm.js | 1330 | `alert('An unexpected error occurred while saving call notes.');` |
| alert() used for UX | static\js\data-tables-enhanced.js | 255 | `alert('Please select a target status from the dropdown.');` |
| alert() used for UX | static\js\data-tables-enhanced.js | 261 | `alert('No leads selected.');` |
| alert() used for UX | templates\accountant\dashboard.html | 591 | `alert('Validation Error: From Date cannot be after To Date.');` |
| alert() used for UX | templates\accountant\verification_list.html | 270 | `<button type="button" class="btn btn-sm btn-outline-secondary" style="padding: 3px 8px; font-size: 0.75rem;" o` |
| alert() used for UX | templates\admin\leads_list.html | 1667 | `alert(data.error // 'Failed to load duplicate information.');` |
| alert() used for UX | templates\admin\leads_list.html | 1977 | `alert('Communication error: ' + err);` |
| alert() used for UX | templates\admin\leads_list.html | 2073 | `alert(data.error // 'Failed to dispatch counselor alert.');` |
| alert() used for UX | templates\admin\leads_list.html | 2085 | `alert("Request failed: " + err);` |
| alert() used for UX | templates\admin\leads_list.html | 2411 | `alert('Please select at least one lead from the table or apply a filter.');` |
| alert() used for UX | templates\admin\leads_list.html | 2505 | `alert(data.error // 'Failed to evaluate recipients');` |
| alert() used for UX | templates\admin\leads_list.html | 2529 | `alert('Communication error: ' + err);` |
| alert() used for UX | templates\admin\leads_list.html | 2557 | `alert('Please select at least one lead from the table.');` |
| alert() used for UX | templates\admin\leads_list.html | 2919 | `alert('Please enter a name for your custom view tab.');` |
| alert() used for UX | templates\admin\leads_list.html | 2965 | `alert(data.message // 'Error saving custom view.');` |
| alert() used for UX | templates\admin\leads_list.html | 2970 | `alert('Failed to save custom view. Please check connection.');` |
| alert() used for UX | templates\admin\leads_list.html | 3000 | `alert(data.message // 'Error deleting view.');` |
| alert() used for UX | templates\admin\leads_list.html | 3005 | `alert('Failed to delete view.');` |
| alert() used for UX | templates\admin\lead_queues.html | 423 | `alert("Please select at least one lead from the table to assign.");` |
| alert() used for UX | templates\admin\lead_queues.html | 744 | `alert("Please select at least one target branch.");` |
| alert() used for UX | templates\admin\lead_queues.html | 748 | `alert("Please select at least one target telecaller.");` |
| alert() used for UX | templates\admin\lead_queues.html | 796 | `alert(breakdownMsg);` |
| alert() used for UX | templates\admin\lead_queues.html | 799 | `alert(`Error: ${result.error // 'Failed to assign leads.'}`);` |
| alert() used for UX | templates\admin\lead_queues.html | 804 | `alert(`Request error: ${err.message}`);` |
| alert() used for UX | templates\admin\offline_leads.html | 1055 | `alert(data.message // 'Sync complete!');` |
| alert() used for UX | templates\admin\offline_leads.html | 1059 | `alert('Sync error: ' + err);` |
| alert() used for UX | templates\admin\offline_leads.html | 1075 | `alert(` ${data.message}`);` |
| alert() used for UX | templates\admin\offline_leads.html | 1077 | `alert(` ${data.error}`);` |
| alert() used for UX | templates\admin\offline_leads.html | 1081 | `alert('Test connection error: ' + err);` |
| alert() used for UX | templates\admin\offline_leads.html | 1234 | `alert('Failed to inspect spreadsheet: ' + (data.error // 'Unknown error'));` |
| alert() used for UX | templates\admin\offline_leads.html | 1239 | `alert('Error inspecting spreadsheet mapping: ' + err);` |
| alert() used for UX | templates\admin\offline_leads.html | 1496 | `alert('Preview failed: ' + (data.error // 'Unknown error'));` |
| alert() used for UX | templates\admin\offline_leads.html | 1502 | `alert('Dry-run preview failed: ' + err);` |
| alert() used for UX | templates\admin\offline_leads.html | 1547 | `alert(' Synchronization complete! ' + (syncData.sync_result?.message // 'Updated successfully.'));` |
| alert() used for UX | templates\admin\offline_leads.html | 1552 | `alert(' Column mapping configuration saved successfully!');` |
| alert() used for UX | templates\admin\offline_leads.html | 1561 | `alert('Error: ' + err);` |
| alert() used for UX | templates\admin\status_leads_list.html | 213 | `alert(data.error // 'Failed to update lead status');` |
| alert() used for UX | templates\admin\status_leads_list.html | 219 | `alert('Communication error: ' + err);` |
| alert() used for UX | templates\admin\telecallers_list.html | 462 | `alert('Please select a counselor.');` |
| alert() used for UX | templates\admin\telecallers_list.html | 506 | `alert('Please select a branch.');` |
| alert() used for UX | templates\admin\telecallers_list.html | 615 | `alert('Error updating telecallers: ' + (data.error // 'Server error'));` |
| alert() used for UX | templates\admin\telecallers_list.html | 626 | `alert('Network error while processing bulk update: ' + err.message);` |
| alert() used for UX | templates\admin\walkin_desk.html | 906 | `alert(`Error updating visitor status: ${data.error // 'Failed'}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 909 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 943 | `alert(`Visitor Token #${data.token_number} generated! Visitor checked in successfully.`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 974 | `alert("Notice: Matching student record(s) already exist in the CRM. You can check in the existing student dire` |
| alert() used for UX | templates\admin\walkin_desk.html | 976 | `alert(`Error: ${data.error // 'Failed to check in visitor.'}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 981 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 1006 | `alert(data.message // `Existing student checked in successfully! Token #${data.token_number}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 1009 | `alert(`Error: ${data.error // 'Failed to check in existing student.'}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 1012 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 1043 | `alert(`Error: ${data.error // 'Failed to assign counselor.'}`);` |
| alert() used for UX | templates\admin\walkin_desk.html | 1048 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\admin\walkin_forms_list.html | 406 | `alert('Public link copied to clipboard: ' + url);` |
| alert() used for UX | templates\admin\walkin_form_editor.html | 2941 | `alert('Error saving form: ' + (data.error // 'Server error'));` |
| alert() used for UX | templates\admin\walkin_form_editor.html | 2949 | `alert('Network error saving form. Please try again.');` |
| alert() used for UX | templates\admin_dashboard\dashboard.html | 633 | `alert(' ' + data.message);` |
| alert() used for UX | templates\admin_dashboard\dashboard.html | 636 | `alert(' ' + (data.error // 'Failed to enforce SLAs.'));` |
| alert() used for UX | templates\admin_dashboard\dashboard.html | 642 | `alert('Network error while running SLA escalation.');` |
| alert() used for UX | templates\chat\campaigns\campaign_composer.html | 951 | `alert('Branch assignment is required. Please select a branch for this WhatsApp number.');` |
| alert() used for UX | templates\chat\campaigns\campaign_composer.html | 1011 | `alert(' ' + data.message);` |
| alert() used for UX | templates\chat\campaigns\campaign_composer.html | 1145 | `alert(' ' + data.message);` |
| alert() used for UX | templates\chat\campaigns\campaign_detail.html | 245 | `alert(data.error // 'Control action failed');` |
| alert() used for UX | templates\chat\campaigns\campaign_detail.html | 248 | `.catch(err =>alert('Communication error: ' + err));` |
| alert() used for UX | templates\leads\enrollment_form.html | 512 | `alert('First payment amount must be greater than zero.');` |
| alert() used for UX | templates\leads\enrollment_form.html | 521 | `alert(`First payment amount (₹${val.toFixed(2)}) cannot exceed the total payable fee (₹${totalPayable.toFixed(` |
| alert() used for UX | templates\leads\enrollment_form.html | 529 | `alert(`Transaction / Reference number is required for payment mode '${mode}'.`);` |
| alert() used for UX | templates\leads\partials\bulk_edit_modal.html | 383 | `alert('Please select at least one lead from the table to bulk edit.');` |
| alert() used for UX | templates\leads\partials\bulk_edit_modal.html | 950 | `alert('Bulk operation error: ' + (res.error // 'Failed to apply changes.'));` |
| alert() used for UX | templates\leads\partials\bulk_edit_modal.html | 961 | `alert(res.message);` |
| alert() used for UX | templates\leads\partials\bulk_edit_modal.html | 972 | `alert('Communication error during execution: ' + err);` |
| alert() used for UX | templates\manager\leads_list.html | 1094 | `alert('Please enter a name for your custom view tab.');` |
| alert() used for UX | templates\manager\leads_list.html | 1135 | `alert(data.message // 'Error saving custom view.');` |
| alert() used for UX | templates\manager\leads_list.html | 1140 | `alert('Failed to save custom view. Please check connection.');` |
| alert() used for UX | templates\manager\leads_list.html | 1170 | `alert(data.message // 'Error deleting view.');` |
| alert() used for UX | templates\manager\leads_list.html | 1175 | `alert('Failed to delete view.');` |
| alert() used for UX | templates\receptionist\dashboard.html | 684 | `alert("Please select at least one walk-in lead to assign.");` |
| alert() used for UX | templates\receptionist\dashboard.html | 710 | `alert("Please select at least one walk-in lead.");` |
| alert() used for UX | templates\receptionist\dashboard.html | 717 | `alert("Please select an eligible branch counselor.");` |
| alert() used for UX | templates\receptionist\dashboard.html | 744 | `alert(`Success: ${data.assigned_count} walk-in lead(s) successfully assigned to Counselor ${data.counselor_nam` |
| alert() used for UX | templates\receptionist\dashboard.html | 747 | `alert(`Error: ${data.error // 'Failed to assign leads.'}`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 752 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 963 | `alert("Please select an eligible active counselor.");` |
| alert() used for UX | templates\receptionist\dashboard.html | 998 | `alert(`Student successfully assigned to Counselor ${data.counselor_name}!`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 1001 | `alert(`Error: ${data.error // 'Failed to assign counselor.'}`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 1006 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 1100 | `alert(`Visitor Token #${data.token_number} generated! Student checked in successfully.`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 1130 | `alert("Notice: Matching student record(s) already exist in the CRM. You can review history or assign the exist` |
| alert() used for UX | templates\receptionist\dashboard.html | 1132 | `alert(`Error: ${data.error // 'Failed to check in student.'}`);` |
| alert() used for UX | templates\receptionist\dashboard.html | 1137 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\receptionist\lead_history.html | 395 | `alert("Please select an active counselor.");` |
| alert() used for UX | templates\receptionist\lead_history.html | 429 | `alert(`Student successfully assigned to Counselor ${data.counselor_name}!`);` |
| alert() used for UX | templates\receptionist\lead_history.html | 432 | `alert(`Error: ${data.error // 'Failed to assign counselor.'}`);` |
| alert() used for UX | templates\receptionist\lead_history.html | 437 | `alert(`Error: ${err.message}`);` |
| alert() used for UX | templates\reports\calls.html | 320 | `alert('Please enter a name for the report.');` |
| alert() used for UX | templates\reports\calls.html | 343 | `alert('Report saved successfully!');` |
| alert() used for UX | templates\reports\calls.html | 347 | `alert(data.message // 'Error saving report.');` |
| alert() used for UX | templates\reports\calls.html | 352 | `alert('Failed to save report.');` |

