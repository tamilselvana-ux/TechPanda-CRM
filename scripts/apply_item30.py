import re

p = r"d:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\accountant\dashboard.html"
with open(p, "r", encoding="utf-8") as f:
    c = f.read()

# Replace customRangeToggleBtn
c = re.sub(
    r'<button type="button" id="customRangeToggleBtn".*?</button>',
    '{% include "partials/date_range_picker.html" with from_name="start_date" to_name="end_date" from_val=start_date to_val=end_date %}',
    c,
    flags=re.DOTALL
)

# Remove the redundant hidden accountantCustomDateInputs block
c = re.sub(
    r'<!-- Custom Date Inputs \(Revealed when Custom is clicked or active\) -->\s*<div id="accountantCustomDateInputs".*?</div>\s*</div>',
    '',
    c,
    flags=re.DOTALL
)

with open(p, "w", encoding="utf-8") as f:
    f.write(c)

print("Updated accountant/dashboard.html successfully")
