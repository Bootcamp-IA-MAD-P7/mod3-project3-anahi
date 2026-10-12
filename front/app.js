const API = "http://localhost:8000";
const TOKEN_KEY = "sayless_token";
const EMAIL_KEY = "sayless_email";
const PROVIDER = "groq";
const MODEL = "openai/gpt-oss-120b";
const LONGFORM_PLATFORMS = ["medium", "substack"];
const CITATIONS_PLATFORMS = ["medium", "substack"];
const PLATFORM_URLS = {
  linkedin: "https://www.linkedin.com",
  instagram: "https://www.instagram.com",
  medium: "https://medium.com",
  substack: "https://substack.com",
};
const PLATFORM_NAMES = {
  linkedin: "LinkedIn",
  instagram: "Instagram",
  medium: "Medium",
  substack: "Substack",
};
const PLATFORM_ICONS = {
  linkedin:
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5A2.5 2.5 0 1 1 0 3.5a2.5 2.5 0 0 1 4.98 0zM.5 8.5h4.9V24H.5V8.5zM8.5 8.5h4.7v2.1h.07c.65-1.2 2.25-2.5 4.63-2.5 4.95 0 5.87 3.15 5.87 7.2V24h-4.9v-7.4c0-1.76-.03-4.03-2.46-4.03-2.46 0-2.84 1.92-2.84 3.9V24H8.5V8.5z" /></svg>',
  instagram:
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.16c3.2 0 3.58.01 4.85.07 3.25.15 4.77 1.69 4.92 4.92.06 1.27.07 1.65.07 4.85s-.01 3.58-.07 4.85c-.15 3.23-1.66 4.77-4.92 4.92-1.27.06-1.64.07-4.85.07s-3.58-.01-4.85-.07c-3.26-.15-4.77-1.7-4.92-4.92-.06-1.27-.07-1.64-.07-4.85s.01-3.58.07-4.85C2.38 3.92 3.9 2.38 7.15 2.23 8.42 2.17 8.8 2.16 12 2.16zM12 0C8.74 0 8.33.01 7.05.07 2.7.27.27 2.69.07 7.05.01 8.33 0 8.74 0 12s.01 3.67.07 4.95c.2 4.36 2.62 6.78 6.98 6.98C8.33 23.99 8.74 24 12 24s3.67-.01 4.95-.07c4.35-.2 6.78-2.62 6.98-6.98.06-1.28.07-1.69.07-4.95s-.01-3.67-.07-4.95c-.2-4.35-2.62-6.78-6.98-6.98C15.67.01 15.26 0 12 0zm0 5.84A6.16 6.16 0 1 0 12 18.16 6.16 6.16 0 0 0 12 5.84zm0 10.16A4 4 0 1 1 12 8a4 4 0 0 1 0 8zm6.41-11.85a1.44 1.44 0 1 1-2.88 0 1.44 1.44 0 0 1 2.88 0z" /></svg>',
  medium:
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V4H6.5A2.5 2.5 0 0 0 4 6.5v13z" /><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5" /></svg>',
  substack:
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg>',
};
const CHECK_ICON =
  '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5" /></svg>';
const TOAST_ICON =
  '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5" /></svg>';

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function getEmail() {
  return localStorage.getItem(EMAIL_KEY) || "";
}

function toast(message) {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();
  const el = document.createElement("div");
  el.className = "toast";
  el.innerHTML = TOAST_ICON + "<span></span>";
  el.querySelector("span").textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

function fillProfile() {
  const email = getEmail();
  const name = email ? email.split("@")[0] : "Guest";
  const initial = name.charAt(0).toUpperCase();
  document.querySelectorAll(".profile-name, .nav-user-text").forEach((el) => {
    el.textContent = name;
  });
  document.querySelectorAll(".avatar").forEach((el) => {
    el.textContent = initial;
  });
}

function authHeaders(extra) {
  const token = getToken();
  const headers = Object.assign({}, extra || {});
  if (token) headers.Authorization = "Bearer " + token;
  return headers;
}

async function readDetail(res) {
  try {
    const data = await res.json();
    return data.detail || "";
  } catch {
    return "";
  }
}

async function loadContext() {
  if (!getToken()) return "";
  try {
    const res = await fetch(API + "/me", { headers: authHeaders() });
    if (!res.ok) return "";
    const data = await res.json();
    return data.user_context || "";
  } catch {
    return "";
  }
}

async function saveContext(method, value) {
  const res = await fetch(API + "/me/context", {
    method: method,
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ user_context: value }),
  });
  if (!res.ok) {
    return (await readDetail(res)) || "Could not save your changes";
  }
  return "";
}

