const FALLBACK_THEMES = {
  "sky-powder": {
    background: "#F1B5B5",
    secondary: "#FFF0F5",
    surface: "#FFFFFF",
    primary: "#87CEEB",
    primary_hover: "#6BB8E4",
    text_primary: "#1A1A2E",
    text_secondary: "#5C5C7A",
    text_on_primary: "#FFFFFF",
    border: "#E8D4DC",
    like: "#87CEEB",
    match: "#F78DA7",
  },
  "flamingo-powder": {
    background: "#E8A8A8",
    secondary: "#F1B5B5",
    surface: "#FFFFFF",
    primary: "#F78DA7",
    primary_hover: "#E57693",
    text_primary: "#3D2028",
    text_secondary: "#6B4049",
    text_on_primary: "#FFFFFF",
    border: "#E8A8A8",
    like: "#F78DA7",
    match: "#F78DA7",
  },
  "pink-yl": {
    background: "#F0A898",
    secondary: "#FFE8D6",
    surface: "#FFFFFF",
    primary: "#FF6B9D",
    primary_hover: "#DE4F7F",
    text_primary: "#4A2038",
    text_secondary: "#7A4A5C",
    text_on_primary: "#FFFFFF",
    border: "#F5C4B8",
    like: "#FF7B89",
    match: "#DE4F7F",
  },
};

const STORAGE = {
  guestId: "vd_guest_id",
  guestGender: "vd_guest_gender",
  guestAge: "vd_guest_age",
  accessToken: "vd_access_token",
  refreshToken: "vd_refresh_token",
  userId: "vd_user_id",
  userName: "vd_user_name",
  likesToday: "vd_likes_today",
};

const state = {
  cards: [],
  cardIndex: 0,
  reelsCards: [],
  reelsIndex: 0,
  seenCardIds: [],
  basketTab: "sent",
  isRegistered: false,
  guestId: null,
  accessToken: null,
  refreshToken: null,
  userId: null,
  userName: null,
  guestGender: null,
  guestAge: null,
  likesCount: 0,
  profile: null,
  legal: null,
  faq: null,
  selectedTopupRubles: 400,
  reportUserId: null,
  pendingVideoFile: null,
};

const THEME_PREVIEW = {
  "sky-powder": "linear-gradient(135deg, #FFF0F5 50%, #87CEEB 50%)",
  "flamingo-powder": "linear-gradient(135deg, #F1B5B5 50%, #F78DA7 50%)",
  "pink-yl":
    "linear-gradient(90deg, #FFFACD, #FFD4A8, #FFB88C, #FF9B7A, #FF7B89, #FF6B9D, #DE4F7F)",
};

const GUEST_LIKE_LIMIT = 5;
const USER_LIKE_LIMIT = 30;

function applyTheme(themeId) {
  const colors = FALLBACK_THEMES[themeId];
  if (!colors) return;
  const root = document.documentElement;
  root.style.setProperty("--bg", colors.background);
  root.style.setProperty("--surface", colors.surface);
  root.style.setProperty("--screen", colors.secondary || colors.background);
  root.style.setProperty("--primary", colors.primary);
  root.style.setProperty("--primary-hover", colors.primary_hover);
  root.style.setProperty("--text", colors.text_primary);
  root.style.setProperty("--text-secondary", colors.text_secondary);
  root.style.setProperty("--text-on-primary", colors.text_on_primary);
  root.style.setProperty("--border", colors.border);
  root.style.setProperty("--like", colors.like);
  root.style.setProperty("--match", colors.match);

  document.querySelectorAll(".theme-option").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.theme === themeId);
  });
  const preview = document.getElementById("theme-preview");
  if (preview) preview.style.background = THEME_PREVIEW[themeId] || THEME_PREVIEW["sky-powder"];
  localStorage.setItem("videodating-theme", themeId);
}

async function loadThemesFromApi() {
  try {
    const res = await fetch("/v1/config/themes");
    if (!res.ok) return;
    const data = await res.json();
    for (const theme of data.themes) {
      FALLBACK_THEMES[theme.id] = theme.colors;
    }
    applyTheme(localStorage.getItem("videodating-theme") || data.default_theme_id);
  } catch {
    /* fallback */
  }
}

function showToast(message, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.hidden = false;
  el.classList.toggle("error", isError);
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => {
    el.hidden = true;
  }, 4000);
}

function loadStateFromStorage() {
  state.guestId = localStorage.getItem(STORAGE.guestId);
  state.guestGender = localStorage.getItem(STORAGE.guestGender);
  state.guestAge = localStorage.getItem(STORAGE.guestAge);
  state.accessToken = localStorage.getItem(STORAGE.accessToken);
  state.refreshToken = localStorage.getItem(STORAGE.refreshToken);
  state.userId = localStorage.getItem(STORAGE.userId);
  state.userName = localStorage.getItem(STORAGE.userName);
  state.likesCount = parseInt(localStorage.getItem(STORAGE.likesToday) || "0", 10);
  state.isRegistered = Boolean(state.accessToken && state.userId);
}

