path_walkin = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\views_walkin.py"
with open(path_walkin, "r", encoding="utf-8") as f:
    content = f.read()

old_block = '''        # Standard Student Enquiry Form Fields Extraction
        custom_payload['dob'] = (request.POST.get('dob') or '').strip()
        custom_payload['home_address'] = (request.POST.get('home_address') or request.POST.get('address') or '').strip()
        custom_payload['city'] = (request.POST.get('city') or '').strip()
        custom_payload['state'] = (request.POST.get('state') or '').strip()
        custom_payload['zip_code'] = (request.POST.get('zip_code') or '').strip()
        custom_payload['gender'] = (request.POST.get('gender') or '').strip()
        custom_payload['preferred_contact'] = (request.POST.get('preferred_contact') or '').strip()

        # Education Qualifications
        custom_payload['experience_type'] = (request.POST.get('experience_type') or 'Fresher').strip()
        custom_payload['years_of_experience'] = (request.POST.get('years_of_experience') or '').strip()
        custom_payload['ug_qualification'] = (request.POST.get('ug_qualification') or request.POST.get('ug_degree') or '').strip()
        custom_payload['ug_passed_out_year'] = (request.POST.get('ug_passed_out_year') or request.POST.get('ug_year') or '').strip()
        custom_payload['pg_qualification'] = (request.POST.get('pg_qualification') or request.POST.get('pg_degree') or '').strip()
        custom_payload['pg_passed_out_year'] = (request.POST.get('pg_passed_out_year') or request.POST.get('pg_year') or '').strip()
        custom_payload['backlogs'] = (request.POST.get('backlogs') or 'No').strip()
        custom_payload['highest_education'] = (request.POST.get('highest_education') or '').strip()

        # Current Professional Status
        prof_statuses = {}
        for pkey in ['status_student_fresher', 'status_non_it', 'status_bpo', 'status_freelancer', 'status_it', 'status_business', 'status_career_break']:
            pval = (request.POST.get(pkey) or '').strip()
            if pval:
                prof_statuses[pkey.replace('status_', '')] = pval
        if request.POST.get('status_others'):
            prof_statuses['others'] = request.POST.get('status_others').strip()
        custom_payload['professional_status'] = prof_statuses

        # Career Goals
        career_goals = request.POST.getlist('career_goals')
        goal_other = (request.POST.get('goal_other_text') or '').strip()
        if goal_other:
            career_goals.append(f"Other: {goal_other}")
        custom_payload['career_goals'] = career_goals

        # Prior Digital Marketing Experience
        dm_exp = request.POST.getlist('dm_experience')
        custom_payload['dm_experience'] = dm_exp

        # Interested Course
        interested_courses = request.POST.getlist('interested_course')
        custom_payload['interested_course'] = interested_courses
        course_track = ', '.join(interested_courses) if interested_courses else (request.POST.get('course_track') or '')

        # Student References
        custom_payload['student_reference_1'] = (request.POST.get('student_reference_1') or request.POST.get('ref_1_name') or '').strip()
        custom_payload['student_reference_2'] = (request.POST.get('student_reference_2') or request.POST.get('ref_2_name') or '').strip()

        # Form Metadata
        custom_payload['enquiry_date'] = (request.POST.get('enquiry_date') or '').strip()
        custom_payload['enquiry_time'] = (request.POST.get('enquiry_time') or '').strip()
        
        # Helper data dict for redisplay on validation error
        form_data_dict = dict(request.POST.items())
        form_data_dict['career_goals_str'] = ' | '.join(career_goals)
        form_data_dict['dm_experience_str'] = ' | '.join(dm_exp)
        form_data_dict['interested_course_str'] = ' | '.join(interested_courses)'''

