import os

css_addition = '''
/* Executive Dashboard Grid Architecture (Tier 4, Tier 3, Tier 5) */
.tp-kpi-tier-4 {
  display: grid !important;
  grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
  gap: 14px !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

.tp-kpi-tier-3 {
  display: grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 14px !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

.tp-kpi-tier-5 {
  display: grid !important;
  grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
  gap: 14px !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

.tp-filter-toolbar-tier1 {
  background: var(--tp-surface-card, #ffffff);
  border-radius: 12px;
  box-sizing: border-box;
}

/* Responsive Breakpoints */
@media (max-width: 1200px) {
  .tp-kpi-tier-5 {
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  }
}

@media (max-width: 992px) {
  .tp-kpi-tier-4 {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
  .tp-kpi-tier-3 {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
  .tp-kpi-tier-5 {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}

@media (max-width: 600px) {
  .tp-kpi-tier-4,
  .tp-kpi-tier-3,
  .tp-kpi-tier-5 {
    grid-template-columns: 1fr !important;
  }
}
'''

for css_file in [
    r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\static\css\modern-3d-cinematic.css',
    r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\static\css\crm.css'
]:
    with open(css_file, 'r', encoding='utf-8') as f:
        content = f.read()
    if '.tp-kpi-tier-4' not in content:
        content += '\n' + css_addition
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Updated', css_file)
    else:
        print('Already present in', css_file)
