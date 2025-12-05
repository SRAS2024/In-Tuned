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
      statusNeedAnalysis: "Run an analysis before adding to journal.",
      crisisTitle: "Wait! You are priceless and important.",
      crisisBody:
        "If you or your loved ones are having any thoughts of self harm or suicide, help is always available to you. This world needs you in it.",
      crisisNote:
        "If you feel that you might be in danger, please contact a trusted crisis hotline or your local emergency services right away.",
      crisisHotlineCta: "Contact suicide hotline",
      crisisEmergencyCta: "Contact emergency services",
      crisisClose: "Close",
      langMenuLabel: "Language",
      langSwitchTooltip: "Change language",
      helpButtonLabel: "About In tuned",
      themeToggleLabel: "Toggle light or dark theme",
      settingsThemeLabel: "Theme",
      settingsLanguageLabel: "Language",
      journalNewTitle: "New journal entry",
      journalOriginalTextLabel: "Original text",
      journalAnalysisSnapshotLabel: "Analysis snapshot",
      journalJournalLabel: "Journal",
      journalCancel: "Cancel",
      journalSave: "Save",
      journalDefaultTitle: "Journal entry",
      journalPin: "Pin",
      journalUnpin: "Unpin",
      accountLabel: "Account",
      loginButtonLabel: "Log in",
      maintenanceTitle: "In tuned is temporarily offline",
      maintenanceMessage:
        "Site is currently down due to maintenance. We will be back shortly.",
      maintenanceNote:
        "Thank you for your patience while we finish a few upgrades."
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
      statusNeedAnalysis:
        "Realiza un análisis antes de añadir al diario.",
      crisisTitle: "Espera, tu vida es muy valiosa.",
      crisisBody:
        "Si tú o alguien cercano tiene pensamientos de hacerse daño o de suicidio, siempre hay ayuda disponible. El mundo te necesita aquí.",
      crisisNote:
        "Si sientes que puedes estar en peligro, comunícate de inmediato con una línea de ayuda de confianza o con los servicios de emergencia de tu país.",
      crisisHotlineCta: "Contactar línea de ayuda",
      crisisEmergencyCta: "Contactar servicios de emergencia",
      crisisClose: "Cerrar",
      langMenuLabel: "Idioma",
      langSwitchTooltip: "Cambiar idioma",
      helpButtonLabel: "Acerca de In tuned",
      themeToggleLabel: "Cambiar entre tema claro y oscuro",
      journalNewTitle: "Nueva entrada de diario",
      journalOriginalTextLabel: "Texto original",
      journalAnalysisSnapshotLabel: "Resumen del análisis",
      journalJournalLabel: "Diario",
      journalCancel: "Cancelar",
      journalSave: "Guardar",
      journalDefaultTitle: "Entrada de diario",
      journalPin: "Fijar",
      journalUnpin: "Quitar fijación",
      accountLabel: "Cuenta",
      loginButtonLabel: "Iniciar sesión",
      maintenanceTitle: "In tuned está temporalmente fuera de línea",
      maintenanceMessage:
        "El sitio está en mantenimiento en este momento. Volveremos en breve.",
      maintenanceNote:
        "Gracias por tu paciencia mientras terminamos algunas mejoras."
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
      statusNeedAnalysis:
        "Faça uma análise antes de adicionar ao diário.",
      crisisTitle: "Espere, a sua vida é preciosa.",
      crisisBody:
        "Se você ou alguém próximo está tendo pensamentos de autoagressão ou suicídio, sempre existe ajuda disponível. O mundo precisa de você aqui.",
      crisisNote:
        "Se você sentir que pode estar em perigo, procure imediatamente uma linha de apoio de confiança ou os serviços de emergência da sua região.",
      crisisHotlineCta: "Contato linha de apoio",
      crisisEmergencyCta: "Contato serviços de emergência",
      crisisClose: "Fechar",
      langMenuLabel: "Idioma",
      langSwitchTooltip: "Alterar idioma",
      helpButtonLabel: "Sobre o In tuned",
      themeToggleLabel: "Alternar entre tema claro e escuro",
      journalNewTitle: "Nova entrada de diário",
      journalOriginalTextLabel: "Texto original",
      journalAnalysisSnapshotLabel: "Resumo da análise",
      journalJournalLabel: "Diário",
      journalCancel: "Cancelar",
      journalSave: "Salvar",
      journalDefaultTitle: "Entrada de diário",
      journalPin: "Fixar",
      journalUnpin: "Desafixar",
      accountLabel: "Conta",
      loginButtonLabel: "Entrar",
      maintenanceTitle: "In tuned está temporariamente fora do ar",
      maintenanceMessage:
        "O site está em manutenção no momento. Voltaremos em breve.",
      maintenanceNote:
        "Obrigado pela sua paciência enquanto concluímos algumas melhorias."
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

/* ---------- Global state ---------- */

let currentUser = null;
let lastAcceptedText = "";
let lastAnalysisSnapshot = null;
let journals = [];
let currentJournal = null;
let isEditingJournal = false;
let isCreatingJournal = false;

const root = document.documentElement;

/* ---------- Simple API helpers ---------- */

async function apiFetchJSON(path, options = {}) {
  const opts = {
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(options.method && options.method !== "GET"
        ? { "Content-Type": "application/json" }
        : {}),
      ...(options.headers || {})
    },
    ...options
  };

  const res = await fetch(path, opts);
  let json;
  try {
    json = await res.json();
  } catch (e) {
    json = null;
  }

  if (!res.ok) {
    const message =
      (json && (json.error || json.message)) ||
      `Request failed with status ${res.status}`;
    throw new Error(message);
  }

  return json || {};
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
  emotion: $("v-emotion"),
  secondary_emotion: $("v-secondary"),
  mixed_state: $("v-mixed"),
  valence: $("v-valence"),
  activation: $("v-activation"),
  intensity: $("v-intensity"),
  confidence_metric: $("v-confidence"),
  pattern: $("v-pattern"),
  prototype: $("v-prototype")
};

const emojiTray = $("emojiTray");
const textArea = $("text");
const wordInfo = $("wordInfo");

/* Header and layout */
const appHeader = $("appHeader");
const appMain = $("appMain");
const appFooter = $("appFooter");
const noticeBanner = $("noticeBanner");
const maintenanceShell = $("maintenanceShell");
const maintenanceMessageEl = $("maintenanceMessage");

/* Settings and language (guest) */
const settingsControl = $("settingsControl");
const settingsBtn = $("settingsBtn");
const settingsMenu = $("settingsMenu");
const langToggle = $("langToggle");
const langMenu = $("langMenu");
const langCurrentLabel = $("langCurrentLabel");

