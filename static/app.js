const chatEl = document.getElementById("chat");
const form = document.getElementById("chatForm");
const promptEl = document.getElementById("prompt");
const sendBtn = document.getElementById("sendBtn");
const newChatBtn = document.getElementById("newChatBtn");
const modelSelect = document.getElementById("modelSelect");
const emptyStateTpl = document.getElementById("tpl-empty-state");
const conversationsListEl = document.getElementById("conversationsList");
const chatTitleHeader = document.getElementById("chatTitleHeader");
const sidebar = document.getElementById("sidebar");
const sidebarOverlay = document.getElementById("sidebarOverlay");
const toggleSidebarBtn = document.getElementById("toggleSidebarBtn");
const closeSidebarBtn = document.getElementById("closeSidebarBtn");
const attachBtn = document.getElementById("attachBtn");
const attachMenu = document.getElementById("attachMenu");
const menuAddFiles = document.getElementById("menuAddFiles");
const menuAddPhotos = document.getElementById("menuAddPhotos");
const fileInputDocs = document.getElementById("fileInputDocs");
const fileInputImages = document.getElementById("fileInputImages");
const presetsBtn = document.getElementById("presetsBtn");
const presetsMenu = document.getElementById("presetsMenu");
const attachmentPreview = document.getElementById("attachmentPreview");
const attachmentName = document.getElementById("attachmentName");
const attachmentSize = document.getElementById("attachmentSize");
const removeAttachmentBtn = document.getElementById("removeAttachmentBtn");
const collapseSidebarBtn = document.getElementById("collapseSidebarBtn");
const sidebarSearchInput = document.getElementById("sidebarSearchInput");
const sidebarSearchClearBtn = document.getElementById("sidebarSearchClearBtn");
const themeToggleBtn = document.getElementById("themeToggleBtn");
const editChatTitleBtn = document.getElementById("editChatTitleBtn");

let currentMode = localStorage.getItem("cortex_mode") || "auto";

// Microphone & Artifact Split Panel Elements
const micBtn = document.getElementById("micBtn");
const artifactSplitPanel = document.getElementById("artifactSplitPanel");
const artifactTitle = document.getElementById("artifactTitle");
const artifactSubtitle = document.getElementById("artifactSubtitle");
const artifactTabPreview = document.getElementById("artifactTabPreview");
const artifactTabCode = document.getElementById("artifactTabCode");
const artifactIframe = document.getElementById("artifactIframe");
const artifactCodeWrap = document.getElementById("artifactCodeWrap");
const artifactCodeContent = document.getElementById("artifactCodeContent");
const artifactCopyBtn = document.getElementById("artifactCopyBtn");
const artifactDownloadBtn = document.getElementById("artifactDownloadBtn");
const artifactCloseBtn = document.getElementById("artifactCloseBtn");

// Sidebar, Topbar, & Suite Elements
const sidebarArtifactsBtn = document.getElementById("sidebarArtifactsBtn");
const sidebarArtifactsCount = document.getElementById("sidebarArtifactsCount");
const topbarUsagePill = document.getElementById("topbarUsagePill");
const topbarUsageText = document.getElementById("topbarUsageText");
const topbarUsageBar = document.getElementById("topbarUsageBar");
const guideBtn = document.getElementById("guideBtn");
const guideDrawer = document.getElementById("guideDrawer");
const guideCloseBtn = document.getElementById("guideCloseBtn");

// Artifacts Library View Elements
const artifactsView = document.getElementById("artifactsView");
const artifactsGrid = document.getElementById("artifactsGrid");
const artifactsSearchInput = document.getElementById("artifactsSearchInput");
const artifactsCloseViewBtn = document.getElementById("artifactsCloseViewBtn");
const artifactsCountBadge = document.getElementById("artifactsCountBadge");

// Onboarding Tour & Confetti Elements
const tourOverlay = document.getElementById("tourOverlay");
const tourSpotlight = document.getElementById("tourSpotlight");
const tourCard = document.getElementById("tourCard");
const tourCloseBtn = document.getElementById("tourCloseBtn");
const tourSkipBtn = document.getElementById("tourSkipBtn");
const tourPrevBtn = document.getElementById("tourPrevBtn");
const tourNextBtn = document.getElementById("tourNextBtn");
const confettiCanvas = document.getElementById("confettiCanvas");
const celebrationToast = document.getElementById("celebrationToast");
const quotaToast = document.getElementById("quotaToast");

// Landing Page & Auth Elements
const landingView = document.getElementById("landingView");
const appView = document.getElementById("appView");
const navSignInBtn = document.getElementById("navSignInBtn");
const navRegisterBtn = document.getElementById("navRegisterBtn");
const heroSignInBtn = document.getElementById("heroSignInBtn");
const heroGetStartedBtn = document.getElementById("heroGetStartedBtn");
const showcaseGetStartedBtn = document.getElementById("showcaseGetStartedBtn");
const bottomGetStartedBtn = document.getElementById("bottomGetStartedBtn");
const savingsGetStartedBtn = document.getElementById("savingsGetStartedBtn");
const sidebarBrandBtn = document.getElementById("sidebarBrandBtn");

const authModal = document.getElementById("authModal");
const authModalCloseBtn = document.getElementById("authModalCloseBtn");
const authModalTitle = document.getElementById("authModalTitle");
const authModalSubtitle = document.getElementById("authModalSubtitle");
const tabSignIn = document.getElementById("tabSignIn");
const tabRegister = document.getElementById("tabRegister");
const authErrorAlert = document.getElementById("authErrorAlert");
const authForm = document.getElementById("authForm");
const authUsername = document.getElementById("authUsername");
const emailGroup = document.getElementById("emailGroup");
const authEmail = document.getElementById("authEmail");
const authPassword = document.getElementById("authPassword");
const authSubmitBtn = document.getElementById("authSubmitBtn");
const authTogglePasswordBtn = document.getElementById("authTogglePasswordBtn");
const passwordStrengthWrap = document.getElementById("passwordStrengthWrap");
const passwordStrengthBar = document.getElementById("passwordStrengthBar");
const passwordStrengthText = document.getElementById("passwordStrengthText");
const authDemoBtn = document.getElementById("authDemoBtn");
const showcaseDemoBtn = document.getElementById("showcaseDemoBtn");

// Interactive Claude Code Terminal Simulator Elements
const terminalSimWindow = document.getElementById("terminalSimWindow");
const simTypedText = document.getElementById("simTypedText");
const simStepsContainer = document.getElementById("simStepsContainer");
const simCustomInput = document.getElementById("simCustomInput");
const simRunBtn = document.getElementById("simRunBtn");

// Interactive Frontier Models Fleet Elements
const modelsFleetGrid = document.getElementById("modelsFleetGrid");
const modelInspectorCard = document.getElementById("modelInspectorCard");
const inspectorModelName = document.getElementById("inspectorModelName");
const inspectorModelStatus = document.getElementById("inspectorModelStatus");
const inspectorTryBtn = document.getElementById("inspectorTryBtn");
const inspectorArch = document.getElementById("inspectorArch");
const inspectorContext = document.getElementById("inspectorContext");
const inspectorTtft = document.getElementById("inspectorTtft");
const inspectorTools = document.getElementById("inspectorTools");

const userAvatar = document.getElementById("userAvatar");
const userNameDisplay = document.getElementById("userNameDisplay");
const signOutBtn = document.getElementById("signOutBtn");
const userProfileBtn = document.getElementById("userProfileBtn");
const userProfileMenu = document.getElementById("userProfileMenu");
const userMenuAnchor = document.querySelector(".user-menu-anchor");
const userMenuEmail = document.getElementById("userMenuEmail");
const menuSettingsBtn = document.getElementById("menuSettingsBtn");
const menuSignOutBtn = document.getElementById("menuSignOutBtn");

// Settings Modal Elements
const settingsModal = document.getElementById("settingsModal");
const settingsModalCloseBtn = document.getElementById("settingsModalCloseBtn");
const settingsModalDoneBtn = document.getElementById("settingsModalDoneBtn");
const settingsAvatar = document.getElementById("settingsAvatar");
const settingsUsername = document.getElementById("settingsUsername");
const settingsEmail = document.getElementById("settingsEmail");
const settingsThemeDarkBtn = document.getElementById("settingsThemeDarkBtn");
const settingsThemeLightBtn = document.getElementById("settingsThemeLightBtn");

// Image Lightbox Modal Elements
const imageLightboxModal = document.getElementById("imageLightboxModal");
const lightboxFilename = document.getElementById("lightboxFilename");
const lightboxSize = document.getElementById("lightboxSize");
const lightboxImage = document.getElementById("lightboxImage");
const lightboxZoomLevel = document.getElementById("lightboxZoomLevel");
const lightboxZoomInBtn = document.getElementById("lightboxZoomInBtn");
const lightboxZoomOutBtn = document.getElementById("lightboxZoomOutBtn");
const lightboxResetZoomBtn = document.getElementById("lightboxResetZoomBtn");
const lightboxDownloadBtn = document.getElementById("lightboxDownloadBtn");
const lightboxCloseBtn = document.getElementById("lightboxCloseBtn");
const lightboxBody = document.getElementById("lightboxBody");

// Project Workspaces Elements & State
const projectModal = document.getElementById("projectModal");
const projectModalHeading = document.getElementById("projectModalHeading");
const projectModalCloseBtn = document.getElementById("projectModalCloseBtn");
const projectNameInput = document.getElementById("projectNameInput");
const projectDescInput = document.getElementById("projectDescInput");
const projectPromptInput = document.getElementById("projectPromptInput");
const projectModalDeleteBtn = document.getElementById("projectModalDeleteBtn");
const projectModalCancelBtn = document.getElementById("projectModalCancelBtn");
const projectModalSaveBtn = document.getElementById("projectModalSaveBtn");
const createProjectBtn = document.getElementById("createProjectBtn");
const projectsListContainer = document.getElementById("projectsListContainer");

let currentProjectId = ""; // Empty string means "All Chats"
let userProjects = [];
let editingProjectId = null;

let authToken = localStorage.getItem("cortex_auth_token") || null;
let currentUser = null;
let authMode = "login"; // "login" | "register"

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  return headers;
}

let currentConversationId = null;
let conversations = [];
let messages = []; // { id, role, content, tools_used }
let busy = false;
let abortController = null;
let attachedFile = null; // { filename, size, text, truncated }
let artifactIdCounter = 0;
const artifactRegistry = new Map();
let docIdCounter = 0;
const docRegistry = new Map();

const CORTEX_AVATAR_HTML = `
  <div class="avatar ai" title="Cortex Agent" aria-label="Cortex Agent">
    <svg viewBox="0 0 32 32" width="18" height="18" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M16 3L27 9.5V22.5L16 29L5 22.5V9.5L16 3Z" stroke="#22c55e" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
      <path d="M16 8.5L22.5 12.25V19.75L16 23.5L9.5 19.75V12.25L16 8.5Z" fill="#22c55e" fill-opacity="0.25" stroke="#22c55e" stroke-width="1.7" stroke-linejoin="round"/>
      <circle cx="16" cy="16" r="2.5" fill="#4ade80"/>
      <path d="M16 3V8.5M16 23.5V29M5 9.5L9.5 12.25M22.5 19.75L27 22.5M27 9.5L22.5 12.25M9.5 19.75L5 22.5" stroke="#22c55e" stroke-width="1.6" stroke-linecap="round"/>
    </svg>
  </div>
`.trim();

const ICONS = {
  copy: `<svg viewBox="0 0 24 24" fill="none" width="13" height="13"><rect x="8" y="8" width="12" height="12" rx="2" stroke="currentColor" stroke-width="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" stroke="currentColor" stroke-width="2"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" width="13" height="13"><path d="M5 13l4 4L19 7" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  code: `<svg viewBox="0 0 24 24" fill="none" width="13" height="13" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
  retry: `<svg viewBox="0 0 24 24" fill="none" width="13" height="13"><path d="M4 4v6h6M20 20v-6h-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M5.5 15a7 7 0 1 0 1-8.5L4 10M18.5 9a7 7 0 0 1-1 8.5L20 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  tool: `<svg viewBox="0 0 24 24" fill="none" width="12" height="12"><path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L4 17v3h3l5.3-5.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2-2 2.5-2.5z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>`,
  trash: `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`,
  chevron: `<svg class="chevron" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>`,
  download: `<svg viewBox="0 0 24 24" fill="none" width="13" height="13" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>`,
  file: `<svg viewBox="0 0 24 24" fill="none" width="14" height="14" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
  eye: `<svg viewBox="0 0 24 24" fill="none" width="13" height="13" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`,
  pin: `<svg viewBox="0 0 24 24" fill="none" width="13" height="13" stroke="currentColor" stroke-width="2"><line x1="12" y1="17" x2="12" y2="22"/><path d="M5 17h14l-1.5-5.5 1-3.5H5.5l1 3.5z"/><line x1="9" y1="3" x2="15" y2="3"/></svg>`,
  pinnedActive: `<svg viewBox="0 0 24 24" fill="currentColor" width="13" height="13"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>`,
  edit: `<svg viewBox="0 0 24 24" fill="none" width="13" height="13" stroke="currentColor" stroke-width="2"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg>`,
  branch: `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" y1="3" x2="6" y2="15"></line><circle cx="18" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><path d="M18 9a9 9 0 0 1-9 9"></path></svg>`,
  thumbUp: `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>`,
  thumbDown: `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path></svg>`,
};

const TOOL_LABELS = {
  calculator: "Calculator",
  web_search: "Web search",
  fetch_webpage: "Webpage reader",
  wikipedia_lookup: "Wikipedia",
  weather_lookup: "Weather",
  current_datetime: "Date & time",
  document_reader: "Document extraction",
  code_generator: "Code generation",
  chart_renderer: "Interactive Chart",
  remember: "Memory Storage",
};

const TOOL_ICONS = {
  calculator: `<svg viewBox="0 0 24 24" fill="none" width="12" height="12" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="8" y2="10"/><line x1="12" y1="10" x2="12" y2="10"/><line x1="16" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="8" y2="14"/><line x1="12" y1="14" x2="12" y2="14"/><line x1="16" y1="14" x2="16" y2="14"/><line x1="8" y1="18" x2="8" y2="18"/><line x1="12" y1="18" x2="12" y2="18"/><line x1="16" y1="18" x2="16" y2="18"/></svg>`,
  web_search: `<svg viewBox="0 0 24 24" fill="none" width="12" height="12" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
  fetch_webpage: `<svg viewBox="0 0 24 24" fill="none" width="12" height="12" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`,
  wikipedia_lookup: `<svg viewBox="0 0 24 24" fill="none" width="12" height="12" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`,
  weather_lookup: `<svg viewBox="0 0 24 24" fill="none" width="12" height="12" stroke="currentColor" stroke-width="2"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>`,
  current_datetime: `<svg viewBox="0 0 24 24" fill="none" width="12" height="12" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
  document_reader: `<svg viewBox="0 0 24 24" fill="none" width="12" height="12" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
  code_generator: `<svg viewBox="0 0 24 24" fill="none" width="12" height="12" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`,
  chart_renderer: `<svg viewBox="0 0 24 24" fill="none" width="12" height="12" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  remember: `<svg viewBox="0 0 24 24" fill="none" width="12" height="12" stroke="currentColor" stroke-width="2"><path d="M12 2a5 5 0 0 1 5 5v1a5 5 0 0 1-10 0V7a5 5 0 0 1 5-5z"/><path d="M19 11v1a7 7 0 0 1-14 0v-1"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>`,
};

const EXT_MAP = {
  markdown: "md",
  md: "md",
  python: "py",
  py: "py",
  javascript: "js",
  js: "js",
  typescript: "ts",
  ts: "ts",
  json: "json",
  html: "html",
  htm: "html",
  css: "css",
  csv: "csv",
  sql: "sql",
  bash: "sh",
  sh: "sh",
  shell: "sh",
  yaml: "yaml",
  yml: "yml",
  xml: "xml",
  text: "txt",
  txt: "txt",
};

const MIME_MAP = {
  md: "text/markdown;charset=utf-8",
  py: "text/x-python;charset=utf-8",
  js: "application/javascript;charset=utf-8",
  ts: "application/typescript;charset=utf-8",
  json: "application/json;charset=utf-8",
  html: "text/html;charset=utf-8",
  csv: "text/csv;charset=utf-8",
  sql: "text/plain;charset=utf-8",
  sh: "text/x-shellscript;charset=utf-8",
  yaml: "text/yaml;charset=utf-8",
  yml: "text/yaml;charset=utf-8",
  txt: "text/plain;charset=utf-8",
};

function healMarkdownPlots(text) {
  if (!text) return "";
  let s = String(text);

  // 1. Fix split markdown image tags: ![alt]\n(data:...) or ![alt]\r\n(data:...)
  s = s.replace(/!\[([^\]]*)\]\s*\r?\n+\s*\(((?:data:image\/[a-zA-Z0-9+\-_]+;base64,[A-Za-z0-9+/=]+|https?:\/\/[^\)\s]+))\)/g, (m, alt, url) => {
    return '![' + alt + '](' + url + ')';
  });

  // 2. Fix parenthesized standalone data URIs: (data:image/png;base64,iVBORw0KGgo...)
  s = s.replace(/(?:^|\n)[ \t]*\(((?:data:image\/[a-zA-Z0-9+\-_]+;base64,[A-Za-z0-9+/=]{20,}))\)[ \t]*(?:\n|$)/g, (m, uri) => {
    return '\n\n![Generated Plot](' + uri + ')\n\n';
  });

  // 3. Fix raw naked data URIs standing alone on their own line: data:image/png;base64,iVBORw0KGgo...
  s = s.replace(/(?:^|\n)[ \t]*(data:image\/[a-zA-Z0-9+\-_]+;base64,[A-Za-z0-9+/=]{20,})[ \t]*(?:\n|$)/g, (m, uri) => {
    return '\n\n![Generated Plot](' + uri + ')\n\n';
  });

  // 4. Fix split within normal lines if LLM emitted [alt]\n(data:...) without leading !:
  s = s.replace(/(?:^|[^!])\[([^\]]*)\]\s*\r?\n+\s*\((data:image\/[a-zA-Z0-9+\-_]+;base64,[A-Za-z0-9+/=]+)\)/g, (m, alt, uri) => {
    return '\n\n![' + alt + '](' + uri + ')\n\n';
  });

  return s;
}

function cleanMarkdownFences(text) {
  if (!text) return "";
  let s = healMarkdownPlots(String(text).trim());
  // Strip opening fence like ```markdown:filename=... or ```md or ```markdown
  s = s.replace(/^```(?:markdown|md|text)?(?::[^\r\n]+)?\r?\n/i, "");
  // Strip trailing fence if present at the very end
  s = s.replace(/\r?\n```\s*$/i, "");
  return s.trim();
}

function normalizeMarkdownForExport(text) {
  if (!text) return "";
  let s = cleanMarkdownFences(text);

  // 1. Unwrap display math inside blockquotes for Notion & Obsidian compatibility:
  s = s.replace(/^[ \t]*>[ \t]*\$\$([\s\S]*?)\$\$/gm, (_m, math) => {
    return `\n\n$$\n${math.trim()}\n$$\n\n`;
  });

  // 2. Convert display math: \[ ... \] -> $$ ... $$
  s = s.replace(/\\\[([\s\S]*?)\\\]/g, (_m, math) => {
    return `\n\n$$\n${math.trim()}\n$$\n\n`;
  });

  // 3. Ensure display math $$...$$ has clean blank lines around it for Notion
  s = s.replace(/(?<!\n)\$\$([\s\S]*?)\$\$/g, (_m, math) => {
    return `\n\n$$\n${math.trim()}\n$$\n\n`;
  });

  // 4. Convert inline math: \( ... \) -> $ ... $
  s = s.replace(/\\\(([\s\S]*?)\\\)/g, (_m, math) => {
    return `$${math.trim()}$`;
  });

  return s.trim();
}

