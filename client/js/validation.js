/**
 * Form Validation Module for In-Tuned
 * Client-side validation for forms
 */

const Validation = (function() {
  'use strict';

  // Validation patterns
  const patterns = {
    email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    username: /^[a-zA-Z0-9_-]{3,30}$/,
    password: /^.{8,}$/,
    strongPassword: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/
  };

  // Error messages (localized)
  const messages = {
    en: {
      required: 'This field is required',
      email: 'Please enter a valid email address',
      username: 'Username must be 3-30 characters (letters, numbers, _ or -)',
      passwordLength: 'Password must be at least 8 characters',
      passwordStrength: 'Password must include uppercase, lowercase, number, and special character',
      passwordMatch: 'Passwords do not match',
      minLength: 'Must be at least {min} characters',
      maxLength: 'Must be no more than {max} characters',
      wordLimit: 'Maximum {max} words allowed'
    },
    es: {
      required: 'Este campo es obligatorio',
      email: 'Por favor, ingresa un email válido',
      username: 'El nombre de usuario debe tener 3-30 caracteres (letras, números, _ o -)',
      passwordLength: 'La contraseña debe tener al menos 8 caracteres',
      passwordStrength: 'La contraseña debe incluir mayúscula, minúscula, número y carácter especial',
      passwordMatch: 'Las contraseñas no coinciden',
      minLength: 'Debe tener al menos {min} caracteres',
      maxLength: 'Debe tener como máximo {max} caracteres',
      wordLimit: 'Máximo {max} palabras permitidas'
    },
    pt: {
      required: 'Este campo é obrigatório',
      email: 'Por favor, insira um email válido',
      username: 'O nome de usuário deve ter 3-30 caracteres (letras, números, _ ou -)',
      passwordLength: 'A senha deve ter pelo menos 8 caracteres',
      passwordStrength: 'A senha deve incluir maiúscula, minúscula, número e caractere especial',
      passwordMatch: 'As senhas não coincidem',
      minLength: 'Deve ter pelo menos {min} caracteres',
      maxLength: 'Deve ter no máximo {max} caracteres',
      wordLimit: 'Máximo de {max} palavras permitidas'
    }
  };

  let currentLocale = 'en';

  /**
   * Set the current locale for error messages
   * @param {string} locale - Locale code
   */
  function setLocale(locale) {
    if (messages[locale]) {
      currentLocale = locale;
    }
  }

  /**
   * Get localized message
   * @param {string} key - Message key
   * @param {Object} params - Parameters to replace
   * @returns {string} Localized message
   */
  function getMessage(key, params = {}) {
    let msg = messages[currentLocale]?.[key] || messages.en[key] || key;
    Object.entries(params).forEach(([k, v]) => {
      msg = msg.replace(`{${k}}`, v);
    });
    return msg;
  }

  /**
   * Validate a single field
   * @param {HTMLElement} field - Input element
   * @param {Object} rules - Validation rules
   * @returns {Object} { valid: boolean, error: string|null }
   */
  function validateField(field, rules = {}) {
    const value = field.value?.trim() || '';
    const errors = [];

    // Required check
    if (rules.required && !value) {
      return { valid: false, error: getMessage('required') };
    }

    // Skip other validations if empty and not required
    if (!value && !rules.required) {
      return { valid: true, error: null };
    }

    // Email validation
    if (rules.email && !patterns.email.test(value)) {
      errors.push(getMessage('email'));
    }

    // Username validation
    if (rules.username && !patterns.username.test(value)) {
      errors.push(getMessage('username'));
    }

    // Minimum length
    if (rules.minLength && value.length < rules.minLength) {
      errors.push(getMessage('minLength', { min: rules.minLength }));
    }

    // Maximum length
    if (rules.maxLength && value.length > rules.maxLength) {
      errors.push(getMessage('maxLength', { max: rules.maxLength }));
    }

    // Password strength
    if (rules.password) {
      if (!patterns.password.test(value)) {
        errors.push(getMessage('passwordLength'));
      }
      if (rules.strong && !patterns.strongPassword.test(value)) {
        errors.push(getMessage('passwordStrength'));
      }
    }

    // Word limit
    if (rules.maxWords) {
      const wordCount = value.split(/\s+/).filter(w => w).length;
      if (wordCount > rules.maxWords) {
        errors.push(getMessage('wordLimit', { max: rules.maxWords }));
      }
    }

    // Custom validation function
    if (rules.custom && typeof rules.custom === 'function') {
      const customError = rules.custom(value, field);
      if (customError) {
        errors.push(customError);
      }
    }

    return {
      valid: errors.length === 0,
      error: errors[0] || null
    };
  }

  /**
   * Validate password confirmation
   * @param {string} password - Password value
   * @param {string} confirmation - Confirmation value
   * @returns {Object} { valid: boolean, error: string|null }
   */
  function validatePasswordMatch(password, confirmation) {
    if (password !== confirmation) {
      return { valid: false, error: getMessage('passwordMatch') };
    }
    return { valid: true, error: null };
  }

  /**
   * Validate an entire form
   * @param {HTMLFormElement} form - Form element
   * @param {Object} fieldRules - Rules for each field by name
   * @returns {Object} { valid: boolean, errors: Object }
   */
  function validateForm(form, fieldRules) {
    const errors = {};
    let isValid = true;

    Object.entries(fieldRules).forEach(([fieldName, rules]) => {
      const field = form.querySelector(`[name="${fieldName}"]`) ||
                    form.querySelector(`#${fieldName}`);

      if (field) {
        const result = validateField(field, rules);
        if (!result.valid) {
          isValid = false;
          errors[fieldName] = result.error;
        }
      }
    });

    return { valid: isValid, errors };
  }

  /**
   * Show error on a field
   * @param {HTMLElement} field - Input element
   * @param {string} error - Error message
   */
  function showFieldError(field, error) {
    // Remove existing error
    clearFieldError(field);

    // Add error class
    field.classList.add('error');
    field.setAttribute('aria-invalid', 'true');

    // Create error message element
    const errorEl = document.createElement('span');
    errorEl.className = 'field-error';
    errorEl.setAttribute('role', 'alert');
    errorEl.textContent = error;

    // Insert after field
    field.parentNode.insertBefore(errorEl, field.nextSibling);
  }

  /**
   * Clear error from a field
   * @param {HTMLElement} field - Input element
   */
  function clearFieldError(field) {
    field.classList.remove('error');
    field.removeAttribute('aria-invalid');

    const errorEl = field.parentNode.querySelector('.field-error');
    if (errorEl) {
      errorEl.remove();
    }
  }

  /**
   * Setup real-time validation on a form
   * @param {HTMLFormElement} form - Form element
   * @param {Object} fieldRules - Rules for each field
   */
  function setupLiveValidation(form, fieldRules) {
    Object.entries(fieldRules).forEach(([fieldName, rules]) => {
      const field = form.querySelector(`[name="${fieldName}"]`) ||
                    form.querySelector(`#${fieldName}`);

      if (field) {
        // Validate on blur
        field.addEventListener('blur', () => {
          const result = validateField(field, rules);
          if (!result.valid) {
            showFieldError(field, result.error);
          } else {
            clearFieldError(field);
          }
        });

        // Clear error on input
        field.addEventListener('input', () => {
          clearFieldError(field);
        });
      }
    });
  }

  /**
   * Word counter for textarea
   * @param {HTMLTextAreaElement} textarea - Textarea element
   * @param {HTMLElement} counter - Counter display element
   * @param {number} maxWords - Maximum words allowed
   */
  function setupWordCounter(textarea, counter, maxWords) {
    function updateCounter() {
      const text = textarea.value.trim();
      const words = text ? text.split(/\s+/).filter(w => w).length : 0;
      const remaining = maxWords - words;

      counter.textContent = `${words} / ${maxWords}`;

      if (remaining < 0) {
        counter.classList.add('over-limit');
        textarea.classList.add('over-limit');
      } else if (remaining < 20) {
        counter.classList.add('near-limit');
        counter.classList.remove('over-limit');
        textarea.classList.remove('over-limit');
      } else {
        counter.classList.remove('near-limit', 'over-limit');
        textarea.classList.remove('over-limit');
      }
    }

    textarea.addEventListener('input', updateCounter);
    updateCounter();
  }

  return {
    setLocale,
    validateField,
    validateForm,
    validatePasswordMatch,
    showFieldError,
    clearFieldError,
    setupLiveValidation,
    setupWordCounter,
    patterns,
    getMessage
  };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Validation;
}