/* Help modal */
const helpBtn = $("helpBtn");
const overlay = $("overlay");
const closeModal = $("closeModal");

/* Crisis overlay */
const crisisOverlay = $("crisisOverlay");
const closeCrisis = $("closeCrisis");
const crisisHotlineBtn = $("crisisHotline");
const crisisEmergencyBtn = $("crisisEmergency");
const crisisHotlineNumberSpan = $("crisisHotlineNumber");
const crisisEmergencyNumberSpan = $("crisisEmergencyNumber");

/* Auth header controls */
const loginBtn = $("loginBtn");
const accountControl = $("accountControl");
const accountBtn = $("accountBtn");
const accountMenu = $("accountMenu");
const accountNameLabel = $("accountNameLabel");

/* Auth overlays and forms */
const authOverlayLogin = $("authOverlayLogin");
const authOverlayRegister = $("authOverlayRegister");
const authOverlayForgot = $("authOverlayForgot");

// Login form
const loginForm = $("loginForm");
const loginIdentifierInput = $("loginIdentifier");
const loginPasswordInput = $("loginPassword");
const loginError = $("loginError");
const openRegisterFromLoginBtn = $("openRegisterFromLogin");
const openForgotFromLoginBtn = $("openForgotFromLogin");
const cancelLoginBtn = $("cancelLogin");
const submitLoginBtn = $("submitLogin");

// Register form
const registerForm = $("registerForm");
const registerFirstName = $("registerFirstName");
const registerLastName = $("registerLastName");
const registerUsername = $("registerUsername");
const registerEmail = $("registerEmail");
const registerPassword = $("registerPassword");
const registerConfirmPassword = $("registerConfirmPassword");
const registerError = $("registerError");
const cancelRegisterBtn = $("cancelRegister");
const submitRegisterBtn = $("submitRegister");

// Forgot form (two step flow)
const forgotForm = $("forgotForm");
const forgotEmail = $("forgotEmail");
const forgotFirstName = $("forgotFirstName");
const forgotLastName = $("forgotLastName");
const forgotNewPassword = $("forgotNewPassword");
const forgotConfirmPassword = $("forgotConfirmPassword");
const forgotError = $("forgotError");
const cancelForgotBtn = $("cancelForgot");
const submitForgotBtn = $("submitForgot");
const forgotStepIdentity = $("forgotStepIdentity");
const forgotStepReset = $("forgotStepReset");
const forgotContinueBtn = $("forgotContinue");
const cancelForgotResetBtn = $("cancelForgotReset");

/* Account settings overlay */
const accountSettingsOverlay = $("accountSettingsOverlay");
const accountSettingsForm = $("accountSettingsForm");
const accountThemeToggle = $("accountThemeToggle");
const accountLangToggle = $("accountLangToggle");
const accountLangMenu = $("accountLangMenu");
const accountLangCurrentLabel = $("accountLangCurrentLabel");
const accountSettingsError = $("accountSettingsError");
const cancelAccountSettingsBtn = $("cancelAccountSettings");
const saveAccountSettingsBtn = $("saveAccountSettings");

/* Journal overlay and controls */
const addJournalButton = $("addJournalButton");
const addJournalHint = $("addJournalHint");
const journalOverlay = $("journalOverlay");
const closeJournalBtn = $("closeJournal");
const pinnedSectionHeader = $("pinnedSectionHeader");
const pinnedJournalList = $("pinnedJournalList");
const journalList = $("journalList");
const journalEmptyState = $("journalEmptyState");
const journalDetail = $("journalDetail");
const journalDetailTitle = $("journalDetailTitle");
const journalDetailMeta = $("journalDetailMeta");
const journalDetailSourceText = $("journalDetailSourceText");
const journalDetailAnalysis = $("journalDetailAnalysis");
const journalDetailText = $("journalDetailText");
const journalDetailActionsRow = $("journalDetailActionsRow");
const journalDetailDominant = $("journalDetailDominant");
const journalDetailEmotion = $("journalDetailEmotion");
const journalDetailBarnhart = $("journalDetailBarnhart");
const journalFlagButton = $("journalFlagButton");
const journalEditMenuBtn = $("journalEditMenu");
const journalEditMenuDropdown = $("journalEditMenuDropdown");
const journalEditButton = $("journalEditButton");
const journalPinToggleButton = $("journalPinToggleButton");
const cancelJournalEditBtn = $("cancelJournalEdit");
const saveJournalEditBtn = $("saveJournalEdit");
const journalDeleteButton = $("journalDeleteButton");
const journalDeleteConfirmOverlay = $("journalDeleteConfirmOverlay");
const cancelJournalDeleteBtn = $("cancelJournalDelete");
const confirmJournalDeleteBtn = $("confirmJournalDelete");
const journalBackButton = $("journalBackButton");

/* Analyze button */
const analyzeBtn = $("analyze");

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

/* ---------- Word count and limit ---------- */

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

function t(key) {
  const loc = LOCALES[currentLocale] || LOCALES.en;
  return loc.strings[key] || LOCALES.en.strings[key] || "";
}

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

function buildLangMenuFor(container) {
  if (!container) return;
  container.innerHTML = "";

  const heading = document.createElement("div");
  heading.className = "langHeading";
  heading.textContent = t("langMenuLabel") || "Language";
  container.appendChild(heading);

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

    container.appendChild(btn);
  });
}

function updateLangUI() {
  const loc = LOCALES[currentLocale] || LOCALES.en;
  const short = loc.short || currentLocale.toUpperCase();

  if (langCurrentLabel) {
    langCurrentLabel.textContent = short;
  }
  if (accountLangCurrentLabel) {
    accountLangCurrentLabel.textContent = short;
  }

  if (langMenu) {
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

  if (accountLangMenu) {
    accountLangMenu
      .querySelectorAll(".langOption")
      .forEach((btn) => {
        const code = btn.dataset.locale;
        btn.setAttribute(
          "aria-checked",
          code === currentLocale ? "true" : "false"
        );
      });
    const heading = accountLangMenu.querySelector(".langHeading");
    if (heading) heading.textContent = t("langMenuLabel") || "Language";
  }
}

function setLocale(locale, { persist = true } = {}) {
  applyLocale(locale);
  updateLangUI();
  if (persist && !currentUser) {
    try {
      localStorage.setItem("in-tuned-locale", currentLocale);
    } catch (e) {}
  }
}

/* ---------- Language dropdown events (guest) ---------- */

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

/* ---------- Settings menu (guest) ---------- */

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

/* ---------- Theme helpers ---------- */

function applyGuestTheme() {
  let theme = "dark";
  try {
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: light)").matches
    ) {
      theme = "light";
    }
  } catch (e) {}
  root.setAttribute("data-theme", theme);
}

