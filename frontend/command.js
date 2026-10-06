(() => {
  const KEY = "oae.api_key";
  const state = { conversation: null, mode: "ask", repositories: [], recognition: null, busy: false, mounted: false, pendingFiles: [] };
  const $ = (id) => document.getElementById(id);
  const esc = (v) => String(v ?? "").replace(/[&<>"]/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;" }[c]));
  const key = () => localStorage.getItem(KEY) || "";

  async function api(path, options = {}) {
    const headers = { ...(options.headers || {}), Authorization: `Bearer ${key()}` };
    const r = await fetch(path, { ...options, headers });
    let body = {};
    try { body = await r.json(); } catch {}
    if (!r.ok) throw new Error(body.detail || body.error || `Request failed (${r.status})`);
    return body;
  }

  function mount() {
    const app = $("app");
    if (!app || app.dataset.commandMounted === "1" || app.hidden) return;
    app.dataset.commandMounted = "1";
    state.mounted = true;
    const shell = document.createElement("section");
    shell.id = "oae-command-center";
    shell.innerHTML = `
      <aside class="oae-command-sidebar">
        <div class="oae-command-brand"><span class="oae-orbit">O</span><div><strong>OAE</strong><small>ENGINEERING AGENT</small></div></div>
        <button id="oae-new-session" class="oae-new-session">＋ New engineering session</button>
        <div class="oae-session-label">RECENT SESSIONS</div>
        <div id="oae-session-list" class="oae-session-list"></div>
        <div class="oae-command-sidebar-foot"><span class="oae-ready-dot"></span> Governed control plane</div>
      </aside>
      <main class="oae-command-main">
        <header class="oae-command-header">
          <div><span class="oae-status-dot"></span><span>OAE</span><span class="oae-status-text">Ready</span></div>
          <div class="oae-context-line" id="oae-context-line">No repository selected</div>
        </header>
        <section class="oae-chat-stage">
          <div id="oae-empty-state" class="oae-empty-state">
            <div class="oae-hero-mark">O</div>
            <p class="oae-kicker">OPEN AUTONOMOUS ENGINEER</p>
            <h1>What do you want me to build?</h1>
            <p>Describe the engineering objective. Add a screenshot, document, voice note, or screen recording when words are not enough.</p>
            <div class="oae-examples">
              <button data-example="Fix the authentication bug and verify the repair.">Fix a bug</button>
              <button data-example="Build a landing page for my solar business.">Build a feature</button>
              <button data-example="Review this repository for security problems.">Review security</button>
              <button data-example="Read the attached specification and implement it.">Implement a specification</button>
            </div>
          </div>
          <div id="oae-messages" class="oae-messages" aria-live="polite"></div>
        </section>
        <section class="oae-composer-wrap">
          <div class="oae-toolbar">
            <label class="oae-select"><span>MODE</span><select id="oae-mode"><option value="ask">ASK · investigate</option><option value="plan">PLAN · prepare changes</option><option value="execute">EXECUTE · authorized changes</option></select></label>
            <label class="oae-select"><span>REPOSITORY</span><select id="oae-repository"><option value="">Current / none</option></select></label>
            <label class="oae-input-mini"><span>WORKSPACE</span><input id="oae-workspace" placeholder="ready workspace id" /></label>
          </div>
          <form id="oae-composer-form" class="oae-composer">
            <button id="oae-attach" type="button" class="oae-icon-button" title="Attach document, image, audio or video">＋</button>
            <input id="oae-file" type="file" hidden accept=".pdf,.txt,.md,.docx,.png,.jpg,.jpeg,.webp,.mp4,.mp3,.wav,.m4a" multiple />
            <textarea id="oae-input" rows="1" placeholder="Describe an engineering task..."></textarea>
            <button id="oae-mic" type="button" class="oae-icon-button" title="Voice input">●</button>
            <button id="oae-send" class="oae-send" type="submit">Send <span>↗</span></button>
          </form>
          <div id="oae-pending-attachments" class="oae-pending-attachments" aria-live="polite"></div><div class="oae-composer-foot"><span>Ask is read-only. Plan prepares. Execute requires an active governed authorization.</span><span id="oae-attachment-status"></span></div>
        </section>
      </main>
    `;
    app.prepend(shell);
    document.querySelector(".workspace-layout")?.setAttribute("hidden", "");
    bind();
    bootstrap();
  }

  async function bootstrap() {
    try {
      await loadRepositories();
      await createSession();
      await loadSessions();
      if (state.conversation) {
        $("oae-attachment-status").textContent = "Ready";
      }
    } catch (e) {
      toast(e.message || "Unable to open an engineering session.");
    }
  }

  function bind() {
    $("oae-new-session").onclick = createSession;
    $("oae-composer-form").addEventListener("submit", e => { e.preventDefault(); send(); });
    $("oae-attach").onclick = () => $("oae-file").click();
    $("oae-file").onchange = uploadFiles;
    $("oae-mic").onclick = toggleVoice;
    $("oae-mode").onchange = async e => { state.mode = e.target.value; if (state.conversation) await updateContext(); };
    $("oae-repository").onchange = updateContext;
    $("oae-workspace").onchange = updateContext;
    $("oae-input").addEventListener("input", () => autoSizeInput());
    $("oae-input").addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
    });
    document.querySelectorAll("[data-example]").forEach(b => b.onclick = () => {
      $("oae-input").value = b.dataset.example;
      $("oae-input").focus();
    });
  }

  async function loadRepositories() {
    try {
      state.repositories = await api("/v1/repositories");
      $("oae-repository").innerHTML = '<option value="">Current / none</option>' +
        state.repositories.map(r => `<option value="${esc(r.id)}">${esc(r.external_id)} · ${esc(r.default_branch)}</option>`).join("");
    } catch {}
  }

  async function loadSessions() {
    await loadRepositories();
    try {
      const sessions = await api("/v1/conversations");
      $("oae-session-list").innerHTML = sessions.length
        ? sessions.map(s => `<button class="oae-session" data-id="${esc(s.id)}"><strong>${esc(s.title)}</strong><small>${esc(s.mode.toUpperCase())}</small></button>`).join("")
        : '<div class="oae-session-empty">No previous sessions.</div>';
      document.querySelectorAll(".oae-session").forEach(b => b.onclick = () => openSession(b.dataset.id));
    } catch {}
  }

  async function createSession() {
    try {
      state.mode = $("oae-mode")?.value || "ask";
      state.conversation = await api("/v1/conversations", {
        method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({ mode:state.mode, repository_id:$("oae-repository")?.value || null, workspace_id:$("oae-workspace")?.value.trim() || null })
      });
      render();
      await loadSessions();
    } catch (e) { toast(`Unable to open engineering session: ${e.message}`); throw e; }
  }

  async function openSession(id) {
    try { state.conversation = await api(`/v1/conversations/${encodeURIComponent(id)}`); state.mode=state.conversation.mode; $("oae-mode").value=state.mode; render(); } catch(e) { toast(e.message); }
  }

  async function updateContext() {
    if (!state.conversation) return;
    try {
      state.conversation = await api(`/v1/conversations/${encodeURIComponent(state.conversation.id)}`, {
        method:"PATCH", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({mode:$("oae-mode").value, repository_id:$("oae-repository").value || null, workspace_id:$("oae-workspace").value.trim() || null})
      });
      state.mode=state.conversation.mode; renderContext();
    } catch(e) { toast(e.message); }
  }

  function renderContext() {
    const c=state.conversation;
    if (!c) return;
    const repo=state.repositories.find(x=>x.id===c.repository_id);
    $("oae-context-line").textContent=(repo?.external_id || "No repository selected") + (c.workspace_id ? ` · workspace ${c.workspace_id}` : "");
    $("oae-mode").value=c.mode;
    $("oae-workspace").value=c.workspace_id || "";
    if (c.repository_id) $("oae-repository").value=c.repository_id;
  }

  function render() {
    if (!state.conversation) return;
    const messages=state.conversation.messages || [];
    $("oae-empty-state").style.display=messages.some(m=>m.role==="user") ? "none" : "flex";
    $("oae-messages").innerHTML=messages.map(m => {
      const meta=m.metadata?.objective;
      const card=meta ? `<div class="oae-objective-card"><span>${esc(meta.intent.toUpperCase())}</span><strong>${esc(meta.mode.toUpperCase())}</strong></div>` : "";
      return `<article class="oae-message ${m.role==="user"?"user":"assistant"}"><div class="oae-message-role">${m.role==="user"?"YOU":"OAE"}</div><div class="oae-message-body">${esc(m.content).replace(/\n/g,"<br>")}${card}</div></article>`;
    }).join("");
    $("oae-messages").scrollTop=$("oae-messages").scrollHeight;
    renderContext();
  }

  function autoSizeInput() {
    const input = $("oae-input");
    if (!input) return;
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 150) + "px";
  }

  function setComposerBusy(busy, label = "Send") {
    state.busy = busy;
    const button = $("oae-send");
    if (!button) return;
    button.disabled = busy;
    button.setAttribute("aria-busy", busy ? "true" : "false");
    button.innerHTML = busy ? `Sending…` : `${esc(label)} <span aria-hidden="true">↗</span>`;
  }

  async function send() {
    const input=$("oae-input"), content=input?.value.trim();
    if ((!content && !state.pendingFiles.length) || state.busy) return;
    if (!state.conversation) {
      setComposerBusy(true, "Opening…");
      $("oae-attachment-status").textContent = "Opening engineering session…";
      try {
        await createSession();
      } catch (e) {
        $("oae-attachment-status").textContent = `Send failed: ${e.message}`;
        setComposerBusy(false);
        return;
      }
      setComposerBusy(false);
    }
    if (!state.conversation) return;
    setComposerBusy(true);
    $("oae-attachment-status").textContent = "Sending to OAE…";
    try {
      if (state.pendingFiles.length) {
        const files = [...state.pendingFiles];
        for (const file of files) {
          const form = new FormData();
          form.append("file", file, file.name);
          state.conversation = await api(`/v1/conversations/${state.conversation.id}/attachments`, { method:"POST", body:form });
        }
        state.pendingFiles = [];
        renderPendingAttachments();
      }
      if (!content) {
        input.value = "";
        render();
        await loadSessions();
        return;
      }
      state.conversation=await api(`/v1/conversations/${state.conversation.id}/messages`, {
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({content,mode:$("oae-mode").value})
      });
      input.value=""; input.style.height="auto"; render();
      if ($("oae-mode").value==="execute") {
        const auth=prompt("EXECUTE mode requires an active worker authorization ID. Enter the authorization ID, or Cancel to keep this objective planned.");
        if (auth) await execute(auth);
      }
      await loadSessions();
    } catch(e) { toast(e.message); $("oae-attachment-status").textContent = `Send failed: ${e.message}`; } finally { setComposerBusy(false); }
  }

  async function execute(auth) {
    try {
      const result=await api(`/v1/conversations/${state.conversation.id}/execute`, {
        method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({authorization_id:auth})
      });
      appendLive("Execution queued. OAE is handing the objective to the governed engineering pipeline.", {job_id:result.job_id});
    } catch(e) { appendLive(`Execution blocked: ${e.message}`); }
  }

  function uploadFiles() {
    const files=[...$("oae-file").files];
    if (!files.length) return;
    const total = [...state.pendingFiles, ...files];
    if (total.length > 10) {
      toast("You can attach up to 10 files per send.");
      $("oae-file").value="";
      return;
    }
    const oversized = files.find(file => file.size > 12 * 1024 * 1024);
    if (oversized) {
      toast(`${oversized.name} exceeds the 12 MB limit.`);
      $("oae-file").value="";
      return;
    }
    state.pendingFiles.push(...files);
    renderPendingAttachments();
    $("oae-file").value="";
  }

  function renderPendingAttachments() {
    const wrap=$("oae-pending-attachments");
    if (!wrap) return;
    wrap.innerHTML = state.pendingFiles.length
      ? state.pendingFiles.map((file,index) => `<span class="oae-attachment-chip"><span>${esc(file.name)}</span><button type="button" data-remove-attachment="${index}" aria-label="Remove ${esc(file.name)}">×</button></span>`).join("")
      : "";
    wrap.querySelectorAll("[data-remove-attachment]").forEach(button => {
      button.onclick=()=> {
        state.pendingFiles.splice(Number(button.dataset.removeAttachment),1);
        renderPendingAttachments();
      };
    });
    $("oae-attachment-status").textContent = state.pendingFiles.length
      ? `${state.pendingFiles.length} attachment${state.pendingFiles.length === 1 ? "" : "s"} ready to send`
      : "";
  }

  function toggleVoice() {
    const SR=window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { toast("Voice input is not supported by this browser."); return; }
    if (state.recognition) { state.recognition.stop(); return; }
    const r=new SR(); r.lang=navigator.language || "en-NG"; r.interimResults=true;
    r.onstart=()=>{ state.recognition=r; $("oae-mic").classList.add("recording"); $("oae-attachment-status").textContent="Listening…"; };
    r.onresult=e=>{ $("oae-input").value=[...e.results].map(x=>x[0].transcript).join(""); };
    r.onend=()=>{ state.recognition=null; $("oae-mic").classList.remove("recording"); $("oae-attachment-status").textContent="Voice captured"; };
    r.onerror=()=>{ state.recognition=null; $("oae-mic").classList.remove("recording"); };
    r.start();
  }

  function appendLive(text, meta={}) {
    const el=document.createElement("article"); el.className="oae-message assistant";
    el.innerHTML=`<div class="oae-message-role">OAE</div><div class="oae-message-body">${esc(text)}${meta.job_id ? `<div class="oae-run-card"><span>MISSION QUEUED</span><code>${esc(meta.job_id)}</code></div>` : ""}</div>`;
    $("oae-messages").appendChild(el); $("oae-messages").scrollTop=$("oae-messages").scrollHeight;
  }

  function toast(message) {
    const t=$("toast"); if (t) { t.hidden=false; t.textContent=message; setTimeout(()=>t.hidden=true,3500); }
  }

  const boot=setInterval(()=>{ if ($("app") && !$("app").hidden && !state.mounted) mount(); if (state.mounted) clearInterval(boot); },250);
  window.addEventListener("storage",()=>{ if ($("app") && !$("app").hidden && !state.mounted) mount(); });
})();