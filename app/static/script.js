const STORE_KEY = "massage_crm_users";
const CURRENT_KEY = "massage_crm_current";

const defaultMessages = [
  { account: "vk.com/shop", from: "Ирина", text: "Здравствуйте, подскажите по доставке?", time: "09:40" },
  { account: "vk.com/agency", from: "Павел", text: "Есть вопрос по тарифу CRM.", time: "10:15" },
  { account: "vk.com/brand", from: "Мария", text: "Когда будет обратный звонок?", time: "11:02" },
];

const authOverlay = document.getElementById("authOverlay");
const layout = document.getElementById("layout");
const toast = document.getElementById("toast");

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const authTabs = document.querySelectorAll("[data-auth-tab]");
const menuItems = document.querySelectorAll(".menu-item");

const messagesList = document.getElementById("messagesList");
const groupForm = document.getElementById("groupForm");
const groupList = document.getElementById("groupList");
const vkForm = document.getElementById("vkForm");
const vkList = document.getElementById("vkList");
const profileForm = document.getElementById("profileForm");
const securityForm = document.getElementById("securityForm");

const sidebarName = document.getElementById("sidebarName");
const sidebarAvatar = document.getElementById("sidebarAvatar");
const logoutBtn = document.getElementById("logoutBtn");
const messageSearch = document.getElementById("messageSearch");

function notify(text) {
  toast.textContent = text;
  toast.classList.add("toast--visible");
  clearTimeout(window.toastTimer);
  window.toastTimer = setTimeout(() => toast.classList.remove("toast--visible"), 2300);
}

function getUsers() {
  const raw = localStorage.getItem(STORE_KEY);
  return raw ? JSON.parse(raw) : {};
}

function saveUsers(users) {
  localStorage.setItem(STORE_KEY, JSON.stringify(users));
}

function currentUserLogin() {
  return localStorage.getItem(CURRENT_KEY);
}

function ensureDefaults() {
  const users = getUsers();
  if (!users.admin) {
    users.admin = {
      password: "123456",
      displayName: "Администратор",
      about: "Главный оператор",
      twoFactor: false,
      groups: [
        { name: "Продажи", description: "Диалоги по новым заявкам" },
        { name: "Поддержка", description: "Помощь клиентам" },
      ],
      vkAccounts: [
        { name: "vk.com/shop", token: "***" },
        { name: "vk.com/agency", token: "***" },
      ],
      messages: defaultMessages,
    };
  }
  saveUsers(users);
}

function openApp(login) {
  localStorage.setItem(CURRENT_KEY, login);
  authOverlay.classList.add("auth-overlay--hidden");
  layout.style.filter = "none";
  render();
}

function closeApp() {
  localStorage.removeItem(CURRENT_KEY);
  authOverlay.classList.remove("auth-overlay--hidden");
  layout.style.filter = "blur(5px)";
}

function renderMessages(items) {
  messagesList.innerHTML = "";
  if (!items.length) {
    messagesList.innerHTML = '<div class="panel">Сообщений пока нет.</div>';
    return;
  }

  items.forEach((msg) => {
    const card = document.createElement("article");
    card.className = "message-card";
    card.innerHTML = `
      <div class="message-meta">${msg.account} • ${msg.time}</div>
      <strong>${msg.from}</strong>
      <p>${msg.text}</p>
    `;
    messagesList.append(card);
  });
}

function renderList(listRoot, items, emptyText, formatter) {
  listRoot.innerHTML = "";
  if (!items.length) {
    listRoot.innerHTML = `<div class="panel">${emptyText}</div>`;
    return;
  }

  items.forEach((item, index) => {
    const row = document.createElement("div");
    row.className = "list-item";
    row.innerHTML = `
      <div>${formatter(item)}</div>
      <button class="btn btn--ghost" data-index="${index}">Удалить</button>
    `;
    listRoot.append(row);
  });
}

function render() {
  const login = currentUserLogin();
  const users = getUsers();

  if (!login || !users[login]) {
    closeApp();
    return;
  }

  const user = users[login];
  sidebarName.textContent = user.displayName || login;
  sidebarAvatar.textContent = (user.displayName || login)[0].toUpperCase();

  document.getElementById("displayName").value = user.displayName || "";
  document.getElementById("about").value = user.about || "";
  document.getElementById("twoFactor").checked = Boolean(user.twoFactor);

  renderMessages(user.messages || []);
  renderList(groupList, user.groups || [], "Групп пока нет.", (g) => `<strong>${g.name}</strong><div>${g.description || "Без описания"}</div>`);
  renderList(vkList, user.vkAccounts || [], "VK аккаунты пока не подключены.", (a) => `<strong>${a.name}</strong><div>Токен: ${a.token.slice(0, 3)}***</div>`);
}