function downloadTextFile(filename, content, mimeType) {
  let finalContent = content;
  if (typeof filename === "string" && (filename.toLowerCase().endsWith(".md") || filename.toLowerCase().endsWith(".markdown"))) {
    finalContent = normalizeMarkdownForExport(content);
  }
  const ext = filename.split(".").pop().toLowerCase();
  const type = mimeType || MIME_MAP[ext] || "text/plain;charset=utf-8";
  const blob = new Blob([finalContent], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function parseLangAndFilename(rawLang, text) {
  let lang = (rawLang || "").trim();
  let filename = "";

  const fnMatch = lang.match(/(?:filename|title)=["']?([^"'\s]+)["']?/i);
  if (fnMatch) {
    filename = fnMatch[1];
    lang = lang.replace(fnMatch[0], "").replace(/[:\s]+$/, "").trim();
  }

  lang = lang.replace(/^[:\s]+/, "").split(/[\s:]/)[0].toLowerCase() || "code";
  const ext = EXT_MAP[lang] || "txt";

  if (!filename) {
    const firstLine = text.trim().split("\n")[0] || "";
    const commentMatch = firstLine.match(/^[#\/\*;\-]{1,3}\s*([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)/);
    if (commentMatch && commentMatch[1].includes(".")) {
      filename = commentMatch[1];
    } else if (lang === "markdown" || lang === "md") {
      const headingMatch = text.trim().match(/^#\s+([a-zA-Z0-9_\-\s]+)/);
      if (headingMatch) {
        const slug = headingMatch[1].trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").slice(0, 30);
        filename = `${slug || "document"}.md`;
      } else {
        filename = "document.md";
      }
    } else if (lang === "python" || lang === "py") {
      filename = "script.py";
    } else if (lang === "csv") {
      filename = "dataset.csv";
    } else if (lang === "json") {
      filename = "data.json";
    } else if (lang === "html") {
      filename = "index.html";
    } else if (lang === "css") {
      filename = "style.css";
    } else if (lang === "javascript" || lang === "js") {
      filename = "script.js";
    } else if (lang === "sql") {
      filename = "query.sql";
    } else if (lang === "bash" || lang === "sh") {
      filename = "script.sh";
    } else {
      filename = `file.${ext}`;
    }
  }

  return { lang, filename, ext };
}

function extractDocumentFilename(text) {
  if (!text) return "cortex_document.md";

  // 1. Check if a script or file name is in code format like `bbc_news_scraper.py`
  const codeFnMatch = text.match(/`([a-zA-Z0-9_\-]+\.(?:py|js|ts|html|css|json|sh|csv|sql|md))`/);
  if (codeFnMatch && codeFnMatch[1]) return codeFnMatch[1];

  // 2. Check for explicit filename directive
  const fnMatch = text.match(/(?:filename|file)=\s*["']?([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)["']?/i);
  if (fnMatch && fnMatch[1]) return fnMatch[1];

  function isCodeOrJunk(str) {
    if (!str) return true;
    const s = str.trim();
    if (/^(?:import|from|def|class|const|let|var|function|return|async|await|if|elif|else|for|while|try|except|with|console\.|print\(|plt\.|np\.)\b/i.test(s)) return true;
    if (/^[a-zA-Z0-9_$]+\s*=[^=]/.test(s)) return true;
    if (s.startsWith("data:image") || s.startsWith("![") || s.includes("base64,")) return true;
    if (/^(?:here\s+is|certainly|sure|below\s+is|i\s+have|alright|ok|okay|note:|pro-tip:)/i.test(s)) return true;
    return false;
  }

  // 3. Search markdown headings (# Title, ## Title) or top bold title
  const textWithoutCode = text.replace(/```[\s\S]*?```/g, "");
  const lines = textWithoutCode.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (!trimmed) continue;
    const isHeading = /^#{1,3}\s+/.test(trimmed);
    const isBoldTitle = trimmed.startsWith("**") && trimmed.endsWith("**") && trimmed.length > 4 && trimmed.length < 80;

    if (isHeading || (i < 3 && isBoldTitle)) {
      const rawTitle = trimmed.replace(/^#{1,3}\s+/, "").replace(/^\*\*|\*\*$/g, "").trim();
      if (isCodeOrJunk(rawTitle)) continue;
      if (/^[-_#=\*\s]+$/.test(rawTitle)) continue;

      let clean = rawTitle
        .replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, "")
        .replace(/[`*_\#]/g, "")
        .replace(/[^a-zA-Z0-9_\-\s]/g, "")
        .trim()
        .replace(/\s+/g, "_")
        .replace(/^-+|-+$/g, "")
        .slice(0, 45);

      if (clean && !/^[-_]+$/.test(clean) && clean.length >= 3) {
        return `${clean.toLowerCase()}.md`;
      }
    }
  }

  return "cortex_document.md";
}

function extractInteractiveArtifact(rawText, preferredFilename = "") {
  if (!rawText) return { filename: preferredFilename || "document.md", content: "", type: "markdown" };

  // If preferredFilename is explicitly a markdown document, preserve it!
  const isMdPreferred =
    preferredFilename &&
    (preferredFilename.toLowerCase().endsWith(".md") || preferredFilename.toLowerCase().endsWith(".markdown"));

  if (isMdPreferred) {
    return {
      filename: preferredFilename,
      content: cleanMarkdownFences(rawText),
      type: "markdown",
    };
  }

  const trimmed = rawText.trim();

  // 1. Check if the artifact is explicitly requested or directly starts with HTML
  const isHtmlFile =
    (preferredFilename && (preferredFilename.toLowerCase().endsWith(".html") || preferredFilename.toLowerCase().endsWith(".htm"))) ||
    trimmed.startsWith("<!DOCTYPE") ||
    trimmed.startsWith("<html") ||
    (trimmed.includes("<head>") && trimmed.includes("<body>"));

  if (isHtmlFile) {
    const htmlBlock = rawText.match(/```(?:html|htm)\s*([\s\S]*?)```/i);
    const content = htmlBlock ? htmlBlock[1].trim() : trimmed;
    return {
      filename: preferredFilename && preferredFilename.endsWith(".html") ? preferredFilename : "index.html",
      content,
      type: "html",
    };
  }

  // 2. Check for SVG
  const isSvgFile =
    (preferredFilename && preferredFilename.toLowerCase().endsWith(".svg")) ||
    (trimmed.startsWith("<svg") && trimmed.includes("</svg>"));

  if (isSvgFile) {
    const svgBlock = rawText.match(/```(?:svg|xml)\s*([\s\S]*?)```/i);
    const content = svgBlock ? svgBlock[1].trim() : trimmed;
    return {
      filename: preferredFilename && preferredFilename.endsWith(".svg") ? preferredFilename : "graphic.svg",
      content,
      type: "svg",
    };
  }

  // 3. Default: Structured Markdown Document / Report
  let cleanMarkdown = cleanMarkdownFences(rawText);
  let docFilename = preferredFilename;
  if (!docFilename || docFilename.endsWith(".html") || docFilename === "uploaded_file") {
    docFilename = extractDocumentFilename(cleanMarkdown);
    if (docFilename.endsWith(".html")) {
      docFilename = docFilename.replace(/\.html$/i, ".md");
    }
  }
  return {
    filename: docFilename,
    content: cleanMarkdown,
    type: "markdown",
  };
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

// ---------------- Markdown, Highlight.js & Chart.js Setup ----------------

const docRenderer = new marked.Renderer();
docRenderer.code = function (arg1, arg2) {
  let text = typeof arg1 === "object" && arg1 !== null ? arg1.text || "" : String(arg1 || "");
  let rawLang = typeof arg1 === "object" && arg1 !== null ? arg1.lang || "code" : String(arg2 || "code");
  const { lang } = parseLangAndFilename(rawLang, text);

  if (lang === "chart" || lang === "json:chart" || lang === "chartjs" || lang === "chart.js") {
    const chartId = "chart-" + Math.random().toString(36).slice(2, 9);
    return `
      <div class="chart-container" data-chart-id="${chartId}">
        <div class="chart-header">
          <span class="chart-title">📊 Interactive Chart</span>
        </div>
        <div class="chart-canvas-wrapper">
          <canvas id="${chartId}"></canvas>
        </div>
        <div class="chart-raw-data" style="display:none;" hidden>${escapeHtml(text)}</div>
      </div>
    `;
  }

  const validLang = lang && hljs.getLanguage(lang) ? lang : null;
  let highlighted = "";
  try {
    highlighted = validLang ? hljs.highlight(text, { language: validLang }).value : hljs.highlightAuto(text).value;
  } catch {
    highlighted = escapeHtml(text);
  }
  return `<pre><code class="hljs ${validLang ? "language-" + validLang : ""}">${highlighted}</code></pre>`;
};

const customRenderer = new marked.Renderer();
customRenderer.code = function (arg1, arg2) {
  let text = "";
  let rawLang = "code";
  if (typeof arg1 === "object" && arg1 !== null) {
    text = arg1.text || "";
    rawLang = arg1.lang || "code";
  } else {
    text = String(arg1 || "");
    rawLang = String(arg2 || "code");
  }

  const { lang, filename, ext } = parseLangAndFilename(rawLang, text);

  // 1. Detect genuine standalone interactive HTML / Web App artifacts
  // Only convert to inline interactive iframe if explicitly requested with :app, :preview, :widget, or :interactive
  const isExplicitApp =
    rawLang.includes(":app") ||
    rawLang.includes(":preview") ||
    rawLang.includes(":widget") ||
    rawLang.includes(":interactive");

  const isInteractiveHtml = isExplicitApp;

  if (isInteractiveHtml) {
    artifactIdCounter++;
    const artifactId = "art-" + artifactIdCounter;
    artifactRegistry.set(artifactId, text);

    let highlighted = "";
    try {
      highlighted = hljs.highlight(text, { language: "html" }).value;
    } catch {
      highlighted = escapeHtml(text);
    }

    const appTitle = filename && filename !== "index.html" ? filename : "Interactive Web Application";

    return `
      <div class="artifact-card" data-artifact-id="${artifactId}">
        <div class="artifact-header">
          <div class="artifact-title">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18M3 9h18"/></svg>
            <span>🌐 ${escapeHtml(appTitle)}</span>
          </div>
          <div class="artifact-actions">
            <button type="button" class="artifact-popout-btn artifact-open-split-btn" title="Open in Claude-style Split Screen Panel">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M15 3v18"/></svg>
              <span>Split Preview</span>
            </button>
            <button type="button" class="artifact-popout-btn artifact-download-html-btn" title="Download HTML file">
              ${ICONS.download}
              <span>Download</span>
            </button>
            <button type="button" class="artifact-popout-btn" title="Open full chart in new tab">
              <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3"/></svg>
              <span>Full Screen</span>
            </button>
            <button type="button" class="artifact-toggle-btn">
              <span>View Code</span>
            </button>
          </div>
        </div>
        <div class="artifact-preview-wrap"></div>
        <div class="artifact-code-wrap" style="display:none;">
          <div class="code-block-wrapper" style="margin:0; border:0; border-radius:0;">
            <div class="code-header">
              <span class="code-lang">HTML</span>
              <button type="button" class="code-copy-btn">
                ${ICONS.copy}
                <span>Copy</span>
              </button>
            </div>
            <pre><code class="hljs language-html">${highlighted}</code></pre>
          </div>
        </div>
      </div>
    `;
  }

  // 2. Detect Chart.js blocks
  if (lang === "chart" || lang === "json:chart" || lang === "chartjs" || lang === "chart.js") {
    const chartId = "chart-" + Math.random().toString(36).slice(2, 9);
    return `
      <div class="chart-container" data-chart-id="${chartId}">
        <div class="chart-header">
          <span class="chart-title">📊 Interactive Chart</span>
        </div>
        <div class="chart-canvas-wrapper">
          <canvas id="${chartId}"></canvas>
        </div>
        <div class="chart-raw-data" style="display:none;" hidden>${escapeHtml(text)}</div>
      </div>
    `;
  }

  // 3. Claude-style Document Artifact Card for Markdown / .md files
  const isMarkdownDoc =
    lang === "markdown" ||
    lang === "md" ||
    filename.toLowerCase().endsWith(".md") ||
    rawLang.toLowerCase().includes("document") ||
    rawLang.toLowerCase().includes("report");

  if (isMarkdownDoc) {
    docIdCounter++;
    const docId = "doc-" + docIdCounter;
    docRegistry.set(docId, { filename, text });

    let renderedBody = "";
    try {
      const { processed: docProcessed, mathMap: docMathMap } = extractMath(text);
      renderedBody = marked.parse(docProcessed, { renderer: docRenderer, breaks: true, gfm: true });
      if (typeof katex !== "undefined" && docMathMap && docMathMap.size > 0) {
        renderedBody = renderedBody.replace(
          /(<div class="cortex-math-display" [^>]*data-math-id="([^"]+)"[^>]*><\/div>|<span class="cortex-math-inline" [^>]*data-math-id="([^"]+)"[^>]*><\/span>)/g,
          (match, _full, displayId, inlineId) => {
            const mId = displayId || inlineId;
            const item = docMathMap.get(mId);
            if (!item) return match;
            try {
              return katex.renderToString(item.tex, {
                displayMode: Boolean(displayId),
                throwOnError: false,
              });
            } catch (err) {
              console.warn("KaTeX renderToString error in doc card:", err);
              return match;
            }
          }
        );
      }
    } catch {
      renderedBody = escapeHtml(text);
    }

    const fileSize = formatBytes(new Blob([text]).size);

    return `
      <div class="document-card" data-doc-id="${docId}">
        <div class="document-header">
          <div class="document-file-info">
            <div class="document-icon">${ICONS.file}</div>
            <div class="document-titles">
              <span class="document-filename">${escapeHtml(filename)}</span>
              <div class="document-meta">
                <span>MARKDOWN DOCUMENT</span>
                <span>•</span>
                <span>${fileSize}</span>
              </div>
            </div>
          </div>
          <div class="document-actions">
            <button type="button" class="document-btn document-view-btn" title="Toggle Raw / Rendered">
              ${ICONS.eye}
              <span>View Raw</span>
            </button>
            <button type="button" class="document-btn document-copy-btn" title="Copy Document Content">
              ${ICONS.copy}
              <span>Copy</span>
            </button>
            <button type="button" class="document-btn document-download-btn" title="Download ${escapeHtml(filename)}">
              ${ICONS.download}
              <span>Download .md</span>
            </button>
          </div>
        </div>
        <div class="document-body">
          <div class="document-rendered-view">${renderedBody}</div>
          <div class="document-raw-view"><pre><code>${escapeHtml(text)}</code></pre></div>
        </div>
      </div>
    `;
  }

  // 4. Standard Code Block with Download and Copy buttons
  const validLang = lang && hljs.getLanguage(lang) ? lang : null;
  let highlighted = "";
  try {
    if (validLang) {
      highlighted = hljs.highlight(text, { language: validLang }).value;
    } else {
      highlighted = hljs.highlightAuto(text).value;
    }
  } catch {
    highlighted = escapeHtml(text);
  }

  const fileSize = formatBytes(new Blob([text]).size);

  return `
    <div class="code-block-wrapper">
      <div class="code-header">
        <div class="code-header-left">
          <span class="code-lang">${escapeHtml(lang || "code")}</span>
          <span class="code-filename">${escapeHtml(filename)}</span>
          <span class="code-size-badge">${fileSize}</span>
        </div>
        <div class="code-header-actions">
          ${(lang === "html" || lang === "htm" || lang === "svg" || lang === "xml" || (text.includes("<!DOCTYPE") || text.includes("<html") || text.includes("<svg"))) ? `
          <button type="button" class="code-preview-btn" title="Live Preview in Side Panel">
            ${ICONS.eye}
            <span>Live Preview</span>
          </button>` : ""}
          <button type="button" class="code-download-btn" title="Download ${escapeHtml(filename)}" data-filename="${escapeHtml(filename)}">
            ${ICONS.download}
            <span>Download</span>
          </button>
          <button type="button" class="code-copy-btn" title="Copy code">
            ${ICONS.copy}
            <span>Copy</span>
          </button>
        </div>
      </div>
      <pre><code class="hljs ${validLang ? "language-" + validLang : ""}">${highlighted}</code></pre>
    </div>
  `;
};

customRenderer.link = function (arg1, arg2, arg3) {
  let href = "";
  let title = "";
  let text = "";
  if (typeof arg1 === "object" && arg1 !== null) {
    href = arg1.href || "";
    title = arg1.title || "";
    text = arg1.text || (arg1.tokens && this.parser ? this.parser.parseInline(arg1.tokens) : "");
  } else {
    href = String(arg1 || "");
    title = String(arg2 || "");
    text = String(arg3 || "");
  }

  const cleanText = text.replace(/<[^>]*>/g, "").trim();
  const isCitation = /^\d+$/.test(cleanText) || /^(source|ref|citation)\b/i.test(cleanText);

  if (isCitation) {
    let domain = "";
    try {
      domain = new URL(href).hostname.replace(/^www\./, "");
    } catch {
      domain = href;
    }
    const tooltip = title ? escapeHtml(title) : escapeHtml(domain);
    return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer" class="citation-pill" title="${tooltip}">${text}</a>`;
  }

  const titleAttr = title ? ` title="${escapeHtml(title)}"` : "";
  return `<a href="${escapeHtml(href)}"${titleAttr} target="_blank" rel="noopener noreferrer">${text}</a>`;
};

customRenderer.image = function (arg1, arg2, arg3) {
  let href = "";
  let title = "";
  let text = "";
  if (typeof arg1 === "object" && arg1 !== null) {
    href = arg1.href || "";
    title = arg1.title || "";
    text = arg1.text || "";
  } else {
    href = String(arg1 || "");
    title = String(arg2 || "");
    text = String(arg3 || "");
  }

  const isDataUri = href.startsWith("data:image/");
  const isPlot = isDataUri || /(?:plot|chart|graph|figure|sin|cos|matplotlib)/i.test(text || title || href);

  if (isPlot || isDataUri) {
    const plotTitle = escapeHtml(text || title || "Generated Plot");
    const dlLink = isDataUri ? href : escapeHtml(href);
    return `
      <div class="chat-plot-card">
        <div class="chat-plot-header">
          <span class="chat-plot-label"><svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg> ${plotTitle}</span>
          <a href="${dlLink}" download="cortex_plot_${Date.now()}.png" class="chat-plot-dl-btn" title="Download High-Res Plot">
            ${ICONS.download}
            <span>Download PNG</span>
          </a>
        </div>
        <div class="chat-plot-img-wrap">
          <img src="${dlLink}" alt="${plotTitle}" class="chat-plot-img" loading="lazy" />
        </div>
      </div>
    `;
  }

  return `<img src="${escapeHtml(href)}" alt="${escapeHtml(text)}" title="${escapeHtml(title)}" class="chat-inline-img" loading="lazy" />`;
};

docRenderer.image = customRenderer.image;

marked.setOptions({ breaks: true, gfm: true, renderer: customRenderer });

// ---------------- LaTeX / Math Formula Parsing (KaTeX) ----------------

function extractMath(text) {
  const mathMap = new Map();
  if (!text) return { processed: "", mathMap };
  let id = 0;

  let s = healMarkdownPlots(text);

  // Protect code blocks (multi-line ```...``` and inline `...`)
  const codeBlocks = [];
  s = s.replace(/(```[\s\S]*?```)/g, (m) => {
    codeBlocks.push(m);
    return `%%CODE_BLOCK_${codeBlocks.length - 1}%%`;
  });
  const inlineCodes = [];
  s = s.replace(/(`[^`\n]+`)/g, (m) => {
    inlineCodes.push(m);
    return `%%INLINE_CODE_${inlineCodes.length - 1}%%`;
  });

  // Unwrap display math inside blockquotes so it doesn't break marked's blockquote parser
  s = s.replace(/^[ \t]*>[ \t]*\$\$([\s\S]*?)\$\$/gm, (_m, math) => {
    return `\n\n$$\n${math.trim()}\n$$\n\n`;
  });

  // Display math: $$ ... $$ and \[ ... \]
  s = s.replace(/\$\$([\s\S]*?)\$\$/g, (m, math) => {
    const key = `math_d_${id++}`;
    const tex = math.trim();
    mathMap.set(key, { tex, display: true });
    return `\n\n<div class="cortex-math-display" data-math-id="${key}" data-tex="${encodeURIComponent(tex)}"></div>\n\n`;
  });
  s = s.replace(/\\\[([\s\S]*?)\\\]/g, (m, math) => {
    const key = `math_d_${id++}`;
    const tex = math.trim();
    mathMap.set(key, { tex, display: true });
    return `\n\n<div class="cortex-math-display" data-math-id="${key}" data-tex="${encodeURIComponent(tex)}"></div>\n\n`;
  });

  // Inline math: \( ... \)
  s = s.replace(/\\\(([\s\S]*?)\\\)/g, (m, math) => {
    const key = `math_i_${id++}`;
    const tex = math.trim();
    mathMap.set(key, { tex, display: false });
    return `<span class="cortex-math-inline" data-math-id="${key}" data-tex="${encodeURIComponent(tex)}"></span>`;
  });

  // Inline math: $ ... $ (excluding pure currency like $50 or $100.00)
  s = s.replace(/(?<!\\|\$)\$(?!\s)([^$\n]+?)(?<!\s)\$(?!\$)/g, (m, math) => {
    if (/^[0-9]+(\.[0-9]+)?$/.test(math.trim())) {
      return m; // keep currency
    }
    const key = `math_i_${id++}`;
    const tex = math.trim();
    mathMap.set(key, { tex, display: false });
    return `<span class="cortex-math-inline" data-math-id="${key}" data-tex="${encodeURIComponent(tex)}"></span>`;
  });

  // Restore code blocks
  s = s.replace(/%%INLINE_CODE_(\d+)%%/g, (_, i) => inlineCodes[i]);
  s = s.replace(/%%CODE_BLOCK_(\d+)%%/g, (_, i) => codeBlocks[i]);

  return { processed: s, mathMap };
}

function renderMarkdownWithMath(text) {
  let safeText = healMarkdownPlots((text ?? "")
    .replace(/```execute_python/gi, "```python")
    .replace(/!\[([^\]]*)\]\((?:attachment:\/\/|sandbox:\/)[^\)]*\)/gi, ""));
  const { processed, mathMap } = extractMath(safeText);
  const html = marked.parse(processed);
  const sanitized = DOMPurify.sanitize(html, {
    ADD_TAGS: ["iframe", "canvas"],
    ADD_ATTR: [
      "sandbox",
      "srcdoc",
      "frameborder",
      "data-artifact-id",
      "data-chart-id",
      "data-doc-id",
      "data-filename",
      "data-math-id",
      "data-tex",
      "loading",
      "download",
    ],
    ALLOW_DATA_ATTR: true,
  });
  return { html: sanitized, mathMap };
}

function renderMarkdown(text) {
  return renderMarkdownWithMath(text).html;
}

function initMath(containerEl, mathMap) {
  let attempts = 0;
  function doRender() {
    if (typeof katex === "undefined") {
      if (attempts < 25) {
        attempts++;
        setTimeout(doRender, 80);
      }
      return;
    }

    // 1. Render all extracted math placeholders
    containerEl.querySelectorAll(".cortex-math-display, .cortex-math-inline").forEach((el) => {
      if (el.getAttribute("data-katex-done")) return;
      el.setAttribute("data-katex-done", "true");
      const mathId = el.getAttribute("data-math-id");
      const item = mathMap ? mathMap.get(mathId) : null;
      let tex = item ? item.tex : "";
      const isDisplay = el.classList.contains("cortex-math-display");
      if (!tex && el.getAttribute("data-tex")) {
        try {
          tex = decodeURIComponent(el.getAttribute("data-tex"));
        } catch {
          tex = el.getAttribute("data-tex");
        }
      }
      if (tex) {
        try {
          katex.render(tex, el, {
            displayMode: isDisplay,
            throwOnError: false,
          });
        } catch (err) {
          console.warn("KaTeX render error:", err);
          el.textContent = tex;
        }
      }
    });

    // 2. Run KaTeX auto-render on container as a safety net for any missed math expressions
    if (typeof renderMathInElement === "function") {
      try {
        renderMathInElement(containerEl, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "\\[", right: "\\]", display: true },
            { left: "\\(", right: "\\)", display: false },
            { left: "$", right: "$", display: false },
          ],
          ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code", "option"],
          throwOnError: false,
        });
      } catch (err) {
        console.warn("KaTeX auto-render error:", err);
      }
    }
  }
  doRender();
}

function initCharts(containerEl) {
  if (!containerEl) return;
  let attempts = 0;

  function escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function balanceJson(str) {
    let inString = false;
    let stringChar = null;
    let isEscaped = false;
    let out = "";
    const stack = [];

    for (let i = 0; i < str.length; i++) {
      const ch = str[i];
      if (inString) {
        out += ch;
        if (isEscaped) isEscaped = false;
        else if (ch === "\\") isEscaped = true;
        else if (ch === stringChar) { inString = false; stringChar = null; }
        continue;
      }
      if (ch === '"' || ch === "'") { inString = true; stringChar = ch; out += ch; continue; }
      if (ch === "{" || ch === "[") { stack.push(ch); out += ch; continue; }
      if (ch === "}") {
        while (stack.length && stack[stack.length - 1] === "[") { out += "]"; stack.pop(); }
        if (stack.length && stack[stack.length - 1] === "{") { stack.pop(); out += "}"; }
        continue;
      }
      if (ch === "]") {
        while (stack.length && stack[stack.length - 1] === "{") { out += "}"; stack.pop(); }
        if (stack.length && stack[stack.length - 1] === "[") { stack.pop(); out += "]"; }
        continue;
      }
      out += ch;
    }
    while (stack.length) {
      const top = stack.pop();
      out += top === "{" ? "}" : "]";
    }
    return out;
  }

  function extractDataAndType(text) {
    let type = "bar";
    const typeMatch = text.match(/["']?type["']?\s*:\s*["']([a-zA-Z]+)["']/i);
    if (typeMatch) type = typeMatch[1].toLowerCase();

    const dataIdx = text.search(/["']?data["']?\s*:\s*\{/i);
    if (dataIdx !== -1) {
      const braceStart = text.indexOf("{", dataIdx);
      if (braceStart !== -1) {
        let depth = 0;
        let inStr = false;
        let strChar = null;
        let esc = false;
        let dataStr = "";
        for (let i = braceStart; i < text.length; i++) {
          const ch = text[i];
          dataStr += ch;
          if (inStr) {
            if (esc) esc = false;
            else if (ch === "\\") esc = true;
            else if (ch === strChar) inStr = false;
            continue;
          }
          if (ch === '"' || ch === "'") { inStr = true; strChar = ch; continue; }
          if (ch === "{") depth++;
          else if (ch === "}") {
            depth--;
            if (depth === 0) break;
          }
        }
        try {
          const parsedData = JSON.parse(balanceJson(dataStr));
          return { type, data: parsedData, options: {} };
        } catch {
          try {
            const parsedData = new Function("return (" + balanceJson(dataStr) + ")")();
            return { type, data: parsedData, options: {} };
          } catch {}
        }
      }
    }
    return null;
  }

  function parseChartConfig(rawText) {
    let text = (rawText || "").trim();
    text = text.replace(/^```(?:chart|json)?\s*/i, "").replace(/\s*```$/i, "").trim();

    // Sanitize unicode and encoded entities commonly emitted by LLMs
    text = text
      .replace(/[\u200B-\u200D\uFEFF]/g, "")
      .replace(/\u202f|\u00a0/g, " ")
      .replace(/[\u2010\u2011\u2012\u2013\u2014]/g, "-")
      .replace(/&quot;/g, '"')
      .replace(/&apos;|&#039;/g, "'")
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">");

    // Remove single line and multi-line comments
    text = text.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:])\/\/[^\n]*/g, "$1");

    // Tier 1: Direct JSON.parse
    try {
      return JSON.parse(text);
    } catch (e1) {}

    // Tier 2: Stripping trailing commas
    try {
      const stripped = text.replace(/,\s*([}\]])/g, "$1");
      return JSON.parse(stripped);
    } catch (e2) {}

    // Tier 3: Balance braces and brackets
    try {
      const balanced = balanceJson(text.replace(/,\s*([}\]])/g, "$1"));
      return JSON.parse(balanced);
    } catch (e3) {}

    // Tier 4: JS eval with Function constructor on balanced string
    try {
      const balanced = balanceJson(text);
      return new Function("return (" + balanced + ")")();
    } catch (e4) {}

    // Tier 5: Direct JS eval with Function constructor on raw text
    try {
      return new Function("return (" + text + ")")();
    } catch (e5) {}

    // Tier 6: Extract data and type even if options is completely broken
    const extracted = extractDataAndType(text);
    if (extracted) return extracted;

    return null;
  }

  function doRender() {
    if (typeof Chart === "undefined") {
      if (attempts < 30) {
        attempts++;
        setTimeout(doRender, 100);
      } else {
        console.warn("Chart.js unavailable for rendering.");
      }
      return;
    }

    const chartContainers = containerEl.querySelectorAll(".chart-container:not([data-rendered='true'])");
    chartContainers.forEach((card) => {
      const rawEl = card.querySelector(".chart-raw-data");
      const canvas = card.querySelector("canvas");
      if (!rawEl || !canvas) return;

      const rawText = (rawEl.textContent || rawEl.innerText || "").trim();
      const rawData = parseChartConfig(rawText);

      if (!rawData || typeof rawData !== "object") {
        console.warn("Could not parse chart config, rendering fallback code block:", rawText);
        card.setAttribute("data-rendered", "true");
        card.innerHTML = `<pre><code>${escapeHtml(rawText)}</code></pre>`;
        return;
      }

      card.setAttribute("data-rendered", "true");

      const chartType = (rawData.type || "bar").toLowerCase();
      const userOptions = rawData.options || {};
      const userPlugins = userOptions.plugins || {};
      const userScales = userOptions.scales || {};

      // Migrate Chart.js v2 title to v3/v4 plugins.title
      if (userOptions.title && !userPlugins.title) {
        userPlugins.title = userOptions.title;
        delete userOptions.title;
      }

      // Migrate Chart.js v2 scales (yAxes/xAxes) to v3/v4 scales (y/x)
      if (userScales.yAxes) {
        if (Array.isArray(userScales.yAxes) && userScales.yAxes[0]) {
          userScales.y = { ...userScales.yAxes[0], ...(userScales.y || {}) };
        }
        delete userScales.yAxes;
      }
      if (userScales.xAxes) {
        if (Array.isArray(userScales.xAxes) && userScales.xAxes[0]) {
          userScales.x = { ...userScales.xAxes[0], ...(userScales.x || {}) };
        }
        delete userScales.xAxes;
      }

      // Compile string callback functions into executable JS functions
      ["x", "y"].forEach((axis) => {
        if (userScales[axis] && userScales[axis].ticks && typeof userScales[axis].ticks.callback === "string") {
          try {
            const fnStr = userScales[axis].ticks.callback.trim();
            if (fnStr.startsWith("function") || fnStr.includes("=>")) {
              userScales[axis].ticks.callback = new Function("return (" + fnStr + ")")();
            } else {
              userScales[axis].ticks.callback = new Function("value", "return " + fnStr + ";");
            }
          } catch (e) {
            delete userScales[axis].ticks.callback;
          }
        }
      });

      const isCircular = chartType === "pie" || chartType === "doughnut" || chartType === "polarArea";

      // Vibrant modern theme palette matching Cortex design system
      const THEME_PALETTE = [
        "rgba(34, 197, 94, 0.85)",   // emerald green
        "rgba(56, 189, 248, 0.85)",  // sky blue
        "rgba(168, 85, 247, 0.85)",  // purple
        "rgba(251, 146, 60, 0.85)",  // amber
        "rgba(244, 63, 94, 0.85)",   // rose
        "rgba(20, 184, 166, 0.85)",  // teal
        "rgba(234, 179, 8, 0.85)",   // yellow
        "rgba(99, 102, 241, 0.85)",  // indigo
      ];

      // Auto-assign colors if missing from datasets
      if (rawData.data && Array.isArray(rawData.data.datasets)) {
        rawData.data.datasets.forEach((ds, dsIdx) => {
          if (!ds.backgroundColor) {
            if (isCircular && Array.isArray(rawData.data.labels)) {
              ds.backgroundColor = rawData.data.labels.map((_, i) => THEME_PALETTE[i % THEME_PALETTE.length]);
            } else {
              ds.backgroundColor = THEME_PALETTE[dsIdx % THEME_PALETTE.length];
            }
          }
          if (!ds.borderColor && !isCircular) {
            ds.borderColor = "rgba(255, 255, 255, 0.15)";
            ds.borderWidth = 1;
          }
        });
      }

      const config = {
        type: chartType,
        data: rawData.data || {},
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 400 },
          ...userOptions,
          plugins: {
            legend: {
              display: true,
              position: "top",
              labels: {
                color: "#ecedef",
                font: { family: "'Space Grotesk', 'Inter', sans-serif", size: 12 },
                boxWidth: 14,
                padding: 12,
              },
              ...(userPlugins.legend || {}),
            },
            tooltip: {
              backgroundColor: "#15181c",
              borderColor: "#262b31",
              borderWidth: 1,
              titleColor: "#4ade80",
              bodyColor: "#ecedef",
              padding: 10,
              cornerRadius: 8,
              ...(userPlugins.tooltip || {}),
            },
            ...userPlugins,
          },
          scales: isCircular
            ? {}
            : {
                x: {
                  ticks: {
                    color: "#8a909a",
                    font: { family: "'Space Grotesk', 'Inter', sans-serif", size: 11 },
                  },
                  grid: { color: "rgba(255, 255, 255, 0.06)" },
                  ...(userScales.x || {}),
                },
                y: {
                  ticks: {
                    color: "#8a909a",
                    font: { family: "'Space Grotesk', 'Inter', sans-serif", size: 11 },
                  },
                  grid: { color: "rgba(255, 255, 255, 0.06)" },
                  ...(userScales.y || {}),
                },
                ...userScales,
              },
        },
      };

      try {
        new Chart(canvas, config);
      } catch (err) {
        console.warn("Chart instantiation with custom options failed, retrying with safe defaults:", err);
        try {
          const existingChart = typeof Chart.getChart === "function" ? Chart.getChart(canvas) : null;
          if (existingChart) existingChart.destroy();
          const safeConfig = {
            type: chartType,
            data: rawData.data || {},
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { display: true, labels: { color: "#ecedef" } },
                title: userPlugins.title ? userPlugins.title : undefined,
              },
              scales: isCircular ? {} : {
                x: { ticks: { color: "#8a909a" }, grid: { color: "rgba(255, 255, 255, 0.06)" } },
                y: { ticks: { color: "#8a909a" }, grid: { color: "rgba(255, 255, 255, 0.06)" } },
              },
            },
          };
          new Chart(canvas, safeConfig);
        } catch (err2) {
          console.warn("Failed to instantiate Chart.js fallback:", err2);
          card.innerHTML = `<pre><code>${escapeHtml(rawText)}</code></pre>`;
        }
      }
    });
  }

  doRender();
}

