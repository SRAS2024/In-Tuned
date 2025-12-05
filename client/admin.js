// admin.js
// Client side logic for the Administrative Site

(function () {
  const loginView = document.getElementById("admin-login-view");
  const loginForm = document.getElementById("admin-login-form");
  const loginButton = document.getElementById("admin-login-button");
  const loginError = document.getElementById("admin-login-error");
  const loginUsername = document.getElementById("admin-username");
  const loginPassword = document.getElementById("admin-password");

  const loadingOverlay = document.getElementById("admin-loading-overlay");
  const loadingFill = document.getElementById("admin-loading-fill");

  const dashboard = document.getElementById("admin-dashboard");
  const logoutButton = document.getElementById("admin-logout-button");

  const maintenanceToggle = document.getElementById("maintenance-toggle");
  const maintenanceMessageInput = document.getElementById("maintenance-message");
  const maintenanceStatusChip = document.getElementById("maintenance-status-chip");
  const maintenanceError = document.getElementById("maintenance-error");

  const noticeText = document.getElementById("notice-text");
  const noticeActiveCheckbox = document.getElementById("notice-active");
  const addNoticeButton = document.getElementById("add-notice-button");
  const noticeError = document.getElementById("notice-error");
  const noticeList = document.getElementById("notice-list");

  const lexiconUploadForm = document.getElementById("lexicon-upload-form");
  const lexiconLanguageSelect = document.getElementById("lexicon-language");
  const lexiconFileInput = document.getElementById("lexicon-file");
  const lexiconError = document.getElementById("lexicon-error");
  const lexiconFileList = document.getElementById("lexicon-file-list");

  const devPasswordModal = document.getElementById("dev-password-modal");
  const devPasswordInput = document.getElementById("dev-password-input");
  const devPasswordError = document.getElementById("dev-password-error");
  const devPasswordCancel = document.getElementById("dev-password-cancel");
  const devPasswordConfirm = document.getElementById("dev-password-confirm");

  const sitePreviewFrame = document.querySelector(".site-preview-frame");

  let currentMaintenanceEnabled = false;
  let maintenanceToggleProgrammatic = false;
  let pendingMaintenanceEnable = false;

  // Utility helpers

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

  async function apiFetchForm(path, formData, options = {}) {
    const opts = {
      method: "POST",
      credentials: "same-origin",
      body: formData,
      ...(options || {})
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

  function showElement(el) {
    if (!el) return;
    el.classList.remove("hidden");
  }

  function hideElement(el) {
    if (!el) return;
    el.classList.add("hidden");
  }

  function refreshSitePreview() {
    const frame = sitePreviewFrame || document.querySelector(".site-preview-frame");
    if (frame && frame.contentWindow) {
      frame.contentWindow.location.reload();
    }
  }

  function setChipState(enabled) {
    currentMaintenanceEnabled = enabled;
    if (!maintenanceStatusChip) return;
    if (enabled) {
      maintenanceStatusChip.textContent = "Offline";
      maintenanceStatusChip.classList.add("offline");
    } else {
      maintenanceStatusChip.textContent = "Online";
      maintenanceStatusChip.classList.remove("offline");
    }
  }

  function formatDateTime(value) {
    try {
      const d = new Date(value);
      if (Number.isNaN(d.getTime())) return "";
      return d.toLocaleString();
    } catch (e) {
      return "";
    }
  }

  // Loading overlay helpers

  function showLoadingOverlay() {
    if (!loadingOverlay || !loadingFill) return;
    loadingFill.style.width = "0%";
    loadingOverlay.classList.add("show");
    requestAnimationFrame(() => {
      loadingFill.style.width = "100%";
    });
  }

  function hideLoadingOverlay() {
    if (!loadingOverlay || !loadingFill) return;
    loadingOverlay.classList.remove("show");
    loadingFill.style.width = "0%";
  }

  // Login flow

  async function handleAdminLogin(event) {
    event.preventDefault();
    hideElement(loginError);
    hideLoadingOverlay();

    const username = loginUsername.value.trim();
    const password = loginPassword.value;

    if (!username || !password) {
      loginError.textContent = "Not authorized";
      showElement(loginError);
      return;
    }

    loginButton.disabled = true;

    try {
      const data = await apiFetchJSON("/api/admin/login", {
        method: "POST",
        body: JSON.stringify({ username, password })
      });

      if (!data.ok) {
        throw new Error(data.error || "Not authorized");
      }

      // Hide login card, then show centered loading overlay
      if (loginView) {
        hideElement(loginView);
      }

      showLoadingOverlay();

      setTimeout(async () => {
        hideLoadingOverlay();

        if (dashboard) {
          showElement(dashboard);
          dashboard.style.display = "flex";
        }

        loginButton.disabled = false;

        try {
          await refreshAdminState();
          refreshSitePreview();
        } catch (e) {
          // Ignore refresh errors in this step
        }
      }, 3000);
    } catch (err) {
      loginButton.disabled = false;
      loginError.textContent = "Not authorized";
      showElement(loginError);
      hideLoadingOverlay();
      if (loginView) {
        showElement(loginView);
      }
    }
  }

  async function handleAdminLogout() {
    try {
      await apiFetchJSON("/api/admin/logout", {
        method: "POST"
      });
    } catch (e) {
      // Ignore logout error
    }

    if (loginView) {
      showElement(loginView);
    }

    if (dashboard) {
      hideElement(dashboard);
      dashboard.style.display = "none";
    }

    loginPassword.value = "";
    hideLoadingOverlay();
    hideElement(loginError);
    loginError.textContent = "";
  }

  // Admin state loading

  async function loadSiteSettings() {
    try {
      const data = await apiFetchJSON("/api/admin/site-state", {
        method: "GET"
      });

      const settings = data.settings || {};
      const notices = data.notices || [];

      const enabled = Boolean(settings.maintenance_mode);
      const message =
        settings.maintenance_message ||
        "Site is currently down due to maintenance. We will be back shortly.";

      maintenanceToggleProgrammatic = true;
      if (maintenanceToggle) {
        maintenanceToggle.checked = enabled;
      }
      maintenanceToggleProgrammatic = false;

      if (maintenanceMessageInput) {
        maintenanceMessageInput.value = message;
      }
      setChipState(enabled);

      renderNotices(notices);
      hideElement(maintenanceError);
      maintenanceError.textContent = "";

      refreshSitePreview();
    } catch (err) {
      if (maintenanceError) {
        maintenanceError.textContent = err.message;
        showElement(maintenanceError);
      }
    }
  }

  async function loadLexicons() {
    try {
      const data = await apiFetchJSON("/api/admin/lexicons", {
        method: "GET"
      });
      const files = data.files || [];
      renderLexiconFiles(files);
      hideElement(lexiconError);
      lexiconError.textContent = "";
    } catch (err) {
      if (lexiconError) {
        lexiconError.textContent = err.message;
        showElement(lexiconError);
      }
      if (lexiconFileList) {
        lexiconFileList.innerHTML = "";
      }
    }
  }

  async function refreshAdminState() {
    await Promise.all([loadSiteSettings(), loadLexicons()]);
  }

  // Maintenance toggle and modal

  function openDevPasswordModal() {
    if (!devPasswordModal || !devPasswordInput || !devPasswordError) return;
    devPasswordInput.value = "";
    devPasswordError.textContent = "";
    hideElement(devPasswordError);
    devPasswordModal.classList.add("show");
    devPasswordInput.focus();
  }

  function closeDevPasswordModal() {
    if (!devPasswordModal || !devPasswordInput || !devPasswordError) return;
    devPasswordModal.classList.remove("show");
    devPasswordInput.value = "";
    devPasswordError.textContent = "";
    hideElement(devPasswordError);
    pendingMaintenanceEnable = false;
  }

  async function handleMaintenanceToggleChange() {
    if (maintenanceToggleProgrammatic || !maintenanceToggle) return;

    const wantEnabled = maintenanceToggle.checked;

    if (wantEnabled) {
      pendingMaintenanceEnable = true;
      openDevPasswordModal();
    } else {
      try {
        const message =
          (maintenanceMessageInput &&
            maintenanceMessageInput.value.trim()) ||
          "Site is currently down due to maintenance. We will be back shortly.";
        await apiFetchJSON("/api/admin/maintenance", {
          method: "POST",
          body: JSON.stringify({
            enabled: false,
            message
          })
        });
        setChipState(false);
        hideElement(maintenanceError);
        maintenanceError.textContent = "";
        refreshSitePreview();
      } catch (err) {
        maintenanceError.textContent = err.message;
        showElement(maintenanceError);
        maintenanceToggleProgrammatic = true;
        maintenanceToggle.checked = true;
        maintenanceToggleProgrammatic = false;
        setChipState(true);
      }
    }
  }

  async function handleDevPasswordConfirm() {
    const password = devPasswordInput ? devPasswordInput.value : "";
    if (!pendingMaintenanceEnable) {
      closeDevPasswordModal();
      return;
    }
    if (!password) {
      if (devPasswordError) {
        devPasswordError.textContent = "Developer password is required.";
        showElement(devPasswordError);
      }
      return;
    }

    try {
      const message =
        (maintenanceMessageInput &&
          maintenanceMessageInput.value.trim()) ||
        "Site is currently down due to maintenance. We will be back shortly.";

      await apiFetchJSON("/api/admin/maintenance", {
        method: "POST",
        body: JSON.stringify({
          enabled: true,
          message,
          dev_password: password
        })
      });

      setChipState(true);
      hideElement(maintenanceError);
      maintenanceError.textContent = "";

      closeDevPasswordModal();
      pendingMaintenanceEnable = false;
      refreshSitePreview();
    } catch (err) {
      if (devPasswordError) {
        devPasswordError.textContent = err.message;
        showElement(devPasswordError);
      }
      maintenanceToggleProgrammatic = true;
      if (maintenanceToggle) {
        maintenanceToggle.checked = false;
      }
      maintenanceToggleProgrammatic = false;
      setChipState(false);
      refreshSitePreview();
    }
  }

  function handleDevPasswordCancel() {
    closeDevPasswordModal();
    maintenanceToggleProgrammatic = true;
    if (maintenanceToggle) {
      maintenanceToggle.checked = currentMaintenanceEnabled;
    }
    maintenanceToggleProgrammatic = false;
  }

  // Notices

  function renderNotices(notices) {
    if (!noticeList) return;

    if (!Array.isArray(notices) || notices.length === 0) {
      noticeList.innerHTML =
        '<p style="font-size:0.8rem;color:#9ca3af;margin:4px 0;">No notices yet.</p>';
      return;
    }

    noticeList.innerHTML = "";

    notices.forEach((notice) => {
      const row = document.createElement("div");
      row.className = "noticeRow";

      const main = document.createElement("div");
      main.className = "noticeMain";

      const textSpan = document.createElement("span");
      textSpan.textContent = notice.text || "";

      const metaSpan = document.createElement("span");
      metaSpan.style.fontSize = "0.75rem";
      metaSpan.style.color = "#9ca3af";
      metaSpan.textContent = formatDateTime(notice.created_at);

      main.appendChild(textSpan);
      main.appendChild(metaSpan);

      const side = document.createElement("div");
      side.style.display = "flex";
      side.style.flexDirection = "column";
      side.style.alignItems = "flex-end";
      side.style.gap = "4px";

      const badge = document.createElement("span");
      badge.className = "badge" + (notice.is_active ? "" : " inactive");
      badge.textContent = notice.is_active ? "Active" : "Inactive";

      const button = document.createElement("button");
      button.className = "ghost";
      button.textContent = notice.is_active ? "Deactivate" : "Activate";
      button.addEventListener("click", () =>
        toggleNoticeActive(notice.id, !notice.is_active)
      );

      side.appendChild(badge);
      side.appendChild(button);

      row.appendChild(main);
      row.appendChild(side);

      noticeList.appendChild(row);
    });
  }

  async function toggleNoticeActive(noticeId, isActive) {
    try {
      await apiFetchJSON(`/api/admin/notices/${noticeId}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: isActive })
      });
      await loadSiteSettings();
      hideElement(noticeError);
      noticeError.textContent = "";
      refreshSitePreview();
    } catch (err) {
      noticeError.textContent = err.message;
      showElement(noticeError);
    }
  }

  async function handleAddNotice() {
    hideElement(noticeError);
    noticeError.textContent = "";

    const text = noticeText ? noticeText.value.trim() : "";
    const isActive = noticeActiveCheckbox ? noticeActiveCheckbox.checked : true;

    if (!text) {
      noticeError.textContent = "Notice text is required.";
      showElement(noticeError);
      return;
    }

    addNoticeButton.disabled = true;

    try {
      await apiFetchJSON("/api/admin/notices", {
        method: "POST",
        body: JSON.stringify({ text, is_active: isActive })
      });

      if (noticeText) {
        noticeText.value = "";
      }
      if (noticeActiveCheckbox) {
        noticeActiveCheckbox.checked = true;
      }
      await loadSiteSettings();
      refreshSitePreview();
    } catch (err) {
      noticeError.textContent = err.message;
      showElement(noticeError);
    } finally {
      addNoticeButton.disabled = false;
    }
  }

  // Lexicons

  function renderLexiconFiles(files) {
    if (!lexiconFileList) return;

    if (!Array.isArray(files) || files.length === 0) {
      lexiconFileList.innerHTML =
        '<p style="font-size:0.8rem;color:#9ca3af;margin:4px 0;">No lexicon files uploaded yet.</p>';
      return;
    }

    lexiconFileList.innerHTML = "";

    files.forEach((file) => {
      const row = document.createElement("div");
      row.className = "fileRow";

      const main = document.createElement("div");
      main.className = "fileRowMain";

      const nameSpan = document.createElement("span");
      nameSpan.textContent = file.filename || "";

      const languageSpan = document.createElement("span");
      languageSpan.className = "language";
      languageSpan.textContent = `${(file.language || "").toUpperCase()} · ${formatDateTime(
        file.uploaded_at
      )}`;

      main.appendChild(nameSpan);
      main.appendChild(languageSpan);

      const side = document.createElement("div");
      const deleteButton = document.createElement("button");
      deleteButton.className = "ghost";
      deleteButton.textContent = "Delete";
      deleteButton.style.fontSize = "0.8rem";
      deleteButton.addEventListener("click", () => deleteLexiconFile(file.id));

      side.appendChild(deleteButton);

      row.appendChild(main);
      row.appendChild(side);

      lexiconFileList.appendChild(row);
    });
  }

  async function deleteLexiconFile(id) {
    if (!window.confirm("Delete this lexicon file?")) return;

    try {
      await apiFetchJSON(`/api/admin/lexicons/${id}`, {
        method: "DELETE"
      });
      await loadLexicons();
      hideElement(lexiconError);
      lexiconError.textContent = "";
    } catch (err) {
      lexiconError.textContent = err.message;
      showElement(lexiconError);
    }
  }

  async function handleLexiconUpload(event) {
    event.preventDefault();
    hideElement(lexiconError);
    lexiconError.textContent = "";

    const language = lexiconLanguageSelect ? lexiconLanguageSelect.value : "";
    const file = lexiconFileInput && lexiconFileInput.files
      ? lexiconFileInput.files[0]
      : null;

    if (!language || !file) {
      lexiconError.textContent = "Language and file are required.";
      showElement(lexiconError);
      return;
    }

    const formData = new FormData();
    formData.append("language", language);
    formData.append("file", file);

    const button = document.getElementById("upload-lexicon-button");
    if (button) {
      button.disabled = true;
    }

    try {
      await apiFetchForm("/api/admin/lexicons/upload", formData);
      if (lexiconFileInput) {
        lexiconFileInput.value = "";
      }
      await loadLexicons();
    } catch (err) {
      lexiconError.textContent = err.message;
      showElement(lexiconError);
    } finally {
      if (button) {
        button.disabled = false;
      }
    }
  }

  // Event bindings

  document.addEventListener("DOMContentLoaded", () => {
    if (loginForm) {
      loginForm.addEventListener("submit", handleAdminLogin);
    }
    if (logoutButton) {
      logoutButton.addEventListener("click", handleAdminLogout);
    }
    if (maintenanceToggle) {
      maintenanceToggle.addEventListener("change", handleMaintenanceToggleChange);
    }
    if (devPasswordConfirm) {
      devPasswordConfirm.addEventListener("click", handleDevPasswordConfirm);
    }
    if (devPasswordCancel) {
      devPasswordCancel.addEventListener("click", handleDevPasswordCancel);
    }
    if (devPasswordModal) {
      devPasswordModal.addEventListener("click", (event) => {
        if (event.target === devPasswordModal) {
          handleDevPasswordCancel();
        }
      });
    }
    if (addNoticeButton) {
      addNoticeButton.addEventListener("click", handleAddNotice);
    }
    if (lexiconUploadForm) {
      lexiconUploadForm.addEventListener("submit", handleLexiconUpload);
    }

    if (devPasswordInput) {
      devPasswordInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          handleDevPasswordConfirm();
        }
      });
    }
  });
})();
