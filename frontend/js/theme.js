/**
 * AgriGrid — Keystone Day/Night Dial Theme Controller
 * Manages data-theme attribute on <html>, persists preference in localStorage under 'agrigrid_theme',
 * and synchronizes #themeToggle button aria-label.
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'agrigrid_theme';

  function getSavedTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY) || 'dark';
    } catch (e) {
      return 'dark';
    }
  }

  function applyTheme(theme) {
    if (theme === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
    updateToggleAria(theme);
  }

  function updateToggleAria(currentTheme) {
    var toggleBtn = document.getElementById('themeToggle');
    if (!toggleBtn) return;
    if (currentTheme === 'light') {
      toggleBtn.setAttribute('aria-label', 'Switch to dark mode');
      toggleBtn.setAttribute('title', 'Switch to dark mode');
    } else {
      toggleBtn.setAttribute('aria-label', 'Switch to light mode');
      toggleBtn.setAttribute('title', 'Switch to light mode');
    }
  }

  function toggleTheme() {
    var isLight = document.documentElement.getAttribute('data-theme') === 'light';
    var next = isLight ? 'dark' : 'light';
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (e) {
      // Ignore storage errors if disabled/sandboxed
    }
    applyTheme(next);
  }

  function init() {
    var theme = getSavedTheme();
    applyTheme(theme);

    var toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', toggleTheme);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
