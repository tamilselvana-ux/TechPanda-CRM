/**
 * iTechPanda CRM - Accountant Verification Image Zoom & Rotation Lightbox
 * Provides accountants high-resolution inspection tools (2x-4x zoom, 90° rotation,
 * contrast enhancement, and drag-to-pan) to verify mobile UPI transaction receipts.
 */

let lbState = {
  scale: 1,
  rotation: 0,
  contrastMode: 0, // 0: Normal, 1: High Contrast, 2: Sharp Inverted
  isDragging: false,
  startX: 0,
  startY: 0,
  translateX: 0,
  translateY: 0
};

function openProofLightbox(imgUrl, receiptNo, utrNo, studentName, amount) {
  const modal = document.getElementById('proofLightboxModal');
  const img = document.getElementById('lightboxProofImg');
  const title = document.getElementById('lightboxStudentInfo');
  const utrEl = document.getElementById('lightboxUtrText');

  if (!modal || !img) return;

  // Reset transforms
  lbState = {
    scale: 1,
    rotation: 0,
    contrastMode: 0,
    isDragging: false,
    startX: 0,
    startY: 0,
    translateX: 0,
    translateY: 0
  };

  img.src = imgUrl;
  applyLightboxTransforms();

  if (title) {
    title.innerHTML = `<strong>${studentName}</strong> &bull; Receipt: <code>${receiptNo}</code> (₹${amount})`;
  }
  if (utrEl) {
    utrEl.textContent = utrNo || 'No UTR specified';
  }

  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeProofLightbox() {
  const modal = document.getElementById('proofLightboxModal');
  if (modal) modal.style.display = 'none';
  document.body.style.overflow = '';
}

function applyLightboxTransforms() {
  const img = document.getElementById('lightboxProofImg');
  const zoomText = document.getElementById('lightboxZoomLevel');
  if (!img) return;

  // Contrast filter cycles
  let filterStr = 'none';
  if (lbState.contrastMode === 1) {
    filterStr = 'contrast(170%) brightness(105%)';
  } else if (lbState.contrastMode === 2) {
    filterStr = 'contrast(220%) grayscale(100%)';
  }

  img.style.filter = filterStr;
  img.style.transform = `translate(${lbState.translateX}px, ${lbState.translateY}px) rotate(${lbState.rotation}deg) scale(${lbState.scale})`;

  if (zoomText) {
    zoomText.textContent = `${Math.round(lbState.scale * 100)}%`;
  }
}

function zoomLightbox(factor) {
  lbState.scale = Math.min(Math.max(0.5, lbState.scale + factor), 4.5);
  applyLightboxTransforms();
}

function rotateLightbox() {
  lbState.rotation = (lbState.rotation + 90) % 360;
  applyLightboxTransforms();
}

function toggleContrastLightbox() {
  lbState.contrastMode = (lbState.contrastMode + 1) % 3;
  const btn = document.getElementById('btnToggleContrast');
  if (btn) {
    const labels = ['Normal', 'High Contrast', 'Mono B&W'];
    btn.title = `Filter: ${labels[lbState.contrastMode]}`;
  }
  applyLightboxTransforms();
}

function resetLightbox() {
  lbState.scale = 1;
  lbState.rotation = 0;
  lbState.contrastMode = 0;
  lbState.translateX = 0;
  lbState.translateY = 0;
  applyLightboxTransforms();
}

function copyLightboxUTR() {
  const utrEl = document.getElementById('lightboxUtrText');
  if (utrEl && utrEl.textContent) {
    navigator.clipboard.writeText(utrEl.textContent.trim()).then(() => {
      const copyBtn = document.getElementById('btnCopyLightboxUtr');
      if (copyBtn) {
        copyBtn.textContent = 'Copied!';
        setTimeout(() => { copyBtn.textContent = 'Copy UTR'; }, 2000);
      }
    });
  }
}

// Drag & Pan support
document.addEventListener('DOMContentLoaded', () => {
  const img = document.getElementById('lightboxProofImg');
  const viewport = document.getElementById('lightboxViewport');

  if (viewport && img) {
    viewport.addEventListener('mousedown', (e) => {
      if (lbState.scale <= 1) return;
      lbState.isDragging = true;
      lbState.startX = e.clientX - lbState.translateX;
      lbState.startY = e.clientY - lbState.translateY;
      viewport.style.cursor = 'grabbing';
    });

    window.addEventListener('mousemove', (e) => {
      if (!lbState.isDragging) return;
      lbState.translateX = e.clientX - lbState.startX;
      lbState.translateY = e.clientY - lbState.startY;
      applyLightboxTransforms();
    });

    window.addEventListener('mouseup', () => {
      lbState.isDragging = false;
      if (viewport) viewport.style.cursor = lbState.scale > 1 ? 'grab' : 'default';
    });

    // Wheel zoom
    viewport.addEventListener('wheel', (e) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.25 : -0.25;
      zoomLightbox(delta);
    }, { passive: false });
  }

  // Escape key closes modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const modal = document.getElementById('proofLightboxModal');
      if (modal && modal.style.display === 'flex') {
        closeProofLightbox();
      }
    }
  });
});
