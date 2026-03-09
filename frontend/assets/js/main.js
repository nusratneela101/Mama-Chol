// MAMA CHOL VPN — Main JavaScript

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initMobileMenu();
  initLanguageSwitcher();
  initScrollAnimations();
  initSmoothScroll();
  initChatbot();
  initCounters();
  initFAQ();
  initTabs();
  initCopyButtons();
  initPaymentMethods();
});

// ============================================================
// NAVBAR — sticky scroll effect
// ============================================================
function initNavbar() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;
  const handler = () => navbar.classList.toggle('scrolled', window.scrollY > 60);
  window.addEventListener('scroll', handler, { passive: true });
  handler();
}

// ============================================================
// MOBILE MENU
// ============================================================
function initMobileMenu() {
  const hamburger = document.querySelector('.hamburger');
  const mobileMenu = document.querySelector('.mobile-menu');
  if (!hamburger || !mobileMenu) return;

  hamburger.addEventListener('click', () => {
    const isOpen = mobileMenu.classList.toggle('open');
    hamburger.setAttribute('aria-expanded', isOpen);
    const spans = hamburger.querySelectorAll('span');
    if (isOpen) {
      spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
      spans[1].style.opacity = '0';
      spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
    } else {
      spans[0].style.transform = '';
      spans[1].style.opacity = '';
      spans[2].style.transform = '';
    }
  });

  document.addEventListener('click', (e) => {
    if (!hamburger.contains(e.target) && !mobileMenu.contains(e.target)) {
      mobileMenu.classList.remove('open');
    }
  });

  mobileMenu.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => mobileMenu.classList.remove('open'));
  });
}

// ============================================================
// LANGUAGE SWITCHER
// ============================================================
function initLanguageSwitcher() {
  const currentLang = localStorage.getItem('mamachol_lang') || detectLanguage();
  applyLanguage(currentLang);

  document.querySelectorAll('.lang-selector').forEach(sel => {
    sel.value = currentLang;
    sel.addEventListener('change', (e) => {
      applyLanguage(e.target.value);
      localStorage.setItem('mamachol_lang', e.target.value);
      document.querySelectorAll('.lang-selector').forEach(s => s.value = e.target.value);
      if (window.currencyConverter && window.LANG_CURRENCY) {
        window.currencyConverter.setCurrency(window.LANG_CURRENCY[e.target.value]);
      }
    });
  });
}

function detectLanguage() {
  const browserLang = navigator.language.split('-')[0];
  const supported = ['en', 'bn', 'zh', 'hi', 'ar'];
  return supported.includes(browserLang) ? browserLang : 'en';
}

function applyLanguage(lang) {
  if (!window.TRANSLATIONS || !window.TRANSLATIONS[lang]) return;
  const t = window.TRANSLATIONS[lang];

  if (window.LANG_DIRECTIONS) {
    document.documentElement.setAttribute('dir', window.LANG_DIRECTIONS[lang] || 'ltr');
    document.documentElement.setAttribute('lang', lang);
  }

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    const value = getNestedValue(t, key);
    if (value) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = value;
      } else {
        el.textContent = value;
      }
    }
  });

  document.querySelectorAll('[data-i18n-html]').forEach(el => {
    const key = el.dataset.i18nHtml;
    const value = getNestedValue(t, key);
    if (value) el.innerHTML = value;
  });
}

function getNestedValue(obj, path) {
  return path.split('.').reduce((curr, key) => curr && curr[key], obj);
}

// ============================================================
// SCROLL ANIMATIONS
// ============================================================
function initScrollAnimations() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
  );

  document.querySelectorAll('.fade-in, .slide-up, .slide-left, .slide-right').forEach(el => {
    observer.observe(el);
  });
}

// ============================================================
// SMOOTH SCROLL
// ============================================================
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
      const href = a.getAttribute('href');
      if (href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        const offset = 80;
        const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });
}

// ============================================================
// FAQ ACCORDION
// ============================================================
function initFAQ() {
  document.querySelectorAll('.faq-question').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.faq-item');
      const isOpen = item.classList.contains('open');
      // Close all
      document.querySelectorAll('.faq-item.open').forEach(i => i.classList.remove('open'));
      // Toggle current
      if (!isOpen) item.classList.add('open');
    });
  });
}

// ============================================================
// TABS
// ============================================================
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabGroup = btn.closest('[data-tab-group]') || btn.closest('.tabs').parentElement;
      const target = btn.dataset.tab;

      tabGroup.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      tabGroup.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const pane = tabGroup.querySelector(`[data-tab-pane="${target}"]`);
      if (pane) pane.classList.add('active');
    });
  });
}

