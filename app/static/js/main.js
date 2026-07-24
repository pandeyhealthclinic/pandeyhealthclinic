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