function saveCurrent(mutator) {
  const login = currentUserLogin();
  const users = getUsers();
  if (!login || !users[login]) return;

  mutator(users[login]);
  saveUsers(users);
  render();
}

authTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    authTabs.forEach((btn) => btn.classList.remove("auth-tab--active"));
    tab.classList.add("auth-tab--active");

    const isLogin = tab.dataset.authTab === "login";
    loginForm.classList.toggle("auth-form--active", isLogin);
    registerForm.classList.toggle("auth-form--active", !isLogin);
  });
});

loginForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const login = document.getElementById("login").value.trim();
  const password = document.getElementById("password").value;
  const users = getUsers();

  if (!users[login] || users[login].password !== password) {
    notify("Неверный логин или пароль");
    return;
  }

  openApp(login);
  loginForm.reset();
  notify("Вход выполнен");
});

registerForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const login = document.getElementById("newLogin").value.trim();
  const password = document.getElementById("newPassword").value;
  const users = getUsers();

  if (!login || password.length < 6) {
    notify("Введите логин и пароль от 6 символов");
    return;
  }

  if (users[login]) {
    notify("Пользователь уже существует");
    return;
  }

  users[login] = {
    password,
    displayName: login,
    about: "",
    twoFactor: false,
    groups: [],
    vkAccounts: [],
    messages: [],
  };

  saveUsers(users);
  openApp(login);
  registerForm.reset();
  notify("Аккаунт создан");
});

menuItems.forEach((item) => {
  item.addEventListener("click", () => {
    menuItems.forEach((btn) => btn.classList.remove("menu-item--active"));
    item.classList.add("menu-item--active");

    const target = item.dataset.view;
    document.querySelectorAll(".view").forEach((view) => view.classList.remove("view--active"));
    document.getElementById(`view-${target}`).classList.add("view--active");
  });
});

groupForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const name = document.getElementById("groupName").value.trim();
  const description = document.getElementById("groupDescription").value.trim();

  if (!name) return;

  saveCurrent((user) => {
    user.groups.push({ name, description });
  });
  groupForm.reset();
  notify("Группа добавлена");
});

vkForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const name = document.getElementById("vkName").value.trim();
  const token = document.getElementById("vkToken").value.trim();

  if (!name || !token) return;

  saveCurrent((user) => {
    user.vkAccounts.push({ name, token });
  });
  vkForm.reset();
  notify("VK аккаунт подключен");
});

groupList.addEventListener("click", (e) => {
  const button = e.target.closest("button[data-index]");
  if (!button) return;
  const index = Number(button.dataset.index);

  saveCurrent((user) => {
    user.groups.splice(index, 1);
  });
  notify("Группа удалена");
});

vkList.addEventListener("click", (e) => {
  const button = e.target.closest("button[data-index]");
  if (!button) return;
  const index = Number(button.dataset.index);

  saveCurrent((user) => {
    user.vkAccounts.splice(index, 1);
  });
  notify("VK аккаунт удален");
});

profileForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const displayName = document.getElementById("displayName").value.trim();
  const about = document.getElementById("about").value.trim();

  saveCurrent((user) => {
    user.displayName = displayName || "Оператор";
    user.about = about;
  });
  notify("Профиль обновлен");
});

securityForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const newPass = document.getElementById("newPass").value;
  const twoFactor = document.getElementById("twoFactor").checked;

  saveCurrent((user) => {
    user.password = newPass;
    user.twoFactor = twoFactor;
  });

  securityForm.reset();
  document.getElementById("twoFactor").checked = twoFactor;
  notify("Настройки безопасности сохранены");
});

logoutBtn.addEventListener("click", () => {
  closeApp();
  notify("Вы вышли из аккаунта");
});

messageSearch.addEventListener("input", () => {
  const query = messageSearch.value.trim().toLowerCase();
  const login = currentUserLogin();
  const users = getUsers();
  if (!login || !users[login]) return;

  const allMessages = users[login].messages || [];
  const filtered = !query
    ? allMessages
    : allMessages.filter((msg) =>
      `${msg.account} ${msg.from} ${msg.text}`.toLowerCase().includes(query));

  renderMessages(filtered);
});

ensureDefaults();
if (currentUserLogin()) {
  authOverlay.classList.add("auth-overlay--hidden");
} else {
  layout.style.filter = "blur(5px)";
}
render();
