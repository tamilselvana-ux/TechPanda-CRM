/* Compact Date Range Picker: iTechPanda CRM (vanilla JS, no dependencies)
 *
 * Markup (inside the EXISTING filter form; keep the existing parameter names):
 *   <div class="drp-root" data-from-name="date_from" data-to-name="date_to" data-autosubmit="true"
 *        data-max-date="" data-min-date="">
 *     <input type="hidden" name="date_from" value="{{ request.GET.date_from }}">
 *     <input type="hidden" name="date_to"   value="{{ request.GET.date_to }}">
 *   </div>
 * Behaviour: click field → one small calendar → 1st click = From, 2nd click = To → values set,
 * calendar closes, form submits (if data-autosubmit="true"). Escape/outside click cancels an
 * unfinished selection and keeps the previous range. "Clear" removes the date filter.
 * Values are YYYY-MM-DD (local calendar dates, no timezone shifting). Initialises every
 * .drp-root once, including ones added later via DrpInit(container).
 */
(function () {
  const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  const WD = ["Su","Mo","Tu","We","Th","Fr","Sa"];
  const pad = (n) => String(n).padStart(2, "0");
  const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const parse = (s) => { const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || ""); if (!m) return null;
    const d = new Date(+m[1], +m[2] - 1, +m[3]); return d.getMonth() === +m[2] - 1 ? d : null; };
  const same = (a, b) => a && b && a.getTime() === b.getTime();
  const fmt = (d) => d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
  const today = () => { const t = new Date(); return new Date(t.getFullYear(), t.getMonth(), t.getDate()); };
  const ICON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></svg>';

  function setup(root) {
    if (root.dataset.drpReady) return; root.dataset.drpReady = "1";
    const fromName = root.dataset.fromName || "date_from";
    const toName = root.dataset.toName || "date_to";
    const fromIn = root.querySelector(`input[name="${fromName}"]`);
    const toIn = root.querySelector(`input[name="${toName}"]`);
    if (!fromIn || !toIn) { console.warn("drp: hidden inputs not found", root); return; }
    const minD = parse(root.dataset.minDate), maxD = parse(root.dataset.maxDate);
    const label = root.dataset.label || "Date range";
    const uid = "drp" + Math.random().toString(36).slice(2, 8);

    const trigger = document.createElement("button");
    trigger.type = "button"; trigger.className = "drp-trigger";
    trigger.setAttribute("aria-haspopup", "dialog"); trigger.setAttribute("aria-expanded", "false");
    trigger.setAttribute("aria-controls", uid); trigger.dataset.testid = "date-range-trigger";
    const pop = document.createElement("div");
    pop.className = "drp-pop"; pop.id = uid; pop.setAttribute("role", "dialog"); pop.setAttribute("aria-label", label);
    pop.hidden = true;
    root.append(trigger, pop);

    let start = parse(fromIn.value), end = parse(toIn.value), hover = null, pending = null;
    let view = new Date((start || today()).getFullYear(), (start || today()).getMonth(), 1);
    let focusDate = start || today();

    const renderTrigger = () => {
      const s = parse(fromIn.value), e = parse(toIn.value);
      if (s && e) {
        trigger.innerHTML = `${ICON}<span>${fmt(s)} – ${fmt(e)}</span><span class="drp-trigger-clear" role="button" tabindex="0" aria-label="Clear date range" title="Clear date filter" style="margin-left:auto;padding:0 4px;font-size:16px;line-height:1;opacity:0.75;cursor:pointer;">&times;</span>`;
      } else if (s) {
        trigger.innerHTML = `${ICON}<span>${fmt(s)}</span><span class="drp-trigger-clear" role="button" tabindex="0" aria-label="Clear date range" title="Clear date filter" style="margin-left:auto;padding:0 4px;font-size:16px;line-height:1;opacity:0.75;cursor:pointer;">&times;</span>`;
      } else {
        trigger.innerHTML = `${ICON}<span class="drp-placeholder">Select date range</span>`;
      }
      trigger.setAttribute("aria-label", `${label}: ${s && e ? fmt(s) + " to " + fmt(e) : "not set"}`);
    };
    const disabled = (d) => (minD && d < minD) || (maxD && d > maxD);

    function render() {
      const y = view.getFullYear(), m = view.getMonth();
      const first = new Date(y, m, 1), startOff = first.getDay();
      const s = pending || start, e = pending ? (hover && hover >= pending ? hover : null) : end;
      let html = `<div class="drp-head"><button type="button" class="drp-nav" data-nav="-1" aria-label="Previous month">‹</button>
        <div class="drp-title" aria-live="polite">${MONTHS[m]} ${y}</div>
        <button type="button" class="drp-nav" data-nav="1" aria-label="Next month">›</button></div>
        <div class="drp-grid" role="grid">` + WD.map((w) => `<div class="drp-wd" role="columnheader">${w}</div>`).join("");
      for (let i = 0; i < 42; i++) {
        const d = new Date(y, m, 1 - startOff + i);
        const cls = ["drp-day"];
        if (d.getMonth() !== m) cls.push("drp-out");
        if (same(d, today())) cls.push("drp-today");
        if (s && same(d, s)) cls.push("drp-start");
        if (e && same(d, e)) cls.push("drp-end");
        if (s && e && d >= s && d <= e) cls.push("drp-in");
        const sel = (s && same(d, s)) || (e && same(d, e));
        html += `<button type="button" class="${cls.join(" ")}" data-date="${iso(d)}" tabindex="${same(d, focusDate) ? 0 : -1}"
          aria-label="${d.toDateString()}" aria-selected="${sel ? "true" : "false"}" ${disabled(d) ? "disabled" : ""}><span>${d.getDate()}</span></button>`;
      }
      const hint = pending ? "Select end date" : (start && end ? `${fmt(start)} – ${fmt(end)}` : "Select start date");
      html += `</div><div class="drp-foot"><span>${hint}</span><button type="button" class="drp-clear" data-clear ${(fromIn.value || toIn.value) ? "" : "hidden"}>Clear</button></div>`;
      pop.innerHTML = html;
    }

    function place() {
      pop.classList.remove("drp-up"); pop.style.left = "0px";
      const r = pop.getBoundingClientRect();
      if (r.bottom > window.innerHeight - 8 && trigger.getBoundingClientRect().top > r.height + 16) pop.classList.add("drp-up");
      const overflow = r.right - (window.innerWidth - 8);
      if (overflow > 0) pop.style.left = `${-overflow}px`;
    }
    function open() {
      if (!pop.hidden) return;
      start = parse(fromIn.value); end = parse(toIn.value); pending = null; hover = null;
      view = new Date((start || today()).getFullYear(), (start || today()).getMonth(), 1); focusDate = start || today();
      render(); pop.hidden = false; place();
      requestAnimationFrame(() => pop.classList.add("drp-open"));
      trigger.setAttribute("aria-expanded", "true");
      (pop.querySelector('.drp-day[tabindex="0"]') || pop.querySelector(".drp-day")).focus();
      document.addEventListener("mousedown", outside, true);
    }
    function close(returnFocus = true) {
      if (pop.hidden) return;
      pending = null; hover = null; pop.classList.remove("drp-open"); pop.hidden = true;
      trigger.setAttribute("aria-expanded", "false"); document.removeEventListener("mousedown", outside, true);
      if (returnFocus) trigger.focus();
    }
    function outside(ev) { if (!root.contains(ev.target)) close(false); }
    function commit(s, e) {
      fromIn.value = s ? iso(s) : ""; toIn.value = e ? iso(e) : "";
      const periodIn = root.querySelector('input[data-drp-period="1"]');
      if (periodIn) {
        periodIn.value = (s && e) ? (periodIn.dataset.drpPeriodVal || "custom") : "";
      }
      [fromIn, toIn].forEach((i) => i.dispatchEvent(new Event("change", { bubbles: true })));
      renderTrigger(); close();
      root.dispatchEvent(new CustomEvent("drp:change", { bubbles: true, detail: { from: fromIn.value, to: toIn.value } }));
      if (root.dataset.autosubmit === "true") {
        const f = root.closest("form");
        if (f) {
          const pageInput = f.querySelector('input[name="page"]');
          if (pageInput) pageInput.value = "1";
          (f.requestSubmit ? f.requestSubmit() : f.submit());
        }
      }
    }
    function pick(d) {
      if (!pending) { pending = d; focusDate = d; render(); focusCell(d); return; }
      let s = pending, e = d; if (e < s) [s, e] = [e, s];
      start = s; end = e; commit(s, e);
    }
    const focusCell = (d) => { const b = pop.querySelector(`.drp-day[data-date="${iso(d)}"]`); if (b) b.focus(); };
    function moveFocus(days, months) {
      const d = new Date(focusDate); if (months) d.setMonth(d.getMonth() + months); else d.setDate(d.getDate() + days);
      focusDate = d;
      if (d.getMonth() !== view.getMonth() || d.getFullYear() !== view.getFullYear()) view = new Date(d.getFullYear(), d.getMonth(), 1);
      render(); focusCell(d);
    }

    trigger.addEventListener("click", (ev) => {
      if (ev.target.closest(".drp-trigger-clear")) {
        ev.stopPropagation();
        ev.preventDefault();
        start = end = null;
        commit(null, null);
        return;
      }
      (pop.hidden ? open() : close());
    });
    pop.addEventListener("click", (ev) => {
      const nav = ev.target.closest("[data-nav]");
      if (nav) { view.setMonth(view.getMonth() + +nav.dataset.nav); render(); return; }
      if (ev.target.closest("[data-clear]")) { start = end = null; commit(null, null); return; }
      const day = ev.target.closest(".drp-day"); if (day && !day.disabled) pick(parse(day.dataset.date));
    });
    pop.addEventListener("mouseover", (ev) => {
      const day = ev.target.closest(".drp-day"); if (!pending || !day) return;
      const d = parse(day.dataset.date); if (!same(d, hover)) { hover = d; render(); }
    });
    pop.addEventListener("keydown", (ev) => {
      const k = ev.key;
      if (k === "Escape") { ev.preventDefault(); close(); return; }
      if (!ev.target.classList.contains("drp-day")) return;
      const map = { ArrowLeft: [-1], ArrowRight: [1], ArrowUp: [-7], ArrowDown: [7], PageUp: [0, -1], PageDown: [0, 1] };
      if (map[k]) { ev.preventDefault(); moveFocus(map[k][0], map[k][1]); if (pending) { hover = focusDate; render(); focusCell(focusDate); } }
      else if (k === "Enter" || k === " ") { ev.preventDefault(); if (!ev.target.disabled) pick(parse(ev.target.dataset.date)); }
    });
    window.addEventListener("resize", () => { if (!pop.hidden) place(); });
    renderTrigger();
  }

  function init(container) { (container || document).querySelectorAll(".drp-root").forEach(setup); }
  window.DrpInit = init;
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => init()); else init();
})();
