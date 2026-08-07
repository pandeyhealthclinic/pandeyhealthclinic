// Pandey Health Clinic — main.js
// Vanilla JS only (per PRD tech stack). Handles:
//   1. Double-submit guard — fixes duplicate messages/bookings from
//      double-clicks or slow networks.
//   2. A top loading progress bar + soft fade transition between
//      pages, so navigation feels instant instead of a hard reload.
//   3. Scroll-reveal animation for cards.
//   4. Mobile nav toggle.
//   5. Notification bell polling + a short beep sound when new
//      notifications arrive (logged-in users only).

document.addEventListener('DOMContentLoaded', () => {
  initNavToggle();
  initScrollReveal();
  initDoubleSubmitGuard();
  initPageTransitions();
  initNotificationPolling();
  initToastAutoDismiss();
  initAutoRefresh();
  initLeadPopup();
  document.body.classList.add('page-ready');
});

// ---------------------------------------------------------------------
// 0. Toast auto-dismiss
// ---------------------------------------------------------------------
function initToastAutoDismiss() {
  document.querySelectorAll('.toast').forEach((toast, index) => {
    setTimeout(() => {
      toast.classList.add('is-leaving');
      setTimeout(() => toast.remove(), 250);
    }, 4500 + index * 300);
  });
}

// ---------------------------------------------------------------------
// 1. Double-submit guard
// ---------------------------------------------------------------------
// Root cause of "message sent twice" style bugs is almost always a
// double-click or a slow response tempting a second click before the
// first request finishes. This disables every submit button in a form
// the instant it's submitted, so a second click can't fire a second
// request. The Post/Redirect/Get pattern already used server-side
// prevents duplicates on refresh; this covers the client-side case.
function initDoubleSubmitGuard() {
  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      if (form.dataset.submitted === 'true') {
        return;
      }
      form.dataset.submitted = 'true';
      form.querySelectorAll('button[type="submit"], button:not([type])').forEach((btn) => {
        btn.disabled = true;
        btn.dataset.originalText = btn.dataset.originalText || btn.textContent;
        btn.textContent = btn.dataset.loadingText || 'Please wait...';
      });
    });
  });
}

// ---------------------------------------------------------------------
// 2. Page transitions — top progress bar + fade
// ---------------------------------------------------------------------
function initPageTransitions() {
  const bar = document.getElementById('pageProgressBar');
  if (!bar) return;

  const startProgress = () => {
    bar.classList.add('is-active');
    bar.style.transform = 'scaleX(0.7)';
  };

  document.querySelectorAll('a[href]').forEach((link) => {
    const url = link.getAttribute('href') || '';
    const isInternal = url && !url.startsWith('#') && !url.startsWith('http') && !url.startsWith('mailto:') && !url.startsWith('tel:');
    const opensNewTab = link.target === '_blank';
    if (isInternal && !opensNewTab) {
      link.addEventListener('click', (e) => {
        if (e.metaKey || e.ctrlKey) return; // let cmd/ctrl-click open in new tab normally
        startProgress();
      });
    }
  });

  document.querySelectorAll('form').forEach((form) => {
    if (form.method && form.method.toLowerCase() === 'post') {
      form.addEventListener('submit', startProgress);
    }
  });

  window.addEventListener('pageshow', () => {
    bar.classList.remove('is-active');
    bar.style.transform = 'scaleX(0)';
  });
}