function applyUserTheme(theme) {
  let tTheme = theme;
  if (tTheme !== "light" && tTheme !== "dark") {
    tTheme = "dark";
    try {
      if (
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: light)").matches
      ) {
        tTheme = "light";
      }
    } catch (e) {}
  }
  root.setAttribute("data-theme", tTheme || "dark");
}

/* ---------- Region helper for backend ---------- */

function detectRegionFromNavigator() {
  const navLang =
    (navigator.languages && navigator.languages[0]) ||
    navigator.language ||
    "en-US";

  const parts = navLang.split("-");
  if (parts.length > 1) {
    const regionCandidate = parts[1].toUpperCase();
    if (EMERGENCY_NUMBERS[regionCandidate]) {
      return regionCandidate;
    }
  }

  const base = parts[0].toLowerCase();
  if (base === "pt") return "BR";
  if (base === "es") return "ES";
  if (base === "fr") return "CA";
  return "US";
}

/* ---------- Helpers for analysis result labels and snapshots ---------- */

function getResultEmotionLabel(entry) {
  if (!entry) return "";
  return (
    entry.labelLocalized ||
    entry.nuancedLabelLocalized ||
    entry.nuancedLabel ||
    entry.label ||
    entry.emotionId ||
    ""
  );
}

/* Metric rendering helper for valence, activation, intensity, confidence, pattern, prototype */

function renderMetricField(el, sourceObj, fallbackNumber) {
  if (!el) return;

  if (!sourceObj && typeof fallbackNumber !== "number") {
    el.textContent = "N/A";
    return;
  }

  const obj = sourceObj || {};
  const parts = [];

  const label =
    obj.labelLocalized ||
    obj.label ||
    obj.rating ||
    obj.bucket ||
    obj.name ||
    "";

  if (label) {
    parts.push(label);
  }

  let num = null;
  if (typeof obj.score === "number") {
    num = obj.score;
  } else if (typeof obj.value === "number") {
    num = obj.value;
  } else if (typeof fallbackNumber === "number") {
    num = fallbackNumber;
  }

  if (typeof num === "number") {
    parts.push(num.toFixed(3));
  }

  if (!parts.length) {
    el.textContent = "N/A";
  } else {
    el.textContent = parts.join(" · ");
  }
}

/**
 * Build the text block for an analysis snapshot.
 * Only includes emotions with percent greater than zero,
 * then appends Dominant and Current emotion lines.
 */
function buildAnalysisSnapshotText(analysis) {
  if (!analysis || typeof analysis !== "object") return "";

  const core = Array.isArray(analysis.coreMixture)
    ? analysis.coreMixture
    : [];

  const nonZero = core
    .filter(
      (row) =>
        row &&
        typeof row.percent === "number" &&
        row.percent > 0
    )
    .slice()
    .sort(
      (a, b) =>
        (b.percent || 0) - (a.percent || 0)
    );

  const lines = [];

  nonZero.forEach((row) => {
    const label =
      row.labelLocalized || row.label || row.id || "";
    const pct =
      typeof row.percent === "number"
        ? row.percent.toFixed(1)
        : "0.0";
    if (label) {
      lines.push(`${label}: ${pct}%`);
    }
  });

  const results = analysis.results || {};
  const dom = results.dominant || {};
  const cur = results.current || {};

  const domName = getResultEmotionLabel(dom);
  const curName = getResultEmotionLabel(cur);

  if (domName || curName) {
    const domLabel = t("resultsDominantLabel") || "Dominant";
    const curLabel =
      t("resultsEmotionLabel") || "Current emotion";

    if (lines.length > 0) {
      lines.push("");
    }
    if (domName) {
      lines.push(`${domLabel}: ${domName}`);
    }
    if (curName) {
      lines.push(`${curLabel}: ${curName}`);
    }
  }

  return lines.join("\n");
}

/* ---------- Apply API analysis to UI ---------- */

function renderResultsMeta(data) {
  const results = data.results || {};
  const metrics = data.metrics || {};

  const secondary = results.secondary || {};
  if (fields.secondary_emotion) {
    const label = getResultEmotionLabel(secondary) || "N/A";
    fields.secondary_emotion.textContent = label;
  }

  const mixed = results.mixed_state || {};
  if (fields.mixed_state) {
    let mixedLabel = "N/A";
    if (typeof mixed.is_mixed === "boolean") {
      mixedLabel = mixed.is_mixed
        ? t("resultsMixedYes") || "Yes"
        : t("resultsMixedNo") || "No";
    } else if (mixed.labelLocalized || mixed.label) {
      mixedLabel = mixed.labelLocalized || mixed.label;
    }
    fields.mixed_state.textContent = mixedLabel;
  }

  const valenceObj =
    results.valence ||
    metrics.valence ||
    data.valence ||
    null;
  const activationObj =
    results.activation ||
    metrics.activation ||
    data.activation ||
    null;
  const intensityObj =
    results.intensity ||
    metrics.intensity ||
    data.intensity ||
    null;
  const patternObj =
    results.pattern ||
    data.pattern ||
    metrics.pattern ||
    null;
  const prototypeObj =
    results.prototype ||
    data.prototype ||
    metrics.prototype ||
    null;

  if (fields.valence) {
    renderMetricField(fields.valence, valenceObj);
  }
  if (fields.activation) {
    renderMetricField(fields.activation, activationObj);
  }
  if (fields.intensity) {
    renderMetricField(fields.intensity, intensityObj);
  }
  if (fields.pattern) {
    renderMetricField(fields.pattern, patternObj);
  }
  if (fields.prototype) {
    renderMetricField(fields.prototype, prototypeObj);
  }

  if (fields.confidence_metric) {
    const confidenceObj =
      results.confidence ||
      metrics.confidence_detail ||
      null;
    const confidenceNumber =
      typeof metrics.confidence === "number"
        ? metrics.confidence
        : undefined;
    renderMetricField(
      fields.confidence_metric,
      confidenceObj,
      confidenceNumber
    );
  }
}

function applyAnalysisFromApi(data, sourceText) {
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

  const domLabel =
    getResultEmotionLabel(dom) || "N/A";

  const curLabel =
    getResultEmotionLabel(cur) || "N/A";

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

  renderResultsMeta(data);

  const risk = data.risk || {};
  applyRiskToUI(risk);

  lastAnalysisSnapshot = {
    text: sourceText,
    data
  };
}

/* ---------- Analyze button handler ---------- */

