from fastapi.responses import HTMLResponse


LANDING_PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OAE — Autonomous Engineering</title>
<style>
:root{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#e8edf5;background:#0b1020}*{box-sizing:border-box}body{margin:0}a{color:inherit}.wrap{max-width:1040px;margin:auto;padding:24px}.nav{display:flex;justify-content:space-between;align-items:center}.brand{font-weight:800;font-size:20px}.pill{border:1px solid #2b3650;border-radius:999px;padding:8px 13px;font-size:13px}.hero{padding:86px 0 56px;max-width:760px}.eyebrow{color:#8fb7ff;font-weight:700;letter-spacing:.08em;text-transform:uppercase;font-size:12px}.hero h1{font-size:clamp(42px,7vw,76px);line-height:.98;margin:14px 0}.hero p{font-size:19px;line-height:1.6;color:#aeb8c9}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card{background:#11182a;border:1px solid #202b42;border-radius:18px;padding:20px}.card h3{margin-top:0}.muted{color:#8f9bb0}.cta{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}.button{border:0;border-radius:12px;padding:13px 18px;font-weight:700;cursor:pointer;background:#6ea2ff;color:#07101f}.button.secondary{background:#172137;color:#e8edf5;border:1px solid #2b3650}.panel{display:none;max-width:560px;background:#11182a;border:1px solid #202b42;border-radius:18px;padding:24px;margin:20px 0}.panel.active{display:block}input,textarea{width:100%;background:#0b1020;color:#e8edf5;border:1px solid #2b3650;border-radius:10px;padding:12px;margin:7px 0 14px}label{font-size:13px;color:#aeb8c9}.result{white-space:pre-wrap;background:#080d18;border-radius:12px;padding:14px;overflow:auto}.status{margin:12px 0;color:#9fb0c9}@media(max-width:700px){.grid{grid-template-columns:1fr}.hero{padding-top:54px}}
</style>
</head>
<body>
<div class="wrap">
<nav class="nav"><div class="brand">OAE</div><div class="pill">SaaS Beta</div></nav>
<section class="hero">
<div class="eyebrow">Open Autonomous Engineer</div>
<h1>Understand your repository before you change it.</h1>
<p>OAE analyzes public GitHub repositories, turns findings into structured engineering work, and keeps sensitive execution behind explicit security controls.</p>
<div class="cta"><button class="button" onclick="show('signup')">Start testing</button><button class="button secondary" onclick="show('login')">Developer login</button></div>
</section>
<div class="grid"><div class="card"><h3>Analyze</h3><p class="muted">Get repository structure, Python coverage, tests, configuration and GitHub metadata.</p></div><div class="card"><h3>Review</h3><p class="muted">Turn engineering findings into a structured review without modifying the repository.</p></div><div class="card"><h3>Verify</h3><p class="muted">Record verification checks and keep the engineering result explicit.</p></div></div>
<section id="signup" class="panel"><h2>Create your developer workspace</h2><p class="muted">No payment required for the beta. Your API key is shown once.</p><label>Workspace name</label><input id="signupName" placeholder="Acme Engineering"><button class="button" onclick="signup()">Create workspace</button><div id="signupStatus" class="status"></div></section>
<section id="login" class="panel"><h2>Developer login</h2><p class="muted">Paste the API key issued when your workspace was created.</p><label>API key</label><input id="loginKey" placeholder="oae_..."><button class="button" onclick="login()">Continue</button><div id="loginStatus" class="status"></div></section>
<section id="dashboard" class="panel"><h2>Engineering workspace</h2><div id="me" class="status"></div><label>Public GitHub repository</label><input id="repo" value="https://github.com/Olori24/oae-core"><button class="button" onclick="analyze()">Analyze repository</button><button class="button secondary" onclick="logout()">Log out</button><div id="jobStatus" class="status"></div><pre id="result" class="result"></pre></section>
</div>
<script>
const api=location.origin;const key=()=>sessionStorage.getItem('oae_key');
function show(id){document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');window.scrollTo({top:document.getElementById(id).offsetTop-20,behavior:'smooth'})}
async function signup(){const name=document.getElementById('signupName').value.trim();if(!name)return set('signupStatus','Enter a workspace name.');const r=await fetch(api+'/v1/tenants',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});const d=await r.json();if(!r.ok)return set('signupStatus',d.detail||'Could not create workspace.');sessionStorage.setItem('oae_key',d.api_key);alert('Save this API key now:\n\n'+d.api_key+'\n\nIt will not be shown again.');show('dashboard');loadMe()}
async function login(){const k=document.getElementById('loginKey').value.trim();if(!k)return set('loginStatus','Enter your API key.');sessionStorage.setItem('oae_key',k);const ok=await loadMe();if(ok)show('dashboard');else sessionStorage.removeItem('oae_key')}
async function loadMe(){const r=await fetch(api+'/v1/me',{headers:{Authorization:'Bearer '+key()}});const d=await r.json();if(!r.ok){set('loginStatus',d.detail||'Invalid API key.');return false}document.getElementById('me').textContent='Workspace: '+d.name+' · '+d.tenant_id;return true}
async function analyze(){const repo=document.getElementById('repo').value.trim();set('jobStatus','Queueing analysis…');const r=await fetch(api+'/v1/jobs',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+key()},body:JSON.stringify({operation:'analyze',payload:{repository_url:repo}})});const d=await r.json();if(!r.ok)return set('jobStatus',d.detail||'Could not queue analysis.');set('jobStatus','Job '+d.id+' queued.');for(let i=0;i<20;i++){await new Promise(x=>setTimeout(x,700));const q=await fetch(api+'/v1/jobs/'+d.id,{headers:{Authorization:'Bearer '+key()}});const j=await q.json();if(j.status==='completed'||j.status==='failed'){set('jobStatus','Job '+j.status+'.');document.getElementById('result').textContent=JSON.stringify(j.result,null,2);return}}set('jobStatus','Analysis is still running. Refresh the dashboard to check it.')}function logout(){sessionStorage.removeItem('oae_key');show('login')}function set(id,text){document.getElementById(id).textContent=text}if(key())loadMe().then(ok=>{if(ok)show('dashboard')});
</script>
</body></html>
"""


def page() -> HTMLResponse:
    return HTMLResponse(LANDING_PAGE)
"