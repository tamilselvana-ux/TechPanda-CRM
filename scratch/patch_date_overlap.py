import re

crm_path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\static\css\crm.css"
ds_path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\static\css\design-system.css"
m3d_path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\static\css\modern-3d-cinematic.css"

rules = """
/* Date Range & Filter Layout Stability */
.tp-compact-filter-grid {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: wrap !important;
  gap: 12px !important;
  align-items: flex-end !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

.tp-filter-field.tp-filter-field-date {
  flex: 0 0 240px !important;
  min-width: 240px !important;
  max-width: 260px !important;
  box-sizing: border-box !important;
}

.tp-filter-field.tp-filter-field-date .drp-root {
  width: 100% !important;
  display: block !important;
}

.tp-filter-field.tp-filter-field-date .drp-trigger {
  width: 100% !important;
  min-width: 100% !important;
  max-width: 100% !important;
  height: 34px !important;
  box-sizing: border-box !important;
  padding: 0 10px !important;
  font-size: 0.8125rem !important;
}

.tp-filter-field:not(.tp-filter-field-date) {
  flex: 1 1 150px !important;
  min-width: 140px !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 3px !important;
  box-sizing: border-box !important;
}

.tp-filter-action {
  flex: 0 0 auto !important;
  display: flex !important;
  gap: 8px !important;
  align-items: flex-end !important;
  margin-left: auto !important;
}
"""

with open(crm_path, "a", encoding="utf-8") as f:
    f.write(rules)

with open(ds_path, "a", encoding="utf-8") as f:
    f.write(rules)

with open(m3d_path, "a", encoding="utf-8") as f:
    f.write(rules)

print("Appended robust filter layout rules to crm.css, design-system.css, and modern-3d-cinematic.css!")