if (analyzeBtn && textArea) {
  analyzeBtn.addEventListener("click", async () => {
    const text = textArea.value.trim();
    if (!text) {
      setStatus(
        t("statusEnterText") || "Please enter some text."
      );
      textArea.classList.add("input-error");
      resetToZero();
      lastAnalysisSnapshot = null;
      return;
    }

    setStatus(t("statusAnalyzing") || "Analyzing...");
    textArea.classList.remove("input-error");
    if (analyzeBtn) analyzeBtn.disabled = true;

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

      applyAnalysisFromApi(data, text);
    } catch (err) {
      const msg =
        err && err.message ? err.message : "Unexpected error";
      setStatus(msg, true);
      textArea.classList.add("input-error");
      resetToZero();
      lastAnalysisSnapshot = null;
    } finally {
      if (analyzeBtn) analyzeBtn.disabled = false;
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

/* ---------- Site state: maintenance and notice ---------- */

async function loadSiteState() {
  try {
    const data = await apiFetchJSON("/api/site-state", {
      method: "GET"
    });

    const maintenance = !!data.maintenance_mode;
    const message =
      data.maintenance_message ||
      t("maintenanceMessage") ||
      "Site is currently down due to maintenance. We will be back shortly.";
    const notice = data.notice;

    if (maintenance) {
      if (maintenanceShell) {
        maintenanceShell.classList.remove("hidden");
      }
      if (maintenanceMessageEl) {
        maintenanceMessageEl.textContent = message;
      }
      if (appHeader) appHeader.classList.add("hidden");
      if (appMain) appMain.classList.add("hidden");
      if (appFooter) appFooter.classList.add("hidden");
      if (noticeBanner) noticeBanner.classList.add("hidden");
    } else {
      if (maintenanceShell) {
        maintenanceShell.classList.add("hidden");
      }
      if (appHeader) appHeader.classList.remove("hidden");
      if (appMain) appMain.classList.remove("hidden");
      if (appFooter) appFooter.classList.remove("hidden");

      if (notice && notice.text) {
        if (noticeBanner) {
          noticeBanner.textContent = notice.text;
          noticeBanner.classList.remove("hidden");
        }
      } else if (noticeBanner) {
        noticeBanner.textContent = "";
        noticeBanner.classList.add("hidden");
      }
    }
  } catch (e) {
    if (maintenanceShell) maintenanceShell.classList.add("hidden");
    if (appHeader) appHeader.classList.remove("hidden");
    if (appMain) appMain.classList.remove("hidden");
    if (appFooter) appFooter.classList.remove("hidden");
    if (noticeBanner) {
      noticeBanner.textContent = "";
      noticeBanner.classList.add("hidden");
    }
  }
}

/* ---------- Auth overlays helper ---------- */

function hideAllAuthOverlays() {
  if (authOverlayLogin) authOverlayLogin.classList.remove("show");
  if (authOverlayRegister) authOverlayRegister.classList.remove("show");
  if (authOverlayForgot) authOverlayForgot.classList.remove("show");
}

function openLoginOverlay() {
  hideAllAuthOverlays();
  if (authOverlayLogin) authOverlayLogin.classList.add("show");
  if (loginError) {
    loginError.textContent = "";
    loginError.classList.add("hidden");
  }
}

function openRegisterOverlay() {
  hideAllAuthOverlays();
  if (authOverlayRegister) authOverlayRegister.classList.add("show");
  if (registerError) {
    registerError.textContent = "";
    registerError.classList.add("hidden");
  }
}

function openForgotOverlay() {
  hideAllAuthOverlays();
  if (authOverlayForgot) authOverlayForgot.classList.add("show");
  if (forgotError) {
    forgotError.textContent = "";
    forgotError.classList.add("hidden");
  }
  if (forgotStepIdentity) forgotStepIdentity.classList.remove("hidden");
  if (forgotStepReset) forgotStepReset.classList.add("hidden");
  if (forgotNewPassword) forgotNewPassword.value = "";
  if (forgotConfirmPassword) forgotConfirmPassword.value = "";
}

/* Close auth overlays when background clicked */

[authOverlayLogin, authOverlayRegister, authOverlayForgot].forEach(
  (ov) => {
    if (!ov) return;
    ov.addEventListener("click", (e) => {
      if (e.target === ov) {
        hideAllAuthOverlays();
      }
    });
  }
);

/* ---------- Account header state ---------- */

function applyUserState() {
  const loggedIn = !!(currentUser && currentUser.id);

  if (loggedIn) {
    if (loginBtn) loginBtn.classList.add("hidden");
    if (accountControl) accountControl.classList.remove("hidden");
    if (helpBtn) helpBtn.classList.add("hidden");
    if (settingsControl) settingsControl.classList.add("hidden");

    if (accountNameLabel) {
      const fallback = t("accountLabel") || "Account";
      accountNameLabel.textContent =
        currentUser.first_name || fallback;
    }

    const lang = currentUser.preferred_language || currentLocale;
    setLocale(lang, { persist: false });
    applyUserTheme(currentUser.preferred_theme || null);

    if (addJournalButton) addJournalButton.classList.remove("hidden");
    if (addJournalHint) addJournalHint.classList.remove("hidden");
  } else {
    if (loginBtn) {
      loginBtn.classList.remove("hidden");
      const label = t("loginButtonLabel") || "Log in";
      loginBtn.textContent = label;
    }
    if (accountControl) accountControl.classList.add("hidden");
    if (helpBtn) helpBtn.classList.remove("hidden");
    if (settingsControl) settingsControl.classList.remove("hidden");

    applyGuestTheme();
    setLocale(currentLocale, { persist: true });

    if (addJournalButton) addJournalButton.classList.add("hidden");
    if (addJournalHint) addJournalHint.classList.add("hidden");
  }
}

/* ---------- Fetch current user on load ---------- */

async function fetchCurrentUser() {
  try {
    const data = await apiFetchJSON("/api/auth/me", {
      method: "GET"
    });
    currentUser = data.user || null;
  } catch (e) {
    currentUser = null;
  }
  applyUserState();
}

/* ---------- Auth flows ---------- */

/* Login */

if (loginBtn) {
  loginBtn.addEventListener("click", () => {
    openLoginOverlay();
  });
}

if (cancelLoginBtn) {
  cancelLoginBtn.addEventListener("click", () => {
    hideAllAuthOverlays();
  });
}

if (openRegisterFromLoginBtn) {
  openRegisterFromLoginBtn.addEventListener("click", () => {
    openRegisterOverlay();
  });
}

if (openForgotFromLoginBtn) {
  openForgotFromLoginBtn.addEventListener("click", () => {
    openForgotOverlay();
  });
}

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!loginIdentifierInput || !loginPasswordInput) return;

    const identifier = loginIdentifierInput.value.trim();
    const password = loginPasswordInput.value;

    if (!identifier || !password) {
      if (loginError) {
        loginError.textContent =
          "Email or username and password are required.";
        loginError.classList.remove("hidden");
      }
      return;
    }

    if (submitLoginBtn) submitLoginBtn.disabled = true;

    try {
      const data = await apiFetchJSON("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ identifier, password })
      });
      currentUser = data.user || null;
      hideAllAuthOverlays();
      applyUserState();
    } catch (err) {
      if (loginError) {
        loginError.textContent =
          err.message || "Invalid credentials.";
        loginError.classList.remove("hidden");
      }
    } finally {
      if (submitLoginBtn) submitLoginBtn.disabled = false;
      if (loginPasswordInput) loginPasswordInput.value = "";
    }
  });
}

