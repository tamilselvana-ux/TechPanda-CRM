# Fix 1: views_walkin.py GET context includes form_data={}
p_views = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\leads\views_walkin.py"
with open(p_views, "r", encoding="utf-8") as f:
    sv = f.read()

old_get = """    if request.method == "GET":
        return render(request, 'public/student_enquiry_form.html', {
            'form_config': form_config,
            'schema': schema,
            'branding': branding,
            'branch': selected_branch,
            'branches': active_branches,
            'products': active_products,
            'token_preview': token_preview,
        })"""

new_get = """    if request.method == "GET":
        return render(request, 'public/student_enquiry_form.html', {
            'form_config': form_config,
            'schema': schema,
            'branding': branding,
            'branch': selected_branch,
            'branches': active_branches,
            'products': active_products,
            'token_preview': token_preview,
            'form_data': {},
        })"""

assert old_get in sv, "old_get not found"
sv = sv.replace(old_get, new_get, 1)
with open(p_views, "w", encoding="utf-8") as f:
    f.write(sv)

# Fix 2: template nested default lookup
p_tpl = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\public\student_enquiry_form.html"
with open(p_tpl, "r", encoding="utf-8") as f:
    st = f.read()

st = st.replace(
    'value="{{ form_data.enquiry_form_no|default:token_preview|default:\'WI-HQ-001\' }}"',
    'value="{% if form_data.enquiry_form_no %}{{ form_data.enquiry_form_no }}{% else %}{{ token_preview|default:\'WI-HQ-001\' }}{% endif %}"'
)
st = st.replace(
    'value="{{ form_data.current_address|default:form_data.home_address|default:\'\' }}"',
    'value="{{ form_data.current_address|default:\'\' }}"'
)
with open(p_tpl, "w", encoding="utf-8") as f:
    f.write(st)
print("Fixed GET form_data context and template nested lookup.")