// ============================================================
// COPY BUTTONS
// ============================================================
function initCopyButtons() {
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.copyTarget;
      let text = '';
      if (target) {
        const el = document.getElementById(target);
        text = el ? el.textContent.trim() : '';
      } else {
        const codeBlock = btn.closest('.code-block');
        if (codeBlock) {
          text = codeBlock.querySelector('code, span, [data-copy-text]')?.textContent || codeBlock.textContent.replace('Copy', '').trim();
        }
      }
      if (!text) return;
      navigator.clipboard.writeText(text).then(() => {
        const original = btn.textContent;
        btn.textContent = '✓ Copied!';
        btn.style.background = 'rgba(72,187,120,0.3)';
        btn.style.color = '#48bb78';
        setTimeout(() => {
          btn.textContent = original;
          btn.style.background = '';
          btn.style.color = '';
        }, 2000);
      });
    });
  });
}

// ============================================================
// PAYMENT METHOD SELECTION
// ============================================================
function initPaymentMethods() {
  document.querySelectorAll('.payment-method').forEach(card => {
    card.addEventListener('click', () => {
      const group = card.closest('.payment-methods');
      group?.querySelectorAll('.payment-method').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      // Update hidden input if present
      const input = document.getElementById('selectedPaymentMethod');
      if (input) input.value = card.dataset.method || '';
    });
  });
}

// ============================================================
// CHATBOT WIDGET
// ============================================================
function initChatbot() {
  const toggle = document.querySelector('.chatbot-toggle');
  const chatWindow = document.querySelector('.chatbot-window');
  if (!toggle || !chatWindow) return;

  toggle.addEventListener('click', () => {
    chatWindow.classList.toggle('open');
    if (chatWindow.classList.contains('open')) {
      const input = chatWindow.querySelector('.chatbot-input');
      if (input) input.focus();
    }
  });

  const closeBtn = chatWindow.querySelector('.chatbot-close');
  if (closeBtn) closeBtn.addEventListener('click', () => chatWindow.classList.remove('open'));

  const input = chatWindow.querySelector('.chatbot-input');
  const sendBtn = chatWindow.querySelector('.chatbot-send');
  const messages = chatWindow.querySelector('.chatbot-messages');

  if (!input || !sendBtn || !messages) return;

  const sendMessage = async () => {
    const text = input.value.trim();
    if (!text) return;

    appendMessage(messages, text, 'user');
    input.value = '';

    const typing = appendTyping(messages);

    try {
      const response = await fetchAIResponse(text);
      typing.remove();
      appendMessage(messages, response, 'bot');
    } catch(e) {
      typing.remove();
      appendMessage(messages, getLocalizedFallback(), 'bot');
    }
  };

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keypress', (e) => e.key === 'Enter' && sendMessage());
}

function appendMessage(container, text, role) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.innerHTML = `<div class="message-bubble">${escapeHtml(text)}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function appendTyping(container) {
  const div = document.createElement('div');
  div.className = 'message bot typing-indicator';
  div.innerHTML = `<div class="message-bubble">⋯</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

async function fetchAIResponse(message) {
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, lang: localStorage.getItem('mamachol_lang') || 'en' }),
    signal: AbortSignal.timeout(10000)
  });
  if (!response.ok) throw new Error('API error');
  const data = await response.json();
  return data.reply;
}

function getLocalizedFallback() {
  const lang = localStorage.getItem('mamachol_lang') || 'en';
  const fallbacks = {
    en: "Hi! I'm here to help. Please contact support@mamachol.online for assistance.",
    bn: "হ্যালো! আমি সাহায্য করতে এখানে আছি। সহায়তার জন্য support@mamachol.online এ যোগাযোগ করুন।",
    zh: "你好！我在这里帮助你。请联系 support@mamachol.online 获取帮助。",
    hi: "नमस्ते! मैं यहाँ मदद के लिए हूँ। सहायता के लिए support@mamachol.online से संपर्क करें।",
    ar: "مرحباً! أنا هنا للمساعدة. يرجى التواصل مع support@mamachol.online للحصول على المساعدة."
  };
  return fallbacks[lang] || fallbacks.en;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ============================================================
// ANIMATED COUNTERS
// ============================================================
function initCounters() {
  const counters = document.querySelectorAll('[data-count]');
  if (!counters.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(el => observer.observe(el));
}

function animateCounter(el) {
  const target = parseInt(el.dataset.count, 10);
  const suffix = el.dataset.suffix || '';
  const duration = 2000;
  const start = performance.now();

  const tick = (now) => {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.floor(eased * target).toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// ============================================================
// MODAL HELPERS
// ============================================================
function openModal(id) {
  const overlay = document.getElementById(id);
  if (overlay) overlay.classList.add('active');
}

function closeModal(id) {
  const overlay = document.getElementById(id);
  if (overlay) overlay.classList.remove('active');
}

document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.classList.remove('active');
  });
});

// ============================================================
// TOAST NOTIFICATIONS
// ============================================================
function showToast(message, type = 'info', duration = 3000) {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.style.cssText = `
    position: fixed; bottom: 90px; right: 24px; z-index: 9999;
    min-width: 280px; max-width: 380px;
    animation: slideIn 0.3s ease;
    box-shadow: var(--shadow);
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

window.openModal = openModal;
window.closeModal = closeModal;
window.showToast = showToast;