/* Register */

if (cancelRegisterBtn) {
  cancelRegisterBtn.addEventListener("click", () => {
    hideAllAuthOverlays();
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (
      !registerFirstName ||
      !registerLastName ||
      !registerUsername ||
      !registerEmail ||
      !registerPassword ||
      !registerConfirmPassword
    )
      return;

    const first_name = registerFirstName.value.trim();
    const last_name = registerLastName.value.trim();
    const username = registerUsername.value.trim();
    const email = registerEmail.value.trim();
    const password = registerPassword.value;
    const confirm = registerConfirmPassword.value;

    if (!first_name || !last_name || !username || !email || !password) {
      if (registerError) {
        registerError.textContent = "All fields are required.";
        registerError.classList.remove("hidden");
      }
      return;
    }
    if (password !== confirm) {
      if (registerError) {
        registerError.textContent = "Passwords do not match.";
        registerError.classList.remove("hidden");
      }
      return;
    }

    if (submitRegisterBtn) submitRegisterBtn.disabled = true;

    try {
      const data = await apiFetchJSON("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          first_name,
          last_name,
          username,
          email,
          password
        })
      });
      currentUser = data.user || null;
      hideAllAuthOverlays();
      applyUserState();
    } catch (err) {
      if (registerError) {
        registerError.textContent =
          err.message || "Unable to create account.";
        registerError.classList.remove("hidden");
      }
    } finally {
      if (submitRegisterBtn) submitRegisterBtn.disabled = false;
      if (registerPassword) registerPassword.value = "";
      if (registerConfirmPassword) registerConfirmPassword.value = "";
    }
  });
}

/* Forgot password (two step flow) */

if (cancelForgotBtn) {
  cancelForgotBtn.addEventListener("click", () => {
    hideAllAuthOverlays();
  });
}

if (cancelForgotResetBtn) {
  cancelForgotResetBtn.addEventListener("click", () => {
    hideAllAuthOverlays();
  });
}

if (forgotContinueBtn) {
  forgotContinueBtn.addEventListener("click", () => {
    if (!forgotEmail || !forgotFirstName || !forgotLastName) return;

    const email = forgotEmail.value.trim();
    const first_name = forgotFirstName.value.trim();
    const last_name = forgotLastName.value.trim();

    if (!email || !first_name || !last_name) {
      if (forgotError) {
        forgotError.textContent = "All fields are required.";
        forgotError.classList.remove("hidden");
      }
      return;
    }

    if (forgotError) {
      forgotError.textContent = "";
      forgotError.classList.add("hidden");
    }

    if (forgotStepIdentity) forgotStepIdentity.classList.add("hidden");
    if (forgotStepReset) forgotStepReset.classList.remove("hidden");
  });
}

if (forgotForm) {
  forgotForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (
      !forgotEmail ||
      !forgotFirstName ||
      !forgotLastName ||
      !forgotNewPassword ||
      !forgotConfirmPassword
    )
      return;

    const email = forgotEmail.value.trim();
    const first_name = forgotFirstName.value.trim();
    const last_name = forgotLastName.value.trim();
    const new_password = forgotNewPassword.value;
    const confirm_password = forgotConfirmPassword.value;

    if (
      !email ||
      !first_name ||
      !last_name ||
      !new_password ||
      !confirm_password
    ) {
      if (forgotError) {
        forgotError.textContent = "All fields are required.";
        forgotError.classList.remove("hidden");
      }
      return;
    }

    if (new_password !== confirm_password) {
      if (forgotError) {
        forgotError.textContent = "Passwords do not match.";
        forgotError.classList.remove("hidden");
      }
      return;
    }

    if (submitForgotBtn) submitForgotBtn.disabled = true;

    try {
      await apiFetchJSON("/api/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({
          email,
          first_name,
          last_name,
          new_password,
          confirm_password
        })
      });
      hideAllAuthOverlays();
      openLoginOverlay();
    } catch (err) {
      if (forgotError) {
        forgotError.textContent =
          err.message || "Unable to reset password.";
        forgotError.classList.remove("hidden");
      }
    } finally {
      if (submitForgotBtn) submitForgotBtn.disabled = false;
      if (forgotNewPassword) forgotNewPassword.value = "";
      if (forgotConfirmPassword) forgotConfirmPassword.value = "";
    }
  });
}

/* ---------- Account menu actions ---------- */

if (accountBtn && accountMenu) {
  accountBtn.addEventListener("click", () => {
    const isOpen = accountMenu.classList.contains("open");
    if (isOpen) {
      accountMenu.classList.remove("open");
      accountBtn.setAttribute("aria-expanded", "false");
    } else {
      accountMenu.classList.add("open");
      accountBtn.setAttribute("aria-expanded", "true");
    }
  });

  document.addEventListener("click", (e) => {
    if (!accountMenu.classList.contains("open")) return;
    if (
      accountMenu.contains(e.target) ||
      accountBtn.contains(e.target)
    )
      return;
    accountMenu.classList.remove("open");
    accountBtn.setAttribute("aria-expanded", "false");
  });

  accountMenu.addEventListener("click", async (e) => {
    const btn = e.target.closest(".accountMenuItem");
    if (!btn) return;
    const action = btn.dataset.action;

    if (action === "journal") {
      openJournalOverlay();
    } else if (action === "settings") {
      openAccountSettingsOverlay();
    } else if (action === "logout") {
      try {
        await apiFetchJSON("/api/auth/logout", {
          method: "POST"
        });
      } catch (err) {}
      currentUser = null;
      applyUserState();
    }

    accountMenu.classList.remove("open");
    accountBtn.setAttribute("aria-expanded", "false");
  });
}

/* ---------- Account settings overlay ---------- */

let accountSettingsSnapshot = {
  theme: null,
  language: null
};