function saveAuthTokens(data, name = null) {
  state.accessToken = data.access_token;
  state.refreshToken = data.refresh_token;
  state.userId = data.user_id;
  state.isRegistered = true;
  localStorage.setItem(STORAGE.accessToken, data.access_token);
  localStorage.setItem(STORAGE.refreshToken, data.refresh_token);
  localStorage.setItem(STORAGE.userId, data.user_id);
  if (name) {
    state.userName = name;
    localStorage.setItem(STORAGE.userName, name);
  }
}

function clearAuth() {
  state.accessToken = null;
  state.refreshToken = null;
  state.userId = null;
  state.userName = null;
  state.isRegistered = false;
  localStorage.removeItem(STORAGE.accessToken);
  localStorage.removeItem(STORAGE.refreshToken);
  localStorage.removeItem(STORAGE.userId);
  localStorage.removeItem(STORAGE.userName);
}

function saveGuestSession(guest) {
  state.guestId = guest.guest_session_id;
  state.guestGender = guest.gender;
  state.guestAge = String(guest.age);
  localStorage.setItem(STORAGE.guestId, guest.guest_session_id);
  localStorage.setItem(STORAGE.guestGender, guest.gender);
  localStorage.setItem(STORAGE.guestAge, String(guest.age));
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (state.accessToken) {
    headers.Authorization = `Bearer ${state.accessToken}`;
  } else if (state.guestId) {
    headers["X-Guest-UUID"] = state.guestId;
  }
  return headers;
}

async function api(path, options = {}) {
  const res = await fetch(`/v1${path}`, {
    ...options,
    headers: authHeaders({
      "Content-Type": "application/json",
      ...(options.headers || {}),
    }),
  });

  if (res.status === 401 && state.refreshToken) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return api(path, options);
    }
  }

  let body = null;
  const text = await res.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }

  if (!res.ok) {
    const detail = body?.detail;
    const msg = typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((d) => d.msg).join(", ") : `Ошибка ${res.status}`;
    throw new Error(msg);
  }

  return body;
}

async function tryRefresh() {
  try {
    const data = await fetch("/v1/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: state.refreshToken }),
    }).then((r) => (r.ok ? r.json() : Promise.reject()));

    saveAuthTokens(data);
    return true;
  } catch {
    clearAuth();
    updateAuthUI();
    return false;
  }
}

function updateAuthUI() {
  const actions = document.getElementById("auth-actions");

  if (state.isRegistered) {
    actions.innerHTML = `
      <span class="user-badge">${state.userName || "Аккаунт"}</span>
      <button type="button" class="btn-text danger" id="btn-logout-header">Выйти</button>
    `;
    document.getElementById("btn-logout-header")?.addEventListener("click", handleLogout);
  } else if (state.guestId) {
    actions.innerHTML = `
      <button type="button" class="btn-text" id="btn-login">Войти</button>
      <button type="button" class="btn-primary-sm" id="btn-register">Регистрация</button>
    `;
    bindAuthButtons();
  } else {
    actions.innerHTML = `
      <button type="button" class="btn-text" id="btn-login">Войти</button>
      <button type="button" class="btn-primary-sm" id="btn-register">Регистрация</button>
    `;
    bindAuthButtons();
  }

  const receivedTab = document.getElementById("basket-received-tab");
  if (receivedTab) {
    receivedTab.classList.toggle("locked", !state.isRegistered);
    receivedTab.disabled = !state.isRegistered;
  }
}

function bindAuthButtons() {
  document.getElementById("btn-login")?.addEventListener("click", () => openAuthModal("login"));
  document.getElementById("btn-register")?.addEventListener("click", () => openAuthModal("register"));
}

function showMainApp() {
  document.getElementById("screen-onboarding").classList.remove("active");
  document.getElementById("tabbar").hidden = false;
  switchScreen("screen-feed");
}

function showOnboarding() {
  document.querySelectorAll(".screen:not(#screen-onboarding)").forEach((s) => s.classList.remove("active"));
  document.getElementById("screen-onboarding").classList.add("active");
  document.getElementById("tabbar").hidden = true;
}

function switchScreen(screenId) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
  document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
  document.getElementById(screenId)?.classList.add("active");
  document.querySelector(`.tab[data-screen="${screenId}"]`)?.classList.add("active");

  if (screenId === "screen-feed") loadFeed();
  if (screenId === "screen-reels") loadReels();
  if (screenId === "screen-chats") loadChats();
  if (screenId === "screen-basket") loadBasket();
  if (screenId === "screen-profile") loadProfile();
}

function openAuthModal(mode = "login") {
  document.getElementById("modal-auth").hidden = false;
  setAuthModalTab(mode);
}