new_block = '''        # Basic Information Extraction (Training & Placement Student Enquiry Form)
        custom_payload['enquiry_form_no'] = (request.POST.get('enquiry_form_no') or '').strip()
        custom_payload['enquiry_date'] = (request.POST.get('enquiry_date') or '').strip()
        custom_payload['enquiry_time'] = (request.POST.get('enquiry_time') or '').strip()
        custom_payload['gender'] = (request.POST.get('gender') or '').strip()
        custom_payload['dob'] = (request.POST.get('dob') or '').strip()
        custom_payload['age'] = (request.POST.get('age') or '').strip()
        custom_payload['whatsapp_number'] = (request.POST.get('whatsapp_number') or request.POST.get('whatsapp') or '').strip()
        custom_payload['emergency_contact'] = (request.POST.get('emergency_contact') or request.POST.get('emergency_contact_number') or '').strip()
        custom_payload['preferred_contact'] = (request.POST.get('preferred_contact') or '').strip()

        # Location & Mode
        curr_addr = (request.POST.get('current_address') or request.POST.get('home_address') or request.POST.get('address') or '').strip()
        custom_payload['current_address'] = curr_addr
        custom_payload['home_address'] = curr_addr
        custom_payload['location'] = curr_addr
        custom_payload['city'] = (request.POST.get('city') or '').strip()
        custom_payload['state'] = (request.POST.get('state') or '').strip()
        custom_payload['zip_code'] = (request.POST.get('zip_code') or '').strip()
        pref_mode = (request.POST.get('preferred_training_mode') or request.POST.get('join_preference') or '').strip()
        custom_payload['preferred_training_mode'] = pref_mode
        if pref_mode:
            custom_payload['join_preference'] = pref_mode

        # Education Qualifications
        custom_payload['experience_type'] = (request.POST.get('experience_type') or 'Fresher').strip()
        custom_payload['years_of_experience'] = (request.POST.get('years_of_experience') or '').strip()
        if custom_payload['years_of_experience']:
            custom_payload['total_experience'] = custom_payload['years_of_experience']
        ug_qual = (request.POST.get('ug_qualification') or request.POST.get('ug_degree') or '').strip()
        ug_yop = (request.POST.get('ug_passed_out_year') or request.POST.get('ug_year') or '').strip()
        pg_qual = (request.POST.get('pg_qualification') or request.POST.get('pg_degree') or '').strip()
        pg_yop = (request.POST.get('pg_passed_out_year') or request.POST.get('pg_year') or '').strip()
        custom_payload['ug_qualification'] = ug_qual
        custom_payload['ug_degree'] = ug_qual
        custom_payload['ug_passed_out_year'] = ug_yop
        custom_payload['ug_year'] = ug_yop
        custom_payload['pg_qualification'] = pg_qual
        custom_payload['pg_degree'] = pg_qual
        custom_payload['pg_passed_out_year'] = pg_yop
        custom_payload['pg_year'] = pg_yop
        custom_payload['backlogs'] = (request.POST.get('backlogs') or 'No').strip()
        custom_payload['highest_education'] = (request.POST.get('highest_education') or '').strip()
        if custom_payload['highest_education']:
            custom_payload['degree'] = custom_payload['highest_education']
        elif pg_qual:
            custom_payload['degree'] = pg_qual
        elif ug_qual:
            custom_payload['degree'] = ug_qual
        if pg_yop or ug_yop:
            custom_payload['passed_out'] = pg_yop or ug_yop

        # Work Experience Section
        custom_payload['has_work_experience'] = (request.POST.get('has_work_experience') or '').strip()
        custom_payload['company_name'] = (request.POST.get('company_name') or '').strip()
        custom_payload['designation'] = (request.POST.get('designation') or '').strip()
        custom_payload['work_start_date'] = (request.POST.get('work_start_date') or '').strip()
        custom_payload['work_end_date'] = (request.POST.get('work_end_date') or '').strip()
        custom_payload['current_ctc'] = (request.POST.get('current_ctc') or '').strip()
        custom_payload['it_experience'] = (request.POST.get('it_experience') or '').strip()
        custom_payload['absconded'] = (request.POST.get('absconded') or '').strip()
        custom_payload['has_pf_uan'] = (request.POST.get('has_pf_uan') or '').strip()
        custom_payload['expected_ctc'] = (request.POST.get('expected_ctc') or '').strip()
        custom_payload['reason_for_leaving'] = (request.POST.get('reason_for_leaving') or '').strip()

        # Backward-compatible optional keys (for API / legacy callers)
        if request.POST.get('career_objective'):
            custom_payload['career_objective'] = request.POST.get('career_objective').strip()
        career_goals = request.POST.getlist('career_goals')
        if career_goals:
            custom_payload['career_goals'] = career_goals

        # Interested Courses
        interested_courses = [c.strip() for c in request.POST.getlist('interested_course') if c.strip()]
        course_other = (request.POST.get('course_other_text') or '').strip()
        if course_other:
            custom_payload['course_other_text'] = course_other
            if 'Others' in interested_courses:
                interested_courses = [f"Others ({course_other})" if c == 'Others' else c for c in interested_courses]
            else:
                interested_courses.append(f"Others ({course_other})")
        custom_payload['interested_course'] = interested_courses
        course_track = ', '.join(interested_courses) if interested_courses else (request.POST.get('course_track') or '').strip()

        # Student References
        ref1 = (request.POST.get('student_reference_1') or request.POST.get('ref_1_name') or '').strip()
        ref2 = (request.POST.get('student_reference_2') or request.POST.get('ref_2_name') or '').strip()
        custom_payload['student_reference_1'] = ref1
        custom_payload['student_reference_2'] = ref2
        if request.POST.get('ref_1_name'):
            custom_payload['reference_1_name'] = request.POST.get('ref_1_name').strip()
        if request.POST.get('ref_1_phone'):
            custom_payload['reference_1_phone'] = request.POST.get('ref_1_phone').strip()

        # Helper data dict for redisplay on validation error
        form_data_dict = dict(request.POST.items())
        form_data_dict['interested_course_list'] = interested_courses
        form_data_dict['interested_course_str'] = ' | '.join(interested_courses)'''