function openAccountSettingsOverlay() {
  if (!currentUser) return;
  const currentTheme =
    root.getAttribute("data-theme") || "dark";
  const currentLang = currentLocale;

  accountSettingsSnapshot = {
    theme: currentTheme,
    language: currentLang
  };

  if (accountSettingsOverlay) {
    accountSettingsOverlay.classList.add("show");
  }
  if (accountSettingsError) {
    accountSettingsError.textContent = "";
    accountSettingsError.classList.add("hidden");
  }
}

function closeAccountSettingsOverlay(resetToSnapshot) {
  if (resetToSnapshot && currentUser && accountSettingsSnapshot) {
    applyUserTheme(accountSettingsSnapshot.theme);
    setLocale(accountSettingsSnapshot.language, { persist: false });
  }
  if (accountSettingsOverlay) {
    accountSettingsOverlay.classList.remove("show");
  }
}

if (accountSettingsOverlay) {
  accountSettingsOverlay.addEventListener("click", (e) => {
    if (e.target === accountSettingsOverlay) {
      closeAccountSettingsOverlay(true);
    }
  });
}

if (cancelAccountSettingsBtn) {
  cancelAccountSettingsBtn.addEventListener("click", () => {
    closeAccountSettingsOverlay(true);
  });
}

if (accountThemeToggle) {
  accountThemeToggle.addEventListener("click", () => {
    if (!currentUser) return;
    const current =
      root.getAttribute("data-theme") === "light"
        ? "light"
        : "dark";
    const next = current === "dark" ? "light" : "dark";
    applyUserTheme(next);
    accountSettingsSnapshot.theme = next;
  });
}

if (accountLangToggle && accountLangMenu) {
  accountLangToggle.addEventListener("click", () => {
    const isOpen = accountLangMenu.classList.contains("open");
    if (isOpen) {
      accountLangMenu.classList.remove("open");
      accountLangToggle.setAttribute("aria-expanded", "false");
    } else {
      accountLangMenu.classList.add("open");
      accountLangToggle.setAttribute("aria-expanded", "true");
    }
  });

  accountLangMenu.addEventListener("click", (e) => {
    const btn = e.target.closest(".langOption");
    if (!btn) return;
    const code = btn.dataset.locale;
    if (!code) return;
    const normalized = normalizeLocaleCode(code);
    accountLangMenu.classList.remove("open");
    accountLangToggle.setAttribute("aria-expanded", "false");
    accountSettingsSnapshot.language = normalized;
    setLocale(normalized, { persist: false });
  });

  document.addEventListener("click", (e) => {
    if (!accountLangMenu.classList.contains("open")) return;
    if (
      accountLangMenu.contains(e.target) ||
      accountLangToggle.contains(e.target)
    )
      return;
    accountLangMenu.classList.remove("open");
    accountLangToggle.setAttribute("aria-expanded", "false");
  });
}

if (accountSettingsForm) {
  accountSettingsForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentUser) return;

    const preferred_language = accountSettingsSnapshot.language;
    const preferred_theme = accountSettingsSnapshot.theme;

    if (saveAccountSettingsBtn) saveAccountSettingsBtn.disabled = true;

    try {
      const data = await apiFetchJSON("/api/auth/update-settings", {
        method: "POST",
        body: JSON.stringify({
          preferred_language,
          preferred_theme
        })
      });
      currentUser = data.user || currentUser;
      applyUserTheme(currentUser.preferred_theme || null);
      setLocale(currentUser.preferred_language || currentLocale, {
        persist: false
      });
      if (accountSettingsError) {
        accountSettingsError.textContent = "";
        accountSettingsError.classList.add("hidden");
      }
      closeAccountSettingsOverlay(false);
    } catch (err) {
      if (accountSettingsError) {
        accountSettingsError.textContent =
          err.message || "Unable to save settings.";
        accountSettingsError.classList.remove("hidden");
      }
    } finally {
      if (saveAccountSettingsBtn)
        saveAccountSettingsBtn.disabled = false;
    }
  });
}

/* ---------- Journal overlay and APIs ---------- */

function openJournalOverlay() {
  if (!currentUser) {
    openLoginOverlay();
    return;
  }
  if (journalOverlay) {
    journalOverlay.classList.add("show");
  }
  if (journalEmptyState) journalEmptyState.classList.remove("hidden");
  if (journalDetail) journalDetail.classList.add("hidden");
  loadJournals();
}

function closeJournalOverlay() {
  if (journalOverlay) {
    journalOverlay.classList.remove("show");
  }
  currentJournal = null;
  isEditingJournal = false;
  isCreatingJournal = false;
}

if (closeJournalBtn) {
  closeJournalBtn.addEventListener("click", () => {
    closeJournalOverlay();
  });
}

if (journalOverlay) {
  journalOverlay.addEventListener("click", (e) => {
    if (e.target === journalOverlay) {
      closeJournalOverlay();
    }
  });
}

if (journalBackButton) {
  journalBackButton.addEventListener("click", () => {
    if (journalDetail) journalDetail.classList.add("hidden");
    if (journalEmptyState) journalEmptyState.classList.remove("hidden");
  });
}

async function loadJournals() {
  if (!currentUser) return;
  try {
    const data = await apiFetchJSON("/api/journals", {
      method: "GET"
    });
    journals = data.journals || [];
    renderJournalLists();
  } catch (err) {
  }
}

function renderJournalLists() {
  if (!pinnedJournalList || !journalList) return;

  pinnedJournalList.innerHTML = "";
  journalList.innerHTML = "";

  const pinned = journals.filter((j) => j.is_pinned);
  const others = journals.filter((j) => !j.is_pinned);

  if (pinned.length === 0) {
    pinnedJournalList.classList.add("hidden");
    if (pinnedSectionHeader) pinnedSectionHeader.classList.add("hidden");
  } else {
    pinnedJournalList.classList.remove("hidden");
    if (pinnedSectionHeader) pinnedSectionHeader.classList.remove("hidden");
  }

  function makeRow(journal) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "journalListItem";

    const title = document.createElement("div");
    title.className = "journalListTitle";
    title.textContent =
      journal.title || t("journalDefaultTitle") || "Journal entry";

    const meta = document.createElement("div");
    meta.className = "journalListMeta";
    meta.textContent = formatDateTime(journal.created_at);

    btn.appendChild(title);
    btn.appendChild(meta);

    if (journal.has_self_harm_flag) {
      const flag = document.createElement("span");
      flag.className = "journalListFlag";
      flag.textContent = "⚠️";
      btn.appendChild(flag);
    }

    btn.addEventListener("click", () => {
      openJournalDetail(journal.id);
    });

    return btn;
  }

  pinned.forEach((j) => {
    pinnedJournalList.appendChild(makeRow(j));
  });
  others.forEach((j) => {
    journalList.appendChild(makeRow(j));
  });
}