function parseEvent(part) {
  let event = "message";
  let data = "";
  for (const line of part.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  if (!data) return null;
  return { event: event, data: data };
}

async function streamGenerate(payload, handlers) {
  const res = await fetch(API + "/generate", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error((await readDetail(res)) || "Generation failed");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop();
    for (const part of parts) {
      const evt = parseEvent(part);
      if (!evt) continue;
      if (evt.event === "status") {
        handlers.onStatus(JSON.parse(evt.data).message);
      } else if (evt.event === "result") {
        handlers.onResult(JSON.parse(evt.data));
        return;
      } else if (evt.event === "error") {
        handlers.onError(JSON.parse(evt.data).message);
        return;
      }
    }
  }
}

function initMenu() {
  const btn = document.getElementById("menu-btn");
  const menu = document.getElementById("topbar-menu");
  if (!btn || !menu) return;
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    menu.hidden = !menu.hidden;
  });
  document.addEventListener("click", (e) => {
    if (!menu.contains(e.target)) menu.hidden = true;
  });
}

function initLogin() {
  const form = document.getElementById("login-form");
  if (!form) return;
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value.trim();
    localStorage.setItem(EMAIL_KEY, email);
    window.location.href = "onboarding.html";
  });
  document.getElementById("signup-btn").addEventListener("click", () => {
    window.location.href = "onboarding.html";
  });
  document.getElementById("forgot-btn").addEventListener("click", () => {
    toast("Check your inbox for a reset link");
  });
}

function initOnboarding() {
  const area = document.getElementById("context");
  if (!area) return;
  loadContext().then((ctx) => {
    if (ctx) area.value = ctx;
  });
  document.getElementById("onboard-close").addEventListener("click", () => {
    window.location.href = "generate.html";
  });
  document.getElementById("onboard-next").addEventListener("click", async () => {
    const value = area.value.trim();
    if (value && getToken()) {
      try {
        const error = await saveContext("POST", value);
        if (error) toast(error);
      } catch {
        toast("Cannot reach the server");
      }
    }
    window.location.href = "generate.html";
  });
}

function initSettings() {
  const area = document.getElementById("settings-context");
  if (!area) return;
  loadContext().then((ctx) => {
    if (ctx) area.value = ctx;
  });
  document.getElementById("save-btn").addEventListener("click", async () => {
    if (!getToken()) {
      toast("Sign in to save your context");
      return;
    }
    try {
      const error = await saveContext("PUT", area.value.trim());
      if (error) toast(error);
      else toast("Changes saved");
    } catch {
      toast("Cannot reach the server");
    }
  });
}