function initArtifacts(containerEl) {
  const cards = containerEl.querySelectorAll(".artifact-card:not([data-initialized='true'])");
  cards.forEach((card) => {
    card.setAttribute("data-initialized", "true");
    const artifactId = card.getAttribute("data-artifact-id");
    let rawHtml = artifactRegistry.get(artifactId);

    // Fallback: If not in map, extract from the code-block innerText
    if (!rawHtml) {
      const codeEl = card.querySelector(".artifact-code-wrap code");
      if (codeEl) {
        rawHtml = codeEl.innerText || codeEl.textContent;
      }
    }

    const previewWrap = card.querySelector(".artifact-preview-wrap");
    const codeWrap = card.querySelector(".artifact-code-wrap");
    const toggleBtn = card.querySelector(".artifact-toggle-btn");
    const popoutBtn = card.querySelector(".artifact-popout-btn");

    if (rawHtml && previewWrap) {
      previewWrap.innerHTML = "";
      const iframe = document.createElement("iframe");
      iframe.className = "artifact-iframe";
      iframe.setAttribute("sandbox", "allow-scripts allow-popups allow-modals allow-same-origin allow-forms");
      iframe.setAttribute("loading", "lazy");
      previewWrap.appendChild(iframe);
      iframe.srcdoc = rawHtml;
    }

    if (popoutBtn && rawHtml) {
      popoutBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        const blob = new Blob([rawHtml], { type: "text/html;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        window.open(url, "_blank");
      });
    }

    if (toggleBtn && previewWrap && codeWrap) {
      toggleBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        const isShowingCode = codeWrap.style.display !== "none";
        if (isShowingCode) {
          codeWrap.style.display = "none";
          previewWrap.style.display = "block";
          toggleBtn.innerHTML = `<span>View Code</span>`;
        } else {
          codeWrap.style.display = "block";
          previewWrap.style.display = "none";
          toggleBtn.innerHTML = `<span>View Preview</span>`;
        }
      });
    }
  });
}

// Delegate clicks inside chatEl (Copy, Download, Document Toggle)
chatEl.addEventListener("click", async (e) => {
  // 1. Copy code in standard code block
  const copyBtn = e.target.closest(".code-copy-btn");
  if (copyBtn) {
    const wrapper = copyBtn.closest(".code-block-wrapper");
    const codeEl = wrapper ? wrapper.querySelector("code") : null;
    if (codeEl) {
      try {
        await navigator.clipboard.writeText(codeEl.innerText);
        copyBtn.classList.add("copied");
        copyBtn.innerHTML = `${ICONS.check}<span>Copied</span>`;
        setTimeout(() => {
          copyBtn.classList.remove("copied");
          copyBtn.innerHTML = `${ICONS.copy}<span>Copy</span>`;
        }, 1600);
      } catch {
        /* clipboard fallback */
      }
    }
    return;
  }

  // 2. Download code in standard code block
  const codeDownloadBtn = e.target.closest(".code-download-btn");
  if (codeDownloadBtn) {
    const wrapper = codeDownloadBtn.closest(".code-block-wrapper");
    const codeEl = wrapper ? wrapper.querySelector("code") : null;
    const filename = codeDownloadBtn.dataset.filename || "code.txt";
    if (codeEl) {
      downloadTextFile(filename, codeEl.innerText);
      codeDownloadBtn.classList.add("downloaded");
      codeDownloadBtn.innerHTML = `${ICONS.check}<span>Saved</span>`;
      setTimeout(() => {
        codeDownloadBtn.classList.remove("downloaded");
        codeDownloadBtn.innerHTML = `${ICONS.download}<span>Download</span>`;
      }, 1600);
    }
    return;
  }

  // 3. Document card: Download .md
  const docDownloadBtn = e.target.closest(".document-download-btn");
  if (docDownloadBtn) {
    const card = docDownloadBtn.closest(".document-card");
    const docId = card ? card.dataset.docId : null;
    const docData = docRegistry.get(docId);
    if (docData) {
      downloadTextFile(docData.filename, docData.text, "text/markdown;charset=utf-8");
      docDownloadBtn.classList.add("downloaded");
      docDownloadBtn.innerHTML = `${ICONS.check}<span>Downloaded</span>`;
      setTimeout(() => {
        docDownloadBtn.classList.remove("downloaded");
        docDownloadBtn.innerHTML = `${ICONS.download}<span>Download .md</span>`;
      }, 1600);
    } else {
      const rawEl = card ? card.querySelector(".document-raw-view code") : null;
      const fnEl = card ? card.querySelector(".document-filename") : null;
      const filename = fnEl ? fnEl.textContent.trim() : "document.md";
      if (rawEl) {
        downloadTextFile(filename, rawEl.innerText, "text/markdown;charset=utf-8");
      }
    }
    return;
  }

  // 4. Document card: Copy content
  const docCopyBtn = e.target.closest(".document-copy-btn");
  if (docCopyBtn) {
    const card = docCopyBtn.closest(".document-card");
    const docId = card ? card.dataset.docId : null;
    const docData = docRegistry.get(docId);
    let textToCopy = docData ? docData.text : "";
    if (!textToCopy && card) {
      const rawEl = card.querySelector(".document-raw-view code");
      if (rawEl) textToCopy = rawEl.innerText;
    }
    if (textToCopy) {
      try {
        await navigator.clipboard.writeText(normalizeMarkdownForExport(textToCopy));
        docCopyBtn.classList.add("copied");
        docCopyBtn.innerHTML = `${ICONS.check}<span>Copied</span>`;
        setTimeout(() => {
          docCopyBtn.classList.remove("copied");
          docCopyBtn.innerHTML = `${ICONS.copy}<span>Copy</span>`;
        }, 1600);
      } catch {
        /* fallback */
      }
    }
    return;
  }

  // 5. Document card: Toggle Raw / Rendered
  const docViewBtn = e.target.closest(".document-view-btn");
  if (docViewBtn) {
    const card = docViewBtn.closest(".document-card");
    if (!card) return;
    const renderedView = card.querySelector(".document-rendered-view");
    const rawView = card.querySelector(".document-raw-view");
    if (renderedView && rawView) {
      const isRawShowing = rawView.style.display === "block";
      if (isRawShowing) {
        rawView.style.display = "none";
        renderedView.style.display = "block";
        docViewBtn.innerHTML = `${ICONS.eye}<span>View Raw</span>`;
      } else {
        rawView.style.display = "block";
        renderedView.style.display = "none";
        docViewBtn.innerHTML = `${ICONS.eye}<span>View Rendered</span>`;
      }
    }
    return;
  }

  // 5b. Document card: Open Split Preview Panel
  const docSplitBtn = e.target.closest(".document-preview-split-btn");
  if (docSplitBtn) {
    const card = docSplitBtn.closest(".document-card");
    const docId = card ? card.dataset.docId : null;
    const docData = docRegistry.get(docId);
    const rawEl = card ? card.querySelector(".document-raw-view code") : null;
    const fnEl = card ? card.querySelector(".document-filename") : null;
    const filename = (docData && docData.filename) || (fnEl ? fnEl.textContent.trim() : "document.md");
    const text = (docData && docData.text) || (rawEl ? rawEl.innerText : "");
    if (text) {
      openArtifactPanel({
        filename,
        content: cleanMarkdownFences(text),
        type: "markdown",
      });
    }
    return;
  }

  // 6. Artifact card: Download HTML
  const artifactDownloadBtn = e.target.closest(".artifact-download-html-btn");
  if (artifactDownloadBtn) {
    const card = artifactDownloadBtn.closest(".artifact-card");
    const artifactId = card ? card.getAttribute("data-artifact-id") : null;
    let htmlContent = artifactRegistry.get(artifactId);
    if (!htmlContent && card) {
      const codeEl = card.querySelector(".artifact-code-wrap code");
      if (codeEl) htmlContent = codeEl.innerText;
    }
    if (htmlContent) {
      downloadTextFile("interactive_preview.html", htmlContent, "text/html;charset=utf-8");
      artifactDownloadBtn.innerHTML = `${ICONS.check}<span>Saved</span>`;
      setTimeout(() => {
        artifactDownloadBtn.innerHTML = `${ICONS.download}<span>Download</span>`;
      }, 1600);
    }
    return;
  }

  // 7. Message document banner: Download .md
  const bannerDownloadBtn = e.target.closest(".message-download-doc-btn");
  if (bannerDownloadBtn) {
    const bubble = bannerDownloadBtn.closest(".ai-bubble");
    let rawText = bubble ? bubble._rawFullText : "";
    if (!rawText) {
      const row = bannerDownloadBtn.closest(".message-row");
      const rows = Array.from(chatEl.querySelectorAll(".message-row"));
      const idx = rows.indexOf(row);
      if (idx !== -1 && messages[idx]) rawText = messages[idx].content;
    }
    if (rawText) {
      const filename = extractDocumentFilename(rawText);
      downloadTextFile(filename, rawText, "text/markdown;charset=utf-8");
      bannerDownloadBtn.classList.add("downloaded");
      bannerDownloadBtn.innerHTML = `${ICONS.check}<span>Downloaded</span>`;
      setTimeout(() => {
        bannerDownloadBtn.classList.remove("downloaded");
        bannerDownloadBtn.innerHTML = `${ICONS.download}<span>Download .md</span>`;
      }, 1600);
    }
    return;
  }

  // 8. Message document banner: Live Preview in Artifact Panel
  const bannerPreviewBtn = e.target.closest(".message-preview-doc-btn");
  if (bannerPreviewBtn) {
    const bubble = bannerPreviewBtn.closest(".ai-bubble");
    let rawText = bubble ? bubble._rawFullText : "";
    if (!rawText) {
      const row = bannerPreviewBtn.closest(".message-row");
      const rows = Array.from(chatEl.querySelectorAll(".message-row"));
      const idx = rows.indexOf(row);
      if (idx !== -1 && messages[idx]) rawText = messages[idx].content;
    }
    if (rawText) {
      const filename = extractDocumentFilename(rawText);
      openArtifactPanel({
        filename: filename || "document.md",
        content: cleanMarkdownFences(rawText),
        type: "markdown",
      });
    }
    return;
  }

  // 9. Standard Code Block: Live Preview button
  const codePreviewBtn = e.target.closest(".code-preview-btn");
  if (codePreviewBtn) {
    const wrapper = codePreviewBtn.closest(".code-block-wrapper");
    const codeEl = wrapper?.querySelector("code");
    const filenameEl = wrapper?.querySelector(".code-filename");
    const langEl = wrapper?.querySelector(".code-lang");
    const rawCode = codeEl?.textContent || "";
    const lang = (langEl?.textContent || "html").toLowerCase().trim();
    const filename = filenameEl?.textContent || (lang === "svg" ? "graphic.svg" : "index.html");
    if (rawCode) {
      openArtifactPanel({
        filename,
        content: rawCode,
        type: lang === "svg" ? "svg" : "html",
      });
    }
    return;
  }

  // 10. Interactive Card: Split Preview button
  const splitBtn = e.target.closest(".artifact-open-split-btn");
  if (splitBtn) {
    const card = splitBtn.closest(".artifact-card");
    const artifactId = card?.getAttribute("data-artifact-id");
    let rawHtml = artifactRegistry.get(artifactId);
    if (!rawHtml && card) {
      const codeEl = card.querySelector(".artifact-code-wrap code");
      if (codeEl) rawHtml = codeEl.innerText;
    }
    if (rawHtml) {
      openArtifactPanel({
        filename: "interactive_preview.html",
        content: rawHtml,
        type: "html",
      });
    }
    return;
  }

});

// ---------------- Claude-Style Artifact Split Panel Management ----------------

let currentArtifactData = null; // { filename, content, type }

function openArtifactPanel({ filename, content, type }) {
  if (!artifactSplitPanel) return;

  // Smart resolution if raw text/markdown was passed
  let resolvedType = type;
  let resolvedContent = content;
  let resolvedFilename = filename;

  if (resolvedType === "html" && resolvedContent.includes("```html")) {
    const extracted = extractInteractiveArtifact(resolvedContent, resolvedFilename);
    resolvedContent = extracted.content;
    resolvedType = extracted.type;
    resolvedFilename = extracted.filename;
  }

  if (resolvedType === "markdown") {
    resolvedContent = cleanMarkdownFences(resolvedContent);
  }

  // Auto-fix common LLM JS regex typos (e.g. missing opening slash before unicode minus: .replace(−/g, -> .replace(/−/g,)
  if (resolvedType === "html") {
    resolvedContent = resolvedContent
      .replace(/\.replace\((?:\u2212|−)\/g/g, ".replace(/\\u2212/g")
      .replace(/\.replace\(-\/g/g, ".replace(/-/g");
  }

  currentArtifactData = { filename: resolvedFilename, content: resolvedContent, type: resolvedType };

  if (artifactTitle) artifactTitle.textContent = resolvedFilename || "artifact";
  if (artifactSubtitle) {
    artifactSubtitle.textContent =
      resolvedType === "html"
        ? "Interactive Web App / Artifact Studio"
        : resolvedType === "svg"
        ? "Vector SVG Preview"
        : "Document Reader & Code View";
  }

  // Populate Code view
  if (artifactCodeContent) {
    artifactCodeContent.textContent = resolvedContent;
    if (window.hljs) hljs.highlightElement(artifactCodeContent);
  }

  // Populate Preview iframe
  if (artifactIframe) {
    const isDark = !document.body.classList.contains("light-theme");
    if (resolvedType === "html") {
      let finalDoc = resolvedContent;
      if (!finalDoc.includes("<html") && !finalDoc.includes("<!DOCTYPE")) {
        finalDoc = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      padding: 24px;
      line-height: 1.6;
      color: ${isDark ? "#f4f4f5" : "#18181b"};
      background: ${isDark ? "#0d0f12" : "#ffffff"};
      margin: 0;
    }
  </style>
</head>
<body>
  ${resolvedContent}
</body>
</html>`;
      }
      artifactIframe.srcdoc = finalDoc;
    } else if (resolvedType === "svg") {
      artifactIframe.srcdoc = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      margin: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      background: ${isDark ? "#0d0f12" : "#f8fafc"};
    }
    svg {
      max-width: 90vw;
      max-height: 90vh;
    }
  </style>
</head>
<body>
  ${resolvedContent}
</body>
</html>`;
    } else if (resolvedType === "markdown") {
      const { processed, mathMap } = extractMath(resolvedContent || "");
      let renderedMarkdown = "";
      try {
        renderedMarkdown = window.marked ? marked.parse(processed) : `<pre>${escapeHtml(resolvedContent)}</pre>`;
      } catch {
        renderedMarkdown = `<pre>${escapeHtml(resolvedContent)}</pre>`;
      }

      // Pre-render KaTeX math placeholders into complete HTML
      if (typeof katex !== "undefined" && mathMap && mathMap.size > 0) {
        renderedMarkdown = renderedMarkdown.replace(
          /(<div class="cortex-math-display" [^>]*data-math-id="([^"]+)"[^>]*><\/div>|<span class="cortex-math-inline" [^>]*data-math-id="([^"]+)"[^>]*><\/span>)/g,
          (match, _full, displayId, inlineId) => {
            const mId = displayId || inlineId;
            const item = mathMap.get(mId);
            if (!item) return match;
            try {
              return katex.renderToString(item.tex, {
                displayMode: Boolean(displayId),
                throwOnError: false,
              });
            } catch (err) {
              console.warn("KaTeX renderToString error in artifact:", err);
              return Boolean(displayId) ? `$$${item.tex}$$` : `$${item.tex}$`;
            }
          }
        );
      }

      artifactIframe.srcdoc = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="/static/vendor/katex/katex.min.css?v=20260913_v4">
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      padding: 32px 28px;
      line-height: 1.7;
      color: ${isDark ? "#e4e4e7" : "#18181b"};
      background: ${isDark ? "#0d0f12" : "#ffffff"};
      max-width: 860px;
      margin: 0 auto;
    }
    h1, h2, h3, h4, h5, h6 {
      color: ${isDark ? "#f4f4f5" : "#09090b"};
      margin-top: 1.6em;
      margin-bottom: 0.6em;
      font-weight: 600;
      border-bottom: 1px solid ${isDark ? "#27272a" : "#e4e4e7"};
      padding-bottom: 6px;
    }
    h1 { font-size: 1.85em; }
    h2 { font-size: 1.45em; }
    h3 { font-size: 1.2em; }
    p { margin: 0.85em 0; }
    code {
      background: ${isDark ? "#1f2228" : "#f4f4f5"};
      padding: 2px 6px;
      border-radius: 4px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.88em;
      color: ${isDark ? "#38bdf8" : "#0284c7"};
    }
    pre {
      background: ${isDark ? "#16191f" : "#f8fafc"};
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      border: 1px solid ${isDark ? "#27272a" : "#e2e8f0"};
      margin: 1.2em 0;
    }
    pre code { background: none; padding: 0; color: inherit; font-size: 0.9em; }
    table { width: 100%; border-collapse: collapse; margin: 1.4em 0; }
    th, td { border: 1px solid ${isDark ? "#27272a" : "#e4e4e7"}; padding: 9px 14px; text-align: left; }
    th { background: ${isDark ? "#181b20" : "#f4f4f5"}; color: ${isDark ? "#f4f4f5" : "#09090b"}; font-weight: 600; }
    blockquote {
      border-left: 3px solid #22c55e;
      margin: 1.2em 0;
      padding: 6px 16px;
      background: ${isDark ? "rgba(34, 197, 94, 0.05)" : "rgba(34, 197, 94, 0.08)"};
      border-radius: 0 6px 6px 0;
      color: ${isDark ? "#d4d4d8" : "#4b5563"};
    }
    ul, ol { padding-left: 24px; margin: 0.8em 0; }
    li { margin: 0.35em 0; }
    a { color: #22c55e; text-decoration: none; }
    a:hover { text-decoration: underline; }
    hr { border: 0; border-top: 1px solid ${isDark ? "#27272a" : "#e4e4e7"}; margin: 2em 0; }
    .katex-display {
      overflow-x: auto;
      overflow-y: hidden;
      padding: 8px 0;
      margin: 1.2em 0;
    }
    .katex {
      font-size: 1.05em;
      text-rendering: auto;
    }
    /* Interactive Chart styles inside Artifact Document */
    .chart-container {
      margin: 20px 0;
      padding: 16px;
      background: ${isDark ? "#090a0d" : "#ffffff"};
      border: 1px solid ${isDark ? "#27272a" : "#e4e4e7"};
      border-radius: 12px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
      position: relative;
    }
    .chart-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 14px;
      padding-bottom: 8px;
      border-bottom: 1px solid ${isDark ? "#27272a" : "#e4e4e7"};
    }
    .chart-title {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-weight: 600;
      font-size: 13px;
      color: ${isDark ? "#f4f4f5" : "#09090b"};
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .chart-canvas-wrapper {
      position: relative;
      width: 100%;
      height: 320px;
      min-height: 280px;
    }
    .chart-canvas-wrapper canvas {
      width: 100% !important;
      height: 100% !important;
      display: block;
    }
    /* Matplotlib Generated Plot styles inside Artifact Document */
    .chat-plot-card {
      position: relative;
      margin: 20px 0;
      background: ${isDark ? "#0f141c" : "#ffffff"};
      border: 1px solid ${isDark ? "rgba(255, 255, 255, 0.1)" : "#cbd5e1"};
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    }
    .chat-plot-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      background: ${isDark ? "rgba(255, 255, 255, 0.03)" : "#f8fafc"};
      border-bottom: 1px solid ${isDark ? "rgba(255, 255, 255, 0.06)" : "#e2e8f0"};
      font-size: 12px;
      color: ${isDark ? "#94a3b8" : "#475569"};
      font-weight: 500;
    }
    .chat-plot-label {
      display: flex;
      align-items: center;
      gap: 6px;
      color: ${isDark ? "#e2e8f0" : "#0f172a"};
      font-weight: 600;
    }
    .chat-plot-dl-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      font-size: 11.5px;
      font-weight: 500;
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 6px;
      text-decoration: none;
      cursor: pointer;
    }
    .chat-plot-img-wrap {
      padding: 12px;
      background: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .chat-plot-img-wrap img, .chat-plot-img {
      max-width: 100%;
      height: auto;
      border-radius: 4px;
      display: block;
    }
  </style>
  <script src="/static/vendor/katex/katex.min.js?v=20260913_v4"></script>
  <script src="/static/vendor/katex/auto-render.min.js?v=20260913_v4"></script>
  <script src="/static/vendor/chart.umd.min.js?v=20260914_v1"></script>
</head>
<body>
  ${renderedMarkdown}
  <script>
    (function() {
      function runAutoRender() {
        if (typeof renderMathInElement === "function") {
          try {
            renderMathInElement(document.body, {
              delimiters: [
                { left: "$$", right: "$$", display: true },
                { left: "\\\\[", right: "\\\\]", display: true },
                { left: "\\\\(", right: "\\\\)", display: false },
                { left: "$", right: "$", display: false }
              ],
              ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code", "option"],
              throwOnError: false
            });
          } catch (e) {
            console.warn("Artifact auto-render error:", e);
          }
        }
        if (typeof initCharts === "function") {
          initCharts(document.body);
        }
      }
      ${initCharts.toString()}
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", runAutoRender);
      } else {
        runAutoRender();
      }
    })();
  </script>
</body>
</html>`;
    } else {
      artifactIframe.srcdoc = `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{font-family:monospace;padding:20px;background:${isDark ? "#0d0f12" : "#f5f5f5"};color:${isDark ? "#e4e4e7" : "#111"};white-space:pre-wrap;line-height:1.5;}</style></head><body>${escapeHtml(resolvedContent)}</body></html>`;
    }
  }

  setArtifactTab("preview");
  artifactSplitPanel.style.display = "flex";
  appView?.classList.add("has-artifact-open");
  setTimeout(() => {
    window.dispatchEvent(new Event("resize"));
    if (typeof initCharts === "function") initCharts(chatEl);
  }, 80);
}

function closeArtifactPanel() {
  if (!artifactSplitPanel) return;
  artifactSplitPanel.style.display = "none";
  appView?.classList.remove("has-artifact-open");
  setTimeout(() => {
    window.dispatchEvent(new Event("resize"));
    if (typeof initCharts === "function") initCharts(chatEl);
  }, 80);
}

function setArtifactTab(tab) {
  if (tab === "preview") {
    artifactTabPreview?.classList.add("active");
    artifactTabCode?.classList.remove("active");
    if (artifactIframe) artifactIframe.style.display = "block";
    if (artifactCodeWrap) artifactCodeWrap.style.display = "none";
  } else {
    artifactTabCode?.classList.add("active");
    artifactTabPreview?.classList.remove("active");
    if (artifactIframe) artifactIframe.style.display = "none";
    if (artifactCodeWrap) artifactCodeWrap.style.display = "block";
  }
}

artifactTabPreview?.addEventListener("click", () => setArtifactTab("preview"));
artifactTabCode?.addEventListener("click", () => setArtifactTab("code"));
artifactCloseBtn?.addEventListener("click", closeArtifactPanel);

artifactDownloadBtn?.addEventListener("click", () => {
  if (!currentArtifactData) return;
  const contentToDownload = currentArtifactData.type === "markdown"
    ? normalizeMarkdownForExport(currentArtifactData.content)
    : currentArtifactData.content;
  downloadTextFile(currentArtifactData.filename, contentToDownload, "text/markdown;charset=utf-8");
});

artifactCopyBtn?.addEventListener("click", async () => {
  if (!currentArtifactData || !currentArtifactData.content) return;
  try {
    const textToCopy = currentArtifactData.type === "markdown"
      ? normalizeMarkdownForExport(currentArtifactData.content)
      : currentArtifactData.content;
    await navigator.clipboard.writeText(textToCopy);
    artifactCopyBtn.classList.add("copied");
    artifactCopyBtn.title = "Copied!";
    artifactCopyBtn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7"/></svg>`;
    setTimeout(() => {
      artifactCopyBtn.classList.remove("copied");
      artifactCopyBtn.title = "Copy content";
      artifactCopyBtn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg>`;
    }, 1600);
  } catch (err) {
    console.warn("Failed to copy artifact content:", err);
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && artifactSplitPanel && artifactSplitPanel.style.display !== "none") {
    closeArtifactPanel();
  }
});

// ---------------- Voice Input (Speech-to-Text via Web Speech API) ----------------

let speechRecognition = null;
let isRecordingVoice = false;

const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognitionClass && micBtn) {
  try {
    speechRecognition = new SpeechRecognitionClass();
    speechRecognition.continuous = false;
    speechRecognition.interimResults = true;
    speechRecognition.lang = "en-US";

    speechRecognition.onstart = () => {
      isRecordingVoice = true;
      micBtn.classList.add("recording");
      micBtn.setAttribute("title", "Listening… Click to stop");
      promptEl.placeholder = "Listening… speak in English or Hindi…";
    };

    speechRecognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      if (transcript) {
        promptEl.value = transcript;
        autoResize();
      }
    };

    speechRecognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      stopVoiceInput();
    };

    speechRecognition.onend = () => {
      stopVoiceInput();
    };

    micBtn.addEventListener("click", () => {
      if (isRecordingVoice) {
        speechRecognition.stop();
      } else {
        try {
          speechRecognition.start();
        } catch (e) {
          console.error("Speech start error:", e);
        }
      }
    });
  } catch (err) {
    console.warn("Speech recognition init failed:", err);
    micBtn.style.display = "none";
  }
} else if (micBtn) {
  micBtn.style.display = "none";
}

function stopVoiceInput() {
  isRecordingVoice = false;
  if (micBtn) {
    micBtn.classList.remove("recording");
    micBtn.setAttribute("title", "Voice Input (Speak in Hindi or English)");
  }
  if (promptEl) {
    promptEl.placeholder = "Ask Cortex anything… (type, speak, attach docs, plot charts)";
  }
}

// ---------------- Text-to-Speech (Read Aloud via Web Speech API) ----------------

let activeTTSBtn = null;

function toggleTTS(btn, rawText) {
  if (window.speechSynthesis && window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    if (activeTTSBtn) {
      activeTTSBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        <span>Read</span>
      `;
    }
    if (activeTTSBtn === btn) {
      activeTTSBtn = null;
      return;
    }
  }

  const clean = rawText
    .replace(/```[\s\S]*?```/g, " [code snippet] ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[#*_~>]/g, "")
    .trim();

  if (!clean || !window.speechSynthesis) return;

  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.05;
  utterance.onend = () => {
    btn.innerHTML = `
      <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
      <span>Read</span>
    `;
    activeTTSBtn = null;
  };
  utterance.onerror = () => {
    btn.innerHTML = `
      <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
      <span>Read</span>
    `;
    activeTTSBtn = null;
  };

  activeTTSBtn = btn;
  btn.innerHTML = `
    <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
    <span>Stop</span>
  `;
  window.speechSynthesis.speak(utterance);
}

// ---------------- Scroll Helpers ----------------

function scrollToBottom(smooth = true) {
  requestAnimationFrame(() => {
    chatEl.scrollTo({ top: chatEl.scrollHeight, behavior: smooth ? "smooth" : "auto" });
  });
}

function isNearBottom() {
  return chatEl.scrollHeight - chatEl.scrollTop - chatEl.clientHeight < 140;
}

// ---------------- Project Workspaces ----------------

async function loadProjects() {
  if (!authToken) return;
  try {
    const res = await fetch("/api/projects", { headers: authHeaders() });
    if (res.status === 401) return;
    if (res.ok) {
      userProjects = await res.json();
      renderProjectPills();
    }
  } catch (err) {
    console.error("Failed to load projects:", err);
  }
}

function renderProjectPills() {
  if (!projectsListContainer) return;
  projectsListContainer.innerHTML = "";

  // "All Chats" pill
  const allBtn = document.createElement("button");
  allBtn.className = `project-pill ${!currentProjectId ? "active" : ""}`;
  allBtn.dataset.projectId = "";
  allBtn.type = "button";
  allBtn.textContent = "All Chats";
  allBtn.addEventListener("click", () => {
    selectProject("");
  });
  projectsListContainer.appendChild(allBtn);

  // User project pills
  userProjects.forEach((proj) => {
    const pill = document.createElement("button");
    pill.className = `project-pill ${currentProjectId === proj.id ? "active" : ""}`;
    pill.dataset.projectId = proj.id;
    pill.type = "button";
    pill.title = proj.description || proj.name;

    const span = document.createElement("span");
    span.textContent = proj.name;
    pill.appendChild(span);

    // Edit icon on pill
    const editBtn = document.createElement("span");
    editBtn.style.marginLeft = "6px";
    editBtn.style.opacity = "0.7";
    editBtn.style.cursor = "pointer";
    editBtn.innerHTML = "✎";
    editBtn.title = "Edit Project";
    editBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openProjectModal(proj.id);
    });
    pill.appendChild(editBtn);

    pill.addEventListener("click", () => {
      selectProject(proj.id);
    });
    projectsListContainer.appendChild(pill);
  });
}

function selectProject(projId) {
  currentProjectId = projId;
  renderProjectPills();
  loadConversations(false);
}

function openProjectModal(projectId = null) {
  editingProjectId = projectId;
  if (!projectModal) return;

  if (projectId) {
    const proj = userProjects.find((p) => p.id === projectId);
    if (proj) {
      if (projectModalHeading) projectModalHeading.textContent = "Edit Project Workspace";
      if (projectNameInput) projectNameInput.value = proj.name || "";
      if (projectDescInput) projectDescInput.value = proj.description || "";
      if (projectPromptInput) projectPromptInput.value = proj.system_prompt || "";
      if (projectModalDeleteBtn) projectModalDeleteBtn.style.display = "inline-block";
    }
  } else {
    if (projectModalHeading) projectModalHeading.textContent = "New Project Workspace";
    if (projectNameInput) projectNameInput.value = "";
    if (projectDescInput) projectDescInput.value = "";
    if (projectPromptInput) projectPromptInput.value = "";
    if (projectModalDeleteBtn) projectModalDeleteBtn.style.display = "none";
  }

  projectModal.style.display = "flex";
  projectModal.setAttribute("aria-hidden", "false");
  projectNameInput?.focus();
}

function closeProjectModal() {
  if (!projectModal) return;
  projectModal.style.display = "none";
  projectModal.setAttribute("aria-hidden", "true");
  editingProjectId = null;
}

async function saveProjectFromModal() {
  const name = (projectNameInput ? projectNameInput.value : "").trim();
  if (!name) {
    alert("Please enter a project name.");
    return;
  }
  const description = (projectDescInput ? projectDescInput.value : "").trim();
  const system_prompt = (projectPromptInput ? projectPromptInput.value : "").trim();

  try {
    if (editingProjectId) {
      const res = await fetch(`/api/projects/${editingProjectId}`, {
        method: "PUT",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ name, description, system_prompt }),
      });
      if (!res.ok) throw new Error("Failed to update project");
      const updated = await res.json();
      const idx = userProjects.findIndex((p) => p.id === editingProjectId);
      if (idx !== -1) userProjects[idx] = updated;
    } else {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ name, description, system_prompt }),
      });
      if (!res.ok) throw new Error("Failed to create project");
      const created = await res.json();
      userProjects.push(created);
      currentProjectId = created.id;
    }
    renderProjectPills();
    closeProjectModal();
    loadConversations(false);
  } catch (err) {
    console.error("Save project error:", err);
    alert(err.message || "Failed to save project.");
  }
}