function closeAuthModal() {
  document.getElementById("modal-auth").hidden = true;
}

function setAuthModalTab(mode) {
  document.querySelectorAll(".modal-tab").forEach((t) => {
    t.classList.toggle("active", t.dataset.auth === mode);
  });
  document.getElementById("form-login").hidden = mode !== "login";
  document.getElementById("form-register").hidden = mode !== "register";
}

function renderCurrentCard() {
  const card = state.cards[state.cardIndex];
  const videoEl = document.getElementById("feed-video");
  const nameEl = document.getElementById("feed-name");
  const cityEl = document.getElementById("feed-city");
  const bioEl = document.getElementById("feed-bio");
  const counterEl = document.getElementById("feed-counter");

  if (!card) {
    videoEl.innerHTML = `<p>Анкеты закончились</p><button type="button" class="btn-secondary" id="btn-reload-feed">Обновить</button>`;
    document.getElementById("btn-reload-feed")?.addEventListener("click", () => loadFeed(true));
    nameEl.textContent = "—";
    cityEl.textContent = "—";
    if (bioEl) bioEl.textContent = "";
    counterEl.textContent = "Нет карточек";
    return;
  }

  if (card.video_profile_url) {
    videoEl.innerHTML = `<video src="${card.video_profile_url}" controls playsinline muted loop></video>`;
  } else {
    videoEl.innerHTML = `<span class="play">▶</span><p>Видео-визитка</p>`;
  }

  nameEl.textContent = `${card.name}, ${card.age}`;
  cityEl.textContent = card.city || "—";
  if (bioEl) bioEl.textContent = card.description || "";

  const limit = state.isRegistered ? USER_LIKE_LIMIT : GUEST_LIKE_LIMIT;
  counterEl.textContent = `Карточка ${state.cardIndex + 1} из ${state.cards.length} · Лайков: ${state.likesCount}/${limit}`;
}

async function sendLike(userId) {
  const result = await api("/interactions/like", {
    method: "POST",
    body: JSON.stringify({ receiver_id: userId }),
  });
  state.likesCount += 1;
  localStorage.setItem(STORAGE.likesToday, String(state.likesCount));
  state.seenCardIds.push(userId);
  if (result.is_mutual) {
    showToast("Взаимная симпатия! Чат создан");
  } else {
    showToast("Лайк отправлен");
  }
  return result;
}

function renderReelsCard() {
  const card = state.reelsCards[state.reelsIndex];
  const videoEl = document.getElementById("reels-video");
  const nameEl = document.getElementById("reels-name");
  const cityEl = document.getElementById("reels-city");
  const bioEl = document.getElementById("reels-bio");
  const counterEl = document.getElementById("reels-counter");

  if (!card) {
    videoEl.innerHTML = `<p>Лента закончилась</p><button type="button" class="btn-secondary" id="btn-reload-reels">Обновить</button>`;
    document.getElementById("btn-reload-reels")?.addEventListener("click", () => loadReels(true));
    nameEl.textContent = "—";
    cityEl.textContent = "—";
    if (bioEl) bioEl.textContent = "";
    counterEl.textContent = "";
    return;
  }

  if (card.video_profile_url) {
    videoEl.innerHTML = `<video src="${card.video_profile_url}" controls playsinline muted loop></video>`;
  } else {
    videoEl.innerHTML = `<span class="play">▶</span><p>Видео-визитка</p>`;
  }

  nameEl.textContent = `${card.name}, ${card.age}`;
  cityEl.textContent = card.city || "—";
  if (bioEl) bioEl.textContent = card.description || "";
  const limit = state.isRegistered ? USER_LIKE_LIMIT : GUEST_LIKE_LIMIT;
  counterEl.textContent = `Ролик ${state.reelsIndex + 1} из ${state.reelsCards.length} · Лайков: ${state.likesCount}/${limit}`;
}

async function loadReels(reset = false) {
  if (reset) {
    state.reelsIndex = 0;
    state.reelsCards = [];
  }
  if (state.reelsCards.length && !reset) {
    renderReelsCard();
    return;
  }
  try {
    const exclude = state.seenCardIds.join(",");
    const data = await api(`/feed/reels?limit=20${exclude ? `&exclude=${exclude}` : ""}`);
    state.reelsCards = data.cards || [];
    state.reelsIndex = 0;
    renderReelsCard();
  } catch (e) {
    document.getElementById("reels-video").innerHTML = `<p class="muted center">${e.message}</p>`;
  }
}

async function handleReelsLike() {
  const card = state.reelsCards[state.reelsIndex];
  if (!card) return;
  try {
    await sendLike(card.user_id);
    state.reelsIndex += 1;
    renderReelsCard();
  } catch (e) {
    showToast(e.message, true);
  }
}

function handleReelsSkip() {
  const card = state.reelsCards[state.reelsIndex];
  if (card) state.seenCardIds.push(card.user_id);
  state.reelsIndex += 1;
  renderReelsCard();
}