function initGenerate() {
  const grid = document.getElementById("platform-grid");
  if (!grid) return;
  const topicEl = document.getElementById("topic");
  const audienceEl = document.getElementById("audience");
  const languageEl = document.getElementById("language");
  const overlay = document.getElementById("gen-overlay");
  const genList = document.getElementById("gen-list");
  const result = document.getElementById("result");
  const resultBody = document.getElementById("result-body");
  const resultIcon = document.getElementById("result-icon");
  const resultPlatform = document.getElementById("result-platform");
  const generateBtn = document.getElementById("generate-btn");
  const citationsToggle = document.getElementById("toggle-citations");
  const state = {
    platform: "linkedin",
    tone: "professional",
    image: false,
    citations: true,
    context: "",
    busy: false,
    text: "",
  };

  loadContext().then((ctx) => {
    state.context = ctx;
  });

  function syncCitations() {
    const allowed = CITATIONS_PLATFORMS.includes(state.platform);
    citationsToggle.disabled = !allowed;
    if (!allowed) {
      citationsToggle.classList.remove("is-on");
      citationsToggle.setAttribute("aria-pressed", "false");
      state.citations = false;
    }
  }

  syncCitations();

  grid.addEventListener("click", (e) => {
    const card = e.target.closest(".platform-card");
    if (!card) return;
    grid.querySelectorAll(".platform-card").forEach((el) => {
      el.classList.toggle("is-selected", el === card);
    });
    state.platform = card.dataset.platform;
    syncCitations();
  });

  document.getElementById("tone-row").addEventListener("click", (e) => {
    const pill = e.target.closest(".tone-pill");
    if (!pill) return;
    document.querySelectorAll(".tone-pill").forEach((el) => {
      el.classList.toggle("is-active", el === pill);
    });
    state.tone = pill.dataset.tone;
  });

  document.querySelectorAll(".toggle").forEach((toggle) => {
    toggle.addEventListener("click", () => {
      const on = toggle.classList.toggle("is-on");
      toggle.setAttribute("aria-pressed", String(on));
      if (toggle.dataset.toggle === "image") state.image = on;
      if (toggle.dataset.toggle === "citations") state.citations = on;
    });
  });

  function addLine(text) {
    const current = genList.querySelector("li:not(.is-done)");
    if (current) doneLine(current);
    const li = document.createElement("li");
    li.innerHTML = '<span class="marker spinner"></span><span class="label"></span>';
    li.querySelector(".label").textContent = text;
    genList.appendChild(li);
  }

  function doneLine(li) {
    li.classList.add("is-done");
    li.querySelector(".marker").innerHTML = CHECK_ICON;
  }

  function startProgress() {
    genList.innerHTML = "";
    addLine("Reading your brief");
    overlay.classList.add("is-visible");
    document.body.classList.add("is-generating");
  }

  function finishProgress() {
    genList.querySelectorAll("li:not(.is-done)").forEach(doneLine);
    setTimeout(() => {
      overlay.classList.remove("is-visible");
      document.body.classList.remove("is-generating");
    }, 400);
  }

  function showResult(data) {
    state.text = data.generated_text || "";
    resultIcon.innerHTML = PLATFORM_ICONS[state.platform];
    resultPlatform.textContent = PLATFORM_NAMES[state.platform];
    resultBody.textContent = state.text;
    resultBody.classList.toggle(
      "is-longform",
      LONGFORM_PLATFORMS.includes(state.platform)
    );
    if (data.image_data) {
      const img = document.createElement("img");
      img.src = "data:image/png;base64," + data.image_data;
      img.alt = "Generated visual";
      resultBody.appendChild(img);
    }
    result.hidden = false;
    toast("Draft ready to review");
  }

  function resetResult() {
    result.hidden = true;
  }

  async function runGenerate() {
    if (state.busy) return;
    const topic = topicEl.value.trim();
    if (!topic) {
      toast("Add a topic to get started");
      topicEl.focus();
      return;
    }
    state.busy = true;
    resetResult();
    startProgress();
    const payload = {
      topic: topic,
      platform: state.platform,
      tone: state.tone,
      audience: audienceEl.value.trim(),
      language: languageEl.value,
      model: MODEL,
      provider: PROVIDER,
      image_enabled: state.image,
      citations_enabled: state.citations,
      user_context: state.context,
    };
    try {
      await streamGenerate(payload, {
        onStatus: addLine,
        onResult: (data) => {
          finishProgress();
          showResult(data);
          state.busy = false;
        },
        onError: (message) => {
          finishProgress();
          toast(message);
          state.busy = false;
        },
      });
    } catch (err) {
      finishProgress();
      toast(err.message || "Cannot reach the server");
      state.busy = false;
    }
  }

  generateBtn.addEventListener("click", runGenerate);
  document.getElementById("again-btn").addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    runGenerate();
  });
  document.getElementById("result-close").addEventListener("click", resetResult);
  document.getElementById("result-open").addEventListener("click", () => {
    window.open(PLATFORM_URLS[state.platform], "_blank", "noopener");
  });
  document.getElementById("copy-btn").addEventListener("click", () => {
    navigator.clipboard
      .writeText(state.text)
      .then(() => toast("Copied to clipboard"))
      .catch(() => toast("Could not copy the text"));
  });
}

fillProfile();
initMenu();
initLogin();
initOnboarding();
initSettings();
initGenerate();