async function deleteProjectFromModal() {
  if (!editingProjectId) return;
  if (!confirm("Are you sure you want to delete this project? Conversations inside it will not be deleted, but unassigned.")) return;

  try {
    const res = await fetch(`/api/projects/${editingProjectId}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error("Failed to delete project");
    userProjects = userProjects.filter((p) => p.id !== editingProjectId);
    if (currentProjectId === editingProjectId) {
      currentProjectId = "";
    }
    renderProjectPills();
    closeProjectModal();
    loadConversations(false);
  } catch (err) {
    console.error("Delete project error:", err);
    alert(err.message || "Failed to delete project.");
  }
}

// ---------------- Sidebar & Conversations ----------------

async function loadConversations(autoSelect = false) {
  if (!authToken) return;
  try {
    let url = "/api/conversations";
    if (currentProjectId) {
      url += `?project_id=${encodeURIComponent(currentProjectId)}`;
    }
    const res = await fetch(url, { headers: authHeaders() });
    if (res.status === 401) {
      signOut();
      return;
    }
    conversations = await res.json();
    renderConversationsList();
    if (currentConversationId && currentConversationId !== "new") {
      const active = conversations.find((c) => c.id === currentConversationId);
      if (active && active.title) {
        chatTitleHeader.textContent = active.title;
      }
    }
    if (autoSelect) {
      let targetId = null;
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const qC = urlParams.get("c");
        if (qC && qC !== "new") targetId = qC;
      } catch {}
      if (targetId && targetId !== "new") {
        await switchConversation(targetId);
      }
    }
  } catch (err) {
    console.error("Failed to load conversations:", err);
  }
}

function renderConversationsList() {
  conversationsListEl.innerHTML = "";

  const query = (sidebarSearchInput ? sidebarSearchInput.value : "").trim().toLowerCase();
  if (sidebarSearchClearBtn) {
    sidebarSearchClearBtn.style.display = query ? "inline-flex" : "none";
  }

  const filtered = conversations.filter((c) => {
    if (!query) return true;
    return (c.title || "").toLowerCase().includes(query);
  });

  if (!conversations.length) {
    conversationsListEl.innerHTML = `<div class="sidebar-empty-note">No chats yet</div>`;
    return;
  }

  if (!filtered.length) {
    conversationsListEl.innerHTML = `<div class="sidebar-empty-note">No chats match "${escapeHtml(query)}"</div>`;
    return;
  }

  const pinned = filtered.filter((c) => c.is_pinned === 1 || c.is_pinned === true);
  const recent = filtered.filter((c) => !c.is_pinned);

  if (pinned.length > 0) {
    const pinnedHeader = document.createElement("div");
    pinnedHeader.className = "conv-group-header";
    pinnedHeader.innerHTML = `<span>Pinned</span><span class="conv-count-badge">${pinned.length}</span>`;
    conversationsListEl.appendChild(pinnedHeader);
    pinned.forEach((c) => conversationsListEl.appendChild(createConversationItem(c)));
  }

  if (recent.length > 0) {
    if (pinned.length > 0) {
      const recentHeader = document.createElement("div");
      recentHeader.className = "conv-group-header";
      recentHeader.innerHTML = `<span>Recent</span>`;
      conversationsListEl.appendChild(recentHeader);
    }
    recent.forEach((c) => conversationsListEl.appendChild(createConversationItem(c)));
  }
}

function createConversationItem(c) {
  const isPinned = c.is_pinned === 1 || c.is_pinned === true;
  const item = document.createElement("div");
  item.className = `conversation-item ${c.id === currentConversationId ? "active" : ""} ${isPinned ? "pinned" : ""}`;
  item.dataset.id = c.id;

  const pinTitle = isPinned ? "Unpin chat" : "Pin to top";
  const pinIcon = isPinned ? ICONS.pinnedActive : ICONS.pin;

  item.innerHTML = `
    ${isPinned ? `<span class="conv-pin-badge" title="Pinned chat">${ICONS.pinnedActive}</span>` : ""}
    <span class="conv-title" title="${escapeHtml(c.title)}">${escapeHtml(c.title)}</span>
    <div class="conv-actions">
      <button class="conv-action-btn pin-btn ${isPinned ? "is-pinned" : ""}" type="button" title="${pinTitle}" aria-label="${pinTitle}">
        ${pinIcon}
      </button>
      <button class="conv-action-btn edit-btn" type="button" title="Rename chat" aria-label="Rename chat">
        ${ICONS.edit}
      </button>
      <button class="conv-action-btn delete-btn" type="button" title="Delete chat" aria-label="Delete chat">
        ${ICONS.trash}
      </button>
    </div>
  `;

  item.addEventListener("click", (e) => {
    if (e.target.closest(".conv-actions") || e.target.closest(".conv-rename-input")) return;
    switchConversation(c.id);
  });

  const pinBtn = item.querySelector(".pin-btn");
  pinBtn?.addEventListener("click", async (e) => {
    e.stopPropagation();
    await togglePinConversation(c.id);
  });

  const editBtn = item.querySelector(".edit-btn");
  editBtn?.addEventListener("click", (e) => {
    e.stopPropagation();
    startInlineRename(item, c);
  });

  const delBtn = item.querySelector(".delete-btn");
  delBtn?.addEventListener("click", async (e) => {
    e.stopPropagation();
    if (!confirm(`Delete chat "${c.title}"?\nThis cannot be undone.`)) return;
    await deleteConversation(c.id);
  });

  return item;
}

function sortConversationsList() {
  conversations.sort((a, b) => {
    const aPin = (a.is_pinned === 1 || a.is_pinned === true) ? 1 : 0;
    const bPin = (b.is_pinned === 1 || b.is_pinned === true) ? 1 : 0;
    if (bPin !== aPin) return bPin - aPin;
    const aTime = a.updated_at ? new Date(a.updated_at).getTime() : 0;
    const bTime = b.updated_at ? new Date(b.updated_at).getTime() : 0;
    return bTime - aTime;
  });
}

async function togglePinConversation(id) {
  const conv = conversations.find((c) => c.id === id);
  if (!conv) return;
  const currentStatus = conv.is_pinned === 1 || conv.is_pinned === true;
  const newStatus = !currentStatus;

  // Optimistic update
  conv.is_pinned = newStatus ? 1 : 0;
  sortConversationsList();
  renderConversationsList();

  try {
    const res = await fetch(`/api/conversations/${id}/pin`, {
      method: "PATCH",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ is_pinned: newStatus }),
    });
    if (res.status === 401) {
      signOut();
      return;
    }
    if (!res.ok) {
      conv.is_pinned = currentStatus ? 1 : 0;
      sortConversationsList();
      renderConversationsList();
    }
  } catch (err) {
    console.error("Failed to toggle pin:", err);
    conv.is_pinned = currentStatus ? 1 : 0;
    sortConversationsList();
    renderConversationsList();
  }
}

function startInlineRename(itemEl, conv) {
  if (itemEl.querySelector(".conv-rename-input")) return;

  const titleSpan = itemEl.querySelector(".conv-title");
  const pinBadge = itemEl.querySelector(".conv-pin-badge");
  const actionsDiv = itemEl.querySelector(".conv-actions");
  if (!titleSpan) return;

  const oldTitle = conv.title || "Chat";
  titleSpan.style.display = "none";
  if (pinBadge) pinBadge.style.display = "none";
  if (actionsDiv) actionsDiv.style.display = "none";

  const input = document.createElement("input");
  input.type = "text";
  input.className = "conv-rename-input";
  input.value = oldTitle;
  input.spellcheck = false;

  itemEl.insertBefore(input, actionsDiv || null);
  input.focus();
  input.select();

  let committed = false;

  const cleanup = () => {
    input.remove();
    titleSpan.style.display = "";
    if (pinBadge) pinBadge.style.display = "";
    if (actionsDiv) actionsDiv.style.display = "";
  };

  const commit = async () => {
    if (committed) return;
    committed = true;
    const newTitle = input.value.trim();
    if (!newTitle || newTitle === oldTitle) {
      cleanup();
      return;
    }
    cleanup();
    await renameConversation(conv.id, newTitle);
  };

  const cancel = () => {
    if (committed) return;
    committed = true;
    cleanup();
  };

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      commit();
    } else if (e.key === "Escape") {
      e.preventDefault();
      cancel();
    }
  });

  input.addEventListener("blur", commit);
  input.addEventListener("click", (e) => e.stopPropagation());
}

async function renameConversation(id, newTitle) {
  const conv = conversations.find((c) => c.id === id);
  const oldTitle = conv ? conv.title : "";
  if (conv) conv.title = newTitle;
  if (id === currentConversationId) {
    chatTitleHeader.textContent = newTitle;
  }
  renderConversationsList();

  try {
    const res = await fetch(`/api/conversations/${id}`, {
      method: "PATCH",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ title: newTitle }),
    });
    if (res.status === 401) {
      signOut();
      return;
    }
    if (!res.ok && conv) {
      conv.title = oldTitle;
      if (id === currentConversationId) chatTitleHeader.textContent = oldTitle;
      renderConversationsList();
    }
  } catch (err) {
    console.error("Failed to rename conversation:", err);
    if (conv) {
      conv.title = oldTitle;
      if (id === currentConversationId) chatTitleHeader.textContent = oldTitle;
      renderConversationsList();
    }
  }
}

function promptRenameActiveChat() {
  if (!currentConversationId) return;
  const activeConv = conversations.find((c) => c.id === currentConversationId);
  const currentTitle = activeConv ? activeConv.title : (chatTitleHeader.textContent || "Chat");
  const newTitle = window.prompt("Enter new title for this conversation:", currentTitle);
  if (newTitle === null) return;
  const trimmed = newTitle.trim();
  if (!trimmed || trimmed === currentTitle) return;
  renameConversation(currentConversationId, trimmed);
}

async function switchConversation(id) {
  if (busy || id === currentConversationId) return;
  hideArtifactsView();

  try {
    const res = await fetch(`/api/conversations/${id}`, { headers: authHeaders() });
    if (res.status === 401) {
      signOut();
      return;
    }
    if (!res.ok) return;
    const data = await res.json();

    currentConversationId = id;
    localStorage.setItem("cortex_active_conv", id);
    try {
      const url = new URL(window.location);
      url.searchParams.set("c", id);
      window.history.replaceState({}, "", url);
    } catch {}
    chatTitleHeader.textContent = data.conversation.title || "Chat";
    messages = data.messages || [];

    closeMobileSidebar();
    renderConversationsList();

    if (!messages.length) {
      showEmptyState();
    } else {
      rebuildChatFromMessages();
    }
  } catch (err) {
    console.error("Failed to switch conversation:", err);
  }
}

async function deleteConversation(id) {
  try {
    const res = await fetch(`/api/conversations/${id}`, { method: "DELETE", headers: authHeaders() });
    if (res.status === 401) {
      signOut();
      return;
    }
    conversations = conversations.filter((c) => c.id !== id);
    if (currentConversationId === id) {
      localStorage.removeItem("cortex_active_conv");
      startNewChat();
    } else {
      renderConversationsList();
    }
  } catch (err) {
    console.error("Failed to delete conversation:", err);
  }
}

function showToast(message, duration = 3000) {
  let toast = document.querySelector(".cortex-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "cortex-toast";
    document.body.appendChild(toast);
  }
  toast.innerHTML = message;
  toast.classList.add("show");
  if (toast._hideTimeout) clearTimeout(toast._hideTimeout);
  toast._hideTimeout = setTimeout(() => {
    toast.classList.remove("show");
  }, duration);
}

async function forkConversationAt(messageId) {
  if (!currentConversationId) {
    showToast("Cannot branch an unsaved chat.");
    return;
  }
  try {
    showToast("Branching conversation…");
    const payload = {};
    if (messageId) payload.up_to_message_id = messageId;
    const res = await fetch(`/api/conversations/${currentConversationId}/fork`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    if (res.status === 401) {
      signOut();
      return;
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showToast("Failed to branch: " + (err.detail || "Server error"));
      return;
    }
    const newConv = await res.json();
    await loadConversations(false);
    await switchConversation(newConv.id);
    showToast(`Branched into "${escapeHtml(newConv.title || 'Branched Chat')}" 🔀`);
  } catch (err) {
    console.error("Fork error:", err);
    showToast("Failed to branch conversation.");
  }
}

async function handleMessageFeedback(messageId, value, btnUp, btnDown) {
  if (!messageId) {
    showToast("Message ID not ready yet.");
    return;
  }
  const isAlreadyActive =
    (value === 1 && btnUp?.classList.contains("active")) ||
    (value === -1 && btnDown?.classList.contains("active"));
  const finalValue = isAlreadyActive ? 0 : value;

  try {
    const res = await fetch(`/api/messages/${messageId}/feedback`, {
      method: "PATCH",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ feedback: finalValue }),
    });
    if (res.status === 401) {
      signOut();
      return;
    }
    if (res.ok) {
      if (btnUp) btnUp.classList.toggle("active", finalValue === 1);
      if (btnDown) btnDown.classList.toggle("active", finalValue === -1);

      const m = messages.find((x) => x.id === messageId);
      if (m) m.feedback = finalValue;

      if (finalValue === 1) {
        showToast("Thanks for your positive feedback! 👍");
      } else if (finalValue === -1) {
        showToast("Thanks for your feedback. We'll work to improve! 👎");
      }
    }
  } catch (err) {
    console.error("Feedback error:", err);
  }
}

function startNewChat() {
  if (busy) return;
  hideArtifactsView();
  currentConversationId = null;
  localStorage.setItem("cortex_active_conv", "new");
  try {
    const url = new URL(window.location);
    url.searchParams.delete("c");
    window.history.replaceState({}, "", url.pathname + (url.hash || ""));
  } catch {}
  messages = [];
  if (currentProjectId) {
    const proj = userProjects.find((p) => p.id === currentProjectId);
    chatTitleHeader.textContent = proj ? `New Chat (${proj.name})` : "New Chat";
  } else {
    chatTitleHeader.textContent = "New Chat";
  }
  showEmptyState();
  clearAttachment();
  promptEl.value = "";
  autoResize();
  if (typeof window.setResponseMode === "function") {
    window.setResponseMode("auto");
  }
  renderConversationsList();
  closeMobileSidebar();
  promptEl.focus();
}

function setSidebarCollapsed(collapsed) {
  if (!appView) return;
  if (collapsed) {
    appView.classList.add("sidebar-collapsed");
    sidebar?.classList.add("collapsed");
    localStorage.setItem("cortex_sidebar_collapsed", "true");
    if (collapseSidebarBtn) collapseSidebarBtn.setAttribute("title", "Expand sidebar (Ctrl+B)");
    if (toggleSidebarBtn) toggleSidebarBtn.setAttribute("title", "Expand sidebar (Ctrl+B)");
  } else {
    appView.classList.remove("sidebar-collapsed");
    sidebar?.classList.remove("collapsed");
    localStorage.setItem("cortex_sidebar_collapsed", "false");
    if (collapseSidebarBtn) collapseSidebarBtn.setAttribute("title", "Collapse sidebar (Ctrl+B)");
    if (toggleSidebarBtn) toggleSidebarBtn.setAttribute("title", "Collapse sidebar (Ctrl+B)");
  }
}

function toggleSidebar() {
  if (window.innerWidth <= 768) {
    sidebar.classList.toggle("mobile-open");
    sidebarOverlay.classList.toggle("active");
  } else {
    const isCollapsed = appView.classList.contains("sidebar-collapsed") || sidebar.classList.contains("collapsed");
    setSidebarCollapsed(!isCollapsed);
  }
}

function closeMobileSidebar() {
  sidebar.classList.remove("mobile-open");
  sidebarOverlay.classList.remove("active");
}

toggleSidebarBtn?.addEventListener("click", toggleSidebar);
collapseSidebarBtn?.addEventListener("click", () => setSidebarCollapsed(true));
if (closeSidebarBtn) closeSidebarBtn.addEventListener("click", closeMobileSidebar);
sidebarOverlay?.addEventListener("click", closeMobileSidebar);
newChatBtn?.addEventListener("click", startNewChat);

// Title renaming in topbar
editChatTitleBtn?.addEventListener("click", promptRenameActiveChat);
chatTitleHeader?.addEventListener("click", promptRenameActiveChat);

// Sidebar Search event listeners
sidebarSearchInput?.addEventListener("input", () => {
  const query = (sidebarSearchInput.value || "").trim();
  if (sidebarSearchClearBtn) {
    sidebarSearchClearBtn.style.display = query ? "inline-flex" : "none";
  }
  renderConversationsList();
});

sidebarSearchClearBtn?.addEventListener("click", () => {
  if (sidebarSearchInput) {
    sidebarSearchInput.value = "";
    sidebarSearchClearBtn.style.display = "none";
    sidebarSearchInput.focus();
    renderConversationsList();
  }
});

sidebarSearchInput?.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    sidebarSearchInput.value = "";
    if (sidebarSearchClearBtn) sidebarSearchClearBtn.style.display = "none";
    renderConversationsList();
    sidebarSearchInput.blur();
  }
});

// ---------------- File & Photo Attachment Handling ----------------

function clearAttachment() {
  attachedFile = null;
  attachmentPreview.style.display = "none";
  const chipIcon = attachmentPreview.querySelector(".attachment-icon");
  if (chipIcon) chipIcon.textContent = "📄";
  if (fileInputDocs) fileInputDocs.value = "";
  if (fileInputImages) fileInputImages.value = "";
}

function closeUserProfileMenu() {
  if (userProfileMenu) userProfileMenu.style.display = "none";
  if (userProfileBtn) userProfileBtn.setAttribute("aria-expanded", "false");
  userMenuAnchor?.classList.remove("is-open");
}

function toggleUserProfileMenu() {
  if (!userProfileMenu) return;
  const isShown = userProfileMenu.style.display === "block";
  if (isShown) {
    closeUserProfileMenu();
  } else {
    closeAllDropdowns();
    const rawName = (currentUser && currentUser.username) || localStorage.getItem("cortex_username") || "user";
    const email = currentUser?.email || `${rawName.toLowerCase()}@cortex.ai`;
    if (userMenuEmail) userMenuEmail.textContent = email;
    userProfileMenu.style.display = "block";
    if (userProfileBtn) userProfileBtn.setAttribute("aria-expanded", "true");
    userMenuAnchor?.classList.add("is-open");
  }
}

function closeAllDropdowns() {
  if (attachMenu) {
    attachMenu.style.display = "none";
    attachMenu.classList.remove("open-upwards");
  }
  if (presetsMenu) {
    presetsMenu.style.display = "none";
    presetsMenu.classList.remove("open-upwards");
  }
  closeUserProfileMenu();
}

function toggleDropdown(menu) {
  if (!menu) return;
  const isShown = menu.style.display === "block";
  closeAllDropdowns();
  if (!isShown) {
    menu.classList.remove("open-upwards");
    menu.style.display = "block";
    const rect = menu.getBoundingClientRect();
    if (rect.bottom > window.innerHeight - 10 && rect.top > rect.height) {
      menu.classList.add("open-upwards");
    }
  }
}

// Toggle Attach Menu (+ button)
attachBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  if (busy) return;
  toggleDropdown(attachMenu);
});

// Option 1: Add Files (PDF, CSV, HTML, Code, TXT, etc.)
menuAddFiles?.addEventListener("click", (e) => {
  e.stopPropagation();
  closeAllDropdowns();
  fileInputDocs?.click();
});

// Option 2: Add Photos or Screenshots
menuAddPhotos?.addEventListener("click", (e) => {
  e.stopPropagation();
  closeAllDropdowns();
  fileInputImages?.click();
});

// Toggle Agent Presets Menu (🪄 button)
presetsBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  toggleDropdown(presetsMenu);
});

// Presets click listeners (8 agent actions)
document.querySelectorAll(".preset-item").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    const textToInsert = btn.getAttribute("data-insert") || "";
    if (textToInsert) {
      if (!promptEl.value.includes(textToInsert)) {
        promptEl.value = textToInsert + promptEl.value;
      }
      autoResize();
      promptEl.focus();
    }
    closeAllDropdowns();
  });
});

// Close popup menus on outside click or Escape
document.addEventListener("click", (e) => {
  if (!e.target.closest(".composer-menu-anchor")) {
    if (attachMenu) attachMenu.style.display = "none";
    if (presetsMenu) presetsMenu.style.display = "none";
  }
  if (!e.target.closest(".user-menu-anchor")) {
    closeUserProfileMenu();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (imageLightboxModal && imageLightboxModal.classList.contains("is-open")) {
      closeImageLightbox();
      return;
    }
    closeAllDropdowns();
    closeUserProfileMenu();
    closeSettingsModal();
  }
  if (imageLightboxModal && imageLightboxModal.classList.contains("is-open")) {
    if (e.key === "+" || e.key === "=") {
      setLightboxZoom(lightboxCurrentZoom + 0.25);
    } else if (e.key === "-" || e.key === "_") {
      setLightboxZoom(lightboxCurrentZoom - 0.25);
    } else if (e.key === "0") {
      setLightboxZoom(1.0);
    }
  }
});

async function uploadSingleFile(file) {
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  try {
    if (attachBtn) attachBtn.disabled = true;
    const isImg = file.type.startsWith("image/") || /\.(png|jpe?g|webp|gif|svg|bmp)$/i.test(file.name);
    const chipIcon = attachmentPreview.querySelector(".attachment-icon");
    if (chipIcon) chipIcon.textContent = isImg ? "🖼️" : "📄";
    attachmentName.textContent = `Uploading ${file.name}…`;
    attachmentSize.textContent = "";
    attachmentPreview.style.display = "flex";

    const res = await fetch("/api/upload", {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });

    if (res.status === 401) {
      signOut();
      return;
    }

    if (!res.ok) {
      let detail = "Upload failed";
      try {
        const err = await res.json();
        detail = err.detail || detail;
      } catch {}
      if (res.status === 429 || detail.toLowerCase().includes("limit") || detail.toLowerCase().includes("quota") || detail.toLowerCase().includes("exhausted")) {
        showQuotaToast("⚠️ Daily upload limit reached (10 files/day). Your upload quota will refresh tomorrow at 00:00 UTC.");
      } else {
        showQuotaToast("Upload error: " + detail);
      }
      clearAttachment();
      return;
    }

    const data = await res.json();
    attachedFile = data;

    if (chipIcon) {
      if (isImg && data.image_data_url) {
        chipIcon.innerHTML = `<img src="${data.image_data_url}" alt="thumb" class="attachment-thumb-mini" />`;
      } else {
        chipIcon.textContent = isImg ? "🖼️" : "📄";
      }
    }
    attachmentName.textContent = data.filename;
    attachmentSize.textContent = `(${formatBytes(data.size)}${data.truncated ? " - truncated" : ""})`;
    attachmentPreview.style.display = "flex";
  } catch (err) {
    showQuotaToast("Upload error: " + err.message);
    clearAttachment();
  } finally {
    if (attachBtn) attachBtn.disabled = false;
  }
}

fileInputDocs?.addEventListener("change", (e) => {
  const file = e.target.files && e.target.files[0];
  if (file) uploadSingleFile(file);
});

fileInputImages?.addEventListener("change", (e) => {
  const file = e.target.files && e.target.files[0];
  if (file) uploadSingleFile(file);
});

removeAttachmentBtn?.addEventListener("click", clearAttachment);

// ---------------- Dynamic Greeting & Claude Empty State ----------------

function formatDisplayName(raw) {
  if (!raw || typeof raw !== "string") return "";
  const trimmed = raw.trim();
  if (!trimmed) return "";
  return trimmed
    .split(/\s+/)
    .map((w) => (w ? w.charAt(0).toUpperCase() + w.slice(1) : ""))
    .join(" ");
}

function getDynamicGreeting(username) {
  const rawName =
    username ||
    (currentUser && currentUser.username) ||
    localStorage.getItem("cortex_username") ||
    "Pedro";
  const name = formatDisplayName(rawName) || "Pedro";
  return {
    title: `Hey ${name} , Do you want to explore something with me ?`,
    subtitle: ""
  };
}

function updateDynamicGreeting(username) {
  const greeting = getDynamicGreeting(username);
  const titleEl = document.getElementById("emptyGreetingTitle");
  if (titleEl) titleEl.textContent = greeting.title;
  const subEl = document.getElementById("emptyGreetingSubtitle");
  if (subEl) subEl.textContent = greeting.subtitle;
}

function updateExportButtonVisibility() {
  const btn = document.getElementById("exportChatBtn") || exportChatBtn;
  if (!btn) return;
  if (messages && messages.length > 0) {
    btn.style.display = "inline-flex";
  } else {
    btn.style.display = "none";
  }
}

function showEmptyState() {
  const shell = document.querySelector(".app-shell");
  if (shell) shell.classList.add("is-empty-chat");

  chatEl.innerHTML = "";
  const clone = emptyStateTpl.content.cloneNode(true);

  const greeting = getDynamicGreeting();
  const titleEl = clone.querySelector("#emptyGreetingTitle");
  const subEl = clone.querySelector("#emptyGreetingSubtitle");
  if (titleEl) titleEl.textContent = greeting.title;
  if (subEl) subEl.textContent = greeting.subtitle;

  clone.querySelectorAll(".prompt-card").forEach((button) => {
    button.addEventListener("click", () => {
      promptEl.value = button.dataset.prompt;
      autoResize();
      promptEl.focus();
    });
  });

  chatEl.appendChild(clone);
  updateExportButtonVisibility();
}

function autoResize() {
  promptEl.style.height = "auto";
  promptEl.style.height = `${Math.min(promptEl.scrollHeight, 200)}px`;
}

function clearChatDom() {
  const shell = document.querySelector(".app-shell");
  if (shell) shell.classList.remove("is-empty-chat");
  chatEl.innerHTML = "";
}

function parseUserMessage(rawContent) {
  let text = rawContent || "";
  let imageAttachment = null;
  let docAttachment = null;

  // 1. Check for Attached Image
  const imgHeaderMatch = text.match(/\[Attached Image:\s*([^\]\(\n]+?)(?:\s*\(([^)]+)\))?\]/i);
  const b64Match = text.match(/\(Visual Image Base64:\s*(data:image\/[^;]+;base64,[A-Za-z0-9+/=]+)\)/i);

  if (imgHeaderMatch || b64Match) {
    const filename = imgHeaderMatch ? imgHeaderMatch[1].trim() : "Attached Image";
    const sizeStr = imgHeaderMatch && imgHeaderMatch[2] ? imgHeaderMatch[2].trim() : "";
    const dataUrl = b64Match ? b64Match[1] : null;

    imageAttachment = {
      filename,
      size: sizeStr,
      dataUrl,
    };

    text = text.replace(/\[Attached Image:[^\]]+\]\s*/gi, "");
    text = text.replace(/\(Visual Image Base64:\s*data:image\/[^;]+;base64,[A-Za-z0-9+/=]+\)\s*/gi, "");
    text = text.replace(/\[Previous turn image attachment\]\s*/gi, "");
  }

  // 2. Check for Attached Document
  const docMatch = text.match(/\[Attached Document:\s*([^\]]+)\]/i);
  if (docMatch) {
    const filename = docMatch[1].trim();
    docAttachment = { filename };
    text = text.replace(/\[Attached Document:\s*([^\]]+)\](?:\s*```[\s\S]*?```)?\s*/gi, "");
  }

  return {
    cleanText: text.trim(),
    imageAttachment,
    docAttachment,
  };
}

function addUserMessage(content, msgIndex, attachmentMeta, messageId) {
  const parsed = parseUserMessage(content);
  const cleanPrompt = parsed.cleanText;

  // Prioritize explicit attachmentMeta if provided, else fallback to parsed
  const imgData = attachmentMeta?.is_image && attachmentMeta?.image_data_url
    ? {
        filename: attachmentMeta.filename || "Attached Image",
        size: formatBytes(attachmentMeta.size || 0),
        dataUrl: attachmentMeta.image_data_url,
      }
    : parsed.imageAttachment;

  const docData = (!attachmentMeta?.is_image && attachmentMeta?.filename)
    ? { filename: attachmentMeta.filename }
    : parsed.docAttachment;

  const row = document.createElement("div");
  row.className = "message-row msg-row user";
  if (messageId) row.dataset.messageId = messageId;
  if (msgIndex !== undefined) row.dataset.msgIndex = msgIndex;

  const col = document.createElement("div");
  col.className = "message-col";

  // 1. Image Thumbnail Card (ChatGPT-Style)
  if (imgData && imgData.dataUrl) {
    const imgCard = document.createElement("div");
    imgCard.className = "user-attachment-card image-card";
    imgCard.setAttribute("role", "button");
    imgCard.setAttribute("tabindex", "0");
    imgCard.setAttribute("title", `Click to view ${imgData.filename}`);
    imgCard.innerHTML = `
      <div class="user-thumb-wrapper">
        <img class="user-msg-thumb" src="${imgData.dataUrl}" alt="${escapeHtml(imgData.filename)}" loading="lazy" />
        <div class="user-thumb-overlay">
          <span class="user-thumb-zoom-icon">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              <line x1="11" y1="8" x2="11" y2="14"></line>
              <line x1="8" y1="11" x2="14" y2="11"></line>
            </svg>
          </span>
          <span class="user-thumb-zoom-text">View Image</span>
        </div>
      </div>
      <div class="user-attachment-meta">
        <span class="user-attachment-name" title="${escapeHtml(imgData.filename)}">${escapeHtml(imgData.filename)}</span>
        <span class="user-attachment-size">${escapeHtml(imgData.size || "")}</span>
      </div>
    `;

    const launchLightbox = () => {
      openImageLightbox({
        src: imgData.dataUrl,
        filename: imgData.filename,
        size: imgData.size,
      });
    };

    imgCard.addEventListener("click", launchLightbox);
    imgCard.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        launchLightbox();
      }
    });

    col.appendChild(imgCard);
  } else if (docData && docData.filename) {
    const docCard = document.createElement("div");
    docCard.className = "user-attachment-card doc-card";
    docCard.innerHTML = `
      <span class="doc-card-icon">📄</span>
      <div class="doc-card-details">
        <span class="doc-card-name">${escapeHtml(docData.filename)}</span>
        <span class="doc-card-meta">Document attachment</span>
      </div>
    `;
    col.appendChild(docCard);
  }

  // 2. User Prompt Bubble (render if user typed text or if no image/doc card exists)
  if (cleanPrompt || (!imgData && !docData)) {
    const bubble = document.createElement("div");
    bubble.className = "bubble user-bubble";
    const span = document.createElement("span");
    span.className = "user-content-text";
    span.textContent = cleanPrompt || "Please inspect and analyze this attached image.";
    bubble.appendChild(span);
    col.appendChild(bubble);
  }

  // 3. Action Buttons (Copy, Edit, Fork/Branch)
  const actionsDiv = document.createElement("div");
  actionsDiv.className = "user-actions";
  actionsDiv.innerHTML = `
    <button class="user-action-btn user-copy-btn" type="button" title="Copy prompt" aria-label="Copy prompt">
      ${ICONS.copy}
    </button>
    <button class="user-action-btn user-edit-btn" type="button" title="Edit prompt" aria-label="Edit prompt">
      ${ICONS.edit}
    </button>
    <button class="user-action-btn user-branch-btn" type="button" title="Fork chat from here" aria-label="Fork chat from here">
      ${ICONS.branch}
    </button>
  `;
  col.appendChild(actionsDiv);
  row.appendChild(col);

  const copyBtn = actionsDiv.querySelector(".user-copy-btn");
  copyBtn?.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(cleanPrompt);
      copyBtn.classList.add("copied");
      copyBtn.innerHTML = ICONS.check;
      setTimeout(() => {
        copyBtn.classList.remove("copied");
        copyBtn.innerHTML = ICONS.copy;
      }, 1600);
    } catch {
      /* ignore */
    }
  });

  const editBtn = actionsDiv.querySelector(".user-edit-btn");
  editBtn?.addEventListener("click", () => {
    startUserMessageEdit(row, cleanPrompt, msgIndex);
  });

  const branchBtn = actionsDiv.querySelector(".user-branch-btn");
  branchBtn?.addEventListener("click", () => {
    const mId = row.dataset.messageId || (msgIndex !== undefined && messages[msgIndex]?.id);
    forkConversationAt(mId);
  });

  chatEl.appendChild(row);
  scrollToBottom(false);
  return row;
}

function startUserMessageEdit(row, oldContent, msgIndex) {
  let bubble = row.querySelector(".user-bubble");
  if (!bubble) {
    const col = row.querySelector(".message-col");
    bubble = document.createElement("div");
    bubble.className = "bubble user-bubble";
    const span = document.createElement("span");
    span.className = "user-content-text";
    bubble.appendChild(span);
    const actions = row.querySelector(".user-actions");
    if (actions) col.insertBefore(bubble, actions);
    else col.appendChild(bubble);
  }
  if (bubble.querySelector(".user-edit-box")) return;

  const textSpan = bubble.querySelector(".user-content-text");
  const userActions = row.querySelector(".user-actions");
  if (textSpan) textSpan.style.display = "none";
  if (userActions) userActions.style.display = "none";

  const editBox = document.createElement("div");
  editBox.className = "user-edit-box";
  editBox.innerHTML = `
    <textarea class="user-edit-textarea" rows="2" style="width:100%; min-width:280px; max-width:100%; resize:none; background:rgba(0,0,0,0.35); border:1px solid var(--accent); border-radius:10px; color:var(--text); padding:8px 12px; font-family:inherit; font-size:14px; outline:none;"></textarea>
    <div style="display:flex; justify-content:flex-end; gap:6px; margin-top:8px;">
      <button type="button" class="btn-cancel" style="background:transparent; border:1px solid var(--border); color:var(--muted); padding:5px 12px; border-radius:6px; font-size:12px; cursor:pointer;">Cancel</button>
      <button type="button" class="btn-save" style="background:var(--accent); border:0; color:#0d0f12; font-weight:600; padding:5px 14px; border-radius:6px; font-size:12px; cursor:pointer;">Save & Submit</button>
    </div>
  `;
  const ta = editBox.querySelector(".user-edit-textarea");
  ta.value = oldContent;
  bubble.appendChild(editBox);
  ta.focus();
  ta.select();

  const cleanup = () => {
    editBox.remove();
    if (textSpan) textSpan.style.display = "";
    if (userActions) userActions.style.display = "";
  };

  editBox.querySelector(".btn-cancel").addEventListener("click", cleanup);

  editBox.querySelector(".btn-save").addEventListener("click", () => {
    const newText = ta.value.trim();
    if (!newText || newText === oldContent) {
      cleanup();
      return;
    }
    cleanup();

    if (msgIndex !== undefined && msgIndex >= 0) {
      retryFromMessage(msgIndex, newText);
    } else {
      promptEl.value = newText;
      handleFormSubmit();
    }
  });
}

function addAssistantMessageShell() {
  const row = document.createElement("div");
  row.className = "message-row";
  row.innerHTML = `
    ${CORTEX_AVATAR_HTML}
    <div class="message-col">
      <!-- Dynamic Reasoning Thought Process Box -->
      <div class="thought-box open" style="display:none;">
        <div class="thought-header">
          <div class="thought-title">
            <span class="thought-icon">💭</span>
            <span class="thought-label">Thought Process</span>
            <span class="thought-timer-badge">Thinking…</span>
          </div>
          <span class="thought-toggle-icon">▼</span>
        </div>
        <div class="thought-content"></div>
      </div>

      <div class="tool-activity-wrap">
        <div class="tool-live-badge" style="display:none;">
          <div class="tool-spinner"></div>
          <span class="tool-live-text">Thinking & using tools…</span>
        </div>
        <div class="tool-accordion" style="display:none;">
          <div class="tool-accordion-summary">
            <span class="tool-accordion-title">Used tools</span>
            ${ICONS.chevron}
          </div>
          <div class="tool-accordion-details"></div>
        </div>
      </div>
      <div class="tool-badges" hidden></div>
      <div class="bubble ai-bubble"><span class="stream-cursor"></span></div>
      <div class="msg-actions" hidden></div>
    </div>
  `;
  chatEl.appendChild(row);
  scrollToBottom(false);

  const thoughtBox = row.querySelector(".thought-box");
  const thoughtHeader = row.querySelector(".thought-header");
  thoughtHeader.addEventListener("click", () => {
    thoughtBox.classList.toggle("open");
  });

  const accordionEl = row.querySelector(".tool-accordion");
  const accordionSummary = row.querySelector(".tool-accordion-summary");
  accordionSummary.addEventListener("click", () => {
    accordionEl.classList.toggle("open");
  });

  return {
    row,
    thoughtBox,
    thoughtTimerBadge: row.querySelector(".thought-timer-badge"),
    thoughtContent: row.querySelector(".thought-content"),
    activityWrap: row.querySelector(".tool-activity-wrap"),
    liveBadge: row.querySelector(".tool-live-badge"),
    liveText: row.querySelector(".tool-live-text"),
    accordionEl,
    accordionTitle: row.querySelector(".tool-accordion-title"),
    accordionDetails: row.querySelector(".tool-accordion-details"),
    badgesEl: row.querySelector(".tool-badges"),
    bubbleEl: row.querySelector(".ai-bubble"),
    actionsEl: row.querySelector(".msg-actions"),
  };
}

function setToolBadges(badgesEl, toolsUsed) {
  if (!toolsUsed || !toolsUsed.length) return;
  badgesEl.hidden = false;
  badgesEl.innerHTML = toolsUsed
    .map((name) => {
      const label = TOOL_LABELS[name] || name;
      const icon = TOOL_ICONS[name] || ICONS.tool;
      const extraClass = name.startsWith("code") ? "code-badge" : name.startsWith("doc") ? "doc-badge" : name.startsWith("chart") ? "chart-badge" : name.includes("python") ? "python-badge" : "";
      return `<span class="tool-badge ${extraClass}">${icon}${escapeHtml(label)}</span>`;
    })
    .join("");
}

function isContinuationPrompt(text) {
  if (!text) return false;
  const t = text.trim().toLowerCase();
  if (t.includes("please continue directly from where you left off")) return true;
  if (/^(?:continue|carry on|continue generating|keep going|aage bolo|aage batao|next)\b/i.test(t)) return true;
  return false;
}

function renderStreamedText(bubbleEl, fullText, done, options = {}) {
  let cleanText = (fullText || "")
    .replace(/<tool_call>[\s\S]*?<\/tool_call>/gi, "")
    .replace(/<tool_call>[\s\S]*$/gi, "")
    .replace(/<\/?(?:tool_call|function|parameter|execute_pythoncode)[^>]*>/gi, "")
    .replace(/=\s*<?execute_pythoncode>?/gi, "")
    .replace(/```(?:python|py|json)?\s*(?:execute_python\s*)?\{\s*[\s\S]*?"code"\s*:\s*"((?:[^"\\]|\\.)*)"[\s\S]*?\}\s*```/gi, (m, rawCode) => {
      try {
        return "```python\n" + JSON.parse(`"${rawCode}"`).trim() + "\n```";
      } catch (e) {
        return m;
      }
    })
    .replace(/```execute_python/gi, "```python")
    .replace(/!\[([^\]]*)\]\((?:attachment:\/\/|sandbox:\/)[^\)]*\)/gi, "")
    .replace(/\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[\s\S]*?\}\s*\}\s*(?:null)?/gi, "");

  if (done) {
    cleanText = healMarkdownPlots(cleanText.trim());
    bubbleEl._rawFullText = cleanText;

    const isTruncated = Boolean(options.isTruncated);
    const docTextToUse = (options.documentText || cleanText).trim();

    const { html: rendered, mathMap } = renderMarkdownWithMath(cleanText);
    let finalHtml = rendered;

    // Auto-detect if message is an explicit standalone document or structured report
    // If response was truncated, DO NOT render an incomplete document card preview (render plain markdown)
    if (!isTruncated) {
      const checkText = docTextToUse;
      const textWithoutCode = checkText.replace(/```[\s\S]*?```/g, "");
      const hasHeadings = /^#{1,3}\s+\S+/m.test(textWithoutCode);
      const hasTables = checkText.includes("| --- |") || checkText.includes("|:---:|");
      const hasCodeGuide =
        (checkText.includes("```python") ||
         checkText.includes("```js") ||
         checkText.includes("```html") ||
         checkText.includes("```sql")) &&
        checkText.length > 400;
      const isLongSubstantive =
        checkText.length > 500 &&
        (checkText.includes("##") || checkText.includes("- ") || checkText.includes("1. "));

      const isReport = (hasHeadings || hasTables || hasCodeGuide || isLongSubstantive) && checkText.length > 250;

      if (isReport && !rendered.includes('class="document-card"')) {
        docIdCounter++;
        const docId = "doc-" + docIdCounter;
        const filename = extractDocumentFilename(checkText);
        docRegistry.set(docId, { filename, text: checkText });
        const sizeStr = formatBytes(new Blob([checkText]).size);

        let docRenderedHtml = rendered;
        if (options.documentText) {
          const { html: stitchedHtml, mathMap: stitchedMathMap } = renderMarkdownWithMath(docTextToUse);
          docRenderedHtml = stitchedHtml;
          if (stitchedMathMap && mathMap) {
            for (const [k, v] of stitchedMathMap.entries()) {
              mathMap.set(k, v);
            }
          }
        }

        finalHtml = `
          <div class="document-card" data-doc-id="${docId}">
            <div class="document-header">
              <div class="document-file-info">
                <div class="document-icon">${ICONS.file}</div>
                <div class="document-titles">
                  <span class="document-filename">${escapeHtml(filename)}</span>
                  <div class="document-meta">
                    <span>MARKDOWN DOCUMENT</span>
                    <span>•</span>
                    <span>${sizeStr}</span>
                  </div>
                </div>
              </div>
              <div class="document-actions">
                <button type="button" class="document-btn document-preview-split-btn" title="Open in Split Panel">
                  ${ICONS.eye}
                  <span>Split Preview</span>
                </button>
                <button type="button" class="document-btn document-view-btn" title="Toggle Raw / Rendered">
                  ${ICONS.code}
                  <span>View Raw</span>
                </button>
                <button type="button" class="document-btn document-copy-btn" title="Copy Document Content">
                  ${ICONS.copy}
                  <span>Copy</span>
                </button>
                <button type="button" class="document-btn document-download-btn" title="Download ${escapeHtml(filename)}">
                  ${ICONS.download}
                  <span>Download .md</span>
                </button>
              </div>
            </div>
            <div class="document-body">
              <div class="document-rendered-view">${docRenderedHtml}</div>
              <div class="document-raw-view" style="display:none;"><pre><code>${escapeHtml(checkText)}</code></pre></div>
            </div>
          </div>
        `;
      }
    }

    bubbleEl.innerHTML = finalHtml;
    try { initMath(bubbleEl, mathMap); } catch (e) { console.warn("initMath error:", e); }
    try { initCharts(bubbleEl); } catch (e) { console.warn("initCharts error:", e); }
    try { initArtifacts(bubbleEl); } catch (e) { console.warn("initArtifacts error:", e); }

    // Enable lightbox click for any embedded matplotlib charts or figures
    bubbleEl.querySelectorAll("img").forEach((img) => {
      img.addEventListener("error", () => {
        img.style.display = "none";
      });
      if (!img.classList.contains("lightbox-enabled")) {
        img.classList.add("lightbox-enabled");
        img.style.cursor = "zoom-in";
        img.addEventListener("click", () => {
          openImageLightbox({
            src: img.src,
            filename: img.alt || "Generated Plot",
            size: "",
          });
        });
      }
    });

    return;
  }
  bubbleEl.innerHTML = `<span class="raw-stream">${escapeHtml(cleanText)}</span><span class="stream-cursor"></span>`;
}

