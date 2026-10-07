(() => {
  const KEY = "oae.language";
  const SUPPORTED = {
    en: { name: "English", flag: "EN" },
    it: { name: "Italiano", flag: "IT" },
    fr: { name: "Deutsch", flag: "DE" },\n    fr: { name: "Français", flag: "FR" },\n    es: { name: "Español", flag: "ES" },\n    pt: { name: "Português", flag: "PT" },\n    ar: { name: "العربية", flag: "AR" },\n    yo: { name: "Yorùbá", flag: "YO" },\n    ha: { name: "Hausa", flag: "HA" },\n    ig: { name: "Igbo", flag: "IG" }
  };
  const translations = {
    it: {
      "ENGINEERING AGENT":"AGENTE DI INGEGNERIA","New engineering session":"Nuova sessione","RECENT SESSIONS":"SESSIONI RECENTI",
      "Governed control plane":"Piano di controllo governato","Ready":"Pronto","No repository selected":"Nessun repository selezionato",
      "What do you want me to build?":"Cosa vuoi che costruisca?","Describe the engineering objective. Add a screenshot, document, voice note, or screen recording when words are not enough.":"Descrivi l'obiettivo tecnico. Aggiungi uno screenshot, un documento, una nota vocale o una registrazione dello schermo quando le parole non bastano.",
      "Fix a bug":"Correggi un bug","Build a feature":"Costruisci una funzionalità","Review security":"Controlla la sicurezza","Implement a specification":"Implementa una specifica",
      "BUILD · from idea":"COSTRUISCI · dall'idea","PLAN · prepare changes":"PIANIFICA · prepara modifiche","EXECUTE · authorized changes":"ESEGUI · modifiche autorizzate",
      "MODE":"MODALITÀ","REPOSITORY":"REPOSITORY","WORKSPACE":"AREA DI LAVORO","Current / none":"Attuale / nessuno",
      "Describe an engineering task...":"Descrivi un'attività tecnica...","Send":"Invia","Voice input":"Input vocale",
      "Ask is read-only. Plan prepares. Execute requires an active governed authorization.":"Ask è in sola lettura. Plan prepara. Execute richiede un'autorizzazione governata attiva.",
      "Sending to OAE…":"Invio a OAE…","Ready":"Pronto","Listening…":"In ascolto…","Voice captured":"Voce acquisita",
      "I prepared an isolated engineering workspace. No repository has been changed.":"Ho preparato un'area di lavoro tecnica isolata. Nessun repository è stato modificato.",
      "Opening engineering session…":"Apertura della sessione tecnica…","Opening…":"Apertura…"
    },
    de: {
      "ENGINEERING AGENT":"ENGINEERING-AGENT","New engineering session":"Neue Engineering-Sitzung","RECENT SESSIONS":"LETZTE SITZUNGEN",
      "Governed control plane":"Kontrollierte Steuerungsebene","Ready":"Bereit","No repository selected":"Kein Repository ausgewählt",
      "What do you want me to build?":"Was soll ich für dich bauen?","Describe the engineering objective. Add a screenshot, document, voice note, or screen recording when words are not enough.":"Beschreibe das technische Ziel. Füge einen Screenshot, ein Dokument, eine Sprachnachricht oder eine Bildschirmaufnahme hinzu, wenn Worte nicht ausreichen.",
      "Fix a bug":"Fehler beheben","Build a feature":"Funktion bauen","Review security":"Sicherheit prüfen","Implement a specification":"Spezifikation umsetzen",
      "BUILD · from idea":"BAUEN · aus einer Idee","PLAN · prepare changes":"PLANEN · Änderungen vorbereiten","EXECUTE · authorized changes":"AUSFÜHREN · autorisierte Änderungen",
      "MODE":"MODUS","REPOSITORY":"REPOSITORY","WORKSPACE":"ARBEITSBEREICH","Current / none":"Aktuell / keiner",
      "Describe an engineering task...":"Beschreibe eine technische Aufgabe...","Send":"Senden","Voice input":"Spracheingabe",
      "Ask is read-only. Plan prepares. Execute requires an active governed authorization.":"Ask ist schreibgeschützt. Plan bereitet vor. Execute erfordert eine aktive kontrollierte Autorisierung.",
      "Sending to OAE…":"Wird an OAE gesendet…","Ready":"Bereit","Listening…":"Zuhören…","Voice captured":"Sprache erfasst",
      "I prepared an isolated engineering workspace. No repository has been changed.":"Ich habe einen isolierten technischen Arbeitsbereich vorbereitet. Kein Repository wurde geändert.",
      "Opening engineering session…":"Technische Sitzung wird geöffnet…","Opening…":"Öffnen…"
    }
  };

  function getLanguage() {
    const saved = localStorage.getItem(KEY);
    if (SUPPORTED[saved]) return saved;\n    const browser=(navigator.language || "en").toLowerCase();\n    const match=Object.keys(SUPPORTED).find(code => browser.startsWith(code));\n    return match || "en";
  }
  function t(value, language=getLanguage()) {
    return translations[language]?.[value] || value;
  }
  function apply(root=document) {
    const language=getLanguage();
    root.querySelectorAll("[data-i18n]").forEach(el => {
      const key=el.dataset.i18n;
      if (el.dataset.i18nAttr) el.setAttribute(el.dataset.i18nAttr, t(key, language));
      else el.textContent=t(key, language);
    });
    root.querySelectorAll("[data-i18n-placeholder]").forEach(el => el.placeholder=t(el.dataset.i18nPlaceholder, language));
    root.querySelectorAll("[data-oae-language]").forEach(el => { el.value=language; });
    document.documentElement.lang=language;
  }
  function setLanguage(language) {
    if (!SUPPORTED[language]) return;
    localStorage.setItem(KEY, language);
    apply();
    window.dispatchEvent(new CustomEvent("oae:language", { detail:{ language } }));
  }
  function selector(id="oae-language") {
    const select=document.createElement("select");
    select.id=id; select.className="oae-language-select"; select.setAttribute("aria-label","Language");
    select.dataset.oaeLanguage="1";
    Object.entries(SUPPORTED).forEach(([code,item]) => {
      const option=document.createElement("option");
      option.value=code; option.textContent=item.name; select.appendChild(option);
    });
    select.value=getLanguage();
    select.onchange=()=>setLanguage(select.value);
    return select;
  }
  window.OAEI18n={SUPPORTED,getLanguage,t,apply,setLanguage,selector};
  window.addEventListener("DOMContentLoaded",()=>apply());
})();