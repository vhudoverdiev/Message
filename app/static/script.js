const DEFAULT_LOGIN = "vhudoverdiev";
const DEFAULT_PASSWORD = "123456";

const authOverlay = document.getElementById("authOverlay");
const appLayout = document.getElementById("appLayout");
const toast = document.getElementById("toast");

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const authTabs = document.querySelectorAll(".auth-tab");

const settingsPanel = document.getElementById("settingsPanel");
const settingsBtn = document.getElementById("settingsBtn");
const profileBtn = document.getElementById("profileBtn");

const userName = document.getElementById("userName");
const userAvatar = document.getElementById("userAvatar");
const accountLogin = document.getElementById("accountLogin");

const passwordForm = document.getElementById("passwordForm");
const descriptionForm = document.getElementById("descriptionForm");
const avatarInput = document.getElementById("avatarInput");
const avatarPreview = document.getElementById("avatarPreview");
const twoFactorForm = document.getElementById("twoFactorForm");
const twoFactorToggle = document.getElementById("twoFactorToggle");

const STORE_KEY = "message_accounts";
const USER_KEY = "message_current_user";

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("toast--visible");
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => toast.classList.remove("toast--visible"), 2200);
}

function getAccounts() {
  const raw = localStorage.getItem(STORE_KEY);
  return raw ? JSON.parse(raw) : {};
}

function saveAccounts(accounts) {
  localStorage.setItem(STORE_KEY, JSON.stringify(accounts));
}

function ensureDefaultUser() {
  const accounts = getAccounts();
  if (!accounts[DEFAULT_LOGIN]) {
    accounts[DEFAULT_LOGIN] = {
      password: DEFAULT_PASSWORD,
      description: "",
      avatar: "",
      twoFactor: false,
    };
    saveAccounts(accounts);
  }
}

function setCurrentUser(login) {
  localStorage.setItem(USER_KEY, login);
  renderUser();
}

function getCurrentUser() {
  return localStorage.getItem(USER_KEY);
}

function renderUser() {
  const login = getCurrentUser();
  const accounts = getAccounts();
  if (!login || !accounts[login]) {
    authOverlay.classList.remove("auth-overlay--hidden");
    appLayout.style.filter = "blur(4px)";
    return;
  }

  authOverlay.classList.add("auth-overlay--hidden");
  appLayout.style.filter = "none";

  const firstLetter = login[0]?.toUpperCase() || "A";
  userName.textContent = login;
  accountLogin.value = login;

  if (accounts[login].avatar) {
    userAvatar.style.backgroundImage = `url(${accounts[login].avatar})`;
    userAvatar.style.backgroundSize = "cover";
    userAvatar.textContent = "";
    avatarPreview.style.backgroundImage = `url(${accounts[login].avatar})`;
    avatarPreview.style.backgroundSize = "cover";
    avatarPreview.textContent = "";
  } else {
    userAvatar.style.backgroundImage = "none";
    avatarPreview.style.backgroundImage = "none";
    userAvatar.textContent = firstLetter;
    avatarPreview.textContent = firstLetter;
  }

  document.getElementById("profileDescription").value = accounts[login].description || "";
  twoFactorToggle.checked = Boolean(accounts[login].twoFactor);
}

function toggleSettings() {
  settingsPanel.classList.toggle("settings-panel--open");
}

settingsBtn.addEventListener("click", toggleSettings);
profileBtn.addEventListener("click", toggleSettings);

authTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    authTabs.forEach((button) => button.classList.remove("auth-tab--active"));
    tab.classList.add("auth-tab--active");

    const isLogin = tab.dataset.tab === "login";
    loginForm.classList.toggle("auth-form--active", isLogin);
    registerForm.classList.toggle("auth-form--active", !isLogin);
  });
});

loginForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const login = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value;

  const accounts = getAccounts();
  if (!accounts[login] || accounts[login].password !== password) {
    showToast("Неверный логин или пароль");
    return;
  }

  setCurrentUser(login);
  showToast("Вы успешно вошли");
  loginForm.reset();
});

registerForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const login = document.getElementById("registerUsername").value.trim();
  const password = document.getElementById("registerPassword").value;

  if (!login || password.length < 6) {
    showToast("Пароль должен быть не короче 6 символов");
    return;
  }

  const accounts = getAccounts();
  if (accounts[login]) {
    showToast("Такой логин уже существует");
    return;
  }

  accounts[login] = {
    password,
    description: "",
    avatar: "",
    twoFactor: false,
  };
  saveAccounts(accounts);
  setCurrentUser(login);
  showToast("Аккаунт создан");
  registerForm.reset();
});

passwordForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const login = getCurrentUser();
  const accounts = getAccounts();
  const newPassword = document.getElementById("newPassword").value;

  if (!login || !accounts[login]) return;

  accounts[login].password = newPassword;
  saveAccounts(accounts);
  showToast("Пароль обновлен");
  passwordForm.reset();
});

descriptionForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const login = getCurrentUser();
  const accounts = getAccounts();
  const description = document.getElementById("profileDescription").value.trim();

  if (!login || !accounts[login]) return;

  accounts[login].description = description;
  saveAccounts(accounts);
  showToast("Описание профиля сохранено");
});

avatarInput.addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = () => {
    const login = getCurrentUser();
    const accounts = getAccounts();
    if (!login || !accounts[login]) return;

    accounts[login].avatar = String(reader.result);
    saveAccounts(accounts);
    renderUser();
    showToast("Аватар обновлен");
  };
  reader.readAsDataURL(file);
});

twoFactorForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const login = getCurrentUser();
  const accounts = getAccounts();
  if (!login || !accounts[login]) return;

  accounts[login].twoFactor = twoFactorToggle.checked;
  saveAccounts(accounts);
  showToast(twoFactorToggle.checked ? "2FA включена" : "2FA выключена");
});

ensureDefaultUser();
renderUser();
