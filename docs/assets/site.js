(() => {
  const STORAGE_KEY = 'supracraft-theme';
  const THEMES = new Set(['system', 'light', 'dark']);
  const THEME_OPTIONS = [
    {
      value: 'system',
      label: 'System',
      icon: '<svg class="theme-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3.5" y="4.5" width="17" height="12" rx="2"></rect><path d="M8 20h8M12 16.5V20"></path></svg>',
    },
    {
      value: 'light',
      label: 'Light',
      icon: '<svg class="theme-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="3.5"></circle><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M18.7 5.3l-1.4 1.4M6.7 17.3l-1.4 1.4"></path></svg>',
    },
    {
      value: 'dark',
      label: 'Dark',
      icon: '<svg class="theme-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M15.8 3.5a8.5 8.5 0 1 0 4.7 14.6 7 7 0 0 1-4.7-14.6Z"></path></svg>',
    },
  ];
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

  function syncControls(preference) {
    const fallback = document.getElementById('theme-select');
    if (fallback && fallback.value !== preference) fallback.value = preference;
    document.querySelectorAll('input[name="supracraft-theme-choice"]').forEach(control => {
      control.checked = control.value === preference;
    });
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

    syncControls(normalized);

    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      const mode = effectiveTheme(normalized);
      const value = getComputedStyle(root).getPropertyValue('--browser-theme-color').trim();
      if (value) meta.setAttribute('content', value);
      meta.dataset.effectiveTheme = mode;
    }
  }

  function upgradeThemeControl() {
    const select = document.getElementById('theme-select');
    const wrapper = select?.closest('.theme-control');
    if (!select || !wrapper || wrapper.matches('fieldset')) return null;

    const fieldset = document.createElement('fieldset');
    fieldset.className = 'theme-control theme-segmented';
    fieldset.dataset.themeControl = 'segmented';

    const legend = document.createElement('legend');
    legend.className = 'sr-only';
    legend.textContent = 'Theme';
    fieldset.append(legend);

    const options = document.createElement('span');
    options.className = 'theme-options';

    const preference = readPreference();
    for (const option of THEME_OPTIONS) {
      const label = document.createElement('label');
      label.className = 'theme-option';

      const input = document.createElement('input');
      input.type = 'radio';
      input.name = 'supracraft-theme-choice';
      input.value = option.value;
      input.setAttribute('aria-label', option.label);
      input.checked = option.value === preference;

      const face = document.createElement('span');
      face.className = 'theme-option-face';
      face.style.pointerEvents = 'none';
      face.innerHTML = option.icon;

      const tooltip = document.createElement('span');
      tooltip.className = 'theme-tooltip';
      tooltip.setAttribute('aria-hidden', 'true');
      tooltip.style.pointerEvents = 'auto';
      tooltip.textContent = option.label;
      face.append(tooltip);

      const dismissTooltip = () => {
        tooltip.style.opacity = '0';
        tooltip.style.visibility = 'hidden';
        label.dataset.tooltipDismissed = 'true';
      };
      const restoreTooltip = () => {
        tooltip.style.removeProperty('opacity');
        tooltip.style.removeProperty('visibility');
        delete label.dataset.tooltipDismissed;
      };
      input.addEventListener('focus', restoreTooltip);
      input.addEventListener('blur', restoreTooltip);
      label.addEventListener('mouseenter', restoreTooltip);
      label.addEventListener('mouseleave', () => {
        if (!label.matches(':focus-within')) restoreTooltip();
      });
      label._dismissThemeTooltip = dismissTooltip;

      label.append(input, face);
      options.append(label);
    }

    fieldset.addEventListener('keydown', event => {
      if (event.key !== 'Escape') return;
      fieldset.querySelectorAll('.theme-option').forEach(label => {
        if (label.matches(':hover') || label.matches(':focus-within')) label._dismissThemeTooltip?.();
      });
    });
    document.addEventListener('keydown', event => {
      if (event.key !== 'Escape') return;
      fieldset.querySelectorAll('.theme-option:hover').forEach(label => label._dismissThemeTooltip?.());
    });

    fieldset.append(options);
    wrapper.replaceWith(fieldset);
    return fieldset;
  }

  const initial = readPreference();
  applyPreference(initial, false);

  function bind() {
    const segmented = upgradeThemeControl();
    if (segmented) {
      segmented.querySelectorAll('input[name="supracraft-theme-choice"]').forEach(control => {
        control.addEventListener('change', () => {
          if (control.checked) applyPreference(control.value, true);
        });
      });
    } else {
      const fallback = document.getElementById('theme-select');
      if (fallback) {
        fallback.value = readPreference();
        fallback.addEventListener('change', () => applyPreference(fallback.value, true));
      }
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