async function loadFeed(reset = false) {
  if (reset) {
    state.cardIndex = 0;
    state.cards = [];
  }
  try {
    const data = await api("/feed/cards?limit=20");
    state.cards = data.cards || [];
    if (state.cardIndex >= state.cards.length) state.cardIndex = 0;
    renderCurrentCard();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function loadChats() {
  const container = document.getElementById("chats-list");
  if (!state.isRegistered) {
    container.innerHTML = `<p class="muted center">Чаты доступны после регистрации и взаимной симпатии</p>`;
    return;
  }
  container.innerHTML = `<p class="muted center">Загрузка…</p>`;
  try {
    const data = await api("/chats");
    if (!data.chats?.length) {
      container.innerHTML = `<p class="muted center">Пока нет чатов. Лайкните анкеты — при взаимности откроется чат.</p>`;
      return;
    }
    container.innerHTML = data.chats
      .map(
        (c) => `
      <div class="list-item">
        💞 <strong>${c.partner_name}</strong>
        <span class="muted small">Кружки: вы ${c.my_circles} · они ${c.their_circles}</span>
      </div>`
      )
      .join("");
  } catch (e) {
    container.innerHTML = `<p class="muted center">${e.message}</p>`;
  }
}

async function loadBasket() {
  const container = document.getElementById("basket-list");
  container.innerHTML = `<p class="muted center">Загрузка…</p>`;
  try {
    const path = state.basketTab === "sent" ? "/basket/sent" : "/basket/received";
    const items = await api(path);
    if (!items.length) {
      container.innerHTML = `<p class="muted center">Список пуст</p>`;
      return;
    }
    container.innerHTML = items
      .map(
        (item) => `
      <div class="list-item ${item.is_mutual ? "match" : ""}">
        ${item.is_mutual ? "💞 " : "♥ "}<strong>${item.name}</strong>
        ${item.is_mutual ? '<span class="badge-match">Взаимно</span>' : ""}
      </div>`
      )
      .join("");
  } catch (e) {
    container.innerHTML = `<p class="muted center">${e.message}</p>`;
  }
}

async function loadProfile() {
  const nameEl = document.getElementById("profile-name");
  const metaEl = document.getElementById("profile-meta");
  const avatarEl = document.getElementById("profile-avatar");
  const bioEl = document.getElementById("profile-bio");
  const occEl = document.getElementById("profile-occupation");
  const balanceCard = document.getElementById("balance-card");
  const balanceEl = document.getElementById("profile-balance");
  const editBtn = document.getElementById("btn-edit-profile");
  const avatarBtn = document.getElementById("btn-edit-avatar");
  const videoBtn = document.getElementById("btn-upload-video");
  const settingsBtn = document.getElementById("btn-settings");

  if (!state.isRegistered) {
    nameEl.textContent = "Гость";
    metaEl.textContent = "Зарегистрируйтесь для профиля, баланса и видео-визитки";
    bioEl.textContent = "";
    occEl.textContent = "";
    avatarEl.style.backgroundImage = "";
    balanceCard.hidden = true;
    editBtn.hidden = true;
    avatarBtn.hidden = true;
    videoBtn.hidden = true;
    settingsBtn.hidden = true;
    document.getElementById("btn-logout").hidden = true;
    return;
  }

  document.getElementById("btn-logout").hidden = false;
  editBtn.hidden = false;
  avatarBtn.hidden = false;
  videoBtn.hidden = false;
  settingsBtn.hidden = false;
  balanceCard.hidden = false;

  try {
    const p = await api("/profile/me");
    state.profile = p;
    nameEl.textContent = p.name || "Профиль";
    occEl.textContent = p.occupation || "";
    bioEl.textContent = p.description || "Добавьте короткое описание о себе";
    bioEl.classList.toggle("empty", !p.description);
    metaEl.textContent = `${p.city || "—"} · Видео: ${p.video_status}`;
    balanceEl.textContent = `${Math.round(p.balance_rubles).toLocaleString("ru-RU")} ₽`;
    avatarEl.style.backgroundImage = p.avatar_url ? `url(${p.avatar_url})` : "";
    videoBtn.disabled = p.video_status === "processing";
    videoBtn.textContent =
      p.video_status === "processing" ? "Видео обрабатывается…" : "Загрузить видео-визитку";
    updateFreezeButton(p.profile_frozen);
  } catch (e) {
    metaEl.textContent = e.message;
  }
}

async function loadLegalConfig() {
  try {
    state.legal = await fetch("/v1/config/legal").then((r) => r.json());
  } catch {
    state.legal = null;
  }
}

function openLegalModal(kind) {
  if (!state.legal) {
    showToast("Документ загружается…", true);
    return;
  }
  const doc = kind === "terms" ? state.legal.terms : state.legal.privacy;
  document.getElementById("legal-title").textContent = doc.title;
  document.getElementById("legal-body").innerHTML = doc.sections
    .map((s) => `<article class="legal-section"><h3>${s.heading}</h3><p>${s.body}</p></article>`)
    .join("");
  document.getElementById("modal-legal").hidden = false;
}

function closeLegalModal() {
  document.getElementById("modal-legal").hidden = true;
}

function openProfileModal() {
  const p = state.profile;
  const form = document.getElementById("form-profile");
  const preview = document.getElementById("avatar-preview");
  const box = document.getElementById("avatar-upload-box");
  if (p) {
    form.name.value = p.name || "";
    form.city.value = p.city || "";
    form.occupation.value = p.occupation || "";
    form.description.value = p.description || "";
    if (p.avatar_url) {
      preview.src = p.avatar_url;
      preview.hidden = false;
      box.hidden = true;
    } else {
      preview.hidden = true;
      box.hidden = false;
    }
  }
  form.avatar.value = "";
  document.getElementById("modal-profile").hidden = false;
}

function closeProfileModal() {
  document.getElementById("modal-profile").hidden = true;
}

async function uploadAvatar(file) {
  const contentType = file.type || "image/jpeg";
  const { upload_url, object_key } = await api("/profile/avatar/upload-url", {
    method: "POST",
    body: JSON.stringify({ content_type: contentType }),
  });
  const put = await fetch(upload_url, { method: "PUT", headers: { "Content-Type": contentType }, body: file });
  if (!put.ok) throw new Error("Не удалось загрузить фото");
  return api("/profile/avatar/confirm", {
    method: "POST",
    body: JSON.stringify({ object_key }),
  });
}

async function handleProfileSubmit(e) {
  e.preventDefault();
  const form = e.target;
  try {
    await api("/profile/me", {
      method: "PATCH",
      body: JSON.stringify({
        name: form.name.value.trim(),
        city: form.city.value.trim() || null,
        occupation: form.occupation.value.trim() || null,
        description: form.description.value.trim() || null,
      }),
    });
    if (form.avatar.files?.[0]) {
      await uploadAvatar(form.avatar.files[0]);
    }
    closeProfileModal();
    showToast("Профиль обновлён");
    loadProfile();
  } catch (err) {
    showToast(err.message, true);
  }
}

function openTopupModal() {
  if (!state.isRegistered) {
    showToast("Войдите в аккаунт", true);
    return;
  }
  state.selectedTopupRubles = 400;
  document.querySelectorAll(".topup-chip").forEach((c) => c.classList.toggle("active", c.dataset.rubles === "400"));
  document.getElementById("topup-custom").value = "";
  document.getElementById("modal-topup").hidden = false;
}

function closeTopupModal() {
  document.getElementById("modal-topup").hidden = true;
}

async function handleTopupConfirm() {
  const custom = parseInt(document.getElementById("topup-custom").value, 10);
  const amount = custom > 0 ? custom : state.selectedTopupRubles;
  if (amount < 100) {
    showToast("Минимальная сумма — 100 ₽", true);
    return;
  }
  try {
    const result = await api("/balance/topup", {
      method: "POST",
      body: JSON.stringify({ amount_rubles: amount }),
    });
    showToast(`Баланс: ${result.new_balance_rubles.toLocaleString("ru-RU")} ₽`);
    closeTopupModal();
    loadProfile();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function loadFaq() {
  if (state.faq) return state.faq;
  try {
    state.faq = await fetch("/v1/support/faq").then((r) => r.json());
  } catch {
    state.faq = { items: [] };
  }
  return state.faq;
}

function showSettingsView(view) {
  document.getElementById("settings-menu").hidden = view !== "menu";
  document.getElementById("settings-view-support").hidden = view !== "support";
  document.getElementById("settings-view-faq").hidden = view !== "faq";
  document.getElementById("settings-view-terms").hidden = view !== "terms";
  const titles = { menu: "Настройки", support: "Support", faq: "FAQ", terms: "152-ФЗ" };
  document.getElementById("settings-title").textContent = titles[view] || "Настройки";
}

function updateFreezeButton(frozen) {
  const btn = document.getElementById("btn-freeze-toggle");
  if (!btn) return;
  btn.textContent = frozen ? "Разморозить профиль" : "Заморозить профиль";
  btn.dataset.frozen = frozen ? "1" : "0";
}

async function openSettingsModal() {
  if (!state.isRegistered) {
    showToast("Войдите в аккаунт", true);
    return;
  }
  if (!state.legal) await loadLegalConfig();
  showSettingsView("menu");
  document.getElementById("modal-settings").hidden = false;
}

function closeSettingsModal() {
  document.getElementById("modal-settings").hidden = true;
  showSettingsView("menu");
}

async function openSettingsSubView(view) {
  if (view === "faq") {
    const faq = await loadFaq();
    document.getElementById("settings-faq-list").innerHTML = faq.items
      .map(
        (item) =>
          `<article class="faq-item"><strong>${item.question}</strong><p>${item.answer}</p></article>`
      )
      .join("");
  }
  if (view === "terms" && state.legal) {
    const doc = state.legal.privacy;
    document.getElementById("settings-terms-body").innerHTML = `<h3 class="small">${doc.title}</h3>${doc.sections
      .map((s) => `<article class="legal-section"><h3>${s.heading}</h3><p>${s.body}</p></article>`)
      .join("")}`;
  }
  showSettingsView(view);
}

async function handleFreezeToggle() {
  const btn = document.getElementById("btn-freeze-toggle");
  const frozen = btn.dataset.frozen === "1";
  const path = frozen ? "/profile/unfreeze" : "/profile/freeze";
  const msg = frozen ? "Профиль снова виден в поиске" : "Профиль заморожен и скрыт из ленты";
  if (!frozen && !confirm("Заморозить профиль? Вас не будут видеть другие пользователи.")) return;
  try {
    const p = await api(path, { method: "POST" });
    state.profile = p;
    updateFreezeButton(p.profile_frozen);
    showToast(msg);
  } catch (err) {
    showToast(err.message, true);
  }
}

async function handleDeleteProfile() {
  if (!confirm("Удалить профиль безвозвратно? Это действие нельзя отменить.")) return;
  try {
    await api("/profile/me", { method: "DELETE" });
    closeSettingsModal();
    await handleLogout();
    showToast("Профиль удалён");
  } catch (err) {
    showToast(err.message, true);
  }
}

async function handleSupportSubmit(e) {
  e.preventDefault();
  const form = e.target;
  try {
    await api("/support/messages", {
      method: "POST",
      body: JSON.stringify({
        message: form.message.value.trim(),
        email: form.email.value.trim() || null,
      }),
    });
    form.reset();
    showToast("Сообщение отправлено в поддержку");
  } catch (err) {
    showToast(err.message, true);
  }
}

function getActiveCardUserId() {
  const feedActive = document.getElementById("screen-feed")?.classList.contains("active");
  if (feedActive) {
    return state.cards[state.cardIndex]?.user_id;
  }
  return state.reelsCards[state.reelsIndex]?.user_id;
}

function openReportModal() {
  const userId = getActiveCardUserId();
  if (!userId) {
    showToast("Нет активной анкеты", true);
    return;
  }
  state.reportUserId = userId;
  document.getElementById("form-report").reset();
  document.getElementById("modal-report").hidden = false;
}

function closeReportModal() {
  document.getElementById("modal-report").hidden = true;
  state.reportUserId = null;
}

async function handleReportSubmit(e) {
  e.preventDefault();
  if (!state.reportUserId) return;
  try {
    await api("/support/report", {
      method: "POST",
      body: JSON.stringify({
        reported_user_id: state.reportUserId,
        reason: e.target.reason.value.trim(),
      }),
    });
    closeReportModal();
    showToast("Жалоба отправлена");
  } catch (err) {
    showToast(err.message, true);
  }
}

function openVideoModal() {
  if (!state.isRegistered) {
    showToast("Войдите в аккаунт", true);
    return;
  }
  state.pendingVideoFile = null;
  document.getElementById("video-file-input").value = "";
  document.getElementById("video-upload-status").textContent = "";
  document.getElementById("btn-video-upload-confirm").disabled = true;
  document.getElementById("modal-video").hidden = false;
}

function closeVideoModal() {
  document.getElementById("modal-video").hidden = true;
  state.pendingVideoFile = null;
}

async function uploadVideoFile(file) {
  const contentType = file.type || "video/mp4";
  const { upload_url, object_key } = await api("/profile/video/upload-url", {
    method: "POST",
    body: JSON.stringify({ content_type: contentType }),
  });
  const put = await fetch(upload_url, { method: "PUT", headers: { "Content-Type": contentType }, body: file });
  if (!put.ok) throw new Error("Не удалось загрузить видео");
  await api("/profile/video/confirm", {
    method: "POST",
    body: JSON.stringify({ object_key }),
  });
}

async function handleVideoUploadConfirm() {
  if (!state.pendingVideoFile) return;
  const statusEl = document.getElementById("video-upload-status");
  const btn = document.getElementById("btn-video-upload-confirm");
  btn.disabled = true;
  statusEl.textContent = "Загрузка…";
  try {
    await uploadVideoFile(state.pendingVideoFile);
    closeVideoModal();
    showToast("Видео загружено, идёт обработка");
    loadProfile();
  } catch (err) {
    statusEl.textContent = err.message;
    btn.disabled = false;
    showToast(err.message, true);
  }
}

function handleAvatarFileChange(e) {
  const file = e.target.files?.[0];
  const preview = document.getElementById("avatar-preview");
  const box = document.getElementById("avatar-upload-box");
  if (!file) return;
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  box.hidden = true;
}

function handleVideoFileChange(e) {
  const file = e.target.files?.[0];
  state.pendingVideoFile = file || null;
  const statusEl = document.getElementById("video-upload-status");
  const btn = document.getElementById("btn-video-upload-confirm");
  if (file) {
    statusEl.textContent = file.name;
    btn.disabled = false;
  } else {
    statusEl.textContent = "";
    btn.disabled = true;
  }
}

async function handleLike() {
  const card = state.cards[state.cardIndex];
  if (!card) return;
  try {
    await sendLike(card.user_id);
    state.cardIndex += 1;
    renderCurrentCard();
  } catch (e) {
    showToast(e.message, true);
  }
}

function handleSkip() {
  const card = state.cards[state.cardIndex];
  if (card) state.seenCardIds.push(card.user_id);
  state.cardIndex += 1;
  renderCurrentCard();
}

async function handleGuestSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const gender = form.gender.value;
  const age = parseInt(form.age.value, 10);

  try {
    const guest = await fetch("/v1/session/guest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gender, age }),
    }).then(async (r) => {
      const body = await r.json();
      if (!r.ok) throw new Error(body.detail || "Ошибка сессии");
      return body;
    });

    saveGuestSession(guest);
    updateAuthUI();
    showMainApp();
    showToast("Добро пожаловать! Можно листать анкеты");
  } catch (err) {
    showToast(err.message, true);
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const form = e.target;
  try {
    const data = await fetch("/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        login: form.login.value.trim(),
        password: form.password.value,
      }),
    }).then(async (r) => {
      const body = await r.json();
      if (!r.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Ошибка входа");
      return body;
    });

    saveAuthTokens(data);
    closeAuthModal();
    updateAuthUI();
    showMainApp();
    showToast("Вы вошли в аккаунт");
    loadProfile();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const form = e.target;
  const payload = {
    name: form.name.value.trim(),
    email: form.email.value.trim(),
    password: form.password.value,
    birth_date: form.birth_date.value,
    city: form.city.value.trim(),
    accepted_terms: form.accepted_terms.checked,
  };
  if (state.guestId) payload.guest_session_id = state.guestId;

  try {
    const data = await fetch("/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(async (r) => {
      const body = await r.json();
      if (!r.ok) {
        const detail = body.detail;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }
      return body;
    });

    saveAuthTokens(data, payload.name);
    closeAuthModal();
    updateAuthUI();
    showMainApp();
    showToast("Регистрация успешна!");
    loadProfile();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function handleLogout() {
  if (state.refreshToken) {
    try {
      await fetch("/v1/auth/logout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: state.refreshToken }),
      });
    } catch {
      /* ignore */
    }
  }
  clearAuth();
  updateAuthUI();
  showToast("Вы вышли из аккаунта");
  if (state.guestId) {
    showMainApp();
  } else {
    showOnboarding();
  }
}

async function checkApi() {
  try {
    await fetch("/health");
  } catch {
    /* silent — пользователю не показываем */
  }
}

function initFormControls() {
  document.querySelectorAll(".number-stepper").forEach((wrap) => {
    const input = wrap.querySelector(".stepper-input");
    if (!input) return;
    const min = parseInt(input.min, 10) || 18;
    const max = parseInt(input.max, 10) || 99;

    wrap.querySelector('[data-stepper="minus"]')?.addEventListener("click", () => {
      const value = parseInt(input.value, 10) || min;
      if (value > min) input.value = String(value - 1);
    });
    wrap.querySelector('[data-stepper="plus"]')?.addEventListener("click", () => {
      const value = parseInt(input.value, 10) || min;
      if (value < max) input.value = String(value + 1);
    });
  });
}

function init() {
  loadStateFromStorage();
  updateAuthUI();
  bindAuthButtons();
  initFormControls();

  document.getElementById("form-guest").addEventListener("submit", handleGuestSubmit);
  document.getElementById("form-login").addEventListener("submit", handleLogin);
  document.getElementById("form-register").addEventListener("submit", handleRegister);
  document.getElementById("btn-login-onboarding")?.addEventListener("click", () => openAuthModal("login"));
  document.getElementById("modal-close").addEventListener("click", closeAuthModal);
  document.getElementById("modal-auth").addEventListener("click", (e) => {
    if (e.target.id === "modal-auth") closeAuthModal();
  });

  document.querySelectorAll(".modal-tab").forEach((tab) => {
    tab.addEventListener("click", () => setAuthModalTab(tab.dataset.auth));
  });

  document.getElementById("theme-toggle")?.addEventListener("click", (e) => {
    e.stopPropagation();
    const pop = document.getElementById("theme-popover");
    pop.hidden = !pop.hidden;
  });
  document.querySelector(".theme-picker")?.addEventListener("click", (e) => e.stopPropagation());
  document.querySelectorAll(".theme-option").forEach((btn) => {
    btn.addEventListener("click", () => {
      applyTheme(btn.dataset.theme);
      document.getElementById("theme-popover").hidden = true;
    });
  });
  document.addEventListener("click", () => {
    const pop = document.getElementById("theme-popover");
    if (pop) pop.hidden = true;
  });

  document.querySelectorAll("[data-legal]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      openLegalModal(btn.dataset.legal);
    });
  });

  document.getElementById("btn-settings")?.addEventListener("click", openSettingsModal);
  document.getElementById("modal-settings-close")?.addEventListener("click", closeSettingsModal);
  document.getElementById("modal-settings")?.addEventListener("click", (e) => {
    if (e.target.id === "modal-settings") closeSettingsModal();
  });
  document.querySelectorAll("[data-settings-view]").forEach((btn) => {
    btn.addEventListener("click", () => openSettingsSubView(btn.dataset.settingsView));
  });
  document.querySelectorAll("[data-settings-back]").forEach((btn) => {
    btn.addEventListener("click", () => showSettingsView("menu"));
  });
  document.getElementById("btn-freeze-toggle")?.addEventListener("click", handleFreezeToggle);
  document.getElementById("btn-delete-profile")?.addEventListener("click", handleDeleteProfile);
  document.getElementById("form-support")?.addEventListener("submit", handleSupportSubmit);

  document.getElementById("btn-feed-report")?.addEventListener("click", openReportModal);
  document.getElementById("btn-reels-report")?.addEventListener("click", openReportModal);
  document.getElementById("modal-report-close")?.addEventListener("click", closeReportModal);
  document.getElementById("modal-report")?.addEventListener("click", (e) => {
    if (e.target.id === "modal-report") closeReportModal();
  });
  document.getElementById("form-report")?.addEventListener("submit", handleReportSubmit);

  document.getElementById("btn-upload-video")?.addEventListener("click", openVideoModal);
  document.getElementById("modal-video-close")?.addEventListener("click", closeVideoModal);
  document.getElementById("modal-video")?.addEventListener("click", (e) => {
    if (e.target.id === "modal-video") closeVideoModal();
  });
  document.getElementById("video-file-input")?.addEventListener("change", handleVideoFileChange);
  document.getElementById("btn-video-upload-confirm")?.addEventListener("click", handleVideoUploadConfirm);
  document.querySelector('#form-profile input[name="avatar"]')?.addEventListener("change", handleAvatarFileChange);

  document.getElementById("modal-legal-close")?.addEventListener("click", closeLegalModal);
  document.getElementById("modal-legal")?.addEventListener("click", (e) => {
    if (e.target.id === "modal-legal") closeLegalModal();
  });

  document.getElementById("btn-edit-profile")?.addEventListener("click", openProfileModal);
  document.getElementById("btn-edit-avatar")?.addEventListener("click", openProfileModal);
  document.getElementById("modal-profile-close")?.addEventListener("click", closeProfileModal);
  document.getElementById("modal-profile")?.addEventListener("click", (e) => {
    if (e.target.id === "modal-profile") closeProfileModal();
  });
  document.getElementById("form-profile")?.addEventListener("submit", handleProfileSubmit);

  document.getElementById("btn-topup")?.addEventListener("click", openTopupModal);
  document.getElementById("modal-topup-close")?.addEventListener("click", closeTopupModal);
  document.getElementById("modal-topup")?.addEventListener("click", (e) => {
    if (e.target.id === "modal-topup") closeTopupModal();
  });
  document.getElementById("btn-topup-confirm")?.addEventListener("click", handleTopupConfirm);
  document.querySelectorAll(".topup-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      state.selectedTopupRubles = parseInt(chip.dataset.rubles, 10);
      document.getElementById("topup-custom").value = "";
      document.querySelectorAll(".topup-chip").forEach((c) => c.classList.toggle("active", c === chip));
    });
  });

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchScreen(tab.dataset.screen));
  });

  document.getElementById("btn-like").addEventListener("click", handleLike);
  document.getElementById("btn-skip").addEventListener("click", handleSkip);
  document.getElementById("btn-reels-like")?.addEventListener("click", handleReelsLike);
  document.getElementById("btn-reels-skip")?.addEventListener("click", handleReelsSkip);
  document.getElementById("btn-logout").addEventListener("click", handleLogout);

  document.querySelectorAll(".tab-mini").forEach((tab) => {
    tab.addEventListener("click", () => {
      if (tab.disabled) {
        showToast("Доступно после регистрации", true);
        return;
      }
      document.querySelectorAll(".tab-mini").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      state.basketTab = tab.dataset.basket;
      loadBasket();
    });
  });

  const savedTheme = localStorage.getItem("videodating-theme") || "sky-powder";
  applyTheme(savedTheme);
  loadThemesFromApi();
  loadLegalConfig();
  checkApi();

  if (state.isRegistered || state.guestId) {
    showMainApp();
  } else {
    showOnboarding();
  }
}

init();
