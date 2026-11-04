/**
 * iTechPanda CRM - 3D CINEMATIC INTERACTIVE ENGINE
 * Lightweight, 60fps card specular reflection and perspective tilt micro-interactions
 */
(function () {
  'use strict';

  // Check user preference for reduced motion
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return;
  }

  // Only enable interactive 3D tilt on devices that support hover (non-touch)
  if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    return;
  }

  function init3DTilt() {
    const cards = document.querySelectorAll('.kpi-card, .tp-interactive-card, [data-3d-tilt="true"]');
    if (!cards.length) return;

    cards.forEach((card) => {
      if (card.dataset.tiltReady) return;
      card.dataset.tiltReady = 'true';

      let rect = card.getBoundingClientRect();
      let rafId = null;

      function updateRect() {
        rect = card.getBoundingClientRect();
      }

      window.addEventListener('resize', updateRect, { passive: true });
      window.addEventListener('scroll', updateRect, { passive: true });

      card.addEventListener('mousemove', (e) => {
        if (rafId) cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(() => {
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;

          // Set CSS custom properties for specular highlight
          card.style.setProperty('--mouse-x', `${x}px`);
          card.style.setProperty('--mouse-y', `${y}px`);

          // Subtle 3D perspective tilt (-4deg to +4deg max)
          const centerX = rect.width / 2;
          const centerY = rect.height / 2;
          const rotateX = ((y - centerY) / centerY) * -3.5;
          const rotateY = ((x - centerX) / centerX) * 3.5;

          card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-3px) scale3d(1.01, 1.01, 1.01)`;
        });
      });

      card.addEventListener('mouseleave', () => {
        if (rafId) cancelAnimationFrame(rafId);
        card.style.transform = '';
        card.style.removeProperty('--mouse-x');
        card.style.removeProperty('--mouse-y');
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init3DTilt);
  } else {
    init3DTilt();
  }

  // Expose global init function for dynamic page updates
  window.iTechPanda3D = {
    init: init3DTilt
  };
})();