function attachActions(actionsEl, { getText, onRetry, showRetry, isTruncated, onContinue, messageId, feedback = 0 }) {
  actionsEl.hidden = false;
  actionsEl.innerHTML = "";

  // 1. Copy button
  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "icon-btn";
  copyBtn.innerHTML = `${ICONS.copy}<span>Copy</span>`;
  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(normalizeMarkdownForExport(getText()));
      copyBtn.classList.add("copied");
      copyBtn.innerHTML = `${ICONS.check}<span>Copied</span>`;
      setTimeout(() => {
        copyBtn.classList.remove("copied");
        copyBtn.innerHTML = `${ICONS.copy}<span>Copy</span>`;
      }, 1600);
    } catch {
      /* ignore */
    }
  });
  actionsEl.appendChild(copyBtn);

  // 2. Direct 1-Click Download .md button for ANY assistant response!
  const downloadBtn = document.createElement("button");
  downloadBtn.type = "button";
  downloadBtn.className = "icon-btn";
  downloadBtn.title = "Download this response as Markdown (.md)";
  downloadBtn.innerHTML = `${ICONS.download}<span>Download .md</span>`;
  downloadBtn.addEventListener("click", () => {
    const text = getText();
    const filename = extractDocumentFilename(text);
    downloadTextFile(filename, text, "text/markdown;charset=utf-8");
    downloadBtn.classList.add("copied");
    downloadBtn.innerHTML = `${ICONS.check}<span>Downloaded</span>`;
    setTimeout(() => {
      downloadBtn.classList.remove("copied");
      downloadBtn.innerHTML = `${ICONS.download}<span>Download .md</span>`;
    }, 1600);
  });
  actionsEl.appendChild(downloadBtn);

  // 3. Read Aloud (TTS)
  const ttsBtn = document.createElement("button");
  ttsBtn.type = "button";
  ttsBtn.className = "icon-btn";
  ttsBtn.title = "Read aloud (Text-to-Speech)";
  ttsBtn.innerHTML = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg><span>Read</span>`;
  ttsBtn.addEventListener("click", () => {
    toggleTTS(ttsBtn, getText());
  });
  actionsEl.appendChild(ttsBtn);

  // 4. Quality Feedback Thumbs Up & Thumbs Down
  const thumbUpBtn = document.createElement("button");
  thumbUpBtn.type = "button";
  thumbUpBtn.className = "icon-btn thumb-up" + (feedback === 1 ? " active" : "");
  thumbUpBtn.title = "Helpful response";
  thumbUpBtn.innerHTML = `${ICONS.thumbUp}<span>Helpful</span>`;

  const thumbDownBtn = document.createElement("button");
  thumbDownBtn.type = "button";
  thumbDownBtn.className = "icon-btn thumb-down" + (feedback === -1 ? " active" : "");
  thumbDownBtn.title = "Unhelpful response";
  thumbDownBtn.innerHTML = `${ICONS.thumbDown}<span>Unhelpful</span>`;

  thumbUpBtn.addEventListener("click", () => {
    const row = actionsEl.closest(".message-row");
    const mId = messageId || row?.dataset?.messageId;
    handleMessageFeedback(mId, 1, thumbUpBtn, thumbDownBtn);
  });

  thumbDownBtn.addEventListener("click", () => {
    const row = actionsEl.closest(".message-row");
    const mId = messageId || row?.dataset?.messageId;
    handleMessageFeedback(mId, -1, thumbUpBtn, thumbDownBtn);
  });

  actionsEl.appendChild(thumbUpBtn);
  actionsEl.appendChild(thumbDownBtn);

  // 5. Fork / Branch Conversation Button
  const branchBtn = document.createElement("button");
  branchBtn.type = "button";
  branchBtn.className = "icon-btn branch-btn";
  branchBtn.title = "Fork conversation from this response";
  branchBtn.innerHTML = `${ICONS.branch}<span>Fork</span>`;
  branchBtn.addEventListener("click", () => {
    const row = actionsEl.closest(".message-row");
    const mId = messageId || row?.dataset?.messageId;
    forkConversationAt(mId);
  });
  actionsEl.appendChild(branchBtn);

  // 6. Continue Generating button (when output reached token limit or was truncated)
  if (isTruncated && onContinue) {
    const continueBtn = document.createElement("button");
    continueBtn.type = "button";
    continueBtn.className = "icon-btn continue-action-btn";
    continueBtn.title = "Continue generating response";
    continueBtn.innerHTML = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg><span>Continue</span>`;
    continueBtn.addEventListener("click", onContinue);
    actionsEl.appendChild(continueBtn);
  }

  // 7. Retry button
  if (showRetry) {
    const retryBtn = document.createElement("button");
    retryBtn.type = "button";
    retryBtn.className = "icon-btn";
    retryBtn.innerHTML = `${ICONS.retry}<span>Retry</span>`;
    retryBtn.addEventListener("click", onRetry);
    actionsEl.appendChild(retryBtn);
  }
}

function formatErrorMessage(detail) {
  if (!detail) return "An unexpected error occurred.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && item.msg) {
          const loc = Array.isArray(item.loc) ? item.loc.filter((x) => x !== "body" && x !== "messages").join(" > ") : "";
          return loc ? `${loc}: ${item.msg}` : item.msg;
        }
        return JSON.stringify(item);
      })
      .join("; ");
  }
  if (typeof detail === "object") {
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  return String(detail);
}

function addErrorMessage(detail, onRetry) {
  const cleanDetail = formatErrorMessage(detail);
  const row = document.createElement("div");
  row.className = "message-row actions-visible";
  row.innerHTML = `
    ${CORTEX_AVATAR_HTML}
    <div class="message-col">
      <div class="bubble error-bubble"></div>
      <div class="msg-actions"></div>
    </div>
  `;
  row.querySelector(".error-bubble").textContent = cleanDetail;
  chatEl.appendChild(row);

  const actionsEl = row.querySelector(".msg-actions");
  attachActions(actionsEl, { getText: () => cleanDetail, onRetry, showRetry: true });

  scrollToBottom();
  return row;
}

// ---------------- Rebuilding from History ----------------

function rebuildChatFromMessages() {
  const shell = document.querySelector(".app-shell");
  if (shell) shell.classList.remove("is-empty-chat");
  clearChatDom();
  messages.forEach((msg, idx) => {
    if (msg.role === "user") {
      addUserMessage(msg.content, idx, null, msg.id);
    } else {
      const shell = addAssistantMessageShell();
      if (msg.id) shell.row.dataset.messageId = msg.id;
      let displayedTools = msg.tools_used ? [...msg.tools_used] : [];
      const prevUserMsg = idx > 0 && messages[idx - 1]?.role === "user" ? messages[idx - 1].content : "";
      if (prevUserMsg.includes("[Attached Document:") && !displayedTools.includes("document_reader")) {
        displayedTools.unshift("document_reader");
      }
      if (msg.content.includes("```") && !displayedTools.includes("code_generator")) {
        displayedTools.push("code_generator");
      }
      if (msg.content.includes("```chart") && !displayedTools.includes("chart_renderer")) {
        displayedTools.push("chart_renderer");
      }
      if (displayedTools.length) {
        setToolBadges(shell.badgesEl, displayedTools);
      }
      // Check if this message was truncated (i.e. followed by a user continuation prompt)
      const nextMsg = idx + 1 < messages.length ? messages[idx + 1] : null;
      const isFollowedByContinuation =
        nextMsg && nextMsg.role === "user" && isContinuationPrompt(nextMsg.content);

      // Check if this message is a continuation of prior assistant responses
      let fullStitchedDoc = msg.content;
      const prevMsg = idx > 0 ? messages[idx - 1] : null;
      const isContinuation = prevMsg && prevMsg.role === "user" && isContinuationPrompt(prevMsg.content);

      if (isContinuation) {
        const parts = [];
        let walk = idx;
        while (walk >= 0) {
          if (messages[walk]?.role === "assistant") {
            parts.unshift(messages[walk].content);
            const priorUser = walk > 0 ? messages[walk - 1] : null;
            if (priorUser && priorUser.role === "user" && isContinuationPrompt(priorUser.content)) {
              walk -= 2;
            } else {
              break;
            }
          } else {
            break;
          }
        }
        if (parts.length > 1) {
          fullStitchedDoc = parts.join("\n\n");
        }
      }

      renderStreamedText(shell.bubbleEl, msg.content, true, {
        isTruncated: Boolean(isFollowedByContinuation),
        documentText: fullStitchedDoc,
      });
      attachActions(shell.actionsEl, {
        getText: () => fullStitchedDoc,
        showRetry: true,
        onRetry: () => retryFromMessage(idx - 1),
        messageId: msg.id,
        feedback: msg.feedback || 0,
      });
    }
  });
  updateExportButtonVisibility();
  scrollToBottom(false);
  setTimeout(() => {
    initCharts(chatEl);
  }, 100);
}