assert old_block in content, "old_block not found in views_walkin.py"
content = content.replace(old_block, new_block, 1)

# Also update initial_notes formatting so CRM Detail view displays all key fields
old_notes = '''        initial_notes = (
            f"Student Walk-in Enquiry Form submitted via Reception Desk QR Code.\\n"
            f"Date: {now.strftime('%d-%b-%Y %I:%M %p')}\\n"
            f"Assigned Token: #{token_number}\\n"
            f"Form: {form_config.title if form_config else 'Default'}\\n"
        )'''

new_notes = '''        summary_parts = [
            f"Student Enquiry Form – Training & Placement submitted.",
            f"Date: {now.strftime('%d-%b-%Y %I:%M %p')} | Token: #{token_number}",
        ]
        if custom_payload.get('enquiry_form_no'):
            summary_parts.append(f"Enquiry Form No: {custom_payload['enquiry_form_no']}")
        if pref_mode:
            summary_parts.append(f"Training Mode: {pref_mode}")
        if custom_payload.get('experience_type'):
            exp_str = custom_payload['experience_type']
            if custom_payload.get('years_of_experience'):
                exp_str += f" ({custom_payload['years_of_experience']} yrs)"
            summary_parts.append(f"Experience: {exp_str}")
        if course_track:
            summary_parts.append(f"Interested Courses: {course_track}")
        if custom_payload.get('has_work_experience') == 'Yes' and custom_payload.get('company_name'):
            summary_parts.append(f"Work Exp: {custom_payload['company_name']} ({custom_payload.get('designation', '')})")
        if ref1 or ref2:
            summary_parts.append(f"Student References: {', '.join(r for r in [ref1, ref2] if r)}")
        initial_notes = "\\n".join(summary_parts) + "\\n"'''

assert old_notes in content, "old_notes not found in views_walkin.py"
content = content.replace(old_notes, new_notes, 1)

with open(path_walkin, "w", encoding="utf-8") as f:
    f.write(content)
print("Successfully patched leads/views_walkin.py")
