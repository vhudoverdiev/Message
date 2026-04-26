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
const themeToggle = document.getElementById('theme-toggle');

const applyTheme = (theme) => {
  root.setAttribute('data-theme', theme);
  if (themeToggle) {
    themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
    themeToggle.setAttribute('aria-label', theme === 'dark' ? 'Включить светлую тему' : 'Включить тёмную тему');
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
  themeToggle.addEventListener('click', () => {
    const current = root.getAttribute('data-theme') || 'light';
    const nextTheme = current === 'light' ? 'dark' : 'light';
    applyTheme(nextTheme);
    window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
  });
}
