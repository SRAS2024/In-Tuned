/**
 * UI Utilities Module for In-Tuned
 * Common UI helpers and state management
 */

const UI = (function() {
  'use strict';

  // DOM helper
  const $ = (id) => document.getElementById(id);
  const $$ = (selector) => document.querySelectorAll(selector);
  const $q = (selector) => document.querySelector(selector);

  /**
   * Show an element
   * @param {HTMLElement|string} el - Element or ID
   */
  function show(el) {
    const element = typeof el === 'string' ? $(el) : el;
    if (element) {
      element.classList.remove('hidden');
      element.removeAttribute('aria-hidden');
    }
  }

  /**
   * Hide an element
   * @param {HTMLElement|string} el - Element or ID
   */
  function hide(el) {
    const element = typeof el === 'string' ? $(el) : el;
    if (element) {
      element.classList.add('hidden');
      element.setAttribute('aria-hidden', 'true');
    }
  }

  /**
   * Toggle element visibility
   * @param {HTMLElement|string} el - Element or ID
   * @param {boolean} [visible] - Force visibility state
   */
  function toggle(el, visible) {
    const element = typeof el === 'string' ? $(el) : el;
    if (element) {
      const isVisible = visible ?? element.classList.contains('hidden');
      isVisible ? show(element) : hide(element);
    }
  }

  /**
   * Add class to element
   * @param {HTMLElement|string} el - Element or ID
   * @param {...string} classes - Classes to add
   */
  function addClass(el, ...classes) {
    const element = typeof el === 'string' ? $(el) : el;
    if (element) {
      element.classList.add(...classes);
    }
  }

  /**
   * Remove class from element
   * @param {HTMLElement|string} el - Element or ID
   * @param {...string} classes - Classes to remove
   */
  function removeClass(el, ...classes) {
    const element = typeof el === 'string' ? $(el) : el;
    if (element) {
      element.classList.remove(...classes);
    }
  }

  /**
   * Set text content
   * @param {HTMLElement|string} el - Element or ID
   * @param {string} text - Text content
   */
  function setText(el, text) {
    const element = typeof el === 'string' ? $(el) : el;
    if (element) {
      element.textContent = text;
    }
  }

  /**
   * Set HTML content (use with caution)
   * @param {HTMLElement|string} el - Element or ID
   * @param {string} html - HTML content
   */
  function setHTML(el, html) {
    const element = typeof el === 'string' ? $(el) : el;
    if (element) {
      element.innerHTML = html;
    }
  }

  /**
   * Escape HTML to prevent XSS
   * @param {string} text - Text to escape
   * @returns {string} Escaped HTML
   */
  function escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Show a toast notification
   * @param {string} message - Message to display
   * @param {string} type - 'success', 'error', 'warning', 'info'
   * @param {number} duration - Duration in ms
   */
  function toast(message, type = 'info', duration = 3000) {
    // Remove existing toast
    const existing = $q('.toast');
    if (existing) {
      existing.remove();
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'polite');
    toast.innerHTML = `
      <span class="toast-message">${escapeHTML(message)}</span>
      <button class="toast-close" aria-label="Close">&times;</button>
    `;

    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    // Close button
    toast.querySelector('.toast-close').addEventListener('click', () => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    });

    // Auto-remove
    if (duration > 0) {
      setTimeout(() => {
        if (toast.parentNode) {
          toast.classList.remove('show');
          setTimeout(() => toast.remove(), 300);
        }
      }, duration);
    }
  }

  /**
   * Show loading state on a button
   * @param {HTMLButtonElement} button - Button element
   * @param {boolean} loading - Loading state
   * @param {string} [loadingText] - Text to show while loading
   */
  function setButtonLoading(button, loading, loadingText = 'Loading...') {
    if (!button) return;

    if (loading) {
      button.dataset.originalText = button.textContent;
      button.textContent = loadingText;
      button.disabled = true;
      button.classList.add('loading');
    } else {
      button.textContent = button.dataset.originalText || button.textContent;
      button.disabled = false;
      button.classList.remove('loading');
    }
  }

  /**
   * Create a loading spinner
   * @param {string} size - 'small', 'medium', 'large'
   * @returns {HTMLElement} Spinner element
   */
  function createSpinner(size = 'medium') {
    const spinner = document.createElement('div');
    spinner.className = `spinner spinner-${size}`;
    spinner.setAttribute('role', 'status');
    spinner.setAttribute('aria-label', 'Loading');
    return spinner;
  }

  /**
   * Show loading overlay
   * @param {HTMLElement|string} container - Container element or ID
   */
  function showLoading(container) {
    const element = typeof container === 'string' ? $(container) : container;
    if (!element) return;

    let overlay = element.querySelector('.loading-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'loading-overlay';
      overlay.appendChild(createSpinner());
      element.appendChild(overlay);
    }
    show(overlay);
  }

  /**
   * Hide loading overlay
   * @param {HTMLElement|string} container - Container element or ID
   */
  function hideLoading(container) {
    const element = typeof container === 'string' ? $(container) : container;
    if (!element) return;

    const overlay = element.querySelector('.loading-overlay');
    if (overlay) {
      hide(overlay);
    }
  }

  /**
   * Confirm dialog
   * @param {string} message - Confirmation message
   * @param {Object} options - Dialog options
   * @returns {Promise<boolean>} User's choice
   */
  function confirm(message, options = {}) {
    return new Promise((resolve) => {
      const {
        title = 'Confirm',
        confirmText = 'Confirm',
        cancelText = 'Cancel',
        danger = false
      } = options;

      const overlay = document.createElement('div');
      overlay.className = 'confirm-overlay';
      overlay.innerHTML = `
        <div class="confirm-dialog" role="dialog" aria-modal="true">
          <h3 class="confirm-title">${escapeHTML(title)}</h3>
          <p class="confirm-message">${escapeHTML(message)}</p>
          <div class="confirm-actions">
            <button class="btn btn-secondary confirm-cancel">${escapeHTML(cancelText)}</button>
            <button class="btn ${danger ? 'btn-danger' : 'btn-primary'} confirm-ok">${escapeHTML(confirmText)}</button>
          </div>
        </div>
      `;

      document.body.appendChild(overlay);

      // Focus trap
      const dialog = overlay.querySelector('.confirm-dialog');
      const cancelBtn = overlay.querySelector('.confirm-cancel');
      const okBtn = overlay.querySelector('.confirm-ok');

      cancelBtn.focus();

      const cleanup = (result) => {
        overlay.remove();
        resolve(result);
      };

      cancelBtn.addEventListener('click', () => cleanup(false));
      okBtn.addEventListener('click', () => cleanup(true));

      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) cleanup(false);
      });

      document.addEventListener('keydown', function handler(e) {
        if (e.key === 'Escape') {
          cleanup(false);
          document.removeEventListener('keydown', handler);
        }
      });
    });
  }

  /**
   * Format date for display
   * @param {string|Date} date - Date to format
   * @param {string} locale - Locale code
   * @returns {string} Formatted date
   */
  function formatDate(date, locale = 'en') {
    try {
      const d = new Date(date);
      if (isNaN(d.getTime())) return '';

      return d.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (e) {
      return '';
    }
  }

  /**
   * Format date and time
   * @param {string|Date} date - Date to format
   * @param {string} locale - Locale code
   * @returns {string} Formatted datetime
   */
  function formatDateTime(date, locale = 'en') {
    try {
      const d = new Date(date);
      if (isNaN(d.getTime())) return '';

      return d.toLocaleString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return '';
    }
  }

  /**
   * Format relative time (e.g., "2 hours ago")
   * @param {string|Date} date - Date to format
   * @param {string} locale - Locale code
   * @returns {string} Relative time string
   */
  function formatRelativeTime(date, locale = 'en') {
    try {
      const d = new Date(date);
      if (isNaN(d.getTime())) return '';

      const now = new Date();
      const diff = now - d;
      const seconds = Math.floor(diff / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      const days = Math.floor(hours / 24);

      const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

      if (days > 30) {
        return formatDate(date, locale);
      } else if (days > 0) {
        return rtf.format(-days, 'day');
      } else if (hours > 0) {
        return rtf.format(-hours, 'hour');
      } else if (minutes > 0) {
        return rtf.format(-minutes, 'minute');
      } else {
        return rtf.format(-seconds, 'second');
      }
    } catch (e) {
      return formatDate(date, locale);
    }
  }

  /**
   * Debounce function
   * @param {Function} fn - Function to debounce
   * @param {number} delay - Delay in ms
   * @returns {Function} Debounced function
   */
  function debounce(fn, delay = 300) {
    let timeoutId;
    return function(...args) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  /**
   * Throttle function
   * @param {Function} fn - Function to throttle
   * @param {number} limit - Time limit in ms
   * @returns {Function} Throttled function
   */
  function throttle(fn, limit = 300) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        fn.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  /**
   * Setup dropdown menu
   * @param {HTMLElement} trigger - Trigger button
   * @param {HTMLElement} menu - Menu element
   */
  function setupDropdown(trigger, menu) {
    if (!trigger || !menu) return;

    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = menu.classList.contains('show');

      // Close all other dropdowns
      $$('.dropdown-menu.show').forEach(m => {
        if (m !== menu) m.classList.remove('show');
      });

      menu.classList.toggle('show', !isOpen);
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!menu.contains(e.target) && !trigger.contains(e.target)) {
        menu.classList.remove('show');
      }
    });

    // Close on escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        menu.classList.remove('show');
      }
    });
  }

  /**
   * Setup modal
   * @param {HTMLElement} modal - Modal overlay element
   * @param {Object} options - Modal options
   */
  function setupModal(modal, options = {}) {
    if (!modal) return;

    const { onClose, closeOnOverlay = true, closeOnEscape = true } = options;

    // Close button
    const closeBtn = modal.querySelector('[data-close-modal]');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        hide(modal);
        if (onClose) onClose();
      });
    }

    // Close on overlay click
    if (closeOnOverlay) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          hide(modal);
          if (onClose) onClose();
        }
      });
    }

    // Close on escape
    if (closeOnEscape) {
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
          hide(modal);
          if (onClose) onClose();
        }
      });
    }
  }

  return {
    $,
    $$,
    $q,
    show,
    hide,
    toggle,
    addClass,
    removeClass,
    setText,
    setHTML,
    escapeHTML,
    toast,
    setButtonLoading,
    createSpinner,
    showLoading,
    hideLoading,
    confirm,
    formatDate,
    formatDateTime,
    formatRelativeTime,
    debounce,
    throttle,
    setupDropdown,
    setupModal
  };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = UI;
}
