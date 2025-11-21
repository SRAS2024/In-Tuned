const $ = (id) => document.getElementById(id);

/* ---------- Per tab session support ---------- */

function createUUID() {
  if (window.crypto && window.crypto.randomUUID) {
    return window.crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getSessionId() {
  try {
    let sid = sessionStorage.getItem("in-tuned-session");
    if (!sid) {
      sid = createUUID();
      sessionStorage.setItem("in-tuned-session", sid);
    }
    return sid;
  } catch {
    return createUUID();
  }
}

const SESSION_ID = getSessionId();

/* ---------- Locales: EN, ES, PT only ---------- */

const LOCALES = {
  en: {
    name: "English",
    short: "EN",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "Emotion detector",
      subtitle:
        "A simple space to notice what you are feeling across seven core emotions.",
      inputLabel: "Text",
      inputPlaceholder:
        "Type a short passage. For example: I am grateful and excited to begin something new today.",
      wordInfoDefault: "250 word maximum",
      wordsLabel: "words",
      analyzeButton: "Analyze",
      coreMixtureTitle: "Core mixture",
      analysisTitle: "Analysis",
      resultsTitle: "Results",
      resultsDominantLabel: "Dominant",
      resultsEmotionLabel: "Current emotion",
      resultsSecondaryLabel: "Secondary",
      resultsMixedLabel: "Mixed state",
      resultsMixedYes: "Yes",
      resultsMixedNo: "No",
      resultsValenceLabel: "Valence",
      resultsActivationLabel: "Activation",
      resultsIntensityLabel: "Intensity",
      resultsConfidenceLabel: "Confidence",
      resultsPatternLabel: "Pattern",
      resultsPrototypeLabel: "Closest tone",
      footer: "© 2025 In tuned. All rights reserved.",
      aboutTitle: "About In tuned",
      aboutDescriptionLabel: "Description:",
      aboutBody:
        "In tuned is an intuitive reflection tool that helps you understand what you are feeling in the moment. You write a short passage of up to 250 words and the app highlights a blend of seven core emotions anger, disgust, fear, joy, sadness, passion, and surprise so you can see a simple emotional snapshot of your text. The goal is to support self awareness and healthy reflection only. It is not therapy and it is not a substitute for professional mental health care or medical advice.",
      aboutDone: "Done",
      statusEnterText: "Please enter some text.",
      statusAnalyzing: "Analyzing...",
      statusLowSignal:
        "Too little text to understand how you feel. Try adding a bit more detail.",
      crisisTitle: "Wait! You are priceless and important.",
      crisisBody:
        "If you or your loved ones are having any thoughts of self harm or suicide, help is always available to you. This world needs you in it.",
      crisisNote:
        "This app cannot provide crisis support. The numbers shown are based on common services in your region and may not be complete. If they do not work or you are in immediate danger, please contact any local emergency service or a trusted crisis hotline right away.",
      crisisHotlineCta: "Contact suicide hotline",
      crisisEmergencyCta: "Contact emergency services",
      crisisClose: "Close",
      langMenuLabel: "Language",
      langSwitchTooltip: "Change language",
      helpButtonLabel: "About In tuned",
      themeToggleLabel: "Toggle light or dark theme",
      settingsThemeLabel: "Theme",
      settingsLanguageLabel: "Language"
    },
    emotions: {
      anger: "Anger",
      disgust: "Disgust",
      fear: "Fear",
      joy: "Joy",
      sadness: "Sadness",
      passion: "Passion",
      surprise: "Surprise"
    }
  },
  es: {
    name: "Español",
    short: "ES",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "Detector de emociones",
      subtitle:
        "Un espacio sencillo para notar lo que sientes en siete emociones básicas.",
      inputLabel: "Texto",
      inputPlaceholder:
        "Escribe un texto corto. Por ejemplo: Estoy agradecido y emocionado por empezar algo nuevo hoy.",
      wordInfoDefault: "Máximo 250 palabras",
      wordsLabel: "palabras",
      analyzeButton: "Analizar",
      coreMixtureTitle: "Mezcla principal",
      analysisTitle: "Análisis",
      resultsTitle: "Resultados",
      resultsDominantLabel: "Principal",
      resultsEmotionLabel: "Emoción actual",
      resultsSecondaryLabel: "Secundaria",
      resultsMixedLabel: "Estado mixto",
      resultsMixedYes: "Sí",
      resultsMixedNo: "No",
      resultsValenceLabel: "Valencia",
      resultsActivationLabel: "Activación",
      resultsIntensityLabel: "Intensidad",
      resultsConfidenceLabel: "Confianza",
      resultsPatternLabel: "Patrón",
      resultsPrototypeLabel: "Tono más cercano",
      footer: "© 2025 In tuned. Todos los derechos reservados.",
      aboutTitle: "Acerca de In tuned",
      aboutDescriptionLabel: "Descripción:",
      aboutBody:
        "In tuned es una herramienta de reflexión intuitiva que te ayuda a entender lo que sientes en este momento. Escribes un texto de hasta 250 palabras y la aplicación resalta una mezcla de siete emociones básicas ira, asco, miedo, alegría, tristeza, pasión y sorpresa para que puedas ver una imagen simple de tu tono emocional. Su objetivo es apoyar la conciencia de uno mismo y una reflexión saludable. No es terapia ni sustituye la atención profesional de salud mental o médica.",
      aboutDone: "Listo",
      statusEnterText: "Por favor, escribe algún texto.",
      statusAnalyzing: "Analizando...",
      statusLowSignal:
        "Hay muy poco texto para comprender cómo te sientes. Intenta añadir un poco más de detalle.",
      crisisTitle: "Espera, tu vida es muy valiosa.",
      crisisBody:
        "Si tú o alguien cercano tiene pensamientos de hacerse daño o de suicidio, siempre hay ayuda disponible. El mundo te necesita aquí.",
      crisisNote:
        "Esta aplicación no puede ofrecer apoyo en crisis. Los números mostrados se basan en servicios comunes de tu región y pueden no ser completos. Si no funcionan o estás en peligro inmediato, contacta a cualquier servicio de emergencia local o a una línea de ayuda de confianza.",
      crisisHotlineCta: "Contactar línea de ayuda",
      crisisEmergencyCta: "Contactar servicios de emergencia",
      crisisClose: "Cerrar",
      langMenuLabel: "Idioma",
      langSwitchTooltip: "Cambiar idioma",
      helpButtonLabel: "Acerca de In tuned",
      themeToggleLabel: "Cambiar entre modo claro y oscuro"
    },
    emotions: {
      anger: "Ira",
      disgust: "Asco",
      fear: "Miedo",
      joy: "Alegría",
      sadness: "Tristeza",
      passion: "Pasión",
      surprise: "Sorpresa"
    }
  },
  pt: {
    name: "Português",
    short: "PT",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "Detector de emoções",
      subtitle:
        "Um espaço simples para perceber o que você está sentindo em sete emoções centrais.",
      inputLabel: "Texto",
      inputPlaceholder:
        "Escreva um pequeno texto. Por exemplo: Estou grato e animado para começar algo novo hoje.",
      wordInfoDefault: "Máximo de 250 palavras",
      wordsLabel: "palavras",
      analyzeButton: "Analisar",
      coreMixtureTitle: "Mistura principal",
      analysisTitle: "Análise",
      resultsTitle: "Resultados",
      resultsDominantLabel: "Principal",
      resultsEmotionLabel: "Emoção atual",
      resultsSecondaryLabel: "Secundária",
      resultsMixedLabel: "Estado misto",
      resultsMixedYes: "Sim",
      resultsMixedNo: "Não",
      resultsValenceLabel: "Valência",
      resultsActivationLabel: "Ativação",
      resultsIntensityLabel: "Intensidade",
      resultsConfidenceLabel: "Confiança",
      resultsPatternLabel: "Padrão",
      resultsPrototypeLabel: "Tom mais próximo",
      footer: "© 2025 In tuned. Todos os direitos reservados.",
      aboutTitle: "Sobre o In tuned",
      aboutDescriptionLabel: "Descrição:",
      aboutBody:
        "In tuned é uma ferramenta intuitiva de reflexão que ajuda você a entender o que está sentindo no momento. Você escreve um pequeno texto de até 250 palavras e o aplicativo destaca uma mistura de sete emoções centrais raiva, nojo, medo, alegria, tristeza, paixão e surpresa para mostrar um retrato simples do seu tom emocional. O objetivo é apoiar a autoconsciência e uma reflexão saudável. Não é terapia e não substitui atendimento profissional em saúde mental ou médico.",
      aboutDone: "Concluir",
      statusEnterText: "Por favor, escreva algum texto.",
      statusAnalyzing: "Analisando...",
      statusLowSignal:
        "Há texto insuficiente para entender como você se sente. Tente acrescentar um pouco mais de detalhes.",
      crisisTitle: "Espere, a sua vida é preciosa.",
      crisisBody:
        "Se você ou alguém próximo está tendo pensamentos de autoagressão ou suicídio, sempre existe ajuda disponível. O mundo precisa de você aqui.",
      crisisNote:
        "Este aplicativo não oferece apoio em situações de crise. Os números mostrados usam serviços comuns na sua região e podem não ser completos. Se não funcionarem ou se houver perigo imediato, procure qualquer serviço de emergência local ou um canal de ajuda de confiança.",
      crisisHotlineCta: "Contato linha de apoio",
      crisisEmergencyCta: "Contato serviços de emergência",
      crisisClose: "Fechar",
      langMenuLabel: "Idioma",
      langSwitchTooltip: "Alterar idioma",
      helpButtonLabel: "Sobre o In tuned",
      themeToggleLabel: "Alternar entre tema claro e escuro"
    },
    emotions: {
      anger: "Raiva",
      disgust: "Nojo",
      fear: "Medo",
      joy: "Alegria",
      sadness: "Tristeza",
      passion: "Paixão",
      surprise: "Surpresa"
    }
  }
};