// ---------------------------------------------------------------------
// 3. Scroll reveal
// ---------------------------------------------------------------------
function initScrollReveal() {
  const revealTargets = document.querySelectorAll(
    '.service-card, .why-card, .vision-card, .testimonial-card, .quick-card, .gallery-item, .medicine-card, .stat-card'
  );

  if (!('IntersectionObserver' in window) || !revealTargets.length) return;

  revealTargets.forEach((el) => {
    el.classList.add('reveal-target');
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('reveal-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );

  revealTargets.forEach((el) => observer.observe(el));
}

// ---------------------------------------------------------------------
// 4. Mobile nav toggle
// ---------------------------------------------------------------------
function initNavToggle() {
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');
  if (!navToggle || !navLinks) return;

  navToggle.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('is-open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
  });

  navLinks.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('is-open');
      navToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

// ---------------------------------------------------------------------
// 5. Notification polling + sound
// ---------------------------------------------------------------------
// The bell in the navbar carries a data-unread attribute rendered
// server-side on page load. We poll a small JSON endpoint every 20s
// and play a short beep (generated in-browser, no audio file needed)
// the moment the unread count goes up compared to the last value we
// saw — persisted in localStorage so it survives page navigation.
function initNotificationPolling() {
  const bell = document.getElementById('notificationBell');
  if (!bell) return;

  const initialCount = parseInt(bell.dataset.unread || '0', 10);
  let lastSeen = parseInt(localStorage.getItem('pandeyclinic_last_unread') || '0', 10);
  if (initialCount > lastSeen) {
    lastSeen = initialCount;
    localStorage.setItem('pandeyclinic_last_unread', String(lastSeen));
  }

  const poll = async () => {
    try {
      const resp = await fetch('/dashboard/notifications/unread-count');
      if (!resp.ok) return;
      const data = await resp.json();
      const count = data.count || 0;

      updateBellBadge(bell, count);

      if (count > lastSeen) {
        playNotificationSound();
      }
      lastSeen = count;
      localStorage.setItem('pandeyclinic_last_unread', String(lastSeen));
    } catch (err) {
      // Silent fail — polling is a nice-to-have, not critical path.
    }
  };

  setInterval(poll, 20000);
}

function updateBellBadge(bell, count) {
  let badge = bell.querySelector('.bell-badge');
  if (count > 0) {
    if (!badge) {
      badge = document.createElement('span');
      badge.className = 'bell-badge';
      bell.appendChild(badge);
    }
    badge.textContent = String(count);
  } else if (badge) {
    badge.remove();
  }
}

function playNotificationSound() {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    const ctx = new AudioContextClass();
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();

    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(880, ctx.currentTime);
    oscillator.frequency.setValueAtTime(1108, ctx.currentTime + 0.12);

    gain.gain.setValueAtTime(0.001, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.15, ctx.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);

    oscillator.connect(gain);
    gain.connect(ctx.destination);

    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.35);
  } catch (err) {
    // Web Audio not available — fail silently, it's a nice-to-have.
  }
}

// ---------------------------------------------------------------------
// 6. Silent auto-refresh
// ---------------------------------------------------------------------
// Any element with data-refresh-url gets its innerHTML silently
// replaced on an interval — no page reload, no scroll jump, no lost
// focus (we skip a refresh cycle entirely if the user is actively
// typing inside the element, e.g. never applies here since chat
// inputs live outside the refreshed container). Chat containers add
// data-refresh-chat="true" to get auto-scroll-to-bottom + a sound
// cue when new messages arrive.
function initAutoRefresh() {
  document.querySelectorAll('[data-refresh-url]').forEach((el) => {
    const url = el.dataset.refreshUrl;
    const interval = parseInt(el.dataset.refreshInterval || '5000', 10);
    const isChat = el.dataset.refreshChat === 'true';

    setInterval(async () => {
      // Don't fight the user if a toast/modal interaction is mid-flight
      // in this exact container, and don't refresh a hidden tab.
      if (document.hidden) return;

      try {
        const resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        if (!resp.ok) return;
        const html = await resp.text();
        if (!html) return;

        if (isChat) {
          const previousCount = parseInt(el.dataset.count || '0', 10);
          const wasAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;

          el.innerHTML = html;
          const newCount = el.querySelectorAll('.chat-bubble').length;
          el.dataset.count = String(newCount);

          if (newCount > previousCount) {
            playNotificationSound();
          }
          if (wasAtBottom || newCount > previousCount) {
            el.scrollTop = el.scrollHeight;
          }
        } else {
          el.innerHTML = html;
        }
      } catch (err) {
        // Silent fail — auto-refresh is a nice-to-have, not critical path.
      }
    }, interval);
  });
}

// ---------------------------------------------------------------------
// 6. Lead-capture popup — non-blocking, random-interval "ask for a
//    callback" card. Deliberately NOT a modal: no backdrop, doesn't
//    block scrolling or clicking anything else on the page, and is
//    trivial to dismiss. Shows a couple of times per browsing session
//    at random-ish intervals, then backs off — this is meant to catch
//    people who are "just looking" for cold outreach, not to nag.
// ---------------------------------------------------------------------
function initLeadPopup() {
  const popup = document.getElementById('leadPopup');
  const scrim = document.getElementById('leadPopupScrim');
  if (!popup || !scrim) return;

  // Skip entirely on pages where a popup asking "want a callback?"
  // would be intrusive or redundant (mid-task flows, auth, dashboard).
  const skipPaths = ['/auth/', '/dashboard', '/appointments/book', '/medicines/checkout', '/medicines/cart'];
  if (skipPaths.some((p) => location.pathname.startsWith(p))) return;

  const SUBMITTED_KEY = 'clinicLeadSubmittedAt';
  const DISMISS_COUNT_KEY = 'clinicLeadDismissCount'; // sessionStorage — resets each new browsing session
  const SUBMITTED_COOLDOWN_MS = 30 * 24 * 60 * 60 * 1000; // don't ask again for 30 days after they submit
  const MAX_SHOWS_PER_SESSION = 2;
  const POSITIONS = ['lead-popup--center', 'lead-popup--top', 'lead-popup--top-right', 'lead-popup--bottom-right', 'lead-popup--bottom-left'];

  // Already submitted recently? Never show again until the cooldown passes.
  const submittedAt = parseInt(localStorage.getItem(SUBMITTED_KEY) || '0', 10);
  if (submittedAt && Date.now() - submittedAt < SUBMITTED_COOLDOWN_MS) return;

  let shownCount = parseInt(sessionStorage.getItem(DISMISS_COUNT_KEY) || '0', 10);

  function randomBetween(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function applyRandomPosition() {
    POSITIONS.forEach((cls) => popup.classList.remove(cls));
    const choice = POSITIONS[randomBetween(0, POSITIONS.length - 1)];
    popup.classList.add(choice);
    // The scrim only makes sense (and looks right) behind the centered
    // variant — corner/top placements stay non-blocking with no dimming.
    scrim.dataset.pairedWithCenter = choice === 'lead-popup--center' ? 'true' : 'false';
  }

  function showPopup() {
    if (shownCount >= MAX_SHOWS_PER_SESSION) return;
    applyRandomPosition();
    popup.hidden = false;
    if (scrim.dataset.pairedWithCenter === 'true') {
      scrim.hidden = false;
      requestAnimationFrame(() => scrim.classList.add('is-visible'));
    }
    requestAnimationFrame(() => popup.classList.add('is-visible'));
  }

  function hidePopup() {
    popup.classList.remove('is-visible');
    scrim.classList.remove('is-visible');
    setTimeout(() => { popup.hidden = true; scrim.hidden = true; }, 300); // match CSS transition
  }

  function scheduleNext(delayMs) {
    setTimeout(showPopup, delayMs);
  }

  function dismiss() {
    shownCount += 1;
    sessionStorage.setItem(DISMISS_COUNT_KEY, String(shownCount));
    hidePopup();
    if (shownCount < MAX_SHOWS_PER_SESSION) {
      scheduleNext(randomBetween(60000, 120000)); // 1–2 min later, from a different random spot
    }
  }

  document.getElementById('leadPopupClose').addEventListener('click', dismiss);
  document.getElementById('leadPopupSkip').addEventListener('click', dismiss);
  scrim.addEventListener('click', dismiss); // clicking the dimmed backdrop also dismisses

  const form = document.getElementById('leadPopupForm');
  const status = document.getElementById('leadPopupStatus');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const name = form.name.value.trim();
    const phone = form.phone.value.trim();
    status.textContent = 'Sending...';
    status.className = 'lead-popup-status';

    try {
      const resp = await fetch('/leads/capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, phone, page: location.pathname }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || 'Something went wrong.');

      status.textContent = "Thanks — we'll call you back soon!";
      status.className = 'lead-popup-status lead-popup-status--ok';
      localStorage.setItem(SUBMITTED_KEY, String(Date.now()));
      setTimeout(hidePopup, 2200);
    } catch (err) {
      status.textContent = err.message || 'Could not send — please try again.';
      status.className = 'lead-popup-status lead-popup-status--error';
    }
  });

  // First appearance: near-instant so it's not missed, but still a
  // touch staggered (1.5–3.5s) so it doesn't feel like a jarring
  // flash the moment the page paints.
  scheduleNext(randomBetween(1500, 3500));
}