async function retryFromMessage(userIndex, customText) {
  if (busy) return;
  const target = messages[userIndex];
  if (!target) return;

  let contentToRun = target.content;
  if (customText !== undefined) {
    const imgPrefixMatch = target.content.match(/^(\[Attached Image:[^\]]+\]\s*(?:\(Visual Image Base64:[^)]+\)\s*)?)/i);
    const docPrefixMatch = target.content.match(/^(\[Attached Document:[^\]]+\](?:\s*```[\s\S]*?```)?\s*)/i);
    if (imgPrefixMatch) {
      contentToRun = `${imgPrefixMatch[1].trim()}\n\n${customText}`;
    } else if (docPrefixMatch) {
      contentToRun = `${docPrefixMatch[1].trim()}\n\n${customText}`;
    } else {
      contentToRun = customText;
    }
  }

  // Prune persistent SQLite database for consistency across page refreshes
  const pruneTarget = target;
  if (currentConversationId && pruneTarget?.id) {
    try {
      await fetch(`/api/conversations/${currentConversationId}/messages/${pruneTarget.id}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
    } catch (err) {
      console.warn("Failed to prune conversation turn:", err);
    }
  }

  messages = messages.slice(0, userIndex);
  rebuildChatFromMessages();

  sendUserMessage(contentToRun, { retryUserIndex: userIndex });
}

// ---------------- Streaming & Send Logic ----------------

function setGeneratingState(isGenerating) {
  busy = isGenerating;
  if (isGenerating) {
    sendBtn.classList.add("is-generating");
    sendBtn.title = "Stop generation";
    sendBtn.disabled = false;
  } else {
    sendBtn.classList.remove("is-generating");
    sendBtn.title = "Send message";
    sendBtn.disabled = false;
    abortController = null;
  }
}

async function streamAssistantReply(historyForRequest, { retryUserIndex } = {}) {
  const shell = addAssistantMessageShell();
  let fullText = "";
  let toolsUsed = [];
  const toolSteps = [];
  let settled = false;
  let isTruncated = false;

  const lastUserMsg = historyForRequest[historyForRequest.length - 1]?.content || "";
  const hasFileAttached = lastUserMsg.includes("[Attached Document:");
  const fileExtMatch = lastUserMsg.match(/\[Attached Document:\s*([^\]]+)\]/i);
  const attachedDocName = fileExtMatch ? fileExtMatch[1].trim() : "";
  const fileExt = attachedDocName ? attachedDocName.split(".").pop().toLowerCase() : "";

  const isCodePrompt = /\b(code|python|script|program|fastapi|function|javascript|html|css|sql|class|bug|algorithm|def |import )\b/i.test(lastUserMsg);
  const isChartPrompt = /\b(make|create|plot|draw|generate|banao|show me a)\b.*\b(chart|graph|plot)\b|\b(bar chart|pie chart|line chart|scatter plot|histogram)\b/i.test(lastUserMsg);

  // Determine initial live activity message based on mode & intent
  let initialActivity = "Thinking…";
  if (currentMode === "fast") {
    initialActivity = "Generating response…";
  } else if (currentMode === "thinking") {
    initialActivity = "Deep reasoning & researching…";
  } else if (hasFileAttached) {
    if (fileExt === "pdf") {
      initialActivity = `Extracting & reading PDF document (${attachedDocName})…`;
    } else if (fileExt === "csv") {
      initialActivity = `Parsing CSV dataset & analyzing columns (${attachedDocName})…`;
    } else {
      initialActivity = `Extracting & analyzing document (${attachedDocName})…`;
    }
    toolsUsed.push("document_reader");
    toolSteps.push({
      name: "document_reader",
      label: fileExt === "pdf" ? "PDF Document Extractor" : fileExt === "csv" ? "CSV Dataset Parser" : "Document Extractor",
      args: { file: attachedDocName },
      result: "Extracted and parsed file content successfully.",
    });
  } else if (isCodePrompt) {
    initialActivity = "Planning code architecture…";
  } else if (isChartPrompt) {
    initialActivity = "Analyzing data for chart…";
  }

  // Show live pill immediately!
  shell.liveBadge.style.display = "inline-flex";
  shell.liveText.textContent = initialActivity;

  const streamStartTime = Date.now();
  let thoughtTimer = setInterval(() => {
    if (settled) return;
    const elapsed = ((Date.now() - streamStartTime) / 1000).toFixed(1);
    if (shell.thoughtTimerBadge) {
      shell.thoughtTimerBadge.textContent = `Thinking (${elapsed}s)…`;
    }
  }, 200);

  abortController = new AbortController();
  setGeneratingState(true);

  const finishSuccess = () => {
    if (settled) return;
    settled = true;
    clearInterval(thoughtTimer);

    const totalDuration = ((Date.now() - streamStartTime) / 1000).toFixed(1);
    if (shell.thoughtTimerBadge) {
      shell.thoughtTimerBadge.textContent = `Thought for ${totalDuration}s`;
    }
    if (shell.thoughtBox && toolSteps.length > 0) {
      shell.thoughtBox.classList.remove("open");
    }

    // Detect code or chart generation
    if ((fullText.includes("```") || isCodePrompt) && !toolsUsed.includes("code_generator")) {
      toolsUsed.push("code_generator");
      toolSteps.push({
        name: "code_generator",
        label: "Code Architecture & Generator",
        args: { language: "code/script" },
        result: "Generated structured code implementation with syntax highlighting.",
      });
    }
    if (fullText.includes("```chart") && !toolsUsed.includes("chart_renderer")) {
      toolsUsed.push("chart_renderer");
      toolSteps.push({
        name: "chart_renderer",
        label: "Chart.js Visualizer",
        args: { type: "interactive_chart" },
        result: "Rendered interactive Chart.js visualization in conversation.",
      });
    }
    if (hasFileAttached && !toolsUsed.includes("document_reader")) {
      toolsUsed.unshift("document_reader");
    }

    // Hide live spinner
    shell.liveBadge.style.display = "none";

    const cleanFullText = fullText
      .replace(/<tool_call>[\s\S]*?<\/tool_call>/gi, "")
      .replace(/<tool_call>[\s\S]*$/gi, "")
      .replace(/<\/?(?:function|parameter)[^>]*>/gi, "")
      .trim();

    const hasReply = Boolean(cleanFullText);
    const displayText = hasReply
      ? cleanFullText
      : "*(The AI model did not return any tokens. The provider may be temporarily overloaded or rate-limited. Please click Retry below.)*";

    const isContinuation = isContinuationPrompt(lastUserMsg);
    let fullDocText = cleanFullText;
    if (isContinuation && cleanFullText) {
      const parts = [];
      let walk = messages.length - 1;
      while (walk >= 0) {
        if (messages[walk]?.role === "assistant") {
          parts.unshift(messages[walk].content);
          const priorUser = walk > 0 ? messages[walk - 1] : null;
          if (priorUser && priorUser.role === "user" && isContinuationPrompt(priorUser.content)) {
            walk -= 2;
          } else {
            break;
          }
        } else {
          break;
        }
      }
      if (parts.length > 0) {
        fullDocText = [...parts, cleanFullText].join("\n\n");
      }
    }

    renderStreamedText(shell.bubbleEl, displayText, true, {
      isTruncated,
      documentText: fullDocText,
    });
    if (hasReply) {
      messages.push({
        id: shell.row.dataset.messageId || undefined,
        role: "assistant",
        content: cleanFullText,
        tools_used: toolsUsed,
        feedback: 0,
      });
    }

    if (toolSteps.length > 0) {
      shell.accordionEl.style.display = "block";
      shell.accordionTitle.innerHTML = `${ICONS.tool} Used ${toolsUsed.length} tools (${toolsUsed.map((t) => TOOL_LABELS[t] || t).join(", ")})`;
      shell.accordionDetails.innerHTML = toolSteps
        .map(
          (s) => `
          <div class="tool-detail-item">
            <div class="tool-detail-name">${TOOL_ICONS[s.name] || ICONS.tool}${escapeHtml(s.label)}</div>
            ${s.args && Object.keys(s.args).length ? `<div class="tool-detail-args">Details: <code>${escapeHtml(JSON.stringify(s.args))}</code></div>` : ""}
            ${s.result ? `<div class="tool-detail-preview">${escapeHtml(s.result)}</div>` : ""}
          </div>
        `
        )
        .join("");
    }

    // If response was truncated, inject the continuation pill button directly in the bubble
    if (isTruncated) {
      const continuationPill = document.createElement("div");
      continuationPill.className = "continuation-pill-wrap";
      continuationPill.innerHTML = `
        <button type="button" class="continue-generating-btn" title="Continue generating response from where it stopped">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          <span>Response reached maximum length • Click to Continue Generating</span>
        </button>
      `;
      const btn = continuationPill.querySelector(".continue-generating-btn");
      btn.addEventListener("click", () => {
        continuationPill.remove();
        sendUserMessage("Please continue directly from where you left off. Do not repeat previous text, resume seamlessly from the cutoff point.");
      });
      shell.bubbleEl.appendChild(continuationPill);
    }

    attachActions(shell.actionsEl, {
      getText: () => fullDocText || cleanFullText || fullText,
      showRetry: true,
      onRetry: () => retryFromMessage(retryUserIndex ?? messages.length - 2),
      isTruncated,
      onContinue: () => sendUserMessage("Please continue directly from where you left off. Do not repeat previous text, resume seamlessly from the cutoff point."),
      messageId: shell.row.dataset.messageId,
      feedback: 0,
    });

    setGeneratingState(false);
    promptEl.focus();
    loadConversations();
    loadUserUsage();
    if (toolsUsed.includes("remember")) {
      loadUserMemories();
    }
  };

  const finishError = (detail) => {
    if (settled) return;
    settled = true;
    clearInterval(thoughtTimer);
    shell.row.remove();
    addErrorMessage(detail, () => retryFromMessage(retryUserIndex ?? messages.length - 1));
    setGeneratingState(false);
    promptEl.focus();
  };

  try {
    const selectedModel = modelSelect ? modelSelect.value : undefined;

    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        conversation_id: currentConversationId,
        project_id: currentProjectId || undefined,
        model: selectedModel,
        mode: currentMode,
        messages: historyForRequest,
      }),
      signal: abortController.signal,
    });

    if (response.status === 401) {
      finishError("Your session has expired. Please sign in again.");
      signOut();
      return;
    }

    if (!response.ok || !response.body) {
      let detail = "Request failed.";
      try {
        const errJson = await response.json();
        detail = errJson.detail || detail;
      } catch {
        /* ignore */
      }
      finishError(detail);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop();

      for (const raw of events) {
        const line = raw.trim();
        if (!line.startsWith("data:")) continue;
        const jsonStr = line.slice(5).trim();
        if (!jsonStr) continue;

        let payload;
        try {
          payload = JSON.parse(jsonStr);
        } catch {
          continue;
        }

        if (payload.type === "init") {
          currentConversationId = payload.conversation_id;
          localStorage.setItem("cortex_active_conv", payload.conversation_id);
          try {
            const url = new URL(window.location);
            url.searchParams.set("c", payload.conversation_id);
            window.history.replaceState({}, "", url);
          } catch {}
          if (payload.user_message_id) {
            const userRows = chatEl.querySelectorAll(".message-row.user");
            const lastUserRow = userRows[userRows.length - 1];
            if (lastUserRow) lastUserRow.dataset.messageId = payload.user_message_id;
            const lastUserMsg = [...messages].reverse().find((m) => m.role === "user");
            if (lastUserMsg) lastUserMsg.id = payload.user_message_id;
          }
          if (payload.title) {
            chatTitleHeader.textContent = payload.title;
            const conv = conversations.find((c) => c.id === payload.conversation_id);
            if (conv) {
              conv.title = payload.title;
              renderConversationsList();
            }
          }
        } else if (payload.type === "tool_start") {
          shell.liveBadge.style.display = "inline-flex";
          let activeMsg = `Running ${payload.label || payload.name}…`;
          if (payload.name === "web_search") activeMsg = "Searching the web for latest info…";
          else if (payload.name === "fetch_webpage") activeMsg = "Reading & scraping webpage text…";
          else if (payload.name === "calculator") activeMsg = "Computing mathematical operations…";
          else if (payload.name === "wikipedia_lookup") activeMsg = "Looking up Wikipedia knowledgebase…";
          else if (payload.name === "weather_lookup") activeMsg = "Fetching live weather telemetry…";
          else if (payload.name === "current_datetime") activeMsg = "Fetching current date & time…";
          shell.liveText.textContent = activeMsg;

          if (shell.thoughtBox) {
            shell.thoughtBox.style.display = "block";
            const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
            const stepHtml = `
              <div style="margin-bottom:6px;">
                <span style="opacity:0.6;">[${timeStr}]</span> ▶ <strong>${escapeHtml(payload.label || payload.name)}</strong>
                ${payload.args && Object.keys(payload.args).length ? `<div style="font-size:11px; opacity:0.75; padding-left:12px;">Parameters: <code>${escapeHtml(JSON.stringify(payload.args))}</code></div>` : ""}
              </div>
            `;
            shell.thoughtContent.innerHTML += stepHtml;
          }

          toolSteps.push({
            name: payload.name,
            label: payload.label || payload.name,
            args: payload.args,
            result: null,
          });
        } else if (payload.type === "tool_end") {
          const step = toolSteps.find((s) => s.name === payload.name && s.result === null);
          if (step) step.result = payload.result;
          shell.liveText.textContent = `Completed ${payload.label || payload.name}`;
          if (shell.thoughtContent) {
            shell.thoughtContent.innerHTML += `<div style="margin-bottom:8px; color:var(--accent); font-size:11px; padding-left:12px;">✔ Finished execution of ${escapeHtml(payload.label || payload.name)}</div>`;
          }
        } else if (payload.type === "tools") {
          (payload.tools_used || []).forEach((t) => {
            if (!toolsUsed.includes(t)) toolsUsed.push(t);
          });
          shell.liveBadge.style.display = "inline-flex";
          if (isCodePrompt) {
            shell.liveText.textContent = "Writing code & implementation…";
          } else if (hasFileAttached) {
            shell.liveText.textContent = "Synthesizing document insights…";
          } else if (isChartPrompt) {
            shell.liveText.textContent = "Rendering interactive visualization…";
          } else {
            shell.liveText.textContent = "Generating response…";
          }
        } else if (payload.type === "token") {
          fullText += payload.text;
          renderStreamedText(shell.bubbleEl, fullText, false);
          if (isNearBottom()) scrollToBottom();
        } else if (payload.type === "replace_text") {
          fullText = payload.text;
          renderStreamedText(shell.bubbleEl, fullText, false);
          if (isNearBottom()) scrollToBottom();

          // Live dynamic update during generation
          if (fullText.includes("```python") || fullText.includes("```javascript") || fullText.includes("```html") || fullText.includes("```sh") || fullText.includes("```json") || fullText.includes("```sql")) {
            shell.liveBadge.style.display = "inline-flex";
            shell.liveText.textContent = "Writing code implementation…";
            if (!toolsUsed.includes("code_generator")) toolsUsed.push("code_generator");
          } else if (fullText.includes("```chart")) {
            shell.liveBadge.style.display = "inline-flex";
            shell.liveText.textContent = "Generating interactive Chart.js…";
            if (!toolsUsed.includes("chart_renderer")) toolsUsed.push("chart_renderer");
          } else if (fullText.includes("```markdown")) {
            shell.liveBadge.style.display = "inline-flex";
            shell.liveText.textContent = "Composing document artifact…";
          }
        } else if (payload.type === "truncated") {
          isTruncated = true;
        } else if (payload.type === "done") {
          if (payload.full_text) {
            fullText = payload.full_text;
          }
          if (payload.user_message_id) {
            const userRows = chatEl.querySelectorAll(".message-row.user");
            const lastUserRow = userRows[userRows.length - 1];
            if (lastUserRow) lastUserRow.dataset.messageId = payload.user_message_id;
            const lastUserMsg = [...messages].reverse().find((m) => m.role === "user");
            if (lastUserMsg) lastUserMsg.id = payload.user_message_id;
          }
          if (payload.assistant_message_id) {
            shell.row.dataset.messageId = payload.assistant_message_id;
            const lastAsstMsg = [...messages].reverse().find((m) => m.role === "assistant");
            if (lastAsstMsg) lastAsstMsg.id = payload.assistant_message_id;
          }
          if (payload.usage) {
            const used = payload.usage.tokens_used ?? payload.usage.daily_tokens ?? 0;
            const limit = payload.usage.tokens_limit ?? payload.usage.limit ?? 100000;
            updateUsageDisplay(used, limit);
          }
          loadArtifactsCount();
          finishSuccess();
        } else if (payload.type === "error") {
          finishError(payload.detail || "Something went wrong.");
        }
      }
    }

    finishSuccess();
  } catch (error) {
    if (error.name === "AbortError") {
      // User aborted stream
      finishSuccess();
    } else {
      finishError(error.message || "Connection lost.");
    }
  }
}

async function sendUserMessage(text, options = {}) {
  let messageContent = text;
  const currentAttached = attachedFile ? { ...attachedFile } : null;

  // Prepend file content if a file is attached
  if (attachedFile) {
    if (attachedFile.is_image && attachedFile.image_data_url) {
      messageContent = `[Attached Image: ${attachedFile.filename} (${formatBytes(attachedFile.size)})]\n(Visual Image Base64: ${attachedFile.image_data_url})\n\n${text}`;
    } else {
      messageContent = `[Attached Document: ${attachedFile.filename}]\n\`\`\`\n${attachedFile.text}\n\`\`\`\n\n${text}`;
    }
    clearAttachment();
  }

  const shell = document.querySelector(".app-shell");
  if (shell) shell.classList.remove("is-empty-chat");

  if (messages.length === 0) clearChatDom();

  messages.push({ role: "user", content: messageContent });
  addUserMessage(messageContent, messages.length - 1, currentAttached);
  updateExportButtonVisibility();

  promptEl.value = "";
  autoResize();

  await streamAssistantReply([...messages], options);
}

function handleFormSubmit() {
  if (busy) {
    if (abortController) abortController.abort();
    return;
  }

  const text = promptEl.value.trim();
  if (!text && !attachedFile) return;

  const promptText = text || "Please summarize and explain the key points in this attached file.";
  sendUserMessage(promptText);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  handleFormSubmit();
});

sendBtn.addEventListener("click", (event) => {
  if (busy) {
    event.preventDefault();
    if (abortController) abortController.abort();
  }
});


promptEl.addEventListener("input", autoResize);
promptEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    handleFormSubmit();
  }
});

// ---------------- Response Mode Selector (Auto / Fast / Thinking) ----------------

const MODE_DEFS = {
  auto: { label: "Auto", icon: "🎯" },
  fast: { label: "Fast", icon: "⚡" },
  thinking: { label: "Thinking", icon: "🧠" },
};

function initModeSelector() {
  const wrap = document.getElementById("modePickerWrap");
  const btn = document.getElementById("modeDropdownBtn");
  const menu = document.getElementById("modeMenu");
  const labelEl = document.getElementById("modeLabel");
  const iconEl = document.getElementById("modeIcon");

  if (!btn || !menu) return;

  function updateUi(mode) {
    currentMode = mode;
    localStorage.setItem("cortex_mode", mode);
    const def = MODE_DEFS[mode] || MODE_DEFS.auto;
    if (labelEl) labelEl.textContent = def.label;
    if (iconEl) iconEl.textContent = def.icon;

    menu.querySelectorAll(".mode-option").forEach((opt) => {
      const isMatch = opt.getAttribute("data-mode") === mode;
      opt.classList.toggle("active", isMatch);
      const checkEl = opt.querySelector(".mode-option-check");
      if (checkEl) checkEl.style.display = isMatch ? "inline" : "none";
    });
  }

  window.setResponseMode = updateUi;

  // Initialize from saved setting or default "auto"
  updateUi(currentMode);

  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = menu.style.display === "flex";
    menu.style.display = isOpen ? "none" : "flex";
    if (wrap) wrap.classList.toggle("is-open", !isOpen);
    btn.setAttribute("aria-expanded", !isOpen ? "true" : "false");
  });

  menu.querySelectorAll(".mode-option").forEach((opt) => {
    opt.addEventListener("click", (e) => {
      e.stopPropagation();
      const mode = opt.getAttribute("data-mode");
      if (mode) updateUi(mode);
      menu.style.display = "none";
      if (wrap) wrap.classList.remove("is-open");
      btn.setAttribute("aria-expanded", "false");
    });
  });

  document.addEventListener("click", (e) => {
    if (!menu.contains(e.target) && e.target !== btn) {
      menu.style.display = "none";
      if (wrap) wrap.classList.remove("is-open");
      btn.setAttribute("aria-expanded", "false");
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && menu.style.display === "flex") {
      menu.style.display = "none";
      if (wrap) wrap.classList.remove("is-open");
      btn.setAttribute("aria-expanded", "false");
    }
  });
}

initModeSelector();

// ---------------- Model Selector & Health ----------------

if (modelSelect) {
  const savedModel = localStorage.getItem("cortex_model");
  if (savedModel) modelSelect.value = savedModel;
  modelSelect.addEventListener("change", () => {
    localStorage.setItem("cortex_model", modelSelect.value);
  });
}

async function loadHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (data.available_models && data.available_models.length && modelSelect) {
      const savedModel = localStorage.getItem("cortex_model");
      const currentVal = savedModel || modelSelect.value;
      modelSelect.innerHTML = data.available_models
        .map((m) => `<option value="${m.id}">${escapeHtml(m.name)}</option>`)
        .join("");
      if (currentVal && data.available_models.some((m) => m.id === currentVal)) {
        modelSelect.value = currentVal;
      } else {
        modelSelect.value = data.available_models[0].id;
        localStorage.setItem("cortex_model", modelSelect.value);
      }
    }
  } catch {
    /* ignore health failure */
  }
}

// ---------------- Export Conversation to Markdown (.md) ----------------

const exportChatBtn = document.getElementById("exportChatBtn");

function exportCurrentChatAsMarkdown() {
  if (!messages || !messages.length) {
    alert("No messages to export yet. Start a conversation first!");
    return;
  }

  const title = chatTitleHeader.textContent.trim() || "Cortex_Chat";
  const safeTitle = title.replace(/[^a-zA-Z0-9_\-\s]/g, "").trim().replace(/\s+/g, "_") || "Cortex_Chat";
  const modelName = modelSelect ? modelSelect.options[modelSelect.selectedIndex]?.text || modelSelect.value : "Cortex AI";
  const now = new Date().toLocaleString();

  let md = `# ${title}\n\n`;
  md += `> **Exported from Cortex Agent**  \n`;
  md += `> **Date**: ${now}  \n`;
  md += `> **Model**: ${modelName}  \n\n`;
  md += `---\n\n`;

  let promptCount = 0;
  messages.forEach((msg) => {
    if (msg.role === "user") {
      promptCount += 1;
      md += `### 👤 Prompt ${promptCount} (User)\n\n${msg.content.trim()}\n\n`;
    } else {
      md += `### 🤖 Cortex Agent (${modelName})\n\n`;
      if (msg.tools_used && msg.tools_used.length) {
        md += `> **Tools Used**: \`${msg.tools_used.join("`, `")}\`\n\n`;
      }
      md += `${msg.content.trim()}\n\n`;
    }
    md += `---\n\n`;
  });

  downloadTextFile(`${safeTitle}.md`, md, "text/markdown;charset=utf-8");
}

if (exportChatBtn) {
  exportChatBtn.addEventListener("click", () => {
    exportCurrentChatAsMarkdown();
  });
}

// ---------------- Theme Management (Dark / Light) & Settings ----------------

