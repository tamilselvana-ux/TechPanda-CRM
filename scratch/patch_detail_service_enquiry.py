path = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\detail_service.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old_str = '''    val_degree = find_val(['degree', 'qualification', 'education'])
    val_passed_out = find_val(['passed_out', 'passedout', 'passed out', 'year of pass', 'passing year', 'yop'])
    val_purpose = find_val(['purpose', 'objective', 'reason', 'intent'])
    val_base_branch = lead.branch.name if lead.branch else find_val(['branch', 'base branch'])
    val_pref_branch = ", ".join(lead.get_all_branch_names()) if lead.secondary_branches.exists() else find_val(['pref_branch', 'preferred branch', 'pref branch'])
    val_working_status = find_val(['working_status', 'working status', 'employment status', 'working', 'job status', 'status of work'])
    val_total_exp = find_val(['total_experience', 'total experience', 'experience', 'exp', 'work experience'])
    val_pref_exam_loc = find_val(['pref_exam_loc', 'preferred exam location', 'exam location', 'exam city'])
    val_join_pref = find_val(['join_preference', 'how would you like to join the course', 'joining preference', 'mode', 'course mode', 'batch mode'])
    val_lead_source = lead.channel.name if lead.channel else (lead.source or find_val(['lead source', 'source']))
    val_college = find_val(['college', 'university', 'institution', 'college name'])
    val_retargeted = find_val(['retargeted', 'retarget', 're-target', 'is retargeted'])
    val_capture_freq = find_val(['capture frequency', 'frequency', 'import count'], '1')
    val_designation = find_val(['designation', 'role', 'current role', 'job title'])
    val_courses = lead.product.name if lead.product else find_val(['courses', 'course', 'domain', 'subject'])
    val_location = find_val(['location', 'city', 'native', 'address']) or (lead.branch.city if lead.branch and hasattr(lead.branch, 'city') else '')
    val_current_ctc = find_val(['current ctc', 'ctc', 'current salary', 'salary'])
    val_expected_ctc = find_val(['expected ctc', 'exp ctc', 'expected salary'])'''

new_str = '''    val_degree = find_val(['highest_education', 'degree', 'ug_qualification', 'qualification', 'education'])
    val_passed_out = find_val(['passed_out', 'pg_passed_out_year', 'ug_passed_out_year', 'passedout', 'passed out', 'year of pass', 'passing year', 'yop'])
    val_purpose = find_val(['reason_for_leaving', 'purpose', 'objective', 'reason', 'intent'])
    val_base_branch = lead.branch.name if lead.branch else find_val(['branch', 'base branch'])
    val_pref_branch = ", ".join(lead.get_all_branch_names()) if lead.secondary_branches.exists() else find_val(['pref_branch', 'preferred branch', 'pref branch'])
    val_working_status = find_val(['experience_type', 'working_status', 'working status', 'employment status', 'working', 'job status', 'status of work'])
    val_total_exp = find_val(['total_experience', 'years_of_experience', 'total experience', 'experience', 'exp', 'work experience'])
    val_pref_exam_loc = find_val(['pref_exam_loc', 'preferred exam location', 'exam location', 'exam city'])
    val_join_pref = find_val(['preferred_training_mode', 'join_preference', 'how would you like to join the course', 'joining preference', 'mode', 'course mode', 'batch mode'])
    val_lead_source = lead.channel.name if lead.channel else (lead.source or find_val(['lead source', 'source']))
    val_college = find_val(['company_name', 'college', 'university', 'institution', 'college name'])
    val_retargeted = find_val(['retargeted', 'retarget', 're-target', 'is retargeted'])
    val_capture_freq = find_val(['capture frequency', 'frequency', 'import count'], '1')
    val_designation = find_val(['designation', 'role', 'current role', 'job title'])
    val_courses = lead.product.name if lead.product else find_val(['course_track', 'courses', 'course', 'domain', 'subject'])
    val_location = find_val(['current_address', 'location', 'city', 'native', 'address']) or (lead.branch.city if lead.branch and hasattr(lead.branch, 'city') else '')
    val_current_ctc = find_val(['current_ctc', 'current ctc', 'ctc', 'current salary', 'salary'])
    val_expected_ctc = find_val(['expected_ctc', 'expected ctc', 'exp ctc', 'expected salary'])'''

assert old_str in content, "old_str not found in detail_service.py"
content = content.replace(old_str, new_str, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Successfully patched leads/detail_service.py")
