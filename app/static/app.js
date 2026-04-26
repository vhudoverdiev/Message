document.querySelectorAll('[data-confirm]').forEach((el) => {
  el.addEventListener('submit', (e) => {
    const text = el.getAttribute('data-confirm') || 'Подтвердить действие?';
    if (!window.confirm(text)) {
      e.preventDefault();
    }
  });
});

const THEME_STORAGE_KEY = 'crm-theme';
const root = document.documentElement;
const themeToggle = document.getElementById('theme-toggle-switch');

const applyTheme = (theme) => {
  root.setAttribute('data-theme', theme);
  if (themeToggle) {
    themeToggle.checked = theme === 'dark';
  }
};

const getInitialTheme = () => {
  const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (savedTheme === 'light' || savedTheme === 'dark') {
    return savedTheme;
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

applyTheme(getInitialTheme());

if (themeToggle) {
  themeToggle.addEventListener('change', () => {
    const nextTheme = themeToggle.checked ? 'dark' : 'light';
    applyTheme(nextTheme);
    window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
  });
}

document.querySelectorAll('.js-notification-tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    tab.classList.add('is-pressed');
    window.setTimeout(() => {
      tab.classList.remove('is-pressed');
    }, 180);
  });
});