function updateSettingsThemeButtons(currentTheme) {
  const t = currentTheme || (document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark");
  if (settingsThemeDarkBtn) {
    if (t === "dark") settingsThemeDarkBtn.classList.add("active");
    else settingsThemeDarkBtn.classList.remove("active");
  }
  if (settingsThemeLightBtn) {
    if (t === "light") settingsThemeLightBtn.classList.add("active");
    else settingsThemeLightBtn.classList.remove("active");
  }
}

function setTheme(theme) {
  const sunIcon = themeToggleBtn?.querySelector(".theme-icon-sun");
  const moonIcon = themeToggleBtn?.querySelector(".theme-icon-moon");

  if (theme === "light") {
    document.documentElement.setAttribute("data-theme", "light");
    if (sunIcon) sunIcon.style.display = "none";
    if (moonIcon) moonIcon.style.display = "block";
    if (themeToggleBtn) themeToggleBtn.setAttribute("title", "Switch to Dark Theme");
  } else {
    document.documentElement.removeAttribute("data-theme");
    if (sunIcon) sunIcon.style.display = "block";
    if (moonIcon) moonIcon.style.display = "none";
    if (themeToggleBtn) themeToggleBtn.setAttribute("title", "Switch to Light Theme");
  }
  localStorage.setItem("cortex_theme", theme);
  updateSettingsThemeButtons(theme);
}

const savedTheme = localStorage.getItem("cortex_theme") || "dark";
setTheme(savedTheme);

if (themeToggleBtn) {
  themeToggleBtn.addEventListener("click", () => {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    setTheme(isLight ? "dark" : "light");
  });
}

function openSettingsModal() {
  closeUserProfileMenu();
  if (!settingsModal) return;

  const rawName = (currentUser && currentUser.username) || localStorage.getItem("cortex_username") || "User";
  const name = formatDisplayName(rawName);
  const email = currentUser?.email || `${rawName.toLowerCase()}@cortex.ai`;
  const initial = (name[0] || "U").toUpperCase();

  if (settingsUsername) settingsUsername.textContent = name;
  if (settingsEmail) settingsEmail.textContent = email;
  if (settingsAvatar) settingsAvatar.textContent = initial;

  updateSettingsThemeButtons();
  settingsModal.style.display = "flex";
}

function closeSettingsModal() {
  if (!settingsModal) return;
  settingsModal.style.display = "none";
}

settingsThemeDarkBtn?.addEventListener("click", () => setTheme("dark"));
settingsThemeLightBtn?.addEventListener("click", () => setTheme("light"));
settingsModalCloseBtn?.addEventListener("click", closeSettingsModal);
settingsModalDoneBtn?.addEventListener("click", closeSettingsModal);
settingsModal?.addEventListener("click", (e) => {
  if (e.target === settingsModal) closeSettingsModal();
});

// ---------------- Persistent Agentic Memory & Personalization Controller ----------------

const memoryBtn = document.getElementById("memoryBtn");
const memoryCountBadge = document.getElementById("memoryCountBadge");
const menuMemoriesBtn = document.getElementById("menuMemoriesBtn");
const memoryModal = document.getElementById("memoryModal");
const memoryModalCloseBtn = document.getElementById("memoryModalCloseBtn");
const memoryModalDoneBtn = document.getElementById("memoryModalDoneBtn");
const memTabMemories = document.getElementById("memTabMemories");
const memTabInstructions = document.getElementById("memTabInstructions");
const memoriesPanel = document.getElementById("memoriesPanel");
const instructionsPanel = document.getElementById("instructionsPanel");
const memoriesTabCount = document.getElementById("memoriesTabCount");
const memoriesTotalLabel = document.getElementById("memoriesTotalLabel");
const memoriesListContainer = document.getElementById("memoriesListContainer");
const newMemoryInput = document.getElementById("newMemoryInput");
const newMemoryCategory = document.getElementById("newMemoryCategory");
const addMemoryBtn = document.getElementById("addMemoryBtn");
const clearAllMemoriesBtn = document.getElementById("clearAllMemoriesBtn");
const customInstructionsTextarea = document.getElementById("customInstructionsTextarea");
const saveInstructionsBtn = document.getElementById("saveInstructionsBtn");
const instructionsSaveStatus = document.getElementById("instructionsSaveStatus");

let userMemories = [];

async function loadUserMemories() {
  if (!authToken) return;
  try {
    const res = await fetch("/api/memories", { headers: authHeaders() });
    if (res.ok) {
      userMemories = await res.json();
      renderMemoriesList();
      updateMemoryBadges();
    }
  } catch (err) {
    console.error("Failed to load memories:", err);
  }
}

async function loadUserInstructions() {
  if (!authToken) return;
  try {
    const res = await fetch("/api/user/instructions", { headers: authHeaders() });
    if (res.ok) {
      const data = await res.json();
      if (customInstructionsTextarea) {
        customInstructionsTextarea.value = data.instructions || "";
      }
    }
  } catch (err) {
    console.error("Failed to load instructions:", err);
  }
}

function updateMemoryBadges() {
  const count = userMemories.length;
  if (memoriesTabCount) memoriesTabCount.textContent = count;
  if (memoriesTotalLabel) memoriesTotalLabel.textContent = count;
  if (memoryCountBadge) {
    if (count > 0) {
      memoryCountBadge.textContent = count;
      memoryCountBadge.style.display = "inline-flex";
    } else {
      memoryCountBadge.style.display = "none";
    }
  }
  if (clearAllMemoriesBtn) {
    clearAllMemoriesBtn.style.display = count > 0 ? "inline-block" : "none";
  }
}

function renderMemoriesList() {
  if (!memoriesListContainer) return;
  if (!userMemories || userMemories.length === 0) {
    memoriesListContainer.innerHTML = `
      <div class="memory-empty-state">
        <svg viewBox="0 0 24 24" width="36" height="36" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a5 5 0 0 1 5 5v1a5 5 0 0 1-10 0V7a5 5 0 0 1 5-5z"></path>
          <path d="M19 11v1a7 7 0 0 1-14 0v-1"></path>
          <line x1="12" y1="19" x2="12" y2="23"></line>
          <line x1="8" y1="23" x2="16" y2="23"></line>
        </svg>
        <p>Cortex hasn't saved any memories yet. As you chat, Cortex will remember your preferences, or you can add them manually above.</p>
      </div>
    `;
    return;
  }

  memoriesListContainer.innerHTML = userMemories.map((m) => {
    const cat = escapeHtml(m.category || "preference");
    const content = escapeHtml(m.content || "");
    const dateStr = m.created_at ? new Date(m.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "";
    return `
      <div class="memory-item-card" data-id="${m.id}">
        <div class="memory-card-main">
          <div class="memory-card-meta">
            <span class="memory-badge cat-${cat}">${cat}</span>
            <span class="memory-card-time">${dateStr}</span>
          </div>
          <div class="memory-card-text">${content}</div>
        </div>
        <button class="btn-delete-memory" data-id="${m.id}" title="Delete memory" aria-label="Delete memory">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
    `;
  }).join("");

  memoriesListContainer.querySelectorAll(".btn-delete-memory").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const memId = btn.getAttribute("data-id");
      if (!memId) return;
      await handleDeleteMemory(memId);
    });
  });
}

async function handleAddMemory() {
  const content = newMemoryInput?.value?.trim();
  if (!content) return;
  const category = newMemoryCategory?.value || "preference";
  try {
    if (addMemoryBtn) addMemoryBtn.disabled = true;
    const res = await fetch("/api/memories", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ content, category }),
    });
    if (res.ok) {
      if (newMemoryInput) newMemoryInput.value = "";
      await loadUserMemories();
    }
  } catch (err) {
    console.error("Failed to add memory:", err);
  } finally {
    if (addMemoryBtn) addMemoryBtn.disabled = false;
  }
}

async function handleDeleteMemory(memId) {
  try {
    const res = await fetch(`/api/memories/${memId}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (res.ok) {
      userMemories = userMemories.filter((m) => m.id !== memId);
      renderMemoriesList();
      updateMemoryBadges();
    }
  } catch (err) {
    console.error("Failed to delete memory:", err);
  }
}

async function handleClearAllMemories() {
  if (!confirm("Are you sure you want to delete all saved memories? This cannot be undone.")) return;
  try {
    const res = await fetch("/api/memories", {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (res.ok) {
      userMemories = [];
      renderMemoriesList();
      updateMemoryBadges();
    }
  } catch (err) {
    console.error("Failed to clear memories:", err);
  }
}

async function handleSaveInstructions() {
  const instructions = customInstructionsTextarea?.value || "";
  try {
    if (saveInstructionsBtn) saveInstructionsBtn.disabled = true;
    const res = await fetch("/api/user/instructions", {
      method: "PUT",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ instructions }),
    });
    if (res.ok) {
      if (instructionsSaveStatus) {
        instructionsSaveStatus.style.display = "inline";
        instructionsSaveStatus.textContent = "Saved successfully!";
        setTimeout(() => {
          instructionsSaveStatus.style.display = "none";
        }, 2500);
      }
    }
  } catch (err) {
    console.error("Failed to save instructions:", err);
  } finally {
    if (saveInstructionsBtn) saveInstructionsBtn.disabled = false;
  }
}

function openMemoryModal(activeTab = "memories") {
  closeUserProfileMenu();
  closeSettingsModal();
  if (!memoryModal) return;
  memoryModal.style.display = "flex";
  switchMemoryTab(activeTab);
  loadUserMemories();
  loadUserInstructions();
}

function closeMemoryModal() {
  if (!memoryModal) return;
  memoryModal.style.display = "none";
}

function switchMemoryTab(tab) {
  if (tab === "memories") {
    memTabMemories?.classList.add("active");
    memTabInstructions?.classList.remove("active");
    if (memoriesPanel) memoriesPanel.style.display = "flex";
    if (instructionsPanel) instructionsPanel.style.display = "none";
  } else {
    memTabInstructions?.classList.add("active");
    memTabMemories?.classList.remove("active");
    if (memoriesPanel) memoriesPanel.style.display = "none";
    if (instructionsPanel) instructionsPanel.style.display = "flex";
    setTimeout(() => customInstructionsTextarea?.focus(), 60);
  }
}

memoryBtn?.addEventListener("click", () => openMemoryModal("memories"));
menuMemoriesBtn?.addEventListener("click", () => {
  closeUserProfileMenu();
  openMemoryModal("memories");
});
memoryModalCloseBtn?.addEventListener("click", closeMemoryModal);
memoryModalDoneBtn?.addEventListener("click", closeMemoryModal);
memoryModal?.addEventListener("click", (e) => {
  if (e.target === memoryModal) closeMemoryModal();
});
memTabMemories?.addEventListener("click", () => switchMemoryTab("memories"));
memTabInstructions?.addEventListener("click", () => switchMemoryTab("instructions"));
addMemoryBtn?.addEventListener("click", handleAddMemory);
newMemoryInput?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    handleAddMemory();
  }
});
clearAllMemoriesBtn?.addEventListener("click", handleClearAllMemories);
saveInstructionsBtn?.addEventListener("click", handleSaveInstructions);

// ---------------- Full-Screen Image Lightbox Controller ----------------

let lightboxCurrentZoom = 1.0;

function openImageLightbox({ src, filename, size }) {
  if (!imageLightboxModal) return;

  if (lightboxFilename) lightboxFilename.textContent = filename || "Image Preview";
  if (lightboxSize) lightboxSize.textContent = size ? `(${size})` : "";
  if (lightboxImage) {
    lightboxImage.src = src;
    lightboxImage.alt = filename || "Image Preview";
  }
  if (lightboxDownloadBtn) {
    lightboxDownloadBtn.href = src;
    lightboxDownloadBtn.download = filename || "cortex-image.png";
  }

  setLightboxZoom(1.0);
  imageLightboxModal.style.display = "flex";
  requestAnimationFrame(() => {
    imageLightboxModal.classList.add("is-open");
  });
  imageLightboxModal.setAttribute("aria-hidden", "false");
}

function closeImageLightbox() {
  if (!imageLightboxModal) return;
  imageLightboxModal.classList.remove("is-open");
  imageLightboxModal.setAttribute("aria-hidden", "true");
  setTimeout(() => {
    if (!imageLightboxModal.classList.contains("is-open")) {
      imageLightboxModal.style.display = "none";
      if (lightboxImage) lightboxImage.src = "";
    }
  }, 220);
}

function setLightboxZoom(level) {
  lightboxCurrentZoom = Math.min(Math.max(0.4, Math.round(level * 100) / 100), 3.5);
  if (lightboxZoomLevel) {
    lightboxZoomLevel.textContent = `${Math.round(lightboxCurrentZoom * 100)}%`;
  }
  const stage = imageLightboxModal?.querySelector(".image-lightbox-stage");
  if (stage) {
    stage.style.transform = `scale(${lightboxCurrentZoom})`;
  }
  if (lightboxImage) {
    lightboxImage.classList.toggle("zoomed", lightboxCurrentZoom > 1.05);
  }
}

lightboxZoomInBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  setLightboxZoom(lightboxCurrentZoom + 0.25);
});

lightboxZoomOutBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  setLightboxZoom(lightboxCurrentZoom - 0.25);
});

lightboxResetZoomBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  setLightboxZoom(1.0);
});

lightboxCloseBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  closeImageLightbox();
});

lightboxImage?.addEventListener("click", (e) => {
  e.stopPropagation();
  if (lightboxCurrentZoom > 1.05) {
    setLightboxZoom(1.0);
  } else {
    setLightboxZoom(1.75);
  }
});

lightboxBody?.addEventListener("wheel", (e) => {
  e.preventDefault();
  const step = e.deltaY < 0 ? 0.2 : -0.2;
  setLightboxZoom(lightboxCurrentZoom + step);
}, { passive: false });

imageLightboxModal?.addEventListener("click", (e) => {
  if (e.target === imageLightboxModal || e.target === lightboxBody) {
    closeImageLightbox();
  }
});


// ---------------- Landing Page, Auth & View Management ----------------

function showLandingPage() {
  if (landingView) landingView.style.display = "block";
  if (appView) appView.style.display = "none";
  closeAuthModal();
}

function showChatApp() {
  if (landingView) landingView.style.display = "none";
  if (appView) appView.style.display = "flex";
  closeAuthModal();
  closeUserProfileMenu();
  closeSettingsModal();
  if (currentUser) {
    if (userNameDisplay) userNameDisplay.textContent = currentUser.username;
    if (userAvatar) userAvatar.textContent = (currentUser.username[0] || "U").toUpperCase();
  }
  updateDynamicGreeting();
  const savedSidebarCollapsed = localStorage.getItem("cortex_sidebar_collapsed") === "true";
  if (savedSidebarCollapsed && window.innerWidth > 768) {
    setSidebarCollapsed(true);
  }
  updateExportButtonVisibility();
  loadUserMemories();
  loadUserUsage();
  loadArtifactsCount();
  if (!localStorage.getItem("cortex_tour_completed")) {
    setTimeout(startOnboardingTour, 700);
  }
  promptEl.focus();
}

function openAuthModal(mode = "login") {
  authMode = mode;
  if (!authModal) return;
  authModal.style.display = "flex";
  if (authErrorAlert) {
    authErrorAlert.style.display = "none";
    authErrorAlert.textContent = "";
  }
  if (mode === "login") {
    tabSignIn?.classList.add("active");
    tabRegister?.classList.remove("active");
    if (authModalTitle) authModalTitle.textContent = "Welcome back";
    if (authModalSubtitle) authModalSubtitle.textContent = "Sign in to resume your private workspace & past chats";
    if (emailGroup) emailGroup.style.display = "none";
    if (passwordStrengthWrap) passwordStrengthWrap.style.display = "none";
    if (authSubmitBtn) authSubmitBtn.textContent = "Sign In";
  } else {
    tabRegister?.classList.add("active");
    tabSignIn?.classList.remove("active");
    if (authModalTitle) authModalTitle.textContent = "Create Free Account";
    if (authModalSubtitle) authModalSubtitle.textContent = "Start with 100,000 free tokens & your private workspace";
    if (emailGroup) emailGroup.style.display = "flex";
    if (passwordStrengthWrap) {
      passwordStrengthWrap.style.display = "flex";
      updatePasswordStrength(authPassword?.value || "");
    }
    if (authSubmitBtn) authSubmitBtn.textContent = "Create Account";
  }
  setTimeout(() => authUsername?.focus(), 60);
}

function closeAuthModal() {
  if (!authModal) return;
  authModal.style.display = "none";
  authForm?.reset();
  if (authErrorAlert) authErrorAlert.style.display = "none";
  if (passwordStrengthWrap) passwordStrengthWrap.style.display = "none";
  if (authPassword) authPassword.type = "password";
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const username = authUsername ? authUsername.value.trim() : "";
  const password = authPassword ? authPassword.value : "";
  const email = authEmail?.value?.trim() || "";

  if (!username || !password) return;

  try {
    if (authSubmitBtn) {
      authSubmitBtn.disabled = true;
      authSubmitBtn.textContent = "Connecting…";
    }
    if (authErrorAlert) authErrorAlert.style.display = "none";

    const endpoint = authMode === "register" ? "/api/auth/register" : "/api/auth/login";
    const bodyPayload = authMode === "register"
      ? { username, password, email }
      : { username, password };

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bodyPayload),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Authentication failed.");
    }

    authToken = data.token;
    currentUser = data.user;
    localStorage.setItem("cortex_auth_token", authToken);
    localStorage.setItem("cortex_active_conv", "new");
    if (currentUser && currentUser.username) {
      localStorage.setItem("cortex_username", currentUser.username);
    }
    updateDynamicGreeting();

    showChatApp();
    startNewChat();
    await loadProjects();
    await loadConversations(false);
  } catch (err) {
    if (authErrorAlert) {
      authErrorAlert.textContent = err.message;
      authErrorAlert.style.display = "block";
    }
  } finally {
    if (authSubmitBtn) {
      authSubmitBtn.disabled = false;
      authSubmitBtn.textContent = authMode === "register" ? "Get Started" : "Sign In";
    }
  }
}

function signOut() {
  localStorage.removeItem("cortex_auth_token");
  localStorage.setItem("cortex_active_conv", "new");
  localStorage.removeItem("cortex_username");
  authToken = null;
  currentUser = null;
  conversations = [];
  messages = [];
  userMemories = [];
  updateMemoryBadges();
  userProjects = [];
  currentProjectId = "";
  if (projectsListContainer) {
    projectsListContainer.innerHTML = '<button class="project-pill active" data-project-id="" type="button">All Chats</button>';
  }
  currentConversationId = null;
  startNewChat();
  if (chatEl) chatEl.innerHTML = "";
  if (conversationsListEl) conversationsListEl.innerHTML = "";
  showLandingPage();
}

async function checkAuth() {
  if (!authToken) {
    showLandingPage();
    loadHealth();
    return;
  }

  try {
    const res = await fetch("/api/auth/me", { headers: authHeaders() });
    if (res.ok) {
      currentUser = await res.json();
      if (currentUser && currentUser.username) {
        localStorage.setItem("cortex_username", currentUser.username);
      }
      showChatApp();
      updateDynamicGreeting();
      loadHealth();

      // Strict Clean Re-entry: Only open a previous chat if explicitly given in URL (?c=...)
      let targetConvId = null;
      try {
        const urlParams = new URLSearchParams(window.location.search);
        const qC = urlParams.get("c");
        if (qC && qC !== "new") targetConvId = qC;
      } catch {}

      await loadProjects();
      await loadConversations(false);

      if (targetConvId) {
        await switchConversation(targetConvId);
      } else {
        startNewChat();
      }
    } else {
      localStorage.removeItem("cortex_auth_token");
      localStorage.removeItem("cortex_username");
      localStorage.setItem("cortex_active_conv", "new");
      authToken = null;
      showLandingPage();
      loadHealth();
    }
  } catch {
    showLandingPage();
    loadHealth();
  }
}

// Landing Page & Auth Event Listeners
function handleLaunchOrRegister() {
  if (authToken) {
    showChatApp();
    if (!currentConversationId || currentConversationId === "new") {
      startNewChat();
    }
  } else {
    openAuthModal("register");
  }
}

navSignInBtn?.addEventListener("click", () => openAuthModal("login"));
navRegisterBtn?.addEventListener("click", handleLaunchOrRegister);
heroSignInBtn?.addEventListener("click", () => openAuthModal("login"));
heroGetStartedBtn?.addEventListener("click", handleLaunchOrRegister);
showcaseGetStartedBtn?.addEventListener("click", handleLaunchOrRegister);
bottomGetStartedBtn?.addEventListener("click", handleLaunchOrRegister);
savingsGetStartedBtn?.addEventListener("click", handleLaunchOrRegister);

// Interactive Savings Calculator (Screenshot 3)
const teamSeatSlider = document.getElementById("teamSeatSlider");
const seatCountDisplay = document.getElementById("seatCountDisplay");
const savingsAmountDisplay = document.getElementById("savingsAmountDisplay");
const savingsBreakdownText = document.getElementById("savingsBreakdownText");

function updateSavingsCalculator() {
  const seats = parseInt(teamSeatSlider?.value || "5", 10);
  if (seatCountDisplay) {
    seatCountDisplay.textContent = `${seats} ${seats === 1 ? "seat" : "seats"}`;
  }

  let totalPerSeat = 0;
  document.querySelectorAll("#savingsPillsGrid .tool-pill.active").forEach((pill) => {
    const price = parseInt(pill.getAttribute("data-price") || "0", 10);
    totalPerSeat += price;
  });

  const totalAnnualSavings = totalPerSeat * seats;
  if (savingsAmountDisplay) {
    savingsAmountDisplay.textContent = `$${totalAnnualSavings.toLocaleString()}`;
  }
  if (savingsBreakdownText) {
    savingsBreakdownText.textContent = `Replaces $${totalPerSeat.toLocaleString()} per seat × ${seats} ${seats === 1 ? "seat" : "seats"}`;
  }
}

document.querySelectorAll("#savingsPillsGrid .tool-pill").forEach((pill) => {
  pill.addEventListener("click", () => {
    pill.classList.toggle("active");
    updateSavingsCalculator();
  });
});

teamSeatSlider?.addEventListener("input", updateSavingsCalculator);

// Hero Pill Tabs
document.querySelectorAll(".hero-pill-tabs .pill-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".hero-pill-tabs .pill-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
  });
});

// Research Filter Tabs
document.querySelectorAll(".research-tabs .res-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".research-tabs .res-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const cat = tab.getAttribute("data-category") || "all";
    document.querySelectorAll(".research-card").forEach((card) => {
      const cardCat = card.getAttribute("data-category");
      if (cat === "all" || cardCat === cat) {
        card.style.display = "flex";
      } else {
        card.style.display = "none";
      }
    });
  });
});

// Numbered FAQ Accordion
document.querySelectorAll(".faq-item .faq-question-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const parentItem = btn.closest(".faq-item");
    if (!parentItem) return;
    const isCurrentlyActive = parentItem.classList.contains("active");
    document.querySelectorAll(".faq-item").forEach((item) => item.classList.remove("active"));
    if (!isCurrentlyActive) {
      parentItem.classList.add("active");
    }
  });
});

authModalCloseBtn?.addEventListener("click", closeAuthModal);
authModal?.addEventListener("click", (e) => {
  if (e.target === authModal) closeAuthModal();
});
tabSignIn?.addEventListener("click", () => openAuthModal("login"));
tabRegister?.addEventListener("click", () => openAuthModal("register"));
authForm?.addEventListener("submit", handleAuthSubmit);

// Password Visibility Toggle
authTogglePasswordBtn?.addEventListener("click", () => {
  if (!authPassword) return;
  const isPassword = authPassword.type === "password";
  authPassword.type = isPassword ? "text" : "password";
  authTogglePasswordBtn.innerHTML = isPassword
    ? `<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`
    : `<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
});

// Dynamic Password Strength Meter
function updatePasswordStrength(password) {
  if (!passwordStrengthWrap || !passwordStrengthBar || !passwordStrengthText) return;
  if (!password) {
    passwordStrengthBar.style.width = "0%";
    passwordStrengthText.textContent = "Enter at least 4 characters";
    passwordStrengthText.style.color = "#64748b";
    return;
  }

  let score = 0;
  if (password.length >= 4) score += 1;
  if (password.length >= 8) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[A-Z]/.test(password) || /[^A-Za-z0-9]/.test(password)) score += 1;

  if (score <= 1) {
    passwordStrengthBar.style.width = "25%";
    passwordStrengthBar.style.backgroundColor = "#e0685c";
    passwordStrengthText.textContent = "Weak (minimum 4 characters)";
    passwordStrengthText.style.color = "#ff8579";
  } else if (score === 2) {
    passwordStrengthBar.style.width = "50%";
    passwordStrengthBar.style.backgroundColor = "#f59e0b";
    passwordStrengthText.textContent = "Good password";
    passwordStrengthText.style.color = "#fbbf24";
  } else if (score === 3) {
    passwordStrengthBar.style.width = "75%";
    passwordStrengthBar.style.backgroundColor = "#22c55e";
    passwordStrengthText.textContent = "Strong password";
    passwordStrengthText.style.color = "#4ade80";
  } else {
    passwordStrengthBar.style.width = "100%";
    passwordStrengthBar.style.backgroundColor = "#38bdf8";
    passwordStrengthText.textContent = "Elite cryptographic strength";
    passwordStrengthText.style.color = "#38bdf8";
  }
}

authPassword?.addEventListener("input", (e) => {
  if (authMode === "register") {
    updatePasswordStrength(e.target.value);
  }
});

// 1-Click Frictionless Isolated Guest Test Drive
async function handleGuestTestDrive() {
  if (authDemoBtn) {
    authDemoBtn.disabled = true;
    authDemoBtn.innerHTML = `<span>Connecting Guest Session…</span>`;
  }
  if (showcaseDemoBtn) {
    showcaseDemoBtn.disabled = true;
    showcaseDemoBtn.innerHTML = `<span>Launching Studio…</span>`;
  }

  try {
    const res = await fetch("/api/auth/guest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Guest test drive failed.");
    }

    authToken = data.token;
    currentUser = data.user;
    localStorage.setItem("cortex_auth_token", authToken);
    localStorage.setItem("cortex_active_conv", "new");
    if (currentUser && currentUser.username) {
      localStorage.setItem("cortex_username", currentUser.username);
    }
    updateDynamicGreeting();

    closeAuthModal();
    showChatApp();
    startNewChat();
    await loadProjects();
    await loadConversations(false);
  } catch (err) {
    console.error("Guest drive error:", err);
    if (authErrorAlert) {
      authErrorAlert.textContent = err.message || "Failed to initialize guest session. Please try again.";
      authErrorAlert.style.display = "block";
    }
  } finally {
    if (authDemoBtn) {
      authDemoBtn.disabled = false;
      authDemoBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        <span>1-Click Guest Test Drive (Instant Access)</span>
      `;
    }
    if (showcaseDemoBtn) {
      showcaseDemoBtn.disabled = false;
      showcaseDemoBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        <span>1-Click Test Drive</span>
      `;
    }
  }
}

authDemoBtn?.addEventListener("click", handleGuestTestDrive);
showcaseDemoBtn?.addEventListener("click", handleGuestTestDrive);

// Claude Code Terminal Simulator Engine
const simPresetsData = {
  ratelimiter: {
    prompt: "Design distributed Token-Bucket rate limiter with Redis & benchmark throughput curve",
    steps: [
      {
        type: "thought",
        icon: "💭",
        title: "Autonomous Planning & Architectural Decomposition",
        time: "0.6s",
        detail: "Identified requirement: High-throughput 500k req/s rate limiter. Selecting sliding-window token bucket algorithm with atomic Redis EVAL Lua script to prevent race conditions. Generating benchmark harness and Matplotlib throughput curve."
      },
      {
        type: "tool",
        icon: "🌐",
        title: 'tool: web_search("distributed token bucket redis lua latency benchmark 2026")',
        badge: { text: "200 OK", cls: "done" },
        detail: "✓ Found 4 authoritative citations (ACM, Redis Labs, Cloudflare Engineering). Extracted optimal Lua atomicity patterns.",
        mono: true
      },
      {
        type: "tool",
        icon: "🧠",
        title: 'tool: deep_reasoning(target="distributed_concurrency_analysis")',
        badge: { text: "SYNTHESIZED 0.42s", cls: "done" },
        detail: "✓ Formal invariant verification completed for 500k ops/sec. Verified sliding-window Lua atomicity and Redis cluster failover semantics.",
        mono: true
      },
      {
        type: "artifact",
        icon: "📄",
        title: "Artifact Generated: distributed_rate_limiter.py (100% Type-Annotated)",
        badge: { text: "SAVED .MD", cls: "saved" },
        detail: ""
      }
    ]
  },
  mlpipeline: {
    prompt: "Train XGBoost classifier on customer churn dataset with 5-fold CV & ROC curve",
    steps: [
      {
        type: "thought",
        icon: "💭",
        title: "Feature Engineering & Hyperparameter Optimization",
        time: "0.5s",
        detail: "Preprocessing 100k tabular rows: target encoding high-cardinality features, power transform on tenure, handling class imbalance via SMOTE/scale_pos_weight. Configuring Optuna 50-trial search."
      },
      {
        type: "tool",
        icon: "🌐",
        title: 'tool: web_search("xgboost optuna cross-validation roc auc best practices 2026")',
        badge: { text: "200 OK", cls: "done" },
        detail: "✓ Retrieved latest XGBoost 3.0 API guidelines. Using Hist gradient booster with GPU tree method.",
        mono: true
      },
      {
        type: "tool",
        icon: "📊",
        title: 'tool: chart_renderer(spec="roc_pr_curve_interactive")',
        badge: { text: "RENDERED 0.35s", cls: "done" },
        detail: "✓ Interactive SVG/Chart.js ROC & Precision-Recall curves generated. 5-fold CV Mean ROC-AUC: 0.942 ± 0.009.",
        mono: true
      },
      {
        type: "artifact",
        icon: "📄",
        title: "Artifact Generated: churn_pipeline_production.py (MLflow Annotated)",
        badge: { text: "SAVED .MD", cls: "saved" },
        detail: ""
      }
    ]
  },
  webscrape: {
    prompt: "Research 2026 autonomous agent benchmarks, synthesize SWE-bench SOTA & build summary",
    steps: [
      {
        type: "thought",
        icon: "💭",
        title: "Comprehensive Frontier Literature Synthesis",
        time: "0.4s",
        detail: "Formulating multi-angle research query targeting official SWE-bench Verified leaderboard, GAIA benchmark results, and recent NeurIPS 2025/2026 agentic architecture breakthroughs."
      },
      {
        type: "tool",
        icon: "🌐",
        title: 'tool: web_search("swe-bench verified leaderboard agentic coding sota 2026")',
        badge: { text: "200 OK", cls: "done" },
        detail: "✓ Parsed 8 citations across Stanford, Princeton, and arXiv preprints. Verified top model resolving rates.",
        mono: true
      },
      {
        type: "tool",
        icon: "📄",
        title: 'tool: scrape_page(url="https://swe-bench.github.io")',
        badge: { text: "200 OK", cls: "done" },
        detail: "Extracted verified pass@1 scores: Cortex 5 MoE (71.4%), Claude 3.5 Sonnet (49.0%), GPT-4o (38.8%). Normalized into markdown table.",
        mono: true
      },
      {
        type: "artifact",
        icon: "📄",
        title: "Artifact Generated: agentic_coding_sota_2026.md (Peer-Reviewed Format)",
        badge: { text: "SAVED .MD", cls: "saved" },
        detail: ""
      }
    ]
  },
  mathproof: {
    prompt: "Derive continuous-time Black-Scholes PDE via Itô's Lemma with KaTeX formulas",
    steps: [
      {
        type: "thought",
        icon: "💭",
        title: "Continuous Stochastic Calculus Deduction",
        time: "0.3s",
        detail: "Setting up geometric Brownian motion dS_t = μ S_t dt + σ S_t dW_t. Applying Taylor expansion up to (dW_t)^2 = dt. Constructing delta-hedged riskless portfolio Π = V - Δ S to eliminate Brownian risk."
      },
      {
        type: "tool",
        icon: "📐",
        title: 'tool: calculator(expression="zero_arbitrage_invariant_derivation")',
        badge: { text: "VERIFIED 0.18s", cls: "done" },
        detail: "✓ Formal algebraic verification of zero-arbitrage condition: dΠ = r Π dt\nResulting Black-Scholes PDE: ∂V/∂t + r S ∂V/∂S + 1/2 σ² S² ∂²V/∂S² - r V = 0\nAlgebraic boundary conditions validated.",
        mono: true
      },
      {
        type: "artifact",
        icon: "📄",
        title: "Artifact Generated: black_scholes_rigorous_proof.md (KaTeX Formatted)",
        badge: { text: "SAVED .MD", cls: "saved" },
        detail: ""
      }
    ]
  }
};