function formatDateTime(value) {
  if (!value) return "";
  try {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleString();
  } catch (e) {
    return "";
  }
}

async function openJournalDetail(journalId) {
  if (!currentUser) return;
  try {
    const data = await apiFetchJSON(`/api/journals/${journalId}`, {
      method: "GET"
    });
    const journal = data.journal;
    currentJournal = journal;
    isEditingJournal = false;
    isCreatingJournal = false;

    if (journalEmptyState) journalEmptyState.classList.add("hidden");
    if (journalDetail) journalDetail.classList.remove("hidden");
    if (journalDetailActionsRow)
      journalDetailActionsRow.classList.add("hidden");

    if (journalDetailTitle) {
      journalDetailTitle.textContent =
        journal.title || t("journalDefaultTitle") || "Journal entry";
    }
    if (journalDetailMeta) {
      journalDetailMeta.textContent = formatDateTime(
        journal.created_at
      );
    }
    if (journalDetailSourceText) {
      journalDetailSourceText.textContent = journal.source_text || "";
    }

    const analysis = journal.analysis_json || {};
    if (journalDetailAnalysis) {
      journalDetailAnalysis.textContent =
        buildAnalysisSnapshotText(analysis);
    }

    if (journalDetailText) {
      journalDetailText.value = journal.journal_text || "";
      journalDetailText.disabled = true;
    }

    const results = (analysis && analysis.results) || {};
    const dom = results.dominant || {};
    const cur = results.current || {};
    const metrics = (analysis && analysis.metrics) || {};

    if (journalDetailDominant) {
      journalDetailDominant.textContent =
        getResultEmotionLabel(dom) || "N/A";
    }
    if (journalDetailEmotion) {
      journalDetailEmotion.textContent =
        getResultEmotionLabel(cur) || "N/A";
    }
    if (journalDetailBarnhart) {
      let barnVal = null;
      if (
        metrics.barnhart &&
        typeof metrics.barnhart.score === "number"
      ) {
        barnVal = metrics.barnhart.score;
      } else if (typeof metrics.confidence === "number") {
        barnVal = metrics.confidence;
      }
      journalDetailBarnhart.textContent =
        typeof barnVal === "number" ? barnVal.toFixed(3) : "N/A";
    }

    if (journalFlagButton) {
      if (journal.has_self_harm_flag) {
        journalFlagButton.classList.remove("hidden");
      } else {
        journalFlagButton.classList.add("hidden");
      }
    }

    if (journalPinToggleButton) {
      journalPinToggleButton.textContent = journal.is_pinned
        ? t("journalUnpin") || "Unpin"
        : t("journalPin") || "Pin";
    }
  } catch (err) {
  }
}

if (journalFlagButton) {
  journalFlagButton.addEventListener("click", () => {
    showCrisisModal();
  });
}

/* Journal edit menu */

if (journalEditMenuBtn && journalEditMenuDropdown) {
  journalEditMenuBtn.addEventListener("click", () => {
    const isOpen = !journalEditMenuDropdown.classList.contains(
      "hidden"
    );
    if (isOpen) {
      journalEditMenuDropdown.classList.add("hidden");
    } else {
      journalEditMenuDropdown.classList.remove("hidden");
    }
  });

  document.addEventListener("click", (e) => {
    if (journalEditMenuDropdown.classList.contains("hidden")) return;
    if (
      journalEditMenuDropdown.contains(e.target) ||
      journalEditMenuBtn.contains(e.target)
    )
      return;
    journalEditMenuDropdown.classList.add("hidden");
  });
}

if (journalEditButton) {
  journalEditButton.addEventListener("click", () => {
    if (!currentJournal || !journalDetailText) return;
    isEditingJournal = true;
    isCreatingJournal = false;
    journalDetailText.disabled = false;
    if (journalDetailActionsRow)
      journalDetailActionsRow.classList.remove("hidden");
    if (journalEditMenuDropdown)
      journalEditMenuDropdown.classList.add("hidden");
  });
}

if (journalPinToggleButton) {
  journalPinToggleButton.addEventListener("click", async () => {
    if (!currentJournal) return;
    if (journalEditMenuDropdown)
      journalEditMenuDropdown.classList.add("hidden");
    try {
      const nextPinned = !currentJournal.is_pinned;
      const data = await apiFetchJSON(
        `/api/journals/${currentJournal.id}/pin`,
        {
          method: "POST",
          body: JSON.stringify({ is_pinned: nextPinned })
        }
      );
      currentJournal = data.journal || currentJournal;
      if (journalPinToggleButton) {
        journalPinToggleButton.textContent = currentJournal.is_pinned
          ? t("journalUnpin") || "Unpin"
          : t("journalPin") || "Pin";
      }
      await loadJournals();
    } catch (err) {
    }
  });
}

/* Journal delete menu item and confirmation */

if (journalDeleteButton) {
  journalDeleteButton.addEventListener("click", () => {
    if (!currentJournal || !journalDeleteConfirmOverlay) return;
    if (journalEditMenuDropdown) {
      journalEditMenuDropdown.classList.add("hidden");
    }
    journalDeleteConfirmOverlay.classList.add("show");
  });
}

if (cancelJournalDeleteBtn && journalDeleteConfirmOverlay) {
  cancelJournalDeleteBtn.addEventListener("click", () => {
    journalDeleteConfirmOverlay.classList.remove("show");
  });
}

if (journalDeleteConfirmOverlay) {
  journalDeleteConfirmOverlay.addEventListener("click", (e) => {
    if (e.target === journalDeleteConfirmOverlay) {
      journalDeleteConfirmOverlay.classList.remove("show");
    }
  });
}

if (confirmJournalDeleteBtn && journalDeleteConfirmOverlay) {
  confirmJournalDeleteBtn.addEventListener("click", async () => {
    if (!currentJournal) {
      journalDeleteConfirmOverlay.classList.remove("show");
      return;
    }
    try {
      await apiFetchJSON(`/api/journals/${currentJournal.id}`, {
        method: "DELETE"
      });
      currentJournal = null;
      if (journalDetail) journalDetail.classList.add("hidden");
      if (journalEmptyState)
        journalEmptyState.classList.remove("hidden");
      await loadJournals();
    } catch (err) {
    } finally {
      journalDeleteConfirmOverlay.classList.remove("show");
    }
  });
}

if (cancelJournalEditBtn) {
  cancelJournalEditBtn.addEventListener("click", () => {
    if (!currentJournal || !journalDetailText) return;
    journalDetailText.value = currentJournal.journal_text || "";
    journalDetailText.disabled = true;
    isEditingJournal = false;
    isCreatingJournal = false;
    if (journalDetailActionsRow)
      journalDetailActionsRow.classList.add("hidden");
  });
}