const SUPPORTED_LOCALES = Object.keys(LOCALES);

function normalizeLocaleCode(raw) {
  if (!raw) return "en";
  const lower = String(raw).toLowerCase();
  if (LOCALES[lower]) return lower;
  const base = lower.split("-")[0];
  if (LOCALES[base]) return base;
  return "en";
}

function getInitialLocale() {
  try {
    const stored = localStorage.getItem("in-tuned-locale");
    if (stored && LOCALES[stored]) return stored;
  } catch (e) {}
  const nav =
    (navigator.languages && navigator.languages[0]) ||
    navigator.language ||
    "en";
  return normalizeLocaleCode(nav);
}

let currentLocale = getInitialLocale();

function t(key) {
  const loc = LOCALES[currentLocale] || LOCALES.en;
  return loc.strings[key] || LOCALES.en.strings[key] || "";
}

/* ---------- DOM references ---------- */

const fields = {
  anger: $("v-anger"),
  disgust: $("v-disgust"),
  fear: $("v-fear"),
  joy: $("v-joy"),
  sadness: $("v-sadness"),
  passion: $("v-passion"),
  surprise: $("v-surprise"),
  dominant_emotion: $("v-dominant"),
  emotion: $("v-emotion")
};

const emojiTray = $("emojiTray");
const textArea = $("text");
const wordInfo = $("wordInfo");

