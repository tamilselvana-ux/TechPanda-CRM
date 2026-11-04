path = 'CRM_Integrated_v2/CRM/static/js/landing-page.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

target = '''    initFaqAccordion();
  });'''

replacement = '''    initFaqAccordion();
    initSmoothScrollAnchors();
  });

  // ==========================================================================
  // 6. INTERNAL ANCHOR SMOOTH SCROLL & ACTIVE PULSE
  // ==========================================================================
  function initSmoothScrollAnchors() {
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
      anchor.addEventListener('click', function (e) {
        var href = this.getAttribute('href');
        if (!href || href === '#') return;
        var targetId = href.slice(1);
        var targetEl = document.getElementById(targetId);
        if (targetEl) {
          targetEl.classList.remove('lp-target-highlight');
          void targetEl.offsetWidth;
          targetEl.classList.add('lp-target-highlight');
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }'''

if target in text:
    text = text.replace(target, replacement)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Updated landing-page.js with smooth scroll!')
else:
    print('Target not found in landing-page.js!')
