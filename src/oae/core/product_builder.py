"""Non-coder product discovery and build-readiness logic for OAE."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from oae.core.ai_gateway import AIGatewayUnavailable, generate_engineering_response

@dataclass(frozen=True)
class ProductBrief:
    product_name: str
    problem: str
    users: list[str]
    core_workflows: list[str]
    screens: list[str]
    entities: list[str]
    auth: str
    integrations: list[str]
    payments: bool
    notifications: bool
    deployment: str
    build_ready: bool
    missing: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

_REQUIRED = ("problem", "users", "core_workflows", "deployment")

def _fallback(text: str, language: str = "en") -> ProductBrief:
    lower = text.lower()
    product_name = "New product"
    for marker in ("called ", "named "):
        if marker in lower:
            tail = text[lower.index(marker) + len(marker):].strip(" .")
            product_name = tail[:60] or product_name
            break
    users = ["Product owner"]
    if "school" in lower or "student" in lower:
        users = ["School administrators", "Teachers", "Parents", "Students"]
    elif "clinic" in lower or "patient" in lower:
        users = ["Clinic administrators", "Clinicians", "Patients"]
    workflows = ["User onboarding", "Core product workflow", "Administration"]
    if "payment" in lower or "fee" in lower or "pay" in lower:
        workflows.append("Payments and transaction tracking")
    screens = ["Sign in / onboarding", "Dashboard", "Core workflow", "Settings"]
    entities = ["User", "Organization", "Activity"]
    if "school" in lower or "student" in lower:
        entities += ["Student", "Teacher", "Attendance", "Result", "Fee"]
    if "clinic" in lower or "patient" in lower:
        entities += ["Patient", "Appointment", "Clinical record"]
    missing = ["exact target users", "must-have workflow", "deployment preference"]
    if "school" in lower or "clinic" in lower:
        missing = ["exact MVP scope", "deployment preference"]
    labels = {
        "it": {
            "users": ["Amministratori", "Insegnanti", "Genitori", "Studenti"],
            "workflows": ["Onboarding utenti", "Flusso principale del prodotto", "Amministrazione"],
            "screens": ["Accesso / onboarding", "Dashboard", "Flusso principale", "Impostazioni"],
            "entities": ["Utente", "Organizzazione", "Attività"],
            "auth": "Email/password o SSO dell'organizzazione, da confermare",
            "deployment": "Applicazione web, destinazione da confermare",
            "missing": ["utenti target esatti", "flusso obbligatorio", "preferenza di deployment"],
        },
        "de": {
            "users": ["Administratoren", "Lehrkräfte", "Eltern", "Schüler"],
            "workflows": ["Benutzer-Onboarding", "Kernprozess des Produkts", "Administration"],
            "screens": ["Anmeldung / Onboarding", "Dashboard", "Kernprozess", "Einstellungen"],
            "entities": ["Benutzer", "Organisation", "Aktivität"],
            "auth": "E-Mail/Passwort oder Organisations-SSO, noch zu bestätigen",
            "deployment": "Webanwendung, Zielumgebung noch zu bestätigen",
            "missing": ["genauer Zielnutzerkreis", "verbindlicher Kernprozess", "Deployment-Präferenz"],
        },
    }.get(language, {})
    users = labels.get("users", users)
    workflows = labels.get("workflows", workflows)
    screens = labels.get("screens", screens)
    entities = labels.get("entities", entities)
    auth = labels.get("auth", "Email/password or organization SSO, to be confirmed")
    deployment = labels.get("deployment", "Web application, deployment target to be confirmed")
    missing = labels.get("missing", missing)
    return ProductBrief(
        product_name=product_name,
        problem=text.strip(),
        users=users,
        core_workflows=workflows,
        screens=screens,
        entities=list(dict.fromkeys(entities)),
        auth=auth,
        integrations=[],
        payments=("payment" in lower or "fee" in lower or "pay" in lower),
        notifications=("notification" in lower or "alert" in lower or "sms" in lower),
        deployment=deployment,
        build_ready=False,
        missing=missing,
    )

def build_product_brief(text: str, context: list[dict[str, str]] | None = None, language: str = "en") -> dict[str, Any]:
    prompt = """Return ONLY valid JSON for a software product brief.
Schema:
{"product_name":str,"problem":str,"users":[str],"core_workflows":[str],"screens":[str],"entities":[str],"auth":str,"integrations":[str],"payments":bool,"notifications":bool,"deployment":str,"build_ready":bool,"missing":[str]}
Rules: infer conservatively; missing means information genuinely needed before autonomous implementation. Never claim implementation, testing, deployment, or repository changes. A non-coder should understand the result. Respond entirely in the requested language. Requested language: {language}. Keep technical identifiers and code terms stable where appropriate.
"""
    messages = [{"role":"user","content":text}]
    if context:
        messages = context[-8:] + messages
    try:
        raw = generate_engineering_response(messages=messages, system=prompt)
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("brief must be an object")
        fallback = _fallback(text, language)
        for key, value in fallback.to_dict().items():
            data.setdefault(key, value)
        return data
    except (AIGatewayUnavailable, ValueError, json.JSONDecodeError):
        return _fallback(text, language).to_dict()
