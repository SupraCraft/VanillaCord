(() => {
  const STORAGE_KEY = 'supracraft-theme';
  const THEMES = new Set(['system', 'light', 'dark']);
  const root = document.documentElement;
  const media = window.matchMedia('(prefers-color-scheme: dark)');

  function readPreference() {
    try {
      const value = window.localStorage.getItem(STORAGE_KEY);
      return THEMES.has(value) ? value : 'system';
    } catch (_) {
      return 'system';
    }
  }

  function effectiveTheme(preference) {
    if (preference === 'light' || preference === 'dark') return preference;
    return media.matches ? 'dark' : 'light';
  }

  function applyPreference(preference, persist = false) {
    const normalized = THEMES.has(preference) ? preference : 'system';
    if (normalized === 'system') {
      delete root.dataset.theme;
    } else {
      root.dataset.theme = normalized;
    }
    root.style.colorScheme = normalized === 'system' ? 'light dark' : normalized;

    if (persist) {
      try {
        window.localStorage.setItem(STORAGE_KEY, normalized);
      } catch (_) {
        // A blocked storage API must not make the site unusable.
      }
    }

    const control = document.getElementById('theme-select');
    if (control && control.value !== normalized) control.value = normalized;

    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      const mode = effectiveTheme(normalized);
      const value = getComputedStyle(root).getPropertyValue('--browser-theme-color').trim();
      if (value) meta.setAttribute('content', value);
      meta.dataset.effectiveTheme = mode;
    }
  }

  const initial = readPreference();
  applyPreference(initial, false);

  function bind() {
    const control = document.getElementById('theme-select');
    if (control) {
      control.value = readPreference();
      control.addEventListener('change', () => applyPreference(control.value, true));
    }
    applyPreference(readPreference(), false);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind, { once: true });
  } else {
    bind();
  }

  const onSystemChange = () => {
    if (readPreference() === 'system') applyPreference('system', false);
  };
  if (typeof media.addEventListener === 'function') {
    media.addEventListener('change', onSystemChange);
  } else if (typeof media.addListener === 'function') {
    media.addListener(onSystemChange);
  }
})();
