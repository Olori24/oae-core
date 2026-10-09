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
        "fr": {
            "users": ["Administrateurs", "Équipe", "Clients", "Utilisateurs"],
            "workflows": ["Inscription", "Parcours principal", "Administration"],
            "screens": ["Connexion / inscription", "Tableau de bord", "Parcours principal", "Paramètres"],
            "entities": ["Utilisateur", "Organisation", "Activité"],
            "auth": "E-mail/mot de passe ou SSO d’organisation, à confirmer",
            "deployment": "Application web, destination à confirmer",
            "missing": ["utilisateurs cibles précis", "parcours essentiel", "préférence de déploiement"],
        },
        "es": {
            "users": ["Administradores", "Equipo", "Clientes", "Usuarios"],
            "workflows": ["Registro de usuarios", "Flujo principal", "Administración"],
            "screens": ["Acceso / registro", "Panel", "Flujo principal", "Configuración"],
            "entities": ["Usuario", "Organización", "Actividad"],
            "auth": "Correo/contraseña o SSO de la organización, por confirmar",
            "deployment": "Aplicación web, destino por confirmar",
            "missing": ["usuarios objetivo exactos", "flujo imprescindible", "preferencia de despliegue"],
        },
        "pt": {
            "users": ["Administradores", "Equipa", "Clientes", "Utilizadores"],
            "workflows": ["Registo de utilizadores", "Fluxo principal", "Administração"],
            "screens": ["Entrada / registo", "Painel", "Fluxo principal", "Definições"],
            "entities": ["Utilizador", "Organização", "Atividade"],
            "auth": "E-mail/palavra-passe ou SSO da organização, por confirmar",
            "deployment": "Aplicação web, destino por confirmar",
            "missing": ["utilizadores-alvo exatos", "fluxo obrigatório", "preferência de implementação"],
        },
        "ar": {
            "users": ["المسؤولون", "الفريق", "العملاء", "المستخدمون"],
            "workflows": ["تسجيل المستخدم", "مسار العمل الأساسي", "الإدارة"],
            "screens": ["تسجيل الدخول", "لوحة التحكم", "مسار العمل", "الإعدادات"],
            "entities": ["المستخدم", "المؤسسة", "النشاط"],
            "auth": "البريد الإلكتروني وكلمة المرور أو دخول المؤسسة الموحد، يحتاج إلى تأكيد",
            "deployment": "تطبيق ويب، وجهة النشر تحتاج إلى تأكيد",
            "missing": ["المستخدمون المستهدفون بدقة", "مسار العمل الأساسي", "تفضيل النشر"],
        },
        "yo": {
            "users": ["Àwọn olùṣàkóso", "Ẹgbẹ́ iṣẹ́", "Oníbàárà", "Àwọn olùlò"],
            "workflows": ["Ìforúkọsílẹ̀ olùlò", "Ìlànà iṣẹ́ pàtàkì", "Ìṣàkóso"],
            "screens": ["Wọlé / forúkọsílẹ̀", "Pánẹ́ẹ̀lì", "Ìlànà iṣẹ́", "Ètò"],
            "entities": ["Olùlò", "Àjọ", "Ìṣe"],
            "auth": "Í-meèlì/ọ̀rọ̀ aṣínà tàbí SSO àjọ, a nílò ìmúdájú",
            "deployment": "Ohun èlò wẹ́ẹ̀bù, ibi fífi sílẹ̀ ṣì nílò ìmúdájú",
            "missing": ["àwọn olùlò tí a fẹ́ dé sí", "ìlànà pàtàkì", "àṣàyàn ibi fífi sílẹ̀"],
        },
        "ha": {
            "users": ["Masu gudanarwa", "Ƙungiya", "Abokan ciniki", "Masu amfani"],
            "workflows": ["Rajistar mai amfani", "Babban tsarin aiki", "Gudanarwa"],
            "screens": ["Shiga / rajista", "Allon bayanai", "Babban aiki", "Saituna"],
            "entities": ["Mai amfani", "Ƙungiya", "Aiki"],
            "auth": "Imel/kalmar sirri ko SSO na ƙungiya, sai an tabbatar",
            "deployment": "Manhajar yanar gizo, sai an tabbatar da inda za a ɗora ta",
            "missing": ["ainihin masu amfani da aka nufa", "babban aikin dole", "zaɓin ɗora manhaja"],
        },
        "ig": {
            "users": ["Ndị nchịkwa", "Otu ọrụ", "Ndị ahịa", "Ndị ọrụ"],
            "workflows": ["Ndebanye aha onye ọrụ", "Usoro ọrụ bụ isi", "Nlekọta"],
            "screens": ["Banye / debanye aha", "Dashboard", "Usoro ọrụ", "Ntọala"],
            "entities": ["Onye ọrụ", "Ụlọ ọrụ", "Omume"],
            "auth": "Email/okwuntughe ma ọ bụ SSO ụlọ ọrụ, a ga-akwado",
            "deployment": "Ngwa weebụ, a ga-akwado ebe a ga-etinye ya",
            "missing": ["ndị ọrụ a chọrọ iru", "usoro ọrụ dị mkpa", "nhọrọ ebe ntinye"],
        },
    }.get(language, {})
    users = list(labels["users"]) if "users" in labels else users
    workflows = list(labels["workflows"]) if "workflows" in labels else workflows
    screens = list(labels["screens"]) if "screens" in labels else screens
    entities = list(labels["entities"]) if "entities" in labels else entities
    auth = str(labels.get("auth", "Email/password or organization SSO, to be confirmed"))
    deployment = str(labels.get("deployment", "Web application, deployment target to be confirmed"))
    missing = list(labels["missing"]) if "missing" in labels else missing
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
Rules: infer conservatively; missing means information genuinely needed before autonomous implementation. Never claim implementation, testing, deployment, or repository changes. A non-coder should understand the result. Respond entirely in the requested language. Requested language: """ + language + """. Keep technical identifiers and code terms stable where appropriate.
"""
    messages = [{"role":"user","content":text}]
    if context:
        messages = context[-8:] + messages
    try:
        raw = generate_engineering_response(messages=messages, system=prompt, language=language)
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("brief must be an object")
        fallback = _fallback(text, language)
        for key, value in fallback.to_dict().items():
            data.setdefault(key, value)
        return data
    except (AIGatewayUnavailable, ValueError, json.JSONDecodeError):
        return _fallback(text, language).to_dict()
