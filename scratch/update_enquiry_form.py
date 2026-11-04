path = r'D:\CRM_Integrated_v2\CRM_Integrated_v2\CRM\templates\public\student_enquiry_form.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add CSS
css_target = '''    .choice-item {
      display: inline-flex;'''

css_replacement = '''    .choice-item {
      display: inline-flex;
      padding: 4px 8px;
      border: 1px solid transparent;
      border-radius: var(--radius-sm);
      transition: all 0.2s ease;
    }
    .stacked-choice-row {
      padding: 6px 10px;
      border: 1px solid transparent;
      border-radius: var(--radius-sm);
      transition: all 0.2s ease;
    }
    .choice-item.is-selected,
    .stacked-choice-row.is-selected {
      background-color: var(--dp-green-light) !important;
      border-color: var(--dp-green) !important;
      color: var(--dp-mint-text) !important;
      font-weight: 600;
    }
    .choice-item-orig {
      display: inline-flex;'''

if css_target in text:
    text = text.replace(css_target, css_replacement, 1)
    print("Added CSS!")

# 2. Add JS
js_target = '''    // Prevent duplicate button submission
    const form = document.getElementById('studentEnquiryForm');'''

js_replacement = '''    // Immediate Visual Feedback on Radios, Checkboxes, and Selects
    function updateInputFeedback(el) {
      if (!el) return;
      const label = el.closest('label');
      if (label) {
        if (el.type === 'radio') {
          document.querySelectorAll('input[type="radio"][name="' + el.name + '"]').forEach(r => {
            const parentLabel = r.closest('label');
            if (parentLabel) parentLabel.classList.toggle('is-selected', r.checked);
          });
        } else if (el.type === 'checkbox') {
          label.classList.toggle('is-selected', el.checked);
        }
      }
    }

    document.querySelectorAll('.choice-item input, .stacked-choice-row input').forEach(input => {
      updateInputFeedback(input);
      input.addEventListener('change', function() { updateInputFeedback(this); });
      input.addEventListener('click', function() { updateInputFeedback(this); });
    });

    document.querySelectorAll('.prof-item select').forEach(sel => {
      sel.addEventListener('change', function() {
        const p = this.closest('.prof-item');
        if (p) p.classList.toggle('has-value', !!this.value);
      });
    });

    // Prevent duplicate button submission
    const form = document.getElementById('studentEnquiryForm');'''

if js_target in text:
    text = text.replace(js_target, js_replacement, 1)
    print("Added JS!")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated student_enquiry_form.html successfully!")
