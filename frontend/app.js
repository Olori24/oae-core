(() => {
  const POLL_INTERVAL = 3500;
  const state = { key: "", jobs: [], tenant: null, pollTimer: null, createKey: "" };
  const $ = (id) => document.getElementById(id);

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[char]);
  }

  function errorText(payload, fallback = "The request could not be completed.") {
    const detail = payload?.detail ?? payload?.error;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((item) => item.msg || item.message || "Invalid input").join(" ");
    if (detail && typeof detail === "object") return detail.message || detail.error || fallback;
    return fallback;
  }

  async function api(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    if (state.key) headers.Authorization = `Bearer ${state.key}`;
    if (options.body && !headers["Content-Type"]) headers["Content-Type"] = "application/json";
    const response = await fetch(path, { ...options, headers });
    let payload = {};
    try { payload = await response.json(); } catch { /* keep the status-based fallback */ }
    if (!response.ok) throw new Error(errorText(payload, `Request failed (${response.status}).`));
    return payload;
  }

  function setMessage(target, message = "", type = "") {
    const element = $(target);
    element.textContent = message;
    element.className = `inline-message${type ? ` message-${type}` : ""}`;
  }

  function showWelcome(message = "", type = "error") {
    $("app").hidden = true;
    $("welcome").hidden = false;
    setMessage("welcome-message", message, message ? type : "");
  }

  function showKeyDialog(key) {
    state.createKey = key;
    $("issued-key").textContent = key;
    $("copy-message").textContent = "";
    $("key-dialog").hidden = false;
    $("copy-key").focus();
  }

  function setConnection(label, mode = "") {
    const element = $("connection-status");
    element.className = `connection-status${mode ? ` is-${mode}` : ""}`;
    element.lastChild.textContent = ` ${label}`;
  }

  async function createWorkspace(event) {
    event.preventDefault();
    const button = event.currentTarget.querySelector("button[type=submit]");
    const name = $("workspace-name").value.trim();
    setMessage("welcome-message");
    if (name.length < 2) {
      setMessage("welcome-message", "Enter a workspace name with at least 2 characters.", "error");
      return;
    }
    button.disabled = true;
    button.textContent = "Creating workspace…";
    try {
      const created = await api("/v1/tenants", {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      if (!created.api_key) throw new Error("The service did not return a workspace key. Please try again.");
      showKeyDialog(created.api_key);
    } catch (error) {
      setMessage("welcome-message", error.message, "error");
    } finally {
      button.disabled = false;
      button.innerHTML = 'Create workspace <span aria-hidden="true">→</span>';
    }
  }

  async function signIn(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button[type=submit]");
    const key = $("api-key").value.trim();
    if (!key) return;
    button.disabled = true;
    button.textContent = "Checking key…";
    setMessage("welcome-message");
    state.key = key;
    try {
      state.tenant = await api("/v1/me");
      
      $("api-key").value = "";
      await enterWorkspace();
    } catch (error) {
      state.key = "";
      setMessage("welcome-message", error.message, "error");
    } finally {
      button.disabled = false;
      button.textContent = "Open workspace";
    }
  }

  async function continueAfterKey() {
    if (!state.createKey) return;
    state.key = state.createKey;
    try {
      
      state.tenant = await api("/v1/me");
      $("key-dialog").hidden = true;
      state.createKey = "";
      await enterWorkspace();
    } catch (error) {
      
      state.key = "";
      state.createKey = "";
      $("key-dialog").hidden = true;
      showWelcome(`Workspace created, but the new key could not be confirmed: ${error.message} Sign in with your saved key.`, "error");
    }
  }

  async function enterWorkspace() {
    $("welcome").hidden = true;
    $("app").hidden = false;
    activatePanel("overview");
    $("tenant-name").textContent = state.tenant?.name || state.tenant?.tenant_name || "Workspace";
    const tenantId = state.tenant?.tenant_id || state.tenant?.id || "Authenticated";
    $("tenant-id").textContent = String(tenantId).length > 21 ? `${String(tenantId).slice(0, 8)}…${String(tenantId).slice(-6)}` : tenantId;
    setConnection("Workspace connected", "connected");
    await loadJobs();
    startPolling();
  }

  function signOut() {
    stopPolling();
    
    state.key = "";
    state.tenant = null;
    state.jobs = [];
    $("api-key").value = "";
    showWelcome();
  }

  function activatePanel(name) {
    const panels = ["overview", "missions", "repositories", "how-it-works", "security"];
    if (!panels.includes(name)) return;
    document.querySelectorAll(".workspace-panel").forEach((panel) => {
      const active = panel.id === `panel-${name}`;
      panel.hidden = !active;
      panel.classList.toggle("is-active", active);
    });
    document.querySelectorAll(".nav-item[data-panel]").forEach((button) => {
      const active = button.dataset.panel === name;
      button.classList.toggle("is-active", active);
      if (active) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    });
    window.scrollTo({ top: 0, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }

  function statusClass(status) {
    return `status-${["completed", "running", "queued", "failed"].includes(status) ? status : "queued"}`;
  }

  function statusLabel(job) {
    if (job.status === "running") return "Running";
    if (job.status === "queued") return "Queued";
    if (job.status === "failed") return "Failed";
    if (job.status === "completed") return "Completed";
    return job.status || "Unknown";
  }

  function formatDate(value) {
    if (!value) return "Date unavailable";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "Date unavailable" : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
  }

  function timeAgo(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
    if (seconds < 60) return "just now";
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hr ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
  }

  function repositoryName(job) {
    const result = job.result || {};
    return result.repository || job.payload?.repository_url || job.payload?.repository || "Repository analysis";
  }

  function chip(label, value) {
    return `<div class="evidence-chip"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
  }

  function resultFacts(result) {
    const fields = [
      ["Default branch", result.default_branch || "Not reported"],
      ["Files inspected", result.files ?? "Not reported"],
      ["Python files", result.python_files ?? "Not reported"],
      ["Test files", result.test_files ?? "Not reported"],
      ["Stars", result.stars ?? "Not reported"],
      ["Forks", result.forks ?? "Not reported"],
    ];
    return `<div class="result-facts">${fields.map(([label, value]) => `<div class="result-fact"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")}</div>`;
  }

  function resultPanel(job) {
    if (job.status === "failed") {
      const detail = job.result?.error || job.result?.message || "OAE could not complete this analysis. Check the repository URL and try again later.";
      return `<div class="failure-note"><strong>Analysis failed.</strong> ${escapeHtml(detail)}</div>`;
    }
    if (job.status !== "completed" || !job.result) return "";
    const result = job.result;
    const repository = result.repository || repositoryName(job);
    const summary = result.summary || "OAE recorded the repository facts below. This snapshot is not a full code review or a quality guarantee.";
    return `<div class="result-panel"><h3>${escapeHtml(repository)} · Analysis snapshot</h3><p class="mission-sub">${escapeHtml(summary)}</p>${result.repository ? resultFacts(result) : ""}<details class="mission-detail" style="margin-top:10px"><summary>View complete engineering result</summary><pre class="raw-result">${escapeHtml(JSON.stringify(result, null, 2))}</pre></details></div>`;
  }

  function rowMarkup(job, includeDetails = true) {
    const id = String(job.id || "");
    const name = repositoryName(job);
    const details = includeDetails ? resultPanel(job) : "";
    return `<article class="mission-row"><div class="mission-primary"><span class="mission-name" title="${escapeHtml(name)}">${escapeHtml(name)}</span><span class="mission-sub">${escapeHtml(String(job.operation || "analysis").replace(/^./, (c) => c.toUpperCase()))} · ${escapeHtml(id.slice(0, 8))}</span></div><span class="status-pill ${statusClass(job.status)}">${escapeHtml(statusLabel(job))}</span><time class="mission-date" datetime="${escapeHtml(job.updated_at || job.created_at || "")}">${escapeHtml(formatDate(job.created_at))}</time>${details}</article>`;
  }

  function renderLatest() {
    const latest = state.jobs[0];
    const host = $("latest-mission");
    if (!latest) {
      host.innerHTML = '<div class="empty-state compact"><span class="empty-icon" aria-hidden="true">⌁</span><strong>No missions yet</strong><p>Your first repository analysis will appear here.</p></div>';
      return;
    }
    const result = latest.result || {};
    host.innerHTML = `<div class="latest-item"><div class="latest-item-top"><strong title="${escapeHtml(repositoryName(latest))}">${escapeHtml(repositoryName(latest))}</strong><span class="status-pill ${statusClass(latest.status)}">${escapeHtml(statusLabel(latest))}</span></div><div class="latest-meta"><span>${escapeHtml(timeAgo(latest.updated_at || latest.created_at))}</span><span>Mission ${escapeHtml(String(latest.id || "").slice(0, 8))}</span></div>${latest.status === "completed" && latest.operation === "analyze" ? `<div class="evidence-preview">${chip("FILES", result.files ?? "—")}${chip("PYTHON", result.python_files ?? "—")}${chip("TEST FILES", result.test_files ?? "—")}</div>` : ""}${resultPanel(latest)}</div>`;
  }

  function renderMissionLists() {
    const all = state.jobs;
    const markup = all.length ? all.map((job) => rowMarkup(job)).join("") : '<div class="empty-state"><strong>No missions yet</strong><p>Start an analysis from Overview. Your saved history will appear here.</p><button class="button button-secondary" type="button" data-go="overview">Go to overview</button></div>';
    $("mission-list").innerHTML = markup;
    $("overview-missions").innerHTML = all.length ? all.slice(0, 4).map((job) => rowMarkup(job, false)).join("") : '<div class="empty-state compact"><strong>No activity to show</strong><p>Run an analysis to start building your history.</p></div>';
    $("mission-total").textContent = String(all.length);
    $("stat-missions").textContent = String(all.length);
    $("stat-completed").textContent = String(all.filter((job) => job.status === "completed").length);
    const count = $("mission-nav-count");
    count.textContent = String(all.length);
    count.hidden = all.length === 0;
  }

  function renderRepositories() {
    const unique = new Map();
    state.jobs.filter((job) => job.status === "completed" && job.operation === "analyze" && job.result?.repository).forEach((job) => {
      const name = job.result.repository;
      if (!unique.has(name)) unique.set(name, job);
    });
    const repositories = [...unique.values()];
    $("stat-repositories").textContent = String(repositories.length);
    if (!repositories.length) {
      $("repository-list").innerHTML = '<div class="card empty-state"><span class="empty-icon" aria-hidden="true">⑂</span><strong>No repositories analyzed yet</strong><p>Completed repository analyses will be collected here. OAE does not connect or change repositories in this beta.</p></div>';
      return;
    }
    $("repository-list").innerHTML = repositories.map((job) => {
      const result = job.result;
      return `<article class="card repository-card"><div class="repository-top"><div><h2>${escapeHtml(result.repository)}</h2><p>Default branch: ${escapeHtml(result.default_branch || "Not reported")} · Analyzed ${escapeHtml(timeAgo(result.analyzed_at || job.updated_at))}</p></div><span class="status-pill status-completed">Analyzed</span></div>${resultFacts(result)}</article>`;
    }).join("");
  }

  function renderJobs() {
    renderMissionLists();
    renderLatest();
    renderRepositories();
  }

  async function loadJobs() {
    try {
      const payload = await api("/v1/jobs?limit=100");
      state.jobs = Array.isArray(payload) ? payload : [];
      state.jobs.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
      renderJobs();
      setConnection("Workspace connected", "connected");
      return true;
    } catch (error) {
      if (/401|invalid api key|unauthorized/i.test(error.message)) {
        stopPolling();
        
        state.key = "";
        showWelcome("Your saved key is no longer valid. Sign in with an active workspace key.", "error");
      } else {
        setConnection("Connection issue", "error");
        setMessage("mission-message", `Could not refresh mission history: ${error.message}`, "error");
      }
      return false;
    }
  }

  function startPolling() {
    stopPolling();
    state.pollTimer = window.setInterval(() => { loadJobs(); }, POLL_INTERVAL);
  }

  function stopPolling() {
    if (state.pollTimer) window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }

  function normalizeRepositoryUrl(value) {
    const raw = value.trim().replace(/\.git\/?$/i, "").replace(/\/$/, "");
    let parsed;
    try { parsed = new URL(raw); } catch { throw new Error("Enter a valid GitHub repository URL, such as https://github.com/owner/repository."); }
    const parts = parsed.pathname.split("/").filter(Boolean);
    if (parsed.protocol !== "https:" || parsed.hostname.toLowerCase() !== "github.com" || parts.length !== 2 || parsed.username || parsed.password || parsed.port || parsed.search || parsed.hash) {
      throw new Error("Use a public GitHub URL in this format: https://github.com/owner/repository.");
    }
    return `https://github.com/${parts.map(encodeURIComponent).join("/")}`;
  }

  async function submitMission(event) {
    event.preventDefault();
    const button = $("analyze-button");
    let repositoryUrl;
    try { repositoryUrl = normalizeRepositoryUrl($("repository-url").value); }
    catch (error) { setMessage("mission-message", error.message, "error"); $("repository-url").focus(); return; }
    button.disabled = true;
    button.textContent = "Starting analysis…";
    setMessage("mission-message");
    try {
      const job = await api("/v1/jobs", {
        method: "POST",
        body: JSON.stringify({ operation: "analyze", payload: { repository_url: repositoryUrl } }),
      });
      setMessage("mission-message", `Analysis started. Mission ${String(job.id || "").slice(0, 8)} is now in your history.`, "success");
      $("repository-url").value = "";
      activatePanel("missions");
      await loadJobs();
      startPolling();
    } catch (error) {
      setMessage("mission-message", error.message, "error");
    } finally {
      button.disabled = false;
      button.innerHTML = 'Analyze repository <span aria-hidden="true">→</span>';
    }
  }

  async function copyKey() {
    try {
      await navigator.clipboard.writeText(state.createKey);
      $("copy-message").textContent = "Copied. Save the key somewhere secure before continuing.";
    } catch {
      const range = document.createRange();
      range.selectNodeContents($("issued-key"));
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      $("copy-message").textContent = "Select and copy the highlighted key, then save it somewhere secure.";
    }
  }

  async function boot() {
    $("create-form").addEventListener("submit", createWorkspace);
    $("signin-form").addEventListener("submit", signIn);
    $("mission-form").addEventListener("submit", submitMission);
    $("copy-key").addEventListener("click", copyKey);
    $("continue-button").addEventListener("click", continueAfterKey);
    $("signout-button").addEventListener("click", signOut);
    $("example-repository").addEventListener("click", () => {
      $("repository-url").value = "https://github.com/psf/requests";
      $("repository-url").focus();
    });
    document.addEventListener("click", (event) => {
      const panel = event.target.closest("[data-panel]");
      const go = event.target.closest("[data-go]");
      if (panel?.dataset.panel) activatePanel(panel.dataset.panel);
      if (go?.dataset.go) activatePanel(go.dataset.go);
    });
    $("key-dialog").addEventListener("click", (event) => {
      if (event.target === $("key-dialog")) event.preventDefault();
    });

    // Authentication credentials are intentionally kept only in memory.\n    // Do not persist bearer API keys in localStorage/sessionStorage.\n    showWelcome();

  document.addEventListener("DOMContentLoaded", boot);
})();