const langToggle = $("langToggle");
const langMenu = $("langMenu");
const langCurrentLabel = $("langCurrentLabel");

const settingsBtn = $("settingsBtn");
const settingsMenu = $("settingsMenu");

const crisisOverlay = $("crisisOverlay");
const closeCrisis = $("closeCrisis");
const crisisHotlineBtn = $("crisisHotline");
const crisisEmergencyBtn = $("crisisEmergency");
const crisisHotlineNumberSpan = $("crisisHotlineNumber");
const crisisEmergencyNumberSpan = $("crisisEmergencyNumber");

let lastAcceptedText = textArea ? textArea.value || "" : "";

/* ---------- Utility helpers ---------- */

const titleCase = (s) => {
  if (!s || typeof s !== "string") return "N/A";
  if (s.toUpperCase() === s) return s;
  return s.charAt(0).toUpperCase() + s.slice(1);
};

function setStatus(text, isError = false) {
  const s = $("status");
  if (!s) return;
  s.textContent = text || "";
  s.className = "status" + (isError ? " err" : "");
}

const fmt = (v) =>
  typeof v === "number" ? v.toFixed(3) : String(v ?? "");

function wordCountAndLimit() {
  if (!textArea) return;
  let value = textArea.value;
  if (!value) {
    lastAcceptedText = "";
    if (wordInfo) wordInfo.textContent = t("wordInfoDefault");
    return;
  }

  let tokens = value
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (tokens.length > 250) {
    const prev = lastAcceptedText || "";
    const candidate = value;

    const justPeriodAllowed =
      candidate.length === prev.length + 1 &&
      candidate.endsWith(".") &&
      !prev.trim().endsWith(".");

    if (justPeriodAllowed) {
      lastAcceptedText = candidate;
    } else {
      textArea.value = prev;
    }

    value = textArea.value;
    tokens = value.trim()
      ? value
          .trim()
          .split(/\s+/)
          .filter(Boolean)
      : [];
  } else {
    lastAcceptedText = value;
  }

  const count = tokens.length;
  if (wordInfo) {
    if (count === 0) {
      wordInfo.textContent = t("wordInfoDefault");
    } else {
      wordInfo.textContent = `${count}/250 ${t("wordsLabel")}`;
    }
  }
}

/* ---------- Crisis overlay helpers ---------- */

function showCrisisModal() {
  if (crisisOverlay) crisisOverlay.classList.add("show");
}
function hideCrisisModal() {
  if (crisisOverlay) crisisOverlay.classList.remove("show");
}

if (closeCrisis) {
  closeCrisis.addEventListener("click", hideCrisisModal);
}
if (crisisOverlay) {
  crisisOverlay.addEventListener("click", (e) => {
    if (e.target === crisisOverlay) hideCrisisModal();
  });
}

/* Emergency numbers by region code for the crisis CTA */

const EMERGENCY_NUMBERS = {
  US: "911",
  CA: "911",
  BR: "190",
  PT: "112",
  ES: "112",
  MX: "911",
  INTL: "112"
};

function applyRiskToUI(risk) {
  if (!risk) return;

  const level = risk.level || "none";
  const hotline = risk.hotline || {};
  const regionCode = hotline.regionCode || "INTL";
  const hotlineNumber = hotline.number || "988";
  const emergencyNumber =
    EMERGENCY_NUMBERS[regionCode] || EMERGENCY_NUMBERS.INTL;

  if (crisisHotlineNumberSpan) {
    crisisHotlineNumberSpan.textContent = hotlineNumber;
  }
  if (crisisEmergencyNumberSpan) {
    crisisEmergencyNumberSpan.textContent = emergencyNumber;
  }

  if (crisisHotlineBtn) {
    const clean = String(hotlineNumber || "").replace(/\s+/g, "");
    crisisHotlineBtn.href = clean ? `tel:${clean}` : "#";
  }
  if (crisisEmergencyBtn) {
    const cleanE = String(emergencyNumber || "").replace(/\s+/g, "");
    crisisEmergencyBtn.href = cleanE ? `tel:${cleanE}` : "#";
  }

  if (level && level !== "none") {
    showCrisisModal();
  }
}

/* ---------- Chart setup ---------- */

const CORE_ORDER = [
  "anger",
  "disgust",
  "fear",
  "joy",
  "sadness",
  "passion",
  "surprise"
];
const CORE_COLOR = {
  anger: "var(--c-anger)",
  disgust: "var(--c-disgust)",
  fear: "var(--c-fear)",
  joy: "var(--c-joy)",
  sadness: "var(--c-sadness)",
  passion: "var(--c-passion)",
  surprise: "var(--c-surprise)"
};

function initBars() {
  const container = $("bars");
  if (!container) return;
  container.innerHTML = "";
  CORE_ORDER.forEach((key) => {
    const row = document.createElement("div");
    row.className = "barRow";

    const label = document.createElement("div");
    label.className = "barLabel";
    label.setAttribute("data-emotion-label", key);
    label.textContent = LOCALES.en.emotions[key];

    const track = document.createElement("div");
    track.className = "barTrack";

    const fill = document.createElement("div");
    fill.className = "barFill";
    fill.style.background = CORE_COLOR[key];
    fill.style.width = "0%";
    fill.id = `bar-${key}`;

    track.appendChild(fill);

    const value = document.createElement("div");
    value.className = "barValue";
    value.id = `barv-${key}`;
    value.textContent = "0.0%";

    row.appendChild(label);
    row.appendChild(track);
    row.appendChild(value);
    container.appendChild(row);
  });
}

function renderBars(mixture) {
  if (!mixture || typeof mixture !== "object") return;
  CORE_ORDER.forEach((key) => {
    const v = Number(mixture[key]) || 0;
    const pct = Math.max(0, Math.min(100, v * 100));
    const fill = $(`bar-${key}`);
    const val = $(`barv-${key}`);
    if (fill) fill.style.width = `${pct}%`;
    if (val) val.textContent = `${pct.toFixed(1)}%`;
  });
}

function renderBarsZero() {
  renderBars({
    anger: 0,
    disgust: 0,
    fear: 0,
    joy: 0,
    sadness: 0,
    passion: 0,
    surprise: 0
  });
}

/* Normalize mixture fractions */

function normalizeMix(m) {
  const keys = CORE_ORDER;
  let sum = 0;
  const out = {};
  keys.forEach((k) => {
    out[k] = Math.max(0, Number(m[k] ?? 0));
    sum += out[k];
  });
  if (sum <= 0) {
    keys.forEach((k) => (out[k] = 0));
    return out;
  }
  keys.forEach((k) => (out[k] = out[k] / sum));
  return out;
}

/* ---------- Emoji tray ---------- */

function renderEmojisFromResults(dominant, current) {
  const dom = dominant || {};
  const cur = current || {};

  const domEmoji = dom.emoji || "🤔";
  const curEmoji = cur.emoji || domEmoji;

  const same =
    dom.emotionId &&
    cur.emotionId &&
    dom.emotionId === cur.emotionId;

  if (!emojiTray) return;

  emojiTray.title = same
    ? "Dominant and current emotion match"
    : "Dominant and current emotion";
  emojiTray.textContent = same
    ? domEmoji
    : `${domEmoji} ${curEmoji}`;
}

/* ---------- Reset and error helper ---------- */

function resetToZero() {
  const numericKeys = [
    "anger",
    "disgust",
    "fear",
    "joy",
    "sadness",
    "passion",
    "surprise"
  ];
  Object.entries(fields).forEach(([key, el]) => {
    if (!el) return;
    if (numericKeys.includes(key)) {
      el.textContent = "0.000";
    } else {
      el.textContent = "N/A";
    }
  });
  if (emojiTray) {
    emojiTray.textContent = "🤔";
    emojiTray.title = "";
  }
  renderBarsZero();
}

/* ---------- Locale application ---------- */

function applyLocale(locale) {
  currentLocale = normalizeLocaleCode(locale);
  const loc = LOCALES[currentLocale] || LOCALES.en;
  const strings = loc.strings;

  document.documentElement.setAttribute(
    "lang",
    currentLocale.split("-")[0] || "en"
  );
  document.documentElement.dir = loc.direction || "ltr";

  document
    .querySelectorAll("[data-i18n]")
    .forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!key) return;
      const value =
        strings[key] || LOCALES.en.strings[key] || "";
      el.textContent = value;
    });

  document
    .querySelectorAll("[data-i18n-placeholder]")
    .forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (!key) return;
      const value =
        strings[key] || LOCALES.en.strings[key] || "";
      if (value) el.setAttribute("placeholder", value);
    });

  document
    .querySelectorAll("[data-i18n-aria-label]")
    .forEach((el) => {
      const key = el.getAttribute("data-i18n-aria-label");
      if (!key) return;
      const value =
        strings[key] || LOCALES.en.strings[key] || "";
      if (value) el.setAttribute("aria-label", value);
    });

  document
    .querySelectorAll("[data-emotion-label]")
    .forEach((el) => {
      const emoKey = el.getAttribute("data-emotion-label");
      const emoName =
        loc.emotions[emoKey] ||
        LOCALES.en.emotions[emoKey] ||
        emoKey;
      el.textContent = emoName;
    });

  if (wordInfo) {
    const text = wordInfo.textContent || "";
    if (
      !text ||
      text === LOCALES.en.strings.wordInfoDefault ||
      text === strings.wordInfoDefault
    ) {
      wordInfo.textContent =
        strings.wordInfoDefault ||
        LOCALES.en.strings.wordInfoDefault;
    }
  }
}

function buildLangMenu() {
  if (!langMenu) return;
  langMenu.innerHTML = "";

  const heading = document.createElement("div");
  heading.className = "langHeading";
  heading.textContent = t("langMenuLabel") || "Language";
  langMenu.appendChild(heading);

  SUPPORTED_LOCALES.forEach((code) => {
    const def = LOCALES[code];
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "langOption";
    btn.dataset.locale = code;
    btn.setAttribute("role", "menuitemradio");
    btn.setAttribute(
      "aria-checked",
      code === currentLocale ? "true" : "false"
    );

    const nameSpan = document.createElement("span");
    nameSpan.textContent = def.name;
    const shortSpan = document.createElement("span");
    shortSpan.textContent = def.short || code.toUpperCase();

    btn.appendChild(nameSpan);
    btn.appendChild(shortSpan);

    langMenu.appendChild(btn);
  });
}