function switchSimTab(targetTab) {
  document.querySelectorAll(".sim-tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === targetTab);
  });
  const panes = ["terminal", "sandbox", "artifact", "math"];
  panes.forEach((p) => {
    const paneEl = document.getElementById(`simPane-${p}`);
    if (paneEl) paneEl.style.display = p === targetTab ? "flex" : "none";
  });
}

document.querySelectorAll(".sim-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;
    if (target) switchSimTab(target);
  });
});

function renderSimSteps(steps) {
  if (!simStepsContainer) return;
  simStepsContainer.innerHTML = steps.map((step) => {
    const badgeHtml = step.badge ? `<span class="sim-step-badge ${step.badge.cls}">${step.badge.text}</span>` : "";
    const timeHtml = step.time ? `<span class="sim-step-time">${step.time}</span>` : "";
    const detailHtml = step.detail ? `<div class="sim-step-detail ${step.mono ? 'mono' : ''}">${step.detail}</div>` : "";
    return `
      <div class="sim-step-item ${step.type}">
        <div class="sim-step-header">
          <span class="sim-step-icon">${step.icon}</span>
          <span class="sim-step-title">${step.title}</span>
          ${timeHtml}
          ${badgeHtml}
        </div>
        ${detailHtml}
      </div>
    `;
  }).join("");
}

document.querySelectorAll(".sim-preset-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".sim-preset-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    const presetKey = chip.dataset.preset;
    const data = simPresetsData[presetKey];
    if (!data) return;

    switchSimTab("terminal");
    if (simTypedText) simTypedText.textContent = data.prompt;
    renderSimSteps(data.steps);
  });
});

function executeCustomSimPrompt(userPrompt) {
  if (!userPrompt || !userPrompt.trim()) return;
  const prompt = userPrompt.trim();
  switchSimTab("terminal");
  if (simTypedText) simTypedText.textContent = prompt;
  document.querySelectorAll(".sim-preset-chip").forEach((c) => c.classList.remove("active"));

  const customSteps = [
    {
      type: "thought",
      icon: "💭",
      title: "Autonomous Planning & Task Decomposition",
      time: "0.4s",
      detail: `Deconstructing prompt: "${prompt}". Identifying core requirements, necessary APIs, production architecture patterns, and test suites.`
    },
    {
      type: "tool",
      icon: "🌐",
      title: `tool: web_search("${prompt.slice(0, 45)} best practices 2026")`,
      badge: { text: "200 OK", cls: "done" },
      detail: "✓ Retrieved official documentation and community standards. Extracted production patterns.",
      mono: true
    },
    {
      type: "tool",
      icon: "💻",
      title: 'tool: code_generator(target="production_deliverable")',
      badge: { text: "SYNTHESIZED 0.35s", cls: "done" },
      detail: "Synthesized production-grade, type-annotated code with comprehensive error handling and test suite.",
      mono: true
    },
    {
      type: "artifact",
      icon: "📄",
      title: "Artifact Generated: solution_deliverable.py (Production Ready)",
      badge: { text: "SAVED .MD", cls: "saved" },
      detail: ""
    }
  ];
  renderSimSteps(customSteps);
  if (simCustomInput) simCustomInput.value = "";
}

simRunBtn?.addEventListener("click", () => {
  executeCustomSimPrompt(simCustomInput?.value);
});

simCustomInput?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    executeCustomSimPrompt(simCustomInput.value);
  }
});

// Frontier Models Fleet Showcase & Dynamic Inspector
const modelFleetData = {
  "cortex-5-super": {
    name: "Cortex 5 Super Agent (120B MoE)",
    status: "DEPLOYED & HEALTHY",
    arch: "Sparse Mixture of Experts (MoE) 120B",
    context: "131,072 Tokens (128k)",
    ttft: "< 18ms",
    tools: "Web Search, Code Intelligence, Math, Memory",
    modelValue: "meta/llama-3.1-70b-instruct"
  },
  "cortex-5-ultra": {
    name: "Cortex 5 Ultra Master Agent (550B)",
    status: "FRONTIER ACTIVE",
    arch: "Ultra-Scale Dense/Sparse Hybrid 550B",
    context: "131,072 Tokens (128k)",
    ttft: "< 32ms",
    tools: "Deep Research, Architecture PRDs, Full Codebase Synthesis",
    modelValue: "deepseek-ai/deepseek-r1"
  },
  "cortex-4-deep": {
    name: "Cortex 4 Deep Reasoning (MoE)",
    status: "DEDUCTION ACTIVE",
    arch: "Chain-of-Thought Logic Engine",
    context: "65,536 Tokens (64k)",
    ttft: "< 14ms",
    tools: "Mathematical Proofs, Bug Root Cause Isolation, Algorithms",
    modelValue: "deepseek-ai/deepseek-r1"
  },
  "cortex-4-omni": {
    name: "Cortex 4 Omni Vision MoE",
    status: "VISION PIPELINE ACTIVE",
    arch: "Multimodal Vision-Language Architecture",
    context: "65,536 Tokens (64k)",
    ttft: "< 22ms",
    tools: "High-Resolution Image Inspection, UI OCR, Visual Q&A",
    modelValue: "meta/llama-3.2-11b-vision-instruct"
  },
  "cortex-35-fast": {
    name: "Cortex 3.5 Fast Lightning",
    status: "ULTRA-LOW LATENCY",
    arch: "Distilled Low-Latency Transformer",
    context: "32,768 Tokens (32k)",
    ttft: "< 6ms",
    tools: "Sub-Second Code Autocomplete, Stream Formatting",
    modelValue: "meta/llama-3.1-8b-instruct"
  }
};

let activeFleetModelKey = "cortex-5-super";

function selectFleetModel(modelKey) {
  const info = modelFleetData[modelKey];
  if (!info) return;

  activeFleetModelKey = modelKey;
  document.querySelectorAll("#modelsFleetGrid .model-card").forEach((card) => {
    card.classList.toggle("active-model", card.dataset.modelId === modelKey);
  });

  if (inspectorModelName) inspectorModelName.textContent = info.name;
  if (inspectorModelStatus) inspectorModelStatus.textContent = info.status;
  if (inspectorArch) inspectorArch.textContent = info.arch;
  if (inspectorContext) inspectorContext.textContent = info.context;
  if (inspectorTtft) inspectorTtft.textContent = info.ttft;
  if (inspectorTools) inspectorTools.textContent = info.tools;

  if (modelSelect && info.modelValue) {
    modelSelect.value = info.modelValue;
  }
}

document.querySelectorAll("#modelsFleetGrid .model-card").forEach((card) => {
  card.addEventListener("click", () => {
    const key = card.dataset.modelId;
    if (key) selectFleetModel(key);
  });
});

inspectorTryBtn?.addEventListener("click", () => {
  const info = modelFleetData[activeFleetModelKey];
  if (info && modelSelect && info.modelValue) {
    modelSelect.value = info.modelValue;
  }
  handleLaunchOrRegister();
});

// Project Workspace Modal Listeners
createProjectBtn?.addEventListener("click", () => openProjectModal());
projectModalCloseBtn?.addEventListener("click", closeProjectModal);
projectModalCancelBtn?.addEventListener("click", closeProjectModal);
projectModalSaveBtn?.addEventListener("click", saveProjectFromModal);
projectModalDeleteBtn?.addEventListener("click", deleteProjectFromModal);
projectModal?.addEventListener("click", (e) => {
  if (e.target === projectModal) closeProjectModal();
});


// Sidebar User Profile Popup & Settings
userProfileBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  toggleUserProfileMenu();
});

menuSettingsBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  openSettingsModal();
});

menuSignOutBtn?.addEventListener("click", () => {
  closeUserProfileMenu();
  if (confirm("Are you sure you want to sign out of Cortex?")) {
    signOut();
  }
});

signOutBtn?.addEventListener("click", () => {
  if (confirm("Are you sure you want to sign out of Cortex?")) {
    signOut();
  }
});

// Global Keyboard Shortcuts (Ctrl+B for sidebar, Ctrl+K or / for search)
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && (e.key === "b" || e.key === "B")) {
    e.preventDefault();
    toggleSidebar();
    return;
  }

  if ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K")) {
    e.preventDefault();
    if (appView && appView.style.display !== "none") {
      if (appView.classList.contains("sidebar-collapsed")) {
        setSidebarCollapsed(false);
      }
      sidebarSearchInput?.focus();
      sidebarSearchInput?.select();
    }
    return;
  }

  if (e.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName)) {
    if (appView && appView.style.display !== "none") {
      e.preventDefault();
      if (appView.classList.contains("sidebar-collapsed")) {
        setSidebarCollapsed(false);
      }
      sidebarSearchInput?.focus();
      sidebarSearchInput?.select();
    }
  }

  if (e.key === "Escape") {
    closeGuideDrawer();
    closeArtifactPanel();
  }
});

// ==================== CORTEX 3.1 UX & ARCHITECTURAL SUITE ====================

// 1. Daily Quota Usage & Notification Toast
function updateUsageDisplay(tokensUsed, limit = 100000) {
  const usageText = document.getElementById("topbarUsageText");
  const usageBar = document.getElementById("topbarUsageBar");
  if (!usageText) return;
  const used = Math.max(0, Number(tokensUsed) || 0);
  let formattedUsed = used.toLocaleString();
  if (used >= 1000) {
    formattedUsed = (used / 1000).toFixed(used >= 10000 ? 0 : 1) + "k";
  }
  const formattedLimit = Math.round(limit / 1000) + "k";
  usageText.textContent = `${formattedUsed} / ${formattedLimit}`;
  if (usageBar) {
    const pct = Math.min(100, Math.max(0, (used / limit) * 100));
    usageBar.style.width = `${pct}%`;
  }
}

async function loadUserUsage() {
  if (!authToken) return;
  try {
    const res = await fetch("/api/user/usage", { headers: authHeaders() });
    if (res.ok) {
      const data = await res.json();
      updateUsageDisplay(data.tokens_used, data.tokens_limit || 100000);
    }
  } catch (err) {
    console.error("Failed to load daily usage:", err);
  }
}

function showQuotaToast(message) {
  const toast = document.getElementById("quotaToast") || quotaToast;
  const textEl = document.getElementById("quotaToastText");
  if (!toast) return;
  if (textEl && message) textEl.textContent = message;
  toast.style.display = "flex";
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.style.display = "none";
  }, 5000);
}

// 2. Claude-Style Artifacts Library View
let allUserArtifacts = [];

async function loadArtifactsCount() {
  if (!authToken) return;
  try {
    const res = await fetch("/api/artifacts", { headers: authHeaders() });
    if (res.ok) {
      const data = await res.json();
      allUserArtifacts = data.artifacts || [];
      const countEl = document.getElementById("sidebarArtifactsCount") || sidebarArtifactsCount;
      const viewCountEl = document.getElementById("artifactsCountBadge") || artifactsCountBadge;
      const count = allUserArtifacts.length;
      if (countEl) countEl.textContent = count;
      if (viewCountEl) viewCountEl.textContent = `${count} document${count === 1 ? "" : "s"}`;
    }
  } catch (err) {
    console.error("Failed to load artifacts count:", err);
  }
}

async function showArtifactsView() {
  const chatArea = document.getElementById("chat");
  const composerWrap = document.querySelector(".composer-wrap");
  const artView = document.getElementById("artifactsView") || artifactsView;
  const sidebarBtn = document.getElementById("sidebarArtifactsBtn") || sidebarArtifactsBtn;

  if (!artView) return;

  if (chatArea) chatArea.style.display = "none";
  if (composerWrap) composerWrap.style.display = "none";
  artView.style.display = "flex";
  if (sidebarBtn) sidebarBtn.classList.add("active");

  closeMobileSidebar();
  await loadArtifacts();
}

function hideArtifactsView() {
  const chatArea = document.getElementById("chat");
  const composerWrap = document.querySelector(".composer-wrap");
  const artView = document.getElementById("artifactsView") || artifactsView;
  const sidebarBtn = document.getElementById("sidebarArtifactsBtn") || sidebarArtifactsBtn;

  if (artView) artView.style.display = "none";
  if (chatArea) chatArea.style.display = "";
  if (composerWrap) composerWrap.style.display = "";
  if (sidebarBtn) sidebarBtn.classList.remove("active");
}

async function loadArtifacts() {
  if (!authToken) return;
  try {
    const res = await fetch("/api/artifacts", { headers: authHeaders() });
    if (res.ok) {
      const data = await res.json();
      allUserArtifacts = data.artifacts || [];
      renderArtifactsList(allUserArtifacts);
      const countEl = document.getElementById("sidebarArtifactsCount") || sidebarArtifactsCount;
      const viewCountEl = document.getElementById("artifactsCountBadge") || artifactsCountBadge;
      const count = allUserArtifacts.length;
      if (countEl) countEl.textContent = count;
      if (viewCountEl) viewCountEl.textContent = `${count} document${count === 1 ? "" : "s"}`;
    }
  } catch (err) {
    console.error("Failed to load artifacts:", err);
  }
}

function renderArtifactsList(items) {
  const grid = document.getElementById("artifactsGrid") || artifactsGrid;
  const empty = document.getElementById("artifactsEmptyState");
  if (!grid) return;
  grid.innerHTML = "";

  if (!items || items.length === 0) {
    if (empty) empty.style.display = "block";
    return;
  }
  if (empty) empty.style.display = "none";

  items.forEach((art) => {
    const card = document.createElement("div");
    card.className = "artifact-card";

    const cleanContent = (art.content || "").replace(/```[a-z]*\n?/g, "").trim();
    const snippet = cleanContent.slice(0, 140) || "Markdown artifact document content";
    const dateStr = art.created_at
      ? new Date(art.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
      : "Recently";

    card.innerHTML = `
      <div class="artifact-card-header">
        <div class="artifact-card-icon">📄</div>
        <div class="artifact-card-meta">
          <h3 class="artifact-card-title" title="${escapeHtml(art.filename)}">${escapeHtml(art.filename)}</h3>
          <div class="artifact-card-chat" title="${escapeHtml(art.conversation_title || "Conversation")}">${escapeHtml(art.conversation_title || "Conversation")}</div>
        </div>
      </div>
      <div class="artifact-card-preview">${escapeHtml(snippet)}</div>
      <div class="artifact-card-footer">
        <span class="artifact-card-date">${escapeHtml(dateStr)}</span>
        <div class="artifact-card-actions">
          <button class="artifact-btn-preview" type="button" title="Preview Document in Split Panel">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            <span>Preview</span>
          </button>
          <button class="artifact-btn-download" type="button" title="Download ${escapeHtml(art.filename)}">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
          </button>
        </div>
      </div>
    `;

    // Preview in right split panel via existing openArtifactPanel
    const prevBtn = card.querySelector(".artifact-btn-preview");
    prevBtn.addEventListener("click", () => {
      openArtifactPanel({
        filename: art.filename,
        content: art.content,
        type: "markdown"
      });
    });

    // Download document
    const dlBtn = card.querySelector(".artifact-btn-download");
    dlBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      downloadTextFile(art.filename, art.content, "text/markdown;charset=utf-8");
    });

    grid.appendChild(card);
  });
}

// Artifacts Search Filter
artifactsSearchInput?.addEventListener("input", (e) => {
  const q = (e.target.value || "").trim().toLowerCase();
  if (!q) {
    renderArtifactsList(allUserArtifacts);
    return;
  }
  const filtered = allUserArtifacts.filter((art) => {
    return (
      (art.filename && art.filename.toLowerCase().includes(q)) ||
      (art.conversation_title && art.conversation_title.toLowerCase().includes(q)) ||
      (art.content && art.content.toLowerCase().includes(q))
    );
  });
  renderArtifactsList(filtered);
});

sidebarArtifactsBtn?.addEventListener("click", showArtifactsView);
artifactsCloseViewBtn?.addEventListener("click", hideArtifactsView);

// 3. Cortex Agent Playbook & Guide Drawer
function openGuideDrawer() {
  const drawer = document.getElementById("guideDrawer") || guideDrawer;
  if (drawer) {
    drawer.style.display = "flex";
  }
}

function closeGuideDrawer() {
  const drawer = document.getElementById("guideDrawer") || guideDrawer;
  if (drawer) {
    drawer.style.display = "none";
  }
}

guideBtn?.addEventListener("click", openGuideDrawer);
guideCloseBtn?.addEventListener("click", closeGuideDrawer);

// Guide Navigation Tabs Switching
document.querySelectorAll(".guide-tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".guide-tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".guide-tab-pane").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    const tabName = btn.dataset.tab;
    const targetPane = document.getElementById(`guideTab-${tabName}`);
    if (targetPane) targetPane.classList.add("active");
  });
});

// Guide Prompt Templates: 1-Click Use & Copy Actions
const guideTabPrompting = document.getElementById("guideTab-prompting");
if (guideTabPrompting) {
  guideTabPrompting.addEventListener("click", async (e) => {
    const copyBtn = e.target.closest(".template-copy-btn");
    if (copyBtn) {
      const textToCopy = copyBtn.dataset.copy;
      if (!textToCopy) return;
      try {
        await navigator.clipboard.writeText(textToCopy);
        const original = copyBtn.textContent;
        copyBtn.textContent = "Copied! ✓";
        copyBtn.style.color = "#4ade80";
        setTimeout(() => {
          copyBtn.textContent = original;
          copyBtn.style.color = "";
        }, 1800);
      } catch (err) {
        console.error("Failed to copy template prompt:", err);
      }
      return;
    }

    const useBtn = e.target.closest(".template-use-btn");
    if (useBtn) {
      const textToUse = useBtn.dataset.use;
      if (!textToUse) return;
      if (promptEl) {
        promptEl.value = textToUse;
        autoResize();
        promptEl.focus();
        promptEl.setSelectionRange(promptEl.value.length, promptEl.value.length);
      }
      closeGuideDrawer();
      return;
    }
  });
}

// 4. Step-by-Step Onboarding Tour & Confetti Cannons
const tourSteps = [
  {
    icon: "🚀",
    title: "Welcome to Cortex 3.1 Studio",
    desc: "Experience next-generation autonomous AI with frontier code intelligence, real-time web research, interactive Chart.js charts, and KaTeX math.",
    selector: null
  },
  {
    icon: "💬",
    title: "Sidebar & Project Workspaces",
    desc: "Organize your conversations by project. Click '+ New Chat' anytime to start fresh, or search past chats with Ctrl+K.",
    selector: "#sidebar"
  },
  {
    icon: "📄",
    title: "Artifacts Library",
    desc: "Access all generated Markdown reports, code artifacts, and documents in one place. Click to preview in the split panel or download.",
    selector: "#sidebarArtifactsBtn"
  },
  {
    icon: "🎯",
    title: "Smart Execution Modes",
    desc: "Choose between Auto (smart routing), Fast (instant stream, 0.5s TTFT), and Thinking (multi-step analytical reasoning).",
    selector: "#modePickerWrap"
  },
  {
    icon: "🧠",
    title: "Frontier AI Models",
    desc: "Switch dynamically between 7 state-of-the-art models: Cortex 5 (Super Agent 120B), Cortex 5 Ultra (550B), Cortex 4 Deep Reasoning, Cortex 4 Omni (Vision), and more.",
    selector: "#modelSelect"
  },
  {
    icon: "🪄",
    title: "Agent Presets & Code Architecture",
    desc: "Use magic presets for web research, Chart.js plots, deep reasoning, and production code architecture synthesis.",
    selector: "#presetsBtn"
  }
];

let currentTourStep = 0;

function startOnboardingTour() {
  currentTourStep = 0;
  showTourStep(0);
}

function showTourStep(index) {
  const overlay = document.getElementById("tourOverlay") || tourOverlay;
  const card = document.getElementById("tourCard") || tourCard;
  const spotlight = document.getElementById("tourSpotlight") || tourSpotlight;
  if (!overlay || !card) return;

  if (index < 0 || index >= tourSteps.length) {
    finishTour();
    return;
  }

  currentTourStep = index;
  const step = tourSteps[index];

  const currentStepEl = document.getElementById("tourStepCurrent");
  const totalStepEl = document.getElementById("tourStepTotal");
  const iconEl = document.getElementById("tourIcon");
  const titleEl = document.getElementById("tourTitle");
  const descEl = document.getElementById("tourDescription");

  if (currentStepEl) currentStepEl.textContent = index + 1;
  if (totalStepEl) totalStepEl.textContent = tourSteps.length;
  if (iconEl) iconEl.textContent = step.icon;
  if (titleEl) titleEl.textContent = step.title;
  if (descEl) descEl.textContent = step.desc;

  const prevBtn = document.getElementById("tourPrevBtn") || tourPrevBtn;
  const nextBtn = document.getElementById("tourNextBtn") || tourNextBtn;
  if (prevBtn) prevBtn.style.display = index === 0 ? "none" : "inline-flex";
  if (nextBtn) nextBtn.textContent = index === tourSteps.length - 1 ? "Finish 🎉" : "Next →";

  overlay.style.display = "block";
  card.style.display = "block";

  if (step.selector) {
    const el = document.querySelector(step.selector);
    if (el && el.offsetParent !== null) {
      const rect = el.getBoundingClientRect();
      const pad = 6;
      if (spotlight) {
        spotlight.style.display = "block";
        spotlight.style.top = `${Math.max(0, rect.top - pad)}px`;
        spotlight.style.left = `${Math.max(0, rect.left - pad)}px`;
        spotlight.style.width = `${rect.width + pad * 2}px`;
        spotlight.style.height = `${rect.height + pad * 2}px`;
      }

      // Position tour card adjacent to the spotlighted element
      let cardTop = rect.bottom + 16;
      let cardLeft = rect.left;
      if (cardTop + 240 > window.innerHeight) {
        cardTop = Math.max(20, rect.top - 240);
      }
      if (cardLeft + 380 > window.innerWidth) {
        cardLeft = Math.max(20, window.innerWidth - 400);
      }
      card.style.top = `${cardTop}px`;
      card.style.left = `${cardLeft}px`;
      card.style.transform = "none";
      return;
    }
  }

  // Centered position if no spotlight target
  if (spotlight) spotlight.style.display = "none";
  card.style.top = "50%";
  card.style.left = "50%";
  card.style.transform = "translate(-50%, -50%)";
}

function finishTour() {
  const overlay = document.getElementById("tourOverlay") || tourOverlay;
  const card = document.getElementById("tourCard") || tourCard;
  if (overlay) overlay.style.display = "none";
  if (card) card.style.display = "none";
  localStorage.setItem("cortex_tour_completed", "true");

  // Blast Confetti Cannon & Show Celebration Toast for 4.5 seconds!
  launchConfettiCelebration();
}

function launchConfettiCelebration() {
  const toast = document.getElementById("celebrationToast") || celebrationToast;
  const canvas = document.getElementById("confettiCanvas") || confettiCanvas;

  if (toast) {
    toast.style.display = "flex";
    setTimeout(() => {
      toast.style.animation = "toastPop 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards";
      setTimeout(() => { toast.style.display = "none"; }, 300);
    }, 4500);
  }

  if (canvas) {
    runConfettiAnimation(canvas, 4500);
  }
}

function runConfettiAnimation(canvas, durationMs = 4500) {
  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  canvas.style.display = "block";

  const colors = ["#22c55e", "#4ade80", "#38bdf8", "#fbbf24", "#f43f5e", "#a855f7", "#ffffff"];
  const particles = [];
  const particleCount = 200;

  for (let i = 0; i < particleCount; i++) {
    const isLeft = i % 2 === 0;
    particles.push({
      x: isLeft ? 50 : canvas.width - 50,
      y: canvas.height - 30,
      vx: isLeft ? (Math.random() * 14 + 6) : -(Math.random() * 14 + 6),
      vy: -(Math.random() * 20 + 10),
      gravity: 0.38,
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 16,
      size: Math.random() * 8 + 6,
      color: colors[Math.floor(Math.random() * colors.length)],
      opacity: 1,
      shape: Math.random() > 0.4 ? "rect" : "circle"
    });
  }

  const startTime = performance.now();

  function render(time) {
    const elapsed = time - startTime;
    if (elapsed > durationMs) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      canvas.style.display = "none";
      return;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += p.gravity;
      p.vx *= 0.985;
      p.rotation += p.rotationSpeed;

      if (elapsed > durationMs - 1200) {
        p.opacity = Math.max(0, (durationMs - elapsed) / 1200);
      }

      ctx.save();
      ctx.globalAlpha = p.opacity;
      ctx.translate(p.x, p.y);
      ctx.rotate((p.rotation * Math.PI) / 180);
      ctx.fillStyle = p.color;

      if (p.shape === "rect") {
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 1.6);
      } else {
        ctx.beginPath();
        ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    });

    requestAnimationFrame(render);
  }

  requestAnimationFrame(render);
}

tourNextBtn?.addEventListener("click", () => showTourStep(currentTourStep + 1));
tourPrevBtn?.addEventListener("click", () => showTourStep(currentTourStep - 1));
tourSkipBtn?.addEventListener("click", finishTour);
tourCloseBtn?.addEventListener("click", finishTour);

window.addEventListener("resize", () => {
  const overlay = document.getElementById("tourOverlay");
  if (overlay && overlay.style.display !== "none") {
    showTourStep(currentTourStep);
  }
});

// Initial Boot
showEmptyState();
checkAuth();
