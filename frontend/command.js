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
            <label class="oae-select"><span>MODE</span><select id="oae-mode"><option value="ask">BUILD · from idea</option><option value="plan">PLAN · prepare changes</option><option value="execute">EXECUTE · authorized changes</option></select></label>
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

  async function bootstrap() {
    try {
      await loadRepositories();
      await createSession();
      await loadSessions();
      if (state.conversation) $("oae-attachment-status").textContent = "Ready";
    } catch (e) {
      toast(e.message || "Unable to open an engineering session.");
    }
  }

  async function loadSessions() {

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
    } catch (e) {
      state.conversation = null;
      $("oae-attachment-status").textContent = `Unable to open engineering session: ${e.message}`;
      throw e;
    }
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
      const card=meta ? `<div class="oae-objective-card"><span>${esc(String(meta.intent || "engineering_task").toUpperCase())}</span><strong>${esc(String(meta.mode || m.mode || "ask").toUpperCase())}</strong></div>` : "";
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
      try { await createSession(); } catch (e) {
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
      const wantsToBuild = /\b(build|create|make|develop|launch)\b/i.test(content);
      if (wantsToBuild) {
        const product = await api("/v1/product/brief", {
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body:JSON.stringify({idea:content,context:(state.conversation.messages||[]).filter(m=>m.role==="user"||m.role==="assistant").slice(-8).map(m=>({role:m.role,content:m.content}))})
        });
        appendProductBrief(product.brief);
        if (!state.conversation.workspace_id) {
          const workspace = await api(`/v1/conversations/${state.conversation.id}/greenfield-workspace`, {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
              product_name: product.brief.product_name || "New OAE Product",
              description: product.brief.problem || content
            })
          });
          state.conversation.workspace_id = workspace.workspace_id;
          appendLive("I prepared an isolated engineering workspace. No repository has been changed.");
        }
      }
      const modelReply = await requestModelResponse();
      if (modelReply) appendLive(modelReply, {model:true});

      input.value=""; input.style.height="auto"; render();
      const mode=$("oae-mode").value;
      if (mode==="plan") {
        const planned=await api(`/v1/conversations/${state.conversation.id}/plan`, {
          method:"POST", headers:{"Content-Type":"application/json"},
          body:JSON.stringify({repository_kind:"unknown",has_tests:true,has_linter:true})
        });
        appendPlan(planned.plan, planned.repository_context);
      } else if (mode==="execute") {
        const gate=await api(`/v1/conversations/${state.conversation.id}/authorization`, {
          method:"POST", headers:{"Content-Type":"application/json"},
          body:JSON.stringify({expires_in_seconds:3600})
        });
        appendLive("Execution approval requested. A separate authorized approver must approve this operation before OAE can mutate the workspace.", {
          authorization_id:gate.authorization_id, status:"pending approval"
        });
        watchAuthorization(gate.authorization_id);
      }
      await loadSessions();
    } catch(e) { toast(e.message); $("oae-attachment-status").textContent = `Send failed: ${e.message}`; } finally { setComposerBusy(false); if (!$("oae-attachment-status").textContent.startsWith("Send failed")) $("oae-attachment-status").textContent = "Ready"; }
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

  async function watchAuthorization(authorizationId) {
    for (let attempt=0; attempt<40; attempt++) {
      await new Promise(resolve => setTimeout(resolve, 3000));
      try {
        const result=await api(`/v1/conversations/${state.conversation.id}/authorization`);
        const auth=result.authorization;
        if (auth?.id===authorizationId && auth.status==="approved") {
          appendLive("Execution approved. OAE can now start the governed engineering run.", {
            authorization_id:authorizationId, status:"approved",
            action:`<button type="button" class="oae-run-action" data-run-auth="${esc(authorizationId)}">Start governed run</button>`
          });
          document.querySelector("[data-run-auth]")?.addEventListener("click", e => {
            e.currentTarget.disabled=true;
            executeApproved(authorizationId);
          });
          return;
        }
        if (auth?.id===authorizationId && ["rejected","revoked"].includes(auth.status)) {
          appendLive(`Execution approval ${esc(auth.status)}. No mutation was started.`);
          return;
        }
      } catch {}
    }
  }

  async function executeApproved(authorizationId) {
    try {
      const result=await api(`/v1/conversations/${state.conversation.id}/execute`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({authorization_id:authorizationId})
      });
      appendLive("Governed engineering run started. OAE will verify and repair within the approved pipeline.", {
        run_id:result.run_id, status:result.status
      });
      watchRun(result.run_id);
    } catch(e) {
      appendLive(`Execution blocked: ${e.message}`);
    }
  }

  async function watchRun(runId) {
    for (let attempt=0; attempt<120; attempt++) {
      await new Promise(resolve => setTimeout(resolve, 3000));
      try {
        const run=await api(`/v1/conversations/${state.conversation.id}/runs/${runId}`);
        if (["completed","failed","blocked"].includes(run.status)) {
          appendLive(`Engineering run ${run.status}. Completed steps: ${run.completed_steps.length}.`, {run_id:runId, status:run.status});
          return;
        }
      } catch {}
    }
  }

  async function requestModelResponse() {
    try {
      const messages = (state.conversation?.messages || [])
        .filter(m => m.role === "user" || m.role === "assistant")
        .slice(-12)
        .map(m => ({ role:m.role, content:m.content }));
      const result = await Promise.race([
        api("/v1/ai/respond", {
          method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
          messages,
          system:"You are OAE, a technical co-founder for people who may have never coded. Explain software decisions in plain language, ask only essential questions, turn vague ideas into concrete product requirements, and never claim that code was built, tested, deployed, or changed unless OAE has actual evidence. Repository mutation and consequential actions are handled only by OAE's governed execution pipeline."
        })
      }),
        new Promise((_, reject) => setTimeout(() => reject(new Error("model timeout")), 12000))
      ]);
      return result.response || "";
    } catch (e) {
      return "";
    }
  }

  function appendProductBrief(brief) {
    const missing=(brief.missing||[]).map(x=>`<li>${esc(x)}</li>`).join("");
    const workflows=(brief.core_workflows||[]).map(x=>`<li>${esc(x)}</li>`).join("");
    appendLive("I turned your idea into a product brief. I will not start coding until the missing decisions are clear.", {
      html:`<div class="oae-plan-card"><span>PRODUCT BRIEF</span><strong>${esc(brief.product_name||"New product")}</strong><p>${esc(brief.problem||"")}</p><small><b>Users</b>: ${esc((brief.users||[]).join(", "))}</small><small><b>Workflows</b></small><ol>${workflows}</ol><small><b>Missing before build</b></small><ol>${missing||"<li>None</li>"}</ol></div>`
    });
  }

  function appendPlan(plan, repositoryContext = null) {
    const steps=(plan.steps||[]).map(step => `<li><strong>${esc(step.id)}</strong> · ${esc(step.purpose)} <span class="oae-risk">${esc(step.risk)}</span></li>`).join("");
    const context = repositoryContext?.selected ? `<div class="oae-plan-context"><span>REPOSITORY CONTEXT</span><strong>${esc(repositoryContext.external_id)}</strong><small>${esc(repositoryContext.provider)} · ${esc(repositoryContext.default_branch)} · ${esc(repositoryContext.status)}</small></div>` : `<div class="oae-plan-context"><span>REPOSITORY CONTEXT</span><strong>No repository selected</strong><small>Plan is bounded to the supplied engineering objective.</small></div>`;
    appendLive("Engineering plan ready. No repository mutation was performed.", {plan:true, html:`<div class="oae-plan-card"><span>PLAN ${esc(plan.version)}</span><strong>${esc(plan.objective)}</strong>${context}<ol>${steps}</ol></div>`});
  }

  function appendLive(text, meta={}) {
    const el=document.createElement("article"); el.className="oae-message assistant";
    el.innerHTML=`<div class="oae-message-role">OAE</div><div class="oae-message-body">${esc(text)}${meta.job_id ? `<div class="oae-run-card"><span>MISSION QUEUED</span><code>${esc(meta.job_id)}</code></div>` : ""}${meta.authorization_id ? `<div class="oae-run-card"><span>APPROVAL</span><code>${esc(meta.authorization_id)}</code><small>${esc(meta.status||"pending")}</small>${meta.action||""}</div>` : ""}${meta.run_id ? `<div class="oae-run-card"><span>ENGINEERING RUN</span><code>${esc(meta.run_id)}</code><small>${esc(meta.status||"running")}</small></div>` : ""}${meta.html||""}</div>`;
    $("oae-messages").appendChild(el); $("oae-messages").scrollTop=$("oae-messages").scrollHeight;
  }

  function toast(message) {
    const t=$("toast"); if (t) { t.hidden=false; t.textContent=message; setTimeout(()=>t.hidden=true,3500); }
  }

  const boot=setInterval(()=>{ if ($("app") && !$("app").hidden && !state.mounted) mount(); if (state.mounted) clearInterval(boot); },250);
  window.addEventListener("storage",()=>{ if ($("app") && !$("app").hidden && !state.mounted) mount(); });
})();