// CitizenShield - UI Helpers & Safe DOM Utilities (XSS-Safe)

/**
 * Creates an HTML element safely without innerHTML risk
 */
export function createElement(tag, attributes = {}, text = null, children = []) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (key === 'className' || key === 'class') {
      el.className = value;
    } else if (key.startsWith('data-')) {
      el.setAttribute(key, value);
    } else if (key.startsWith('on') && typeof value === 'function') {
      el.addEventListener(key.slice(2).toLowerCase(), value);
    } else {
      el.setAttribute(key, value);
    }
  }
  if (text !== null && text !== undefined) {
    el.textContent = text;
  }
  if (Array.isArray(children)) {
    children.forEach(child => {
      if (child) {
        if (typeof child === 'string') {
          el.appendChild(document.createTextNode(child));
        } else {
          el.appendChild(child);
        }
      }
    });
  }
  return el;
}

/**
 * Shows an accessible toast notification
 */
export function showToast(message, type = 'info', duration = 4500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = createElement('div', { id: 'toast-container', class: 'toast-container', 'aria-live': 'polite' });
    document.body.appendChild(container);
  }

  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };

  const toast = createElement('div', { class: `toast toast-${type}`, role: 'status' });
  const iconSpan = createElement('span', { class: 'toast-icon' }, icons[type] || 'ℹ');
  const msgSpan = createElement('span', { class: 'toast-message' }, message);
  const closeBtn = createElement('button', { class: 'toast-close', 'aria-label': 'Close notification' }, '×');

  closeBtn.addEventListener('click', () => {
    toast.classList.add('toast-fadeout');
    setTimeout(() => toast.remove(), 250);
  });

  toast.appendChild(iconSpan);
  toast.appendChild(msgSpan);
  toast.appendChild(closeBtn);
  container.appendChild(toast);

  setTimeout(() => {
    if (toast.parentElement) {
      toast.classList.add('toast-fadeout');
      setTimeout(() => toast.remove(), 250);
    }
  }, duration);
}

/**
 * Single-Page Application View Switcher
 */
export function showView(viewId) {
  const views = document.querySelectorAll('.app-view');
  views.forEach(view => {
    if (view.id === viewId) {
      view.classList.remove('hidden');
      view.setAttribute('aria-hidden', 'false');
    } else {
      view.classList.add('hidden');
      view.setAttribute('aria-hidden', 'true');
    }
  });

  // Update navigation link active classes
  const navLinks = document.querySelectorAll('[data-view-target]');
  navLinks.forEach(link => {
    if (link.getAttribute('data-view-target') === viewId) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Open Modal Dialog
 */
export function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
    document.body.classList.add('modal-open');
    const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (firstFocusable) firstFocusable.focus();
  }
}

/**
 * Close Modal Dialog
 */
export function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('modal-open');
  }
}

/**
 * Button Loading State Helper
 */
export function setButtonLoading(button, isLoading, loadingText = 'Processing...') {
  if (!button) return;
  if (isLoading) {
    button.dataset.originalText = button.textContent;
    button.textContent = loadingText;
    button.disabled = true;
    button.classList.add('btn-loading');
  } else {
    button.textContent = button.dataset.originalText || button.textContent;
    button.disabled = false;
    button.classList.remove('btn-loading');
  }
}

/**
 * Formats timestamps or Date objects
 */
export function formatDate(timestamp) {
  if (!timestamp) return 'Just now';
  let date;
  if (timestamp.toDate && typeof timestamp.toDate === 'function') {
    date = timestamp.toDate();
  } else if (timestamp instanceof Date) {
    date = timestamp;
  } else if (typeof timestamp === 'string' || typeof timestamp === 'number') {
    date = new Date(timestamp);
  } else {
    return 'Recently';
  }

  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  }).format(date);
}

/**
 * Returns a styled status badge element
 */
export function createStatusBadge(status) {
  const badgeClasses = {
    'Submitted': 'badge-submitted',
    'Under Review': 'badge-review',
    'In Progress': 'badge-progress',
    'Resolved': 'badge-resolved',
    'Rejected': 'badge-rejected'
  };
  const cls = badgeClasses[status] || 'badge-default';
  return createElement('span', { class: `status-badge ${cls}` }, status || 'Submitted');
}

/**
 * Returns category icon/color descriptor
 */
export function getCategoryBadge(category) {
  return createElement('span', { class: 'category-badge' }, category);
}