if (saveJournalEditBtn) {
  saveJournalEditBtn.addEventListener("click", async () => {
    if (!currentJournal || !journalDetailText) return;
    const updatedText = journalDetailText.value;
    try {
      const data = await apiFetchJSON(
        `/api/journals/${currentJournal.id}`,
        {
          method: "PUT",
          body: JSON.stringify({
            journal_text: updatedText
          })
        }
      );
      currentJournal = data.journal || currentJournal;
      journalDetailText.disabled = true;
      isEditingJournal = false;
      isCreatingJournal = false;
      if (journalDetailActionsRow)
        journalDetailActionsRow.classList.add("hidden");
      await loadJournals();
    } catch (err) {
    }
  });
}

/* ---------- Add to journal from analysis ---------- */

let newJournalOverlay = null;
let newJournalSourceEl = null;
let newJournalAnalysisEl = null;
let newJournalTextEl = null;
let newJournalCancelBtn = null;
let newJournalSaveBtn = null;

function ensureNewJournalOverlay() {
  if (newJournalOverlay) return;

  const overlayEl = document.createElement("div");
  overlayEl.id = "newJournalOverlay";
  overlayEl.className = "overlay";
  overlayEl.setAttribute("role", "dialog");
  overlayEl.setAttribute("aria-modal", "true");

  const modal = document.createElement("div");
  modal.className = "modal authModal";

  const header = document.createElement("div");
  header.className = "journalHeaderRow";

  const h2 = document.createElement("h2");
  h2.textContent = t("journalNewTitle") || "New journal entry";

  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "ghost";
  closeBtn.textContent = t("journalCancel") || "Cancel";

  header.appendChild(h2);
  header.appendChild(closeBtn);

  const content = document.createElement("div");
  content.className = "journalNewContent";

  const srcBlock = document.createElement("div");
  srcBlock.className = "journalSourceBlock";
  const srcTitle = document.createElement("h4");
  srcTitle.textContent =
    t("journalOriginalTextLabel") || "Original text";
  newJournalSourceEl = document.createElement("p");
  srcBlock.appendChild(srcTitle);
  srcBlock.appendChild(newJournalSourceEl);

  const analBlock = document.createElement("div");
  analBlock.className = "journalAnalysisBlock";
  const analTitle = document.createElement("h4");
  analTitle.textContent =
    t("journalAnalysisSnapshotLabel") || "Analysis snapshot";
  newJournalAnalysisEl = document.createElement("pre");
  analBlock.appendChild(analTitle);
  analBlock.appendChild(newJournalAnalysisEl);

  const textBlock = document.createElement("div");
  textBlock.className = "journalTextBlock";
  const textTitle = document.createElement("h4");
  textTitle.textContent =
    t("journalJournalLabel") || "Journal";
  newJournalTextEl = document.createElement("textarea");
  newJournalTextEl.className = "journalEditArea";
  textBlock.appendChild(textTitle);
  textBlock.appendChild(newJournalTextEl);

  content.appendChild(srcBlock);
  content.appendChild(analBlock);
  content.appendChild(textBlock);

  const actionsRow = document.createElement("div");
  actionsRow.className = "actionsRow";
  newJournalCancelBtn = document.createElement("button");
  newJournalCancelBtn.type = "button";
  newJournalCancelBtn.className = "ghost";
  newJournalCancelBtn.textContent =
    t("journalCancel") || "Cancel";
  newJournalSaveBtn = document.createElement("button");
  newJournalSaveBtn.type = "button";
  newJournalSaveBtn.className = "btn";
  newJournalSaveBtn.textContent =
    t("journalSave") || "Save";
  actionsRow.appendChild(newJournalCancelBtn);
  actionsRow.appendChild(newJournalSaveBtn);

  modal.appendChild(header);
  modal.appendChild(content);
  modal.appendChild(actionsRow);
  overlayEl.appendChild(modal);
  document.body.appendChild(overlayEl);

  newJournalOverlay = overlayEl;

  overlayEl.addEventListener("click", (e) => {
    if (e.target === overlayEl) {
      closeNewJournalOverlay();
    }
  });
  closeBtn.addEventListener("click", () => {
    closeNewJournalOverlay();
  });
  newJournalCancelBtn.addEventListener("click", () => {
    closeNewJournalOverlay();
  });
  newJournalSaveBtn.addEventListener("click", () => {
    saveNewJournalEntry();
  });
}

function openNewJournalOverlay() {
  if (!lastAnalysisSnapshot) {
    setStatus(
      t("statusNeedAnalysis") ||
        "Run an analysis before adding to journal."
    );
    return;
  }
  if (!currentUser) {
    openLoginOverlay();
    return;
  }
  ensureNewJournalOverlay();
  const { text, data } = lastAnalysisSnapshot;
  if (newJournalSourceEl) {
    newJournalSourceEl.textContent = text || "";
  }
  if (newJournalAnalysisEl) {
    newJournalAnalysisEl.textContent =
      buildAnalysisSnapshotText(data || {});
  }
  if (newJournalTextEl) {
    newJournalTextEl.value = "";
  }
  if (newJournalOverlay) {
    newJournalOverlay.classList.add("show");
  }
}

function closeNewJournalOverlay() {
  if (newJournalOverlay) {
    newJournalOverlay.classList.remove("show");
  }
}

async function saveNewJournalEntry() {
  if (!lastAnalysisSnapshot || !currentUser || !newJournalTextEl)
    return;
  const { text, data } = lastAnalysisSnapshot;
  const journal_text = newJournalTextEl.value || "";

  const baseTitle = t("journalDefaultTitle") || "Journal entry";
  const title = `${baseTitle} ${new Date().toLocaleString()}`;

  try {
    await apiFetchJSON("/api/journals", {
      method: "POST",
      body: JSON.stringify({
        title,
        source_text: text,
        analysis_json: data,
        journal_text
      })
    });
    closeNewJournalOverlay();
    if (journalOverlay && journalOverlay.classList.contains("show")) {
      await loadJournals();
    }
  } catch (err) {
  }
}

if (addJournalButton) {
  addJournalButton.addEventListener("click", () => {
    if (!currentUser) {
      openLoginOverlay();
      return;
    }
    openNewJournalOverlay();
  });
}

/* ---------- Initial setup ---------- */

function initialSetup() {
  initBars();
  buildLangMenuFor(langMenu);
  buildLangMenuFor(accountLangMenu);
  setLocale(currentLocale);
  renderBarsZero();
  wordCountAndLimit();
  applyGuestTheme();
  loadSiteState();
  fetchCurrentUser();
}

document.addEventListener("DOMContentLoaded", initialSetup);