function updateLangUI() {
  const loc = LOCALES[currentLocale] || LOCALES.en;
  if (langCurrentLabel) {
    langCurrentLabel.textContent =
      loc.short || currentLocale.toUpperCase();
  }
  if (!langMenu) return;
  langMenu
    .querySelectorAll(".langOption")
    .forEach((btn) => {
      const code = btn.dataset.locale;
      btn.setAttribute(
        "aria-checked",
        code === currentLocale ? "true" : "false"
      );
    });
  const heading = langMenu.querySelector(".langHeading");
  if (heading) heading.textContent = t("langMenuLabel") || "Language";
}

function setLocale(locale) {
  applyLocale(locale);
  updateLangUI();
  try {
    localStorage.setItem("in-tuned-locale", currentLocale);
  } catch (e) {}
}

/* ---------- Language dropdown events ---------- */

if (langToggle) {
  langToggle.addEventListener("click", () => {
    if (!langMenu) return;
    const isOpen = langMenu.classList.contains("open");
    if (isOpen) {
      langMenu.classList.remove("open");
      langToggle.setAttribute("aria-expanded", "false");
    } else {
      langMenu.classList.add("open");
      langToggle.setAttribute("aria-expanded", "true");
    }
  });
}

if (langMenu) {
  langMenu.addEventListener("click", (e) => {
    const btn = e.target.closest(".langOption");
    if (!btn) return;
    const code = btn.dataset.locale;
    if (!code) return;
    langMenu.classList.remove("open");
    if (langToggle) langToggle.setAttribute("aria-expanded", "false");
    setLocale(code);
  });
  document.addEventListener("click", (e) => {
    if (!langMenu.classList.contains("open")) return;
    if (
      langMenu.contains(e.target) ||
      (langToggle && langToggle.contains(e.target))
    )
      return;
    langMenu.classList.remove("open");
    if (langToggle) langToggle.setAttribute("aria-expanded", "false");
  });
}

/* ---------- Settings menu ---------- */

if (settingsBtn && settingsMenu) {
  settingsBtn.addEventListener("click", () => {
    const isOpen = settingsMenu.classList.contains("open");
    if (isOpen) {
      settingsMenu.classList.remove("open");
      settingsBtn.setAttribute("aria-expanded", "false");
      if (langMenu) {
        langMenu.classList.remove("open");
        if (langToggle) langToggle.setAttribute("aria-expanded", "false");
      }
    } else {
      settingsMenu.classList.add("open");
      settingsBtn.setAttribute("aria-expanded", "true");
    }
  });

  document.addEventListener("click", (e) => {
    if (!settingsMenu.classList.contains("open")) return;
    if (
      settingsMenu.contains(e.target) ||
      settingsBtn.contains(e.target)
    )
      return;
    settingsMenu.classList.remove("open");
    settingsBtn.setAttribute("aria-expanded", "false");
    if (langMenu) {
      langMenu.classList.remove("open");
      if (langToggle) langToggle.setAttribute("aria-expanded", "false");
    }
  });
}

/* ---------- Help modal ---------- */

const overlay = $("overlay");
const helpBtn = $("helpBtn");
const closeModal = $("closeModal");

if (helpBtn && overlay) {
  helpBtn.addEventListener("click", () =>
    overlay.classList.add("show")
  );
}
if (closeModal && overlay) {
  closeModal.addEventListener("click", () =>
    overlay.classList.remove("show")
  );
}
if (overlay) {
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.classList.remove("show");
  });
}

/* ---------- Theme toggle ---------- */

const modeDot = $("modeDot");
const root = document.documentElement;

function setTheme(theme) {
  root.setAttribute("data-theme", theme);
}

function toggleTheme() {
  const now =
    root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  setTheme(now);
  try {
    localStorage.setItem("in-tuned-theme", now);
  } catch (e) {}
}

if (modeDot) {
  modeDot.addEventListener("click", toggleTheme);
  modeDot.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleTheme();
    }
  });
}

