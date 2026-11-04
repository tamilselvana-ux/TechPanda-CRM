import re

ds_path = r"D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\static\css\design-system.css"

with open(ds_path, "r", encoding="utf-8") as f:
    ds = f.read()

ds_norm = ds.replace("\r\n", "\n")

# Replace .tp-filter-field { ... }
ds_norm = re.sub(
    r'\.tp-filter-field\s*\{[^}]*flex:\s*1\s*1\s*125px[^}]*\}',
    '''.tp-filter-field {
  flex: 1 1 145px !important;
  min-width: 135px !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 3px !important;
  box-sizing: border-box !important;
}''',
    ds_norm
)

# Replace .tp-input-compact, .tp-select-compact { ... }
ds_norm = re.sub(
    r'(\.tp-input-compact\s*,\s*)?\.tp-select-compact\s*\{[^}]*height:\s*34px[^}]*\}',
    '''.tp-input-compact {
  height: 34px !important;
  padding: 4px 10px !important;
  font-size: 0.8125rem !important;
  border-radius: var(--radius-sm, 6px) !important;
  border: 1px solid var(--border-color) !important;
  background: var(--bg-body) !important;
  color: var(--text-main) !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

select.tp-select-compact,
.form-select.tp-select-compact,
.tp-select-compact {
  height: 34px !important;
  padding: 4px 28px 4px 10px !important;
  font-size: 0.8125rem !important;
  border-radius: var(--radius-sm, 6px) !important;
  border: 1px solid var(--border-color) !important;
  background-color: var(--bg-body) !important;
  color: var(--text-main) !important;
  width: 100% !important;
  box-sizing: border-box !important;
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  appearance: none !important;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8' stroke-width='2.2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E") !important;
  background-repeat: no-repeat !important;
  background-position: right 8px center !important;
  background-size: 14px 14px !important;
  cursor: pointer !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

:root[data-theme="light"] select.tp-select-compact,
:root[data-theme="light"] .form-select.tp-select-compact,
html[data-theme="light"] select.tp-select-compact,
body.light-mode select.tp-select-compact {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23475569' stroke-width='2.2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E") !important;
}

select.tp-select-compact::-ms-expand {
  display: none !important;
}''',
    ds_norm
)

with open(ds_path, "w", encoding="utf-8") as f:
    f.write(ds_norm)

print("design-system.css updated successfully with re.sub!")