try {
  const savedTheme = localStorage.getItem("in-tuned-theme");
  if (savedTheme) {
    setTheme(savedTheme);
  } else if (
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: light)").matches
  ) {
    setTheme("light");
  } else {
    setTheme(root.getAttribute("data-theme") || "dark");
  }
} catch (e) {
  setTheme(root.getAttribute("data-theme") || "dark");
}

/* ---------- Region helper for backend ---------- */

function detectRegionFromNavigator() {
  const nav = navigator.language || "en-US";
  const parts = nav.split("-");
  if (parts.length > 1) {
    return parts[1].toUpperCase();
  }
  const base = parts[0].toLowerCase();
  if (base === "pt") return "BR";
  if (base === "es") return "ES";
  return "US";
}

/* ---------- Apply API analysis to UI ---------- */

function applyAnalysisFromApi(data) {
  const analysis = data.analysis || [];
  const analysisById = {};
  analysis.forEach((row) => {
    if (row && row.id) {
      analysisById[row.id] = row;
    }
  });

  CORE_ORDER.forEach((id) => {
    const el = fields[id];
    if (!el) return;
    const row = analysisById[id];
    if (!row) {
      el.textContent = "0.000";
      return;
    }
    if (typeof row.score === "number") {
      el.textContent = fmt(row.score);
    } else if (typeof row.scoreDisplay === "string") {
      el.textContent = row.scoreDisplay;
    } else {
      el.textContent = "0.000";
    }
  });

  const results = data.results || {};
  const dom = results.dominant || {};
  const cur = results.current || {};

  // Dominant: always show core emotion name, not nuanced phrase
  const domLabel =
    dom.labelLocalized ||
    dom.label ||
    dom.emotionId ||
    "N/A";

  // Current: prefer nuanced wording when available
  const curLabel =
    cur.nuancedLabelLocalized ||
    cur.nuancedLabel ||
    cur.labelLocalized ||
    cur.label ||
    cur.emotionId ||
    "N/A";

  if (fields.dominant_emotion) {
    fields.dominant_emotion.textContent = domLabel;
  }
  if (fields.emotion) {
    fields.emotion.textContent = curLabel;
  }

  const mixRows = data.coreMixture || [];
  const mixture = {};
  mixRows.forEach((row) => {
    if (!row || !row.id) return;
    const pct = typeof row.percent === "number" ? row.percent : 0;
    mixture[row.id] = pct / 100;
  });

  const normalized = normalizeMix(mixture);
  renderBars(normalized);
  renderEmojisFromResults(dom, cur);

  const metrics = data.metrics || {};
  if (typeof metrics.confidence === "number") {
    const conf = metrics.confidence || 0;
    if (conf < 0.25) {
      setStatus(t("statusLowSignal"), false);
    } else {
      setStatus("");
    }
  } else {
    setStatus("");
  }

  const risk = data.risk || {};
  applyRiskToUI(risk);
}

/* ---------- Analyze button handler ---------- */

const analyzeBtn = $("analyze");

if (analyzeBtn && textArea) {
  analyzeBtn.addEventListener("click", async () => {
    const text = textArea.value.trim();
    if (!text) {
      setStatus(
        t("statusEnterText") || "Please enter some text."
      );
      textArea.classList.add("input-error");
      resetToZero();
      return;
    }

    setStatus(t("statusAnalyzing") || "Analyzing...");
    textArea.classList.remove("input-error");

    const payload = {
      text,
      locale: currentLocale,
      session_id: SESSION_ID,
      token: "5000",
      region: detectRegionFromNavigator()
    };

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-App-Token": "5000"
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) {
        const msg =
          (data && data.error) || "Request failed";
        throw new Error(msg);
      }

      applyAnalysisFromApi(data);
    } catch (err) {
      const msg =
        err && err.message ? err.message : "Unexpected error";
      setStatus(msg, true);
      textArea.classList.add("input-error");
      resetToZero();
    }
  });
}

/* ---------- Text input handler ---------- */

if (textArea) {
  textArea.addEventListener("input", () => {
    wordCountAndLimit();
    if (textArea.classList.contains("input-error")) {
      textArea.classList.remove("input-error");
    }
    const s = $("status");
    if (s && s.textContent) {
      setStatus("");
    }
  });
}

/* ---------- Initial setup ---------- */

initBars();
buildLangMenu();
setLocale(currentLocale);
renderBarsZero();
wordCountAndLimit();
